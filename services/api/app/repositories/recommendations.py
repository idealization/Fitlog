from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from ..db.models import OutfitCandidateRecord, RecommendationFeedbackRecord, RecommendationRecord, WearLogRecord
from ..db.session import session_scope
from ..domain import (
    OutfitCandidate,
    RecommendationFeedback,
    RecommendationStatus,
    StoredOutfitCandidate,
    StoredRecommendation,
    WearLog,
)
from ..domain.recommendations import outfit_candidate_snapshot


class RecommendationNotFoundError(Exception):
    pass


class RecommendationRepository(Protocol):
    def create(
        self,
        request_payload: dict[str, object],
        candidates: list[OutfitCandidate],
    ) -> StoredRecommendation:
        ...

    def get(self, recommendation_id: str) -> StoredRecommendation:
        ...

    def save(self, recommendation_id: str) -> StoredRecommendation:
        ...

    def mark_worn(self, recommendation_id: str) -> tuple[StoredRecommendation, WearLog]:
        ...

    def add_feedback(
        self,
        recommendation_id: str,
        feedback_type: str,
        note: str | None = None,
    ) -> RecommendationFeedback:
        ...


class InMemoryRecommendationRepository:
    def __init__(self):
        self._recommendations: dict[str, StoredRecommendation] = {}
        self._feedback: dict[str, list[RecommendationFeedback]] = {}
        self._wear_logs: dict[str, list[WearLog]] = {}

    def create(
        self,
        request_payload: dict[str, object],
        candidates: list[OutfitCandidate],
    ) -> StoredRecommendation:
        now = _now()
        recommendation_id = uuid4().hex
        stored_candidates = tuple(
            _candidate_to_stored(recommendation_id, rank, candidate)
            for rank, candidate in enumerate(candidates, start=1)
        )
        recommendation = StoredRecommendation(
            id=recommendation_id,
            status=RecommendationStatus.CANDIDATE,
            request_payload=request_payload,
            candidates=stored_candidates,
            created_at=now,
            updated_at=now,
        )
        self._recommendations[recommendation.id] = recommendation
        return recommendation

    def get(self, recommendation_id: str) -> StoredRecommendation:
        try:
            return self._recommendations[recommendation_id]
        except KeyError as error:
            raise RecommendationNotFoundError(recommendation_id) from error

    def save(self, recommendation_id: str) -> StoredRecommendation:
        return self._set_status(recommendation_id, RecommendationStatus.SAVED)

    def mark_worn(self, recommendation_id: str) -> tuple[StoredRecommendation, WearLog]:
        recommendation = self._set_status(recommendation_id, RecommendationStatus.WORN)
        wear_log = WearLog(
            id=uuid4().hex,
            recommendation_id=recommendation_id,
            item_ids=tuple(recommendation.candidates[0].item_ids) if recommendation.candidates else (),
            created_at=_now(),
        )
        self._wear_logs.setdefault(recommendation_id, []).append(wear_log)
        return recommendation, wear_log

    def add_feedback(
        self,
        recommendation_id: str,
        feedback_type: str,
        note: str | None = None,
    ) -> RecommendationFeedback:
        self.get(recommendation_id)
        feedback = RecommendationFeedback(
            id=uuid4().hex,
            recommendation_id=recommendation_id,
            feedback_type=feedback_type,
            note=note,
            created_at=_now(),
        )
        self._feedback.setdefault(recommendation_id, []).append(feedback)
        return feedback

    def _set_status(self, recommendation_id: str, status: RecommendationStatus) -> StoredRecommendation:
        current = self.get(recommendation_id)
        updated = replace(current, status=status, updated_at=_now())
        self._recommendations[recommendation_id] = updated
        return updated


class SqlAlchemyRecommendationRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def create(
        self,
        request_payload: dict[str, object],
        candidates: list[OutfitCandidate],
    ) -> StoredRecommendation:
        now = _now()
        recommendation_id = uuid4().hex
        recommendation = RecommendationRecord(
            id=recommendation_id,
            status=RecommendationStatus.CANDIDATE.value,
            request_payload=request_payload,
            created_at=now,
            updated_at=now,
        )
        candidate_records = [
            _candidate_to_record(recommendation_id, rank, candidate)
            for rank, candidate in enumerate(candidates, start=1)
        ]

        with session_scope(self._session_factory) as session:
            session.add(recommendation)
            for candidate_record in candidate_records:
                session.add(candidate_record)
            session.flush()

        return self.get(recommendation_id)

    def get(self, recommendation_id: str) -> StoredRecommendation:
        with session_scope(self._session_factory) as session:
            record = session.get(RecommendationRecord, recommendation_id)
            if record is None:
                raise RecommendationNotFoundError(recommendation_id)
            candidates = (
                session.query(OutfitCandidateRecord)
                .filter(OutfitCandidateRecord.recommendation_id == recommendation_id)
                .order_by(OutfitCandidateRecord.rank.asc())
                .all()
            )
            return _record_to_domain(record, candidates)

    def save(self, recommendation_id: str) -> StoredRecommendation:
        return self._set_status(recommendation_id, RecommendationStatus.SAVED)

    def mark_worn(self, recommendation_id: str) -> tuple[StoredRecommendation, WearLog]:
        recommendation = self._set_status(recommendation_id, RecommendationStatus.WORN)
        wear_log = WearLog(
            id=uuid4().hex,
            recommendation_id=recommendation_id,
            item_ids=tuple(recommendation.candidates[0].item_ids) if recommendation.candidates else (),
            created_at=_now(),
        )
        with session_scope(self._session_factory) as session:
            session.add(
                WearLogRecord(
                    id=wear_log.id,
                    recommendation_id=wear_log.recommendation_id,
                    item_ids=list(wear_log.item_ids),
                    created_at=wear_log.created_at,
                )
            )
        return recommendation, wear_log

    def add_feedback(
        self,
        recommendation_id: str,
        feedback_type: str,
        note: str | None = None,
    ) -> RecommendationFeedback:
        self.get(recommendation_id)
        feedback = RecommendationFeedback(
            id=uuid4().hex,
            recommendation_id=recommendation_id,
            feedback_type=feedback_type,
            note=note,
            created_at=_now(),
        )
        with session_scope(self._session_factory) as session:
            session.add(
                RecommendationFeedbackRecord(
                    id=feedback.id,
                    recommendation_id=feedback.recommendation_id,
                    feedback_type=feedback.feedback_type,
                    note=feedback.note,
                    created_at=feedback.created_at,
                )
            )
        return feedback

    def _set_status(self, recommendation_id: str, status: RecommendationStatus) -> StoredRecommendation:
        with session_scope(self._session_factory) as session:
            record = session.get(RecommendationRecord, recommendation_id)
            if record is None:
                raise RecommendationNotFoundError(recommendation_id)
            record.status = status.value
            record.updated_at = _now()
            session.flush()
        return self.get(recommendation_id)


def _candidate_to_stored(
    recommendation_id: str,
    rank: int,
    candidate: OutfitCandidate,
) -> StoredOutfitCandidate:
    return StoredOutfitCandidate(
        id=uuid4().hex,
        recommendation_id=recommendation_id,
        rank=rank,
        item_ids=tuple(candidate.item_ids),
        score=candidate.score,
        reasons=tuple(candidate.reasons),
        items_snapshot=outfit_candidate_snapshot(candidate),
    )


def _candidate_to_record(
    recommendation_id: str,
    rank: int,
    candidate: OutfitCandidate,
) -> OutfitCandidateRecord:
    stored = _candidate_to_stored(recommendation_id, rank, candidate)
    return OutfitCandidateRecord(
        id=stored.id,
        recommendation_id=stored.recommendation_id,
        rank=stored.rank,
        item_ids=list(stored.item_ids),
        score=stored.score,
        reasons=list(stored.reasons),
        items_snapshot=list(stored.items_snapshot),
    )


def _record_to_domain(
    record: RecommendationRecord,
    candidate_records: list[OutfitCandidateRecord],
) -> StoredRecommendation:
    return StoredRecommendation(
        id=record.id,
        status=RecommendationStatus(record.status),
        request_payload=record.request_payload,
        candidates=tuple(_candidate_record_to_domain(candidate) for candidate in candidate_records),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _candidate_record_to_domain(record: OutfitCandidateRecord) -> StoredOutfitCandidate:
    return StoredOutfitCandidate(
        id=record.id,
        recommendation_id=record.recommendation_id,
        rank=record.rank,
        item_ids=tuple(record.item_ids),
        score=record.score,
        reasons=tuple(record.reasons),
        items_snapshot=tuple(dict(item) for item in record.items_snapshot),
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)

