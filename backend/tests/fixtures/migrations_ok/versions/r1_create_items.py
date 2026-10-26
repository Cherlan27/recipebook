"""create items

Revision ID: r1
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "r1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("label", sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("items")
