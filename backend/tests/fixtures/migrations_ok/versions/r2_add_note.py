"""add note column

Revision ID: r2
Revises: r1
"""

import sqlalchemy as sa
from alembic import op

revision = "r2"
down_revision = "r1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("items", sa.Column("note", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("items", "note")
