"""Template for Alembic revision scripts."""

from __future__ import annotations

import re
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = ""  # type: ignore[assignment]
down_revision = None  # type: ignore[assignment]
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

