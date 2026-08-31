from __future__ import annotations

import logging

from aiogram import Bot

from app.config import Settings
from app.runtime_state import RuntimeState
from app.services.alert_engine import AlertEngine
from app.storage.db import Database

logger = logging.getLogger(__name__)


async def send_scheduled_digest(
    *,
    bot: Bot,
    db: Database,
    settings: Settings,
    alert_engine: AlertEngine,
    runtime: RuntimeState,
) -> None:
    if runtime.jobs_paused:
        logger.info('Jobs paused; skipping digest')
        return
    users = await db.list_alert_users()
    for user in users:
        try:
            await alert_engine.send_digest_to_user(user.telegram_id, hours=12)
        except Exception as error:  # noqa: BLE001
            logger.warning('Digest failed for %s: %s', user.telegram_id, error)
