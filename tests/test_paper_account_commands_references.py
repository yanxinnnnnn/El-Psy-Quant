import hashlib
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pandas as pd
import pytest

from el_psy_quant.paper_account import (
    APPROVED_PORTFOLIO_REVIEW_REFERENCE_SCHEMA_VERSION,
    INITIAL_PAPER_ACCOUNT_LIFECYCLE_STATUS,
    MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
    ApprovedPortfolioReviewReference,
    ClosePaperAccountCommand,
    CreatePaperAccountCommand,
    FreezePaperAccountCommand,
    LinkApprovedPortfolioReviewCommand,
    PaperAccountIdentity,
    PaperMoney,
    ReactivatePaperAccountCommand,
    create_approved_portfolio_review_reference,
)
from el_psy_quant.portfolio_review import (
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_decision_artifact,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)


def _decision(
    *,
    outcome: str = "approved",
    decision_id: str = "decision-001",
):
    components = tuple(
        create_portfolio_review_component(
            component_id=f"component-{index}",
            strategy_id=f"strategy-{index}",
            evidence_references=(
                create_portfolio_review_evidence_reference(
                    reference_type="research_run",
                    reference_id=f"run-{index}",
                ),
            ),
            symbols=(f"SYN-{index}",),
        )
        for index in (1, 2)
    )
    source = create_portfolio_review_source(
        source_id="source-001",
        components=components,
        aligned_returns=pd.DataFrame(
            {
                "component-1": (0.01, -0.02, 0.03),
                "component-2": (0.02, 0.01, -0.01),
            },
            index=pd.date_range("2026-07-01", periods=3, freq="D"),
        ),
        evaluation_frequency="daily",
        periods_per_year=252.0,
        created_by="source-actor",
        created_timestamp="2026-07-19T12:00:00Z",
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id="baseline-001",
        source=source,
        weights={"component-1": 1.0, "component-2": 0.0},
        rationale="Explicit baseline",
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id="proposed-001",
        source=source,
        weights={"component-1": 0.6, "component-2": 0.4},
        proposed_component_id="component-2",
        rationale="Explicit proposal",
    )
    analysis = create_portfolio_review_analysis_artifact(
        review_id="review-001",
        source=source,
        scenario_pair=create_portfolio_review_scenario_pair(
            source=source,
            baseline=baseline,
            proposed=proposed,
        ),
        created_by="analysis-actor",
        created_timestamp="2026-07-20T12:00:00Z",
    )
    return create_portfolio_review_decision_artifact(
        decision_id=decision_id,
        analysis=analysis,
        outcome=outcome,
        rationale="Founder governance decision",
        reviewed_by="founder",
        reviewed_timestamp="2026-07-21T12:00:00Z",
        notes=("Not account authority",),
        warnings=("No execution authority",),
    )


def _identity(*, account_id: str = "account-001") -> PaperAccountIdentity:
    return PaperAccountIdentity(
        account_id=account_id,
        display_name="Founder Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=datetime(2026, 7, 22, tzinfo=timezone.utc),
    )


def _expected_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_approved_decision_creates_only_the_bounded_m30_reference() -> None:
    decision = _decision()
    reference = create_approved_portfolio_review_reference(decision)

    assert reference.to_dict() == {
        "schema_version": APPROVED_PORTFOLIO_REVIEW_REFERENCE_SCHEMA_VERSION,
        "review_id": decision.review_id,
        "source_id": decision.source_id,
        "source_digest": decision.source_digest,
        "analysis_digest": decision.analysis_digest,
        "decision_id": decision.decision_id,
        "decision_digest": decision.decision_digest,
        "outcome": "approved",
    }
    forbidden = {
        "weights",
        "returns",
        "rationale",
        "notes",
        "warnings",
        "cash",
        "positions",
        "allocation",
        "orders",
        "fills",
        "execution",
    }
    assert forbidden.isdisjoint(reference.to_dict())
    assert json.loads(json.dumps(reference.to_dict(), allow_nan=False)) == (
        reference.to_dict()
    )
    with pytest.raises(FrozenInstanceError):
        reference.outcome = "rejected"  # type: ignore[misc]


@pytest.mark.parametrize("outcome", ("rejected", "deferred"))
def test_nonapproved_m30_decisions_cannot_be_references(outcome: str) -> None:
    with pytest.raises(ValueError, match="outcome must be approved"):
        create_approved_portfolio_review_reference(_decision(outcome=outcome))


def test_arbitrary_or_tampered_decisions_cannot_be_approved_references() -> None:
    with pytest.raises(ValueError, match="PortfolioReviewDecisionArtifact"):
        create_approved_portfolio_review_reference(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ApprovedPortfolioReviewReference(  # type: ignore[call-arg]
            review_id="review-001",
            source_id="source-001",
            source_digest="0" * 64,
            analysis_digest="1" * 64,
            decision_id="decision-001",
            decision_digest="2" * 64,
            outcome="approved",
        )

    decision = _decision()
    object.__setattr__(decision, "decision_digest", "0" * 64)
    with pytest.raises(ValueError, match="does not match"):
        create_approved_portfolio_review_reference(decision)


def test_create_command_has_exact_payload_and_deterministic_digest() -> None:
    command = CreatePaperAccountCommand(
        account_identity=_identity(),
        initial_cash=PaperMoney.parse("100000.25"),
        command_idempotency_key=" create-key ",
        actor=" founder ",
    )

    expected_without_digest = {
        "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
        "command_type": "create_paper_account",
        "account_identity": _identity().to_dict(),
        "initial_cash": "100000.25",
        "initial_lifecycle_status": INITIAL_PAPER_ACCOUNT_LIFECYCLE_STATUS,
        "command_idempotency_key": "create-key",
        "actor": "founder",
    }
    assert command.to_dict() == {
        **expected_without_digest,
        "command_digest": _expected_digest(expected_without_digest),
    }
    assert command == CreatePaperAccountCommand(
        account_identity=_identity(),
        initial_cash=PaperMoney.parse("100000.25"),
        command_idempotency_key="create-key",
        actor="founder",
    )


def test_create_command_accepts_zero_and_rejects_negative_initial_cash() -> None:
    command = CreatePaperAccountCommand(
        account_identity=_identity(),
        initial_cash=PaperMoney.parse("0"),
        command_idempotency_key="create-key",
        actor="founder",
    )
    assert command.to_dict()["initial_cash"] == "0"

    with pytest.raises(ValueError, match="non-negative"):
        CreatePaperAccountCommand(
            account_identity=_identity(),
            initial_cash=PaperMoney.parse("-0.01"),
            command_idempotency_key="create-key",
            actor="founder",
        )


def test_create_command_digest_changes_with_every_authoritative_field() -> None:
    base_identity = _identity()
    base = CreatePaperAccountCommand(
        account_identity=base_identity,
        initial_cash=PaperMoney.parse("100"),
        command_idempotency_key="create-key",
        actor="founder",
    )
    identity_variants = (
        PaperAccountIdentity(
            account_id="account-002",
            display_name=base_identity.display_name,
            base_currency=base_identity.base_currency,
            created_by=base_identity.created_by,
            created_timestamp=base_identity.created_timestamp,
        ),
        PaperAccountIdentity(
            account_id=base_identity.account_id,
            display_name="Different name",
            base_currency=base_identity.base_currency,
            created_by=base_identity.created_by,
            created_timestamp=base_identity.created_timestamp,
        ),
        PaperAccountIdentity(
            account_id=base_identity.account_id,
            display_name=base_identity.display_name,
            base_currency="CNY",
            created_by=base_identity.created_by,
            created_timestamp=base_identity.created_timestamp,
        ),
        PaperAccountIdentity(
            account_id=base_identity.account_id,
            display_name=base_identity.display_name,
            base_currency=base_identity.base_currency,
            created_by="other-founder",
            created_timestamp=base_identity.created_timestamp,
        ),
        PaperAccountIdentity(
            account_id=base_identity.account_id,
            display_name=base_identity.display_name,
            base_currency=base_identity.base_currency,
            created_by=base_identity.created_by,
            created_timestamp=datetime(2026, 7, 23, tzinfo=timezone.utc),
        ),
    )
    variants = tuple(
        CreatePaperAccountCommand(
            account_identity=identity,
            initial_cash=PaperMoney.parse("100"),
            command_idempotency_key="create-key",
            actor="founder",
        )
        for identity in identity_variants
    ) + (
        CreatePaperAccountCommand(
            account_identity=base_identity,
            initial_cash=PaperMoney.parse("101"),
            command_idempotency_key="create-key",
            actor="founder",
        ),
        CreatePaperAccountCommand(
            account_identity=base_identity,
            initial_cash=PaperMoney.parse("100"),
            command_idempotency_key="other-key",
            actor="founder",
        ),
        CreatePaperAccountCommand(
            account_identity=base_identity,
            initial_cash=PaperMoney.parse("100"),
            command_idempotency_key="create-key",
            actor="other-founder",
        ),
    )

    assert all(variant.command_digest != base.command_digest for variant in variants)
    assert len({variant.command_digest for variant in variants}) == len(variants)


@pytest.mark.parametrize(
    ("command_type", "target_status"),
    (
        (FreezePaperAccountCommand, "frozen"),
        (ReactivatePaperAccountCommand, "active"),
        (ClosePaperAccountCommand, "closed"),
    ),
)
def test_lifecycle_commands_have_fixed_target_and_exact_payload(
    command_type: type[
        FreezePaperAccountCommand
        | ReactivatePaperAccountCommand
        | ClosePaperAccountCommand
    ],
    target_status: str,
) -> None:
    command = command_type(
        account_id=" account-001 ",
        expected_account_version=3,
        command_idempotency_key=" lifecycle-key ",
        actor=" founder ",
        reason=" explicit reason ",
    )

    payload = command.to_dict()
    digest = payload.pop("command_digest")
    assert payload == {
        "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
        "command_type": f"{command_type.__name__.removesuffix('Command').replace('PaperAccount', '_paper_account').lower()}",
        "account_id": "account-001",
        "expected_account_version": 3,
        "command_idempotency_key": "lifecycle-key",
        "actor": "founder",
        "reason": "explicit reason",
        "target_lifecycle_status": target_status,
    }
    assert digest == _expected_digest(payload)


@pytest.mark.parametrize("version", (0, -1, True, 1.5, "1"))
def test_post_creation_commands_require_positive_integer_version(
    version: object,
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        FreezePaperAccountCommand(
            account_id="account-001",
            expected_account_version=version,  # type: ignore[arg-type]
            command_idempotency_key="key",
            actor="founder",
            reason="reason",
        )


@pytest.mark.parametrize("reason", ("", " ", None))
def test_lifecycle_commands_require_an_explicit_reason(reason: object) -> None:
    with pytest.raises(ValueError, match="reason"):
        ReactivatePaperAccountCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key="key",
            actor="founder",
            reason=reason,  # type: ignore[arg-type]
        )


def test_idempotency_keys_are_bounded_and_trimmed() -> None:
    with pytest.raises(ValueError, match="idempotency"):
        ClosePaperAccountCommand(
            account_id="account-001",
            expected_account_version=1,
            command_idempotency_key=(
                "x" * (MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH + 1)
            ),
            actor="founder",
            reason="reason",
        )


def test_evidence_link_command_is_governance_only_and_exact() -> None:
    reference = create_approved_portfolio_review_reference(_decision())
    command = LinkApprovedPortfolioReviewCommand(
        account_id="account-001",
        expected_account_version=4,
        command_idempotency_key="link-key",
        actor="founder",
        reason="Record governance provenance",
        approved_portfolio_review=reference,
    )

    payload = command.to_dict()
    digest = payload.pop("command_digest")
    assert payload == {
        "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
        "command_type": "link_approved_portfolio_review",
        "account_id": "account-001",
        "expected_account_version": 4,
        "command_idempotency_key": "link-key",
        "actor": "founder",
        "reason": "Record governance provenance",
        "approved_portfolio_review": reference.to_dict(),
    }
    assert digest == _expected_digest(payload)
    assert {
        "cash",
        "positions",
        "weights",
        "orders",
        "fills",
        "execution",
    }.isdisjoint(payload)


def test_command_digests_change_with_each_authoritative_field() -> None:
    reference = create_approved_portfolio_review_reference(_decision())
    base = LinkApprovedPortfolioReviewCommand(
        account_id="account-001",
        expected_account_version=4,
        command_idempotency_key="link-key",
        actor="founder",
        reason="Record governance provenance",
        approved_portfolio_review=reference,
    )
    variants = (
        LinkApprovedPortfolioReviewCommand(
            account_id="account-002",
            expected_account_version=4,
            command_idempotency_key="link-key",
            actor="founder",
            reason="Record governance provenance",
            approved_portfolio_review=reference,
        ),
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=5,
            command_idempotency_key="link-key",
            actor="founder",
            reason="Record governance provenance",
            approved_portfolio_review=reference,
        ),
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=4,
            command_idempotency_key="other-key",
            actor="founder",
            reason="Record governance provenance",
            approved_portfolio_review=reference,
        ),
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=4,
            command_idempotency_key="link-key",
            actor="other-founder",
            reason="Record governance provenance",
            approved_portfolio_review=reference,
        ),
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=4,
            command_idempotency_key="link-key",
            actor="founder",
            reason="Different provenance reason",
            approved_portfolio_review=reference,
        ),
        LinkApprovedPortfolioReviewCommand(
            account_id="account-001",
            expected_account_version=4,
            command_idempotency_key="link-key",
            actor="founder",
            reason="Record governance provenance",
            approved_portfolio_review=(
                create_approved_portfolio_review_reference(
                    _decision(decision_id="decision-002")
                )
            ),
        ),
    )

    assert all(variant.command_digest != base.command_digest for variant in variants)
    assert len({variant.command_digest for variant in variants}) == len(variants)


def test_command_types_have_distinct_digests_for_the_same_common_fields() -> None:
    values = {
        "account_id": "account-001",
        "expected_account_version": 1,
        "command_idempotency_key": "key",
        "actor": "founder",
        "reason": "reason",
    }
    commands = (
        FreezePaperAccountCommand(**values),
        ReactivatePaperAccountCommand(**values),
        ClosePaperAccountCommand(**values),
    )
    assert len({command.command_digest for command in commands}) == 3


def test_paper_account_import_has_no_persistence_or_runtime_side_effect() -> None:
    source = (
        "import sys; import el_psy_quant.paper_account; "
        "assert not any(name.startswith('el_psy_quant.persistence') "
        "for name in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", source],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
