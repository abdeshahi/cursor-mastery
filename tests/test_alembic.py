"""Tests for Alembic configuration."""

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_script_directory_loads() -> None:
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert "0001_phase1_baseline" in heads


def test_alembic_baseline_revision_exists() -> None:
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    revision = script.get_revision("0001_phase1_baseline")
    assert revision is not None
    assert revision.down_revision is None
