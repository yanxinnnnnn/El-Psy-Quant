"""Explicit refresh and database-only reads for the compact artifact index."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.application.evidence_manifests import list_evidence_manifests
from el_psy_quant.application.research_artifacts import list_research_runs
from el_psy_quant.persistence import (
    ArtifactIndexEntry,
    SqlAlchemyArtifactIndexRepository,
    create_artifact_index_entry,
)


class ArtifactIndexNotFoundError(Exception):
    """Raised when an exact artifact identity is absent from the product index."""


@dataclass(frozen=True)
class ArtifactIndexRefreshResult:
    """Entries replaced for each explicitly supplied authoritative root."""

    research_entries: tuple[ArtifactIndexEntry, ...] | None
    evidence_entries: tuple[ArtifactIndexEntry, ...] | None


def _discover_research_entries(
    artifact_root: str | Path,
) -> tuple[ArtifactIndexEntry, ...]:
    return tuple(
        create_artifact_index_entry(
            artifact_type="research_run_manifest",
            artifact_key=f"{summary.experiment_slug}/{summary.run_id}",
            source_id=summary.run_id,
        )
        for summary in list_research_runs(artifact_root=artifact_root)
    )


def _discover_evidence_entries(
    artifact_root: str | Path,
) -> tuple[ArtifactIndexEntry, ...]:
    return tuple(
        create_artifact_index_entry(
            artifact_type=summary.manifest_type,
            artifact_key=summary.artifact_key,
            source_id=summary.manifest_id,
        )
        for summary in list_evidence_manifests(artifact_root=artifact_root)
    )


def refresh_artifact_index(
    *,
    session_factory: sessionmaker[Session],
    research_artifact_root: str | Path | None = None,
    evidence_artifact_root: str | Path | None = None,
) -> ArtifactIndexRefreshResult:
    """Discover supplied roots first, then replace them in one transaction."""
    if research_artifact_root is None and evidence_artifact_root is None:
        raise ValueError("at least one artifact root must be supplied")

    research_entries = (
        None
        if research_artifact_root is None
        else _discover_research_entries(research_artifact_root)
    )
    evidence_entries = (
        None
        if evidence_artifact_root is None
        else _discover_evidence_entries(evidence_artifact_root)
    )

    persisted_research: tuple[ArtifactIndexEntry, ...] | None = None
    persisted_evidence: tuple[ArtifactIndexEntry, ...] | None = None
    with session_factory.begin() as session:
        repository = SqlAlchemyArtifactIndexRepository(session=session)
        if research_entries is not None:
            persisted_research = repository.replace_root_entries(
                root_type="research",
                entries=research_entries,
            )
        if evidence_entries is not None:
            persisted_evidence = repository.replace_root_entries(
                root_type="evidence",
                entries=evidence_entries,
            )

    return ArtifactIndexRefreshResult(
        research_entries=persisted_research,
        evidence_entries=persisted_evidence,
    )


def list_indexed_artifacts(
    *,
    session_factory: sessionmaker[Session],
    artifact_type: str | None = None,
    root_type: str | None = None,
) -> tuple[ArtifactIndexEntry, ...]:
    """List compact database rows without reading authoritative files."""
    with session_factory() as session:
        return SqlAlchemyArtifactIndexRepository(session=session).list(
            artifact_type=artifact_type,
            root_type=root_type,
        )


def get_indexed_artifact(
    *,
    session_factory: sessionmaker[Session],
    artifact_type: str,
    artifact_key: str,
) -> ArtifactIndexEntry:
    """Get an exact compact database row without reading authoritative files."""
    with session_factory() as session:
        entry = SqlAlchemyArtifactIndexRepository(session=session).get(
            artifact_type=artifact_type,
            artifact_key=artifact_key,
        )
    if entry is None:
        raise ArtifactIndexNotFoundError("indexed artifact not found")
    return entry
