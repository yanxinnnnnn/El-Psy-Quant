"""Tests for bounded configured evidence-manifest inspection."""

import inspect
import json
import socket
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import el_psy_quant.application.evidence_manifests as service
from el_psy_quant.application import (
    SUPPORTED_EVIDENCE_MANIFEST_TYPES,
    EvidenceArtifactInvalidError,
    EvidenceArtifactRootUnavailableError,
    EvidenceManifestNotFoundError,
    ReportArtifactManifestDetail,
    StrategyDecisionManifestDetail,
    StrategyReviewWorkflowManifestDetail,
    get_evidence_manifest_detail,
    list_evidence_manifests,
)
from el_psy_quant.decision_governance import (
    create_strategy_decision_manifest,
    create_strategy_decision_reference,
)
from el_psy_quant.report_artifacts import (
    create_report_artifact_manifest,
    create_report_artifact_reference,
)
from el_psy_quant.strategy_review import (
    create_strategy_review_workflow_manifest,
    create_strategy_review_workflow_reference,
)

CATEGORIES = {
    "strategy_decision_manifest": "strategy-decisions",
    "report_artifact_manifest": "report-artifacts",
    "strategy_review_workflow_manifest": "strategy-review",
}


def _decision_payload() -> dict[str, object]:
    summary = create_strategy_decision_reference(
        reference_type="strategy_decision_summary",
        reference_id="summary-2",
        label=" Summary ",
    )
    record = create_strategy_decision_reference(
        reference_type="strategy_decision_record",
        reference_id="record-1",
        description="Decision record.",
    )
    return create_strategy_decision_manifest(
        manifest_id=" decision manifest ",
        summary_references=[summary, summary],
        record_references=[record],
        created_by=" founder ",
        created_timestamp="2026-07-12T12:00:00Z",
        description=" Decision evidence. ",
    ).to_dict()


def _report_payload() -> dict[str, object]:
    reference = create_report_artifact_reference(
        reference_type="report_artifact_summary",
        reference_id="report-1",
        label="Report",
    )
    return create_report_artifact_manifest(
        manifest_id="report manifest",
        references=[reference, reference],
        label=" Review package ",
        description=" Report evidence. ",
        created_by=" founder ",
        created_timestamp="2026-07-12T12:00:00Z",
        notes=" Manual context. ",
    ).to_dict()


def _workflow_payload(*, partial: bool = False) -> dict[str, object]:
    snapshot = create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_state_snapshot",
        reference_id="snapshot-1",
    )
    proposal = create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_transition_proposal",
        reference_id="proposal-1",
    )
    record = create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_transition_record",
        reference_id="record-1",
    )
    return create_strategy_review_workflow_manifest(
        manifest_id="workflow manifest",
        state_snapshot_references=[snapshot, snapshot],
        transition_proposal_references=[] if partial else [proposal],
        transition_record_references=[] if partial else [record],
        created_by="founder",
        created_timestamp="2026-07-12T12:00:00Z",
        description="Lifecycle evidence.",
    ).to_dict()


PAYLOADS = {
    "strategy_decision_manifest": _decision_payload,
    "report_artifact_manifest": _report_payload,
    "strategy_review_workflow_manifest": _workflow_payload,
}


def _write(
    root: Path,
    manifest_type: str,
    artifact_key: str,
    payload: object | None = None,
) -> Path:
    path = root / CATEGORIES[manifest_type] / f"{artifact_key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    value = PAYLOADS[manifest_type]() if payload is None else payload
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")


def test_supported_types_are_exact_order_and_functions_keyword_only() -> None:
    assert SUPPORTED_EVIDENCE_MANIFEST_TYPES == (
        "strategy_decision_manifest",
        "report_artifact_manifest",
        "strategy_review_workflow_manifest",
    )
    for function in (list_evidence_manifests, get_evidence_manifest_detail):
        assert all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in inspect.signature(function).parameters.values()
        )


def test_root_validation_empty_root_and_nul_translation(tmp_path: Path) -> None:
    assert list_evidence_manifests(artifact_root=tmp_path) == ()
    for root in (tmp_path / "missing", "", "invalid\0root", object()):
        with pytest.raises(EvidenceArtifactRootUnavailableError):
            list_evidence_manifests(artifact_root=root)  # type: ignore[arg-type]


def test_discovery_uses_fixed_type_then_key_order_and_direct_files(tmp_path: Path) -> None:
    _write(tmp_path, "report_artifact_manifest", "z-report")
    _write(tmp_path, "strategy_decision_manifest", "z-decision")
    _write(tmp_path, "strategy_decision_manifest", "a_decision")
    _write(tmp_path, "strategy_review_workflow_manifest", "workflow")
    category = tmp_path / "strategy-decisions"
    (category / "ignored.txt").write_text("ignored", encoding="utf-8")
    (category / "bad.key.json").write_text("not-json", encoding="utf-8")
    nested = category / "nested"
    nested.mkdir()
    (nested / "hidden.json").write_text("not-json", encoding="utf-8")

    manifests = list_evidence_manifests(artifact_root=tmp_path)

    assert tuple((item.manifest_type, item.artifact_key) for item in manifests) == (
        ("strategy_decision_manifest", "a_decision"),
        ("strategy_decision_manifest", "z-decision"),
        ("report_artifact_manifest", "z-report"),
        ("strategy_review_workflow_manifest", "workflow"),
    )


def test_missing_categories_are_empty_and_non_directory_is_invalid(
    tmp_path: Path,
) -> None:
    (tmp_path / "report-artifacts").write_text("not a directory", encoding="utf-8")
    with pytest.raises(EvidenceArtifactInvalidError):
        list_evidence_manifests(artifact_root=tmp_path)


def test_discoverable_malformed_file_is_not_silently_skipped(tmp_path: Path) -> None:
    _write(tmp_path, "strategy_decision_manifest", "broken", ["not", "object"])
    with pytest.raises(EvidenceArtifactInvalidError):
        list_evidence_manifests(artifact_root=tmp_path)


@pytest.mark.parametrize("manifest_type", SUPPORTED_EVIDENCE_MANIFEST_TYPES)
def test_details_reconstruct_normalize_hide_unknown_and_are_frozen(
    tmp_path: Path, manifest_type: str
) -> None:
    payload = PAYLOADS[manifest_type]()
    payload["unknown"] = {"secret": str(tmp_path)}
    _write(tmp_path, manifest_type, "artifact_1", payload)
    detail = get_evidence_manifest_detail(
        artifact_root=tmp_path,
        manifest_type=manifest_type,
        artifact_key="artifact_1",
    )
    assert detail.manifest_type == manifest_type
    assert detail.schema_version == 1
    assert detail.created_by == "founder"
    expected_timestamp = (
        "2026-07-12T12:00:00Z"
        if manifest_type == "report_artifact_manifest"
        else "2026-07-12T12:00:00+00:00"
    )
    assert detail.created_timestamp == expected_timestamp
    assert not hasattr(detail, "unknown")
    with pytest.raises(FrozenInstanceError):
        detail.artifact_key = "other"  # type: ignore[misc]


def test_decision_group_order_duplicates_and_summary_count(tmp_path: Path) -> None:
    _write(tmp_path, "strategy_decision_manifest", "decision-1")
    detail = get_evidence_manifest_detail(
        artifact_root=tmp_path,
        manifest_type="strategy_decision_manifest",
        artifact_key="decision-1",
    )
    assert isinstance(detail, StrategyDecisionManifestDetail)
    assert tuple(item.reference_id for item in detail.summary_references) == (
        "summary-2",
        "summary-2",
    )
    assert detail.summary_references[0].label == "Summary"
    assert list_evidence_manifests(artifact_root=tmp_path)[0].reference_count == 3


def test_report_fields_and_duplicates_preserve_domain_behavior(tmp_path: Path) -> None:
    _write(tmp_path, "report_artifact_manifest", "report-1")
    detail = get_evidence_manifest_detail(
        artifact_root=tmp_path,
        manifest_type="report_artifact_manifest",
        artifact_key="report-1",
    )
    assert isinstance(detail, ReportArtifactManifestDetail)
    assert tuple(item.reference_id for item in detail.references) == (
        "report-1",
        "report-1",
    )
    assert detail.label == "Review package"
    assert detail.notes == "Manual context."


def test_partial_workflow_is_accepted_and_preserves_duplicates(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "strategy_review_workflow_manifest",
        "workflow-1",
        _workflow_payload(partial=True),
    )
    detail = get_evidence_manifest_detail(
        artifact_root=tmp_path,
        manifest_type="strategy_review_workflow_manifest",
        artifact_key="workflow-1",
    )
    assert isinstance(detail, StrategyReviewWorkflowManifestDetail)
    assert len(detail.state_snapshot_references) == 2
    assert detail.transition_proposal_references == ()
    assert detail.transition_record_references == ()


@pytest.mark.parametrize(
    ("manifest_type", "field"),
    (
        ("strategy_decision_manifest", "summary_references"),
        ("report_artifact_manifest", "references"),
        ("strategy_review_workflow_manifest", "state_snapshot_references"),
    ),
)
@pytest.mark.parametrize("schema_version", (True, 2, None))
def test_exact_manifest_and_reference_schema_versions(
    tmp_path: Path, manifest_type: str, field: str, schema_version: object
) -> None:
    manifest_payload = PAYLOADS[manifest_type]()
    manifest_payload["schema_version"] = schema_version
    _write(tmp_path, manifest_type, "bad-manifest", manifest_payload)
    with pytest.raises(EvidenceArtifactInvalidError):
        get_evidence_manifest_detail(
            artifact_root=tmp_path,
            manifest_type=manifest_type,
            artifact_key="bad-manifest",
        )
    reference_payload = PAYLOADS[manifest_type]()
    reference_payload[field][0]["schema_version"] = schema_version
    _write(tmp_path, manifest_type, "bad-reference", reference_payload)
    with pytest.raises(EvidenceArtifactInvalidError):
        get_evidence_manifest_detail(
            artifact_root=tmp_path,
            manifest_type=manifest_type,
            artifact_key="bad-reference",
        )


@pytest.mark.parametrize("manifest_type", SUPPORTED_EVIDENCE_MANIFEST_TYPES)
def test_domain_invalid_payload_is_artifact_invalid(
    tmp_path: Path, manifest_type: str
) -> None:
    payload = PAYLOADS[manifest_type]()
    payload["manifest_id"] = "   "
    _write(tmp_path, manifest_type, "invalid", payload)
    with pytest.raises(EvidenceArtifactInvalidError):
        get_evidence_manifest_detail(
            artifact_root=tmp_path,
            manifest_type=manifest_type,
            artifact_key="invalid",
        )


def test_grouped_type_rules_remain_domain_authoritative(tmp_path: Path) -> None:
    payload = _decision_payload()
    payload["summary_references"][0]["reference_type"] = "strategy_decision_record"
    _write(tmp_path, "strategy_decision_manifest", "wrong-group", payload)
    with pytest.raises(EvidenceArtifactInvalidError):
        get_evidence_manifest_detail(
            artifact_root=tmp_path,
            manifest_type="strategy_decision_manifest",
            artifact_key="wrong-group",
        )


def test_saved_json_is_reconstructed_through_existing_public_factories(
    tmp_path: Path, monkeypatch
) -> None:
    for manifest_type in SUPPORTED_EVIDENCE_MANIFEST_TYPES:
        _write(tmp_path, manifest_type, "manifest")
    names = (
        "create_strategy_decision_reference",
        "create_strategy_decision_manifest",
        "create_report_artifact_reference",
        "create_report_artifact_manifest",
        "create_strategy_review_workflow_reference",
        "create_strategy_review_workflow_manifest",
    )
    calls: list[str] = []
    for name in names:
        original = getattr(service, name)

        def tracked(*args, _name=name, _original=original, **kwargs):
            calls.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(service, name, tracked)

    list_evidence_manifests(artifact_root=tmp_path)

    assert set(calls) == set(names)


@pytest.mark.parametrize(
    "manifest_type",
    ("unsupported", " strategy_decision_manifest", "STRATEGY_DECISION_MANIFEST"),
)
def test_unsupported_type_is_not_found_before_root_access(manifest_type: str) -> None:
    with pytest.raises(EvidenceManifestNotFoundError):
        get_evidence_manifest_detail(
            artifact_root="invalid\0root",
            manifest_type=manifest_type,
            artifact_key="key",
        )


@pytest.mark.parametrize(
    "artifact_key",
    ("", ".", "..", "a.json", "a/b", "a\\b", " a", "a ", "C:drive", "a%2Fb", "nul\0key"),
)
def test_invalid_keys_are_not_found_before_root_access(artifact_key: str) -> None:
    with pytest.raises(EvidenceManifestNotFoundError):
        get_evidence_manifest_detail(
            artifact_root="invalid\0root",
            manifest_type="strategy_decision_manifest",
            artifact_key=artifact_key,
        )


def test_missing_exact_file_is_not_found(tmp_path: Path) -> None:
    (tmp_path / "strategy-decisions").mkdir()
    with pytest.raises(EvidenceManifestNotFoundError):
        get_evidence_manifest_detail(
            artifact_root=tmp_path,
            manifest_type="strategy_decision_manifest",
            artifact_key="missing",
        )


def test_detail_selection_requires_exact_case_even_if_resolve_does_not(
    tmp_path: Path, monkeypatch
) -> None:
    exact_path = _write(tmp_path, "strategy_decision_manifest", "Key")
    original_resolve = Path.resolve

    def case_insensitive_resolve(path: Path, strict: bool = False) -> Path:
        if path.name == "key.json":
            return exact_path
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", case_insensitive_resolve)

    with pytest.raises(EvidenceManifestNotFoundError):
        get_evidence_manifest_detail(
            artifact_root=tmp_path,
            manifest_type="strategy_decision_manifest",
            artifact_key="key",
        )

    detail = get_evidence_manifest_detail(
        artifact_root=tmp_path,
        manifest_type="strategy_decision_manifest",
        artifact_key="Key",
    )
    assert detail.artifact_key == "Key"


def test_reads_only_manifests_without_writes_network_or_reference_resolution(
    tmp_path: Path, monkeypatch
) -> None:
    for manifest_type in SUPPORTED_EVIDENCE_MANIFEST_TYPES:
        _write(tmp_path, manifest_type, "manifest")
    reads: list[str] = []
    original = Path.read_text

    def tracked(path: Path, *args, **kwargs):
        reads.append(path.name)
        return original(path, *args, **kwargs)

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("out-of-scope side effect")

    monkeypatch.setattr(Path, "read_text", tracked)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    list_evidence_manifests(artifact_root=tmp_path)
    assert reads == ["manifest.json", "manifest.json", "manifest.json"]


def test_category_and_discoverable_file_symlinks_are_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    _symlink_or_skip(tmp_path / "strategy-decisions", outside)
    with pytest.raises(EvidenceArtifactInvalidError):
        list_evidence_manifests(artifact_root=tmp_path)
    (tmp_path / "strategy-decisions").unlink()
    category = tmp_path / "strategy-decisions"
    category.mkdir()
    target = outside / "target.json"
    target.write_text(json.dumps(_decision_payload()), encoding="utf-8")
    _symlink_or_skip(category / "linked.json", target)
    with pytest.raises(EvidenceArtifactInvalidError):
        list_evidence_manifests(artifact_root=tmp_path)


def test_application_package_has_no_broad_artifact_or_workflow_api() -> None:
    from el_psy_quant import application

    forbidden = {
        "resolve_evidence_reference",
        "load_referenced_artifact",
        "write_evidence_manifest",
        "create_evidence_manifest",
        "infer_current_lifecycle_state",
        "validate_evidence_chain",
        "render_report",
        "run_paper_workflow",
        "EvidenceManifestRepository",
    }
    assert all(not hasattr(application, name) for name in forbidden)
