from __future__ import annotations

import pytest

from app.storage.db import Database


@pytest.mark.asyncio
async def test_recent_similar_alert_antispam(tmp_path) -> None:
    db = Database(str(tmp_path / 'test.db'))
    await db.connect()
    await db.upsert_user(123)
    from datetime import datetime, timezone
    from app.storage.models import AlertRecord

    await db.insert_alert(
        AlertRecord(
            id=None,
            user_id=123,
            alert_type='instant',
            direction='rial_weaker',
            message='test',
            created_at=datetime.now(timezone.utc),
        )
    )
    assert await db.recent_similar_alert(123, 'rial_weaker', 'instant', minutes=30) is True
    assert await db.recent_similar_alert(123, 'rial_stronger', 'instant', minutes=30) is False
    await db.close()
