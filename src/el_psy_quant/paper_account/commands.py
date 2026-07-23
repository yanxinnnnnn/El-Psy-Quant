"""Pure immutable Paper Account command contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from el_psy_quant.paper_account.decimals import PaperMoney
from el_psy_quant.paper_account.identity import (
    MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
    PaperAccountIdentity,
)
from el_psy_quant.paper_account.lifecycle import (
    INITIAL_PAPER_ACCOUNT_LIFECYCLE_STATUS,
)
from el_psy_quant.paper_account.references import (
    ApprovedPortfolioReviewReference,
)

PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION = 1

MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH = 128
MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH = 2000


def _normalize_bounded_string(
    value: str,
    field_name: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must be at most {maximum_length} characters"
        )
    return normalized


def _normalize_account_id(value: str) -> str:
    return _normalize_bounded_string(
        value,
        "account_id",
        MAX_PAPER_ACCOUNT_ID_LENGTH,
    )


def _normalize_expected_version(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("expected_account_version must be a positive integer")
    return value


def _normalize_key(value: str) -> str:
    return _normalize_bounded_string(
        value,
        "command_idempotency_key",
        MAX_PAPER_ACCOUNT_COMMAND_IDEMPOTENCY_KEY_LENGTH,
    )


def _normalize_actor(value: str) -> str:
    return _normalize_bounded_string(
        value,
        "actor",
        MAX_PAPER_ACCOUNT_ACTOR_LENGTH,
    )


def _normalize_reason(value: str) -> str:
    return _normalize_bounded_string(
        value,
        "reason",
        MAX_PAPER_ACCOUNT_COMMAND_REASON_LENGTH,
    )


def _command_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CreatePaperAccountCommand:
    """Request creation of one active account with explicit initial cash."""

    account_identity: PaperAccountIdentity
    initial_cash: PaperMoney
    command_idempotency_key: str
    actor: str
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.account_identity) is not PaperAccountIdentity:
            raise ValueError("account_identity must be a PaperAccountIdentity")
        if type(self.initial_cash) is not PaperMoney:
            raise ValueError("initial_cash must be PaperMoney")
        if self.initial_cash.decimal_value < 0:
            raise ValueError("initial_cash must be non-negative")
        object.__setattr__(
            self,
            "command_idempotency_key",
            _normalize_key(self.command_idempotency_key),
        )
        object.__setattr__(self, "actor", _normalize_actor(self.actor))
        object.__setattr__(
            self,
            "command_digest",
            _command_digest(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
            "command_type": "create_paper_account",
            "account_identity": self.account_identity.to_dict(),
            "initial_cash": self.initial_cash.to_json_value(),
            "initial_lifecycle_status": (
                INITIAL_PAPER_ACCOUNT_LIFECYCLE_STATUS
            ),
            "command_idempotency_key": self.command_idempotency_key,
            "actor": self.actor,
        }

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and SHA-256 digest."""
        payload = self._payload_without_digest()
        payload["command_digest"] = self.command_digest
        return payload


@dataclass(frozen=True)
class FreezePaperAccountCommand:
    """Request the fixed active-to-frozen lifecycle meaning."""

    account_id: str
    expected_account_version: int
    command_idempotency_key: str
    actor: str
    reason: str
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "account_id", _normalize_account_id(self.account_id))
        object.__setattr__(
            self,
            "expected_account_version",
            _normalize_expected_version(self.expected_account_version),
        )
        object.__setattr__(
            self,
            "command_idempotency_key",
            _normalize_key(self.command_idempotency_key),
        )
        object.__setattr__(self, "actor", _normalize_actor(self.actor))
        object.__setattr__(self, "reason", _normalize_reason(self.reason))
        object.__setattr__(
            self,
            "command_digest",
            _command_digest(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, object]:
        return _lifecycle_payload(
            command_type="freeze_paper_account",
            target_status="frozen",
            account_id=self.account_id,
            expected_account_version=self.expected_account_version,
            command_idempotency_key=self.command_idempotency_key,
            actor=self.actor,
            reason=self.reason,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and SHA-256 digest."""
        return _with_digest(self._payload_without_digest(), self.command_digest)


@dataclass(frozen=True)
class ReactivatePaperAccountCommand:
    """Request the fixed frozen-to-active lifecycle meaning."""

    account_id: str
    expected_account_version: int
    command_idempotency_key: str
    actor: str
    reason: str
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _normalize_lifecycle_command(self)
        object.__setattr__(
            self,
            "command_digest",
            _command_digest(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, object]:
        return _lifecycle_payload(
            command_type="reactivate_paper_account",
            target_status="active",
            account_id=self.account_id,
            expected_account_version=self.expected_account_version,
            command_idempotency_key=self.command_idempotency_key,
            actor=self.actor,
            reason=self.reason,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and SHA-256 digest."""
        return _with_digest(self._payload_without_digest(), self.command_digest)


@dataclass(frozen=True)
class ClosePaperAccountCommand:
    """Request terminal close without asserting ledger-derived eligibility."""

    account_id: str
    expected_account_version: int
    command_idempotency_key: str
    actor: str
    reason: str
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _normalize_lifecycle_command(self)
        object.__setattr__(
            self,
            "command_digest",
            _command_digest(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, object]:
        return _lifecycle_payload(
            command_type="close_paper_account",
            target_status="closed",
            account_id=self.account_id,
            expected_account_version=self.expected_account_version,
            command_idempotency_key=self.command_idempotency_key,
            actor=self.actor,
            reason=self.reason,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and SHA-256 digest."""
        return _with_digest(self._payload_without_digest(), self.command_digest)


@dataclass(frozen=True)
class LinkApprovedPortfolioReviewCommand:
    """Request a governance-only approved-review provenance link."""

    account_id: str
    expected_account_version: int
    command_idempotency_key: str
    actor: str
    reason: str
    approved_portfolio_review: ApprovedPortfolioReviewReference
    command_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "account_id", _normalize_account_id(self.account_id))
        object.__setattr__(
            self,
            "expected_account_version",
            _normalize_expected_version(self.expected_account_version),
        )
        object.__setattr__(
            self,
            "command_idempotency_key",
            _normalize_key(self.command_idempotency_key),
        )
        object.__setattr__(self, "actor", _normalize_actor(self.actor))
        object.__setattr__(self, "reason", _normalize_reason(self.reason))
        if type(self.approved_portfolio_review) is not (
            ApprovedPortfolioReviewReference
        ):
            raise ValueError(
                "approved_portfolio_review must be an "
                "ApprovedPortfolioReviewReference"
            )
        object.__setattr__(
            self,
            "command_digest",
            _command_digest(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
            "command_type": "link_approved_portfolio_review",
            "account_id": self.account_id,
            "expected_account_version": self.expected_account_version,
            "command_idempotency_key": self.command_idempotency_key,
            "actor": self.actor,
            "reason": self.reason,
            "approved_portfolio_review": (
                self.approved_portfolio_review.to_dict()
            ),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the canonical command payload and SHA-256 digest."""
        return _with_digest(self._payload_without_digest(), self.command_digest)


def _normalize_lifecycle_command(
    command: ReactivatePaperAccountCommand | ClosePaperAccountCommand,
) -> None:
    object.__setattr__(
        command,
        "account_id",
        _normalize_account_id(command.account_id),
    )
    object.__setattr__(
        command,
        "expected_account_version",
        _normalize_expected_version(command.expected_account_version),
    )
    object.__setattr__(
        command,
        "command_idempotency_key",
        _normalize_key(command.command_idempotency_key),
    )
    object.__setattr__(command, "actor", _normalize_actor(command.actor))
    object.__setattr__(command, "reason", _normalize_reason(command.reason))


def _lifecycle_payload(
    *,
    command_type: str,
    target_status: str,
    account_id: str,
    expected_account_version: int,
    command_idempotency_key: str,
    actor: str,
    reason: str,
) -> dict[str, object]:
    return {
        "schema_version": PAPER_ACCOUNT_COMMAND_SCHEMA_VERSION,
        "command_type": command_type,
        "account_id": account_id,
        "expected_account_version": expected_account_version,
        "command_idempotency_key": command_idempotency_key,
        "actor": actor,
        "reason": reason,
        "target_lifecycle_status": target_status,
    }


def _with_digest(
    payload: dict[str, object],
    command_digest: str,
) -> dict[str, object]:
    payload["command_digest"] = command_digest
    return payload


def create_paper_account_command(
    *,
    account_identity: PaperAccountIdentity,
    initial_cash: PaperMoney,
    command_idempotency_key: str,
    actor: str,
) -> CreatePaperAccountCommand:
    """Create one validated account-creation command."""
    return CreatePaperAccountCommand(
        account_identity=account_identity,
        initial_cash=initial_cash,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
    )


def create_freeze_paper_account_command(
    *,
    account_id: str,
    expected_account_version: int,
    command_idempotency_key: str,
    actor: str,
    reason: str,
) -> FreezePaperAccountCommand:
    """Create one validated freeze command."""
    return FreezePaperAccountCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
        reason=reason,
    )


def create_reactivate_paper_account_command(
    *,
    account_id: str,
    expected_account_version: int,
    command_idempotency_key: str,
    actor: str,
    reason: str,
) -> ReactivatePaperAccountCommand:
    """Create one validated reactivation command."""
    return ReactivatePaperAccountCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
        reason=reason,
    )


def create_close_paper_account_command(
    *,
    account_id: str,
    expected_account_version: int,
    command_idempotency_key: str,
    actor: str,
    reason: str,
) -> ClosePaperAccountCommand:
    """Create one validated close request without applying it."""
    return ClosePaperAccountCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
        reason=reason,
    )


def create_link_approved_portfolio_review_command(
    *,
    account_id: str,
    expected_account_version: int,
    command_idempotency_key: str,
    actor: str,
    reason: str,
    approved_portfolio_review: ApprovedPortfolioReviewReference,
) -> LinkApprovedPortfolioReviewCommand:
    """Create one validated governance-evidence link command."""
    return LinkApprovedPortfolioReviewCommand(
        account_id=account_id,
        expected_account_version=expected_account_version,
        command_idempotency_key=command_idempotency_key,
        actor=actor,
        reason=reason,
        approved_portfolio_review=approved_portfolio_review,
    )
