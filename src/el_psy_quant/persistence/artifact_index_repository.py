"""Focused repository boundary for compact artifact-index entries."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from el_psy_quant.persistence.artifact_index import (
    ArtifactIndexEntry,
    _artifact_key,
    _artifact_type,
    _root_type,
)
from el_psy_quant.persistence.artifact_index_model import ArtifactIndexRecord


class ArtifactIndexRepository(Protocol):
    """Caller-owned persistence operations for the artifact index."""

    def get(
        self,
        *,
        artifact_type: str,
        artifact_key: str,
    ) -> ArtifactIndexEntry | None: ...

    def list(
        self,
        *,
        artifact_type: str | None = None,
        root_type: str | None = None,
    ) -> tuple[ArtifactIndexEntry, ...]: ...

    def replace_root_entries(
        self,
        *,
        root_type: str,
        entries: tuple[ArtifactIndexEntry, ...],
    ) -> tuple[ArtifactIndexEntry, ...]: ...


def _entry_from_record(record: ArtifactIndexRecord) -> ArtifactIndexEntry:
    return ArtifactIndexEntry(
        record_schema_version=record.record_schema_version,  # type: ignore[arg-type]
        artifact_type=record.artifact_type,  # type: ignore[arg-type]
        artifact_key=record.artifact_key,
        root_type=record.root_type,  # type: ignore[arg-type]
        relative_path=record.relative_path,
        source_id=record.source_id,
    )


def _record_from_entry(entry: ArtifactIndexEntry) -> ArtifactIndexRecord:
    return ArtifactIndexRecord(
        record_schema_version=entry.record_schema_version,
        artifact_type=entry.artifact_type,
        artifact_key=entry.artifact_key,
        root_type=entry.root_type,
        relative_path=entry.relative_path,
        source_id=entry.source_id,
    )


class SqlAlchemyArtifactIndexRepository:
    """SQLAlchemy implementation that never owns the caller's transaction."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def get(
        self,
        *,
        artifact_type: str,
        artifact_key: str,
    ) -> ArtifactIndexEntry | None:
        """Get one exact indexed identity without touching artifact files."""
        selected_type = _artifact_type(artifact_type)
        selected_key = _artifact_key(selected_type, artifact_key)
        record = self._session.get(
            ArtifactIndexRecord,
            (selected_type, selected_key),
        )
        return None if record is None else _entry_from_record(record)

    def list(
        self,
        *,
        artifact_type: str | None = None,
        root_type: str | None = None,
    ) -> tuple[ArtifactIndexEntry, ...]:
        """List indexed entries in deterministic logical identity order."""
        statement = select(ArtifactIndexRecord)
        if artifact_type is not None:
            statement = statement.where(
                ArtifactIndexRecord.artifact_type == _artifact_type(artifact_type)
            )
        if root_type is not None:
            statement = statement.where(
                ArtifactIndexRecord.root_type == _root_type(root_type)
            )
        statement = statement.order_by(
            ArtifactIndexRecord.artifact_type,
            ArtifactIndexRecord.artifact_key,
        )
        return tuple(
            _entry_from_record(record)
            for record in self._session.scalars(statement).all()
        )

    def replace_root_entries(
        self,
        *,
        root_type: str,
        entries: tuple[ArtifactIndexEntry, ...],
    ) -> tuple[ArtifactIndexEntry, ...]:
        """Replace exactly one root's rows without committing the transaction."""
        selected_root = _root_type(root_type)
        if not isinstance(entries, tuple):
            raise ValueError("entries must be a tuple of ArtifactIndexEntry values")

        identities: set[tuple[str, str]] = set()
        locators: set[str] = set()
        for entry in entries:
            if not isinstance(entry, ArtifactIndexEntry):
                raise ValueError("entries must contain only ArtifactIndexEntry values")
            if entry.root_type != selected_root:
                raise ValueError("all entries must match the selected root_type")
            identity = (entry.artifact_type, entry.artifact_key)
            if identity in identities:
                raise ValueError("entries contain a duplicate artifact identity")
            if entry.relative_path in locators:
                raise ValueError("entries contain a duplicate root locator")
            identities.add(identity)
            locators.add(entry.relative_path)

        existing_records = self._session.scalars(
            select(ArtifactIndexRecord).where(
                ArtifactIndexRecord.root_type == selected_root
            )
        ).all()
        for record in existing_records:
            identity = (record.artifact_type, record.artifact_key)
            if identity not in identities:
                self._session.delete(record)
        for entry in entries:
            self._session.merge(_record_from_entry(entry))
        self._session.flush()
        return self.list(root_type=selected_root)
