from __future__ import annotations

from datetime import datetime, timezone

from aiogram import Bot

from app.analysis.aggregator import cluster_direction_scores, pick_cluster_alert, top_cluster_rows
from app.analysis.schema import AnalysisResult
from app.analysis.scorer import should_send_instant_alert
from app.bot.formatters import format_cluster_alert, format_instant_alert
from app.config import Settings
from app.services.rate_provider import RateSnapshot, get_free_market_usd_rate
from app.storage.db import Database
from app.storage.models import AlertRecord


class AlertEngine:
    def __init__(self, bot: Bot, db: Database, settings: Settings) -> None:
        self.bot = bot
        self.db = db
        self.settings = settings

    async def dispatch_for_analysis(
        self,
        analysis: AnalysisResult,
        *,
        source_name: str,
        link: str,
        weighted_score: float,
    ) -> None:
        rate = await get_free_market_usd_rate()
        users = await self.db.list_alert_users()
        if not users:
            return

        if should_send_instant_alert(analysis, self.settings):
            message = format_instant_alert(
                analysis=analysis,
                source_name=source_name,
                link=link,
                weighted_score=weighted_score,
                rate=rate,
            )
            await self._broadcast(users, message, direction=analysis.direction, alert_type='instant')

        await self._maybe_cluster_alert(rate)

    async def _maybe_cluster_alert(self, rate: RateSnapshot) -> None:
        rows = await self.db.recent_analyses(self.settings.cluster_window_min)
        totals = cluster_direction_scores(rows)
        direction = pick_cluster_alert(totals, min_score=self.settings.cluster_score_min)
        if direction is None:
            return
        top_rows = top_cluster_rows(rows, direction, limit=3)
        message = format_cluster_alert(direction=direction, rows=top_rows, total=totals[direction], rate=rate)
        users = await self.db.list_alert_users()
        await self._broadcast(users, message, direction=direction, alert_type='cluster')

    async def _broadcast(
        self,
        users,
        message: str,
        *,
        direction: str,
        alert_type: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        for user in users:
            if await self.db.recent_similar_alert(user.telegram_id, direction, alert_type, minutes=30):
                continue
            try:
                await self.bot.send_message(user.telegram_id, message, disable_web_page_preview=True)
                await self.db.insert_alert(
                    AlertRecord(
                        id=None,
                        user_id=user.telegram_id,
                        alert_type=alert_type,
                        direction=direction,
                        message=message,
                        created_at=now,
                    )
                )
            except Exception:  # noqa: BLE001
                continue

    async def send_digest_to_user(self, telegram_id: int, *, hours: int = 12) -> str:
        rows = await self.db.digest_rows(hours=hours)
        rate = await get_free_market_usd_rate()
        from app.bot.formatters import format_digest

        message = format_digest(rows=rows, rate=rate, hours=hours)
        await self.bot.send_message(telegram_id, message, disable_web_page_preview=True)
        return message
