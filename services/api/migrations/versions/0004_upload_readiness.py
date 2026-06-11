"""upload readiness metadata

Revision ID: 0004_upload_readiness
Revises: 0003_morning_scheduler
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_upload_readiness"
down_revision = "0003_morning_scheduler"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("image_upload_tickets", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("image_upload_tickets", sa.Column("uploaded_byte_size", sa.Integer(), nullable=True))
    op.add_column("image_upload_tickets", sa.Column("uploaded_checksum_sha256", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("image_upload_tickets", "uploaded_checksum_sha256")
    op.drop_column("image_upload_tickets", "uploaded_byte_size")
    op.drop_column("image_upload_tickets", "uploaded_at")
