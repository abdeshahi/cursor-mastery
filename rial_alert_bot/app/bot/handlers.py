from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.formatters import format_status
from app.bot.keyboards import main_keyboard
from app.config import Settings, get_settings
from app.runtime_state import RuntimeState
from app.services.alert_engine import AlertEngine
from app.services.rate_provider import get_free_market_usd_rate
from app.storage.db import Database

logger = logging.getLogger(__name__)


def build_router(settings: Settings, db: Database, alert_engine: AlertEngine, runtime: RuntimeState) -> Router:
    router = Router()

    def _is_admin(user_id: int) -> bool:
        return user_id in settings.admin_ids

    @router.message(Command('start'))
    async def cmd_start(message: Message) -> None:
        await db.upsert_user(message.from_user.id, alerts_enabled=True)
        text = (
            '👋 به ربات هشدار فاندامنتال ریال خوش آمدید.\n\n'
            'این ربات اخبار اقتصادی/سیاسی/تحریمی/نفتی را تحلیل می‌کند و '
            'جهت فشار احتمالی روی بازار آزاد دلار را اعلام می‌کند.\n\n'
            '⚠️ هشدارها قطعی نیستند و جایگزین تصمیم حرفه‌ای نیستند.\n\n'
            'دستورات: /on /off /status /digest /sources /help'
        )
        await message.answer(text, reply_markup=main_keyboard)

    @router.message(Command('help'))
    async def cmd_help(message: Message) -> None:
        await message.answer(
            '📚 راهنما\n'
            '/on روشن کردن هشدار\n'
            '/off خاموش کردن هشدار\n'
            '/status وضعیت و آخرین تحلیل\n'
            '/digest خلاصه فوری\n'
            '/sources لیست منابع'
        )

    @router.message(Command('on'))
    async def cmd_on(message: Message) -> None:
        await db.upsert_user(message.from_user.id, alerts_enabled=True)
        await message.answer('✅ هشدارها فعال شد.')

    @router.message(Command('off'))
    async def cmd_off(message: Message) -> None:
        await db.upsert_user(message.from_user.id, alerts_enabled=True)
        await db.set_user_alerts(message.from_user.id, False)
        await message.answer('🔕 هشدارها غیرفعال شد.')

    @router.message(Command('status'))
    async def cmd_status(message: Message) -> None:
        rate = await get_free_market_usd_rate()
        latest = await db.latest_analysis()
        users = await db.count_users()
        text = format_status(rate=rate, latest=latest, users=users, jobs_paused=runtime.jobs_paused)
        await message.answer(text)

    @router.message(Command('digest'))
    async def cmd_digest(message: Message) -> None:
        await alert_engine.send_digest_to_user(message.from_user.id, hours=12)

    @router.message(Command('sources'))
    async def cmd_sources(message: Message) -> None:
        lines = ['📡 منابع پیکربندی‌شده:']
        for index, url in enumerate(settings.news_rss_urls, start=1):
            lines.append(f'{index}. {url}')
        lines.append('\n🔎 کلیدواژه‌ها: ' + '، '.join(settings.news_keywords[:8]) + ' ...')
        await message.answer('\n'.join(lines))

    @router.message(Command('broadcast'))
    async def cmd_broadcast(message: Message) -> None:
        if message.from_user is None or not _is_admin(message.from_user.id):
            await message.answer('⛔️ فقط ادمین.')
            return
        text = message.text.replace('/broadcast', '', 1).strip() if message.text else ''
        if not text:
            await message.answer('متن broadcast را بعد از دستور بنویسید.')
            return
        users = await db.list_alert_users()
        sent = 0
        for user in users:
            try:
                await message.bot.send_message(user.telegram_id, text)
                sent += 1
            except Exception:  # noqa: BLE001
                continue
        await message.answer(f'✅ برای {sent} کاربر ارسال شد.')

    @router.message(Command('pause_job'))
    async def cmd_pause_job(message: Message) -> None:
        if message.from_user is None or not _is_admin(message.from_user.id):
            await message.answer('⛔️ فقط ادمین.')
            return
        runtime.jobs_paused = True
        await message.answer('⏸️ jobها متوقف شد.')

    @router.message(Command('resume_job'))
    async def cmd_resume_job(message: Message) -> None:
        if message.from_user is None or not _is_admin(message.from_user.id):
            await message.answer('⛔️ فقط ادمین.')
            return
        runtime.jobs_paused = False
        await message.answer('▶️ jobها از سر گرفته شد.')

    @router.message(F.text)
    async def fallback(message: Message) -> None:
        await message.answer('دستور نامعتبر. /help')

    return router
