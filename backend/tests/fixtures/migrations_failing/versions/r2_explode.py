"""fails when applied

Revision ID: r2
Revises: r1
"""

revision = "r2"
down_revision = "r1"
branch_labels = None
depends_on = None

FAILURE_MESSAGE = "boom from fixture revision r2"


def upgrade() -> None:
    raise RuntimeError(FAILURE_MESSAGE)


def downgrade() -> None:
    pass
