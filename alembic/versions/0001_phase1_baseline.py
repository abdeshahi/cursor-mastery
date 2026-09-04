"""Initial schema placeholder for Phase 1 infrastructure."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_phase1_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Phase 1 baseline: no application tables yet (Phase 2+)."""
    pass


def downgrade() -> None:
    """Phase 1 baseline: nothing to revert."""
    pass
