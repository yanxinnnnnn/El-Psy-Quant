"""Establish the empty product persistence baseline.

Revision ID: 0001_product_baseline
Revises:
Create Date: 2026-07-13
"""

from collections.abc import Sequence

revision: str = "0001_product_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create no business tables in the Sprint 145 baseline."""
    pass


def downgrade() -> None:
    """Remove no business tables from the Sprint 145 baseline."""
    pass
