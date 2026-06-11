"""morning notification scheduler tables

Revision ID: 0003_morning_scheduler
Revises: 0002_recommendations
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_morning_scheduler"
down_revision = "0002_recommendations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_settings",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("timezone", sa.String(length=128), nullable=False),
        sa.Column("weekday_notification_time", sa.String(length=16), nullable=False),
        sa.Column("weekend_notification_time", sa.String(length=16), nullable=True),
        sa.Column("location_label", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "morning_recommendation_runs",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("run_date", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("recommendation_id", sa.String(length=128), sa.ForeignKey("recommendations.id"), nullable=True),
        sa.Column("weather_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "push_dispatches",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("recommendation_id", sa.String(length=128), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("push_dispatches")
    op.drop_table("morning_recommendation_runs")
    op.drop_table("notification_settings")

