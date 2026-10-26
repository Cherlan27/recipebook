"""leaves a row whose foreign key points nowhere

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
    op.create_table("parents", sa.Column("id", sa.Integer, primary_key=True))
    op.create_table(
        "children",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("parents.id"), nullable=False),
    )
    op.get_bind().exec_driver_sql("INSERT INTO children (id, parent_id) VALUES (1, 99)")


def downgrade() -> None:
    op.drop_table("children")
    op.drop_table("parents")
