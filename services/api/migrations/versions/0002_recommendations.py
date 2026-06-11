"""recommendation persistence tables

Revision ID: 0002_recommendations
Revises: 0001_initial
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_recommendations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "outfit_candidates",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("recommendation_id", sa.String(length=128), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("item_ids", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("items_snapshot", sa.JSON(), nullable=False),
    )
    op.create_table(
        "recommendation_feedback",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("recommendation_id", sa.String(length=128), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("feedback_type", sa.String(length=128), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "wear_logs",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("recommendation_id", sa.String(length=128), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("item_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("wear_logs")
    op.drop_table("recommendation_feedback")
    op.drop_table("outfit_candidates")
    op.drop_table("recommendations")

