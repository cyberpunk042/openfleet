"""Rename openclaw_session_id to session_id.

Revision ID: 0007_rename_session
"""
from alembic import op

revision = "0007_rename_session"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("agents", "openclaw_session_id", new_column_name="session_id")
    op.drop_index("ix_agents_openclaw_session_id", table_name="agents")
    op.create_index("ix_agents_session_id", "agents", ["session_id"])


def downgrade() -> None:
    op.alter_column("agents", "session_id", new_column_name="openclaw_session_id")
    op.drop_index("ix_agents_session_id", table_name="agents")
    op.create_index("ix_agents_openclaw_session_id", "agents", ["openclaw_session_id"])
