"""records the foreign_keys setting seen by the migration connection

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
    op.create_table("fk_state", sa.Column("enabled", sa.Integer, nullable=False))
    enabled = op.get_bind().exec_driver_sql("PRAGMA foreign_keys").scalar()
    op.get_bind().exec_driver_sql("INSERT INTO fk_state (enabled) VALUES (?)", (enabled,))


def downgrade() -> None:
    op.drop_table("fk_state")
