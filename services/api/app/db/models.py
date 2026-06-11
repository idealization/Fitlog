from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ClosetItemRecord(Base):
    __tablename__ = "closet_items"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    sub_type: Mapped[str] = mapped_column(String(128), nullable=False)
    seasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    style_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    colors: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    thickness: Mapped[str] = mapped_column(String(64), nullable=False)
    formality: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    warmth: Mapped[int] = mapped_column(Integer, nullable=False)
    rain_safe: Mapped[bool] = mapped_column(Boolean, nullable=False)
    breathability: Mapped[int] = mapped_column(Integer, nullable=False)
    wear_count: Mapped[int] = mapped_column(Integer, nullable=False)
    last_worn_days_ago: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class ImageUploadTicketRecord(Base):
    __tablename__ = "image_upload_tickets"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    upload_url: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    byte_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    headers: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)


class ImageAnalysisJobRecord(Base):
    __tablename__ = "image_analysis_jobs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    upload_id: Mapped[str] = mapped_column(String(128), ForeignKey("image_upload_tickets.id"), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_operations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkerEventRecord(Base):
    __tablename__ = "worker_events"

    job_id: Mapped[str] = mapped_column(String(128), ForeignKey("image_analysis_jobs.id"), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    upload_id: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    requested_operations: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OutfitCandidateRecord(Base):
    __tablename__ = "outfit_candidates"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(String(128), ForeignKey("recommendations.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    item_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    items_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)


class RecommendationFeedbackRecord(Base):
    __tablename__ = "recommendation_feedback"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(String(128), ForeignKey("recommendations.id"), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(128), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WearLogRecord(Base):
    __tablename__ = "wear_logs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(String(128), ForeignKey("recommendations.id"), nullable=False)
    item_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
