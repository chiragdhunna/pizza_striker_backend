"""Initial migration - create all tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="employee"),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('admin', 'employee')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # Create strikes table
    op.create_table(
        "strikes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("given_by_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "category IN ('late', 'bug', 'forgot_meeting', 'dress_code', 'other')",
            name="ck_strikes_category",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["given_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_strikes_user_id", "strikes", ["user_id"])
    op.create_index("idx_strikes_given_by_id", "strikes", ["given_by_id"])
    op.create_index("idx_strikes_is_active", "strikes", ["is_active"])

    # Create pizza_events table
    op.create_table(
        "pizza_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("triggered_by_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'scheduled', 'completed', 'cancelled')",
            name="ck_pizza_events_status",
        ),
        sa.ForeignKeyConstraint(["triggered_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_pizza_events_triggered_by", "pizza_events", ["triggered_by_id"])
    op.create_index("idx_pizza_events_status", "pizza_events", ["status"])

    # Create pizza_event_strikes join table
    op.create_table(
        "pizza_event_strikes",
        sa.Column("pizza_event_id", sa.Integer(), nullable=False),
        sa.Column("strike_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["pizza_event_id"], ["pizza_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strike_id"], ["strikes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pizza_event_id", "strike_id"),
    )

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_is_read", "notifications", ["is_read"])


def downgrade() -> None:
    op.drop_index("idx_notifications_is_read", "notifications")
    op.drop_index("idx_notifications_user_id", "notifications")
    op.drop_table("notifications")
    op.drop_table("pizza_event_strikes")
    op.drop_index("idx_pizza_events_status", "pizza_events")
    op.drop_index("idx_pizza_events_triggered_by", "pizza_events")
    op.drop_table("pizza_events")
    op.drop_index("idx_strikes_is_active", "strikes")
    op.drop_index("idx_strikes_given_by_id", "strikes")
    op.drop_index("idx_strikes_user_id", "strikes")
    op.drop_table("strikes")
    op.drop_index("idx_users_role", "users")
    op.drop_index("idx_users_email", "users")
    op.drop_table("users")
