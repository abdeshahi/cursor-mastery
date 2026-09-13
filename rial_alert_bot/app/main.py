from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from app.bot.handlers import build_router
from app.config import get_settings
from app.runtime_state import RuntimeState
from app.jobs.digest import send_scheduled_digest
from app.jobs.poll_news import poll_news_once
from app.services.alert_engine import AlertEngine
from app.storage.db import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv()
    settings = get_settings()
    runtime = RuntimeState(jobs_paused=settings.jobs_paused)
    logging.getLogger().setLevel(settings.log_level.upper())

    db = Database(settings.database_path)
    await db.connect()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    alert_engine = AlertEngine(bot, db, settings)
    dp.include_router(build_router(settings, db, alert_engine, runtime))

    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    async def _poll_job() -> None:
        try:
            await poll_news_once(bot=bot, db=db, settings=settings, alert_engine=alert_engine, runtime=runtime)
        except Exception as error:  # noqa: BLE001
            logger.exception('Poll job crashed: %s', error)

    async def _digest_job() -> None:
        try:
            await send_scheduled_digest(bot=bot, db=db, settings=settings, alert_engine=alert_engine, runtime=runtime)
        except Exception as error:  # noqa: BLE001
            logger.exception('Digest job crashed: %s', error)

    scheduler.add_job(_poll_job, IntervalTrigger(seconds=settings.poll_seconds), id='poll_news', max_instances=1)
    scheduler.add_job(_digest_job, CronTrigger(hour=8, minute=30), id='digest_morning', max_instances=1)
    scheduler.add_job(_digest_job, CronTrigger(hour=21, minute=0), id='digest_night', max_instances=1)
    scheduler.start()

    logger.info('Rial alert bot started')
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await db.close()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
