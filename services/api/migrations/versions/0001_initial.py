"""initial persistence tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "closet_items",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("sub_type", sa.String(length=128), nullable=False),
        sa.Column("seasons", sa.JSON(), nullable=False),
        sa.Column("style_tags", sa.JSON(), nullable=False),
        sa.Column("colors", sa.JSON(), nullable=False),
        sa.Column("thickness", sa.String(length=64), nullable=False),
        sa.Column("formality", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("warmth", sa.Integer(), nullable=False),
        sa.Column("rain_safe", sa.Boolean(), nullable=False),
        sa.Column("breathability", sa.Integer(), nullable=False),
        sa.Column("wear_count", sa.Integer(), nullable=False),
        sa.Column("last_worn_days_ago", sa.Integer(), nullable=True),
    )
    op.create_table(
        "image_upload_tickets",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("upload_url", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False),
    )
    op.create_table(
        "image_analysis_jobs",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("upload_id", sa.String(length=128), sa.ForeignKey("image_upload_tickets.id"), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("requested_operations", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "worker_events",
        sa.Column("job_id", sa.String(length=128), sa.ForeignKey("image_analysis_jobs.id"), primary_key=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("upload_id", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("requested_operations", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("worker_events")
    op.drop_table("image_analysis_jobs")
    op.drop_table("image_upload_tickets")
    op.drop_table("closet_items")

