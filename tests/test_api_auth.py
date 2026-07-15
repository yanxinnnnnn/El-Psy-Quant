"""Tests for the minimal Founder-only API authentication boundary."""

from base64 import b64encode
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.api.auth import (
    FOUNDER_PASSWORD_ENV,
    FOUNDER_USERNAME_ENV,
    FounderAuthConfig,
    resolve_founder_auth_config,
)
from el_psy_quant.api.middleware import REQUEST_ID_HEADER
from el_psy_quant.api.schemas import ApiErrorResponse


def _basic(username: str, password: str) -> str:
    encoded = b64encode(f"{username}:{password}".encode("ascii")).decode("ascii")
    return f"Basic {encoded}"


def test_authentication_is_disabled_when_both_settings_are_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(FOUNDER_USERNAME_ENV, raising=False)
    monkeypatch.delenv(FOUNDER_PASSWORD_ENV, raising=False)

    assert resolve_founder_auth_config() is None
    assert TestClient(create_app()).get("/api/v1/health").status_code == 200


@pytest.mark.parametrize(
    ("username", "password"),
    (("founder", None), (None, "local-secret")),
)
def test_partial_authentication_configuration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    username: str | None,
    password: str | None,
) -> None:
    monkeypatch.delenv(FOUNDER_USERNAME_ENV, raising=False)
    monkeypatch.delenv(FOUNDER_PASSWORD_ENV, raising=False)
    if username is not None:
        monkeypatch.setenv(FOUNDER_USERNAME_ENV, username)
    if password is not None:
        monkeypatch.setenv(FOUNDER_PASSWORD_ENV, password)

    with pytest.raises(ValueError, match="must be configured together"):
        create_app()


@pytest.mark.parametrize(
    ("username", "password"),
    (
        ("founder:name", "local-secret"),
        ("founder name", "local-secret"),
        ("founder", "local secret"),
        ("founder", ""),
        ("f" * 129, "local-secret"),
    ),
)
def test_invalid_explicit_credentials_are_rejected_without_exposing_values(
    username: str,
    password: str,
) -> None:
    with pytest.raises(ValueError):
        create_app(founder_username=username, founder_password=password)


def test_auth_config_representation_redacts_both_values() -> None:
    config = FounderAuthConfig(username="private-founder", password="private-secret")

    representation = repr(config)

    assert "private-founder" not in representation
    assert "private-secret" not in representation
    assert representation.count("<redacted>") == 2


def test_configured_authentication_protects_every_versioned_route() -> None:
    client = TestClient(
        create_app(founder_username="founder", founder_password="local-secret")
    )

    health = client.get("/api/v1/health")
    strategies = client.get("/api/v1/strategies")

    for response in (health, strategies):
        assert response.status_code == 401
        assert response.headers["www-authenticate"].startswith(
            'Basic realm="El-Psy-Quant Founder"'
        )
        assert response.headers["cache-control"] == "no-store"
        payload = ApiErrorResponse.model_validate(response.json())
        assert payload.error.code == "founder_authentication_required"
        assert payload.error.message == "Founder authentication required"
        assert payload.request_id == response.headers[REQUEST_ID_HEADER]
        assert str(UUID(payload.request_id)) == payload.request_id
        assert "local-secret" not in response.text


@pytest.mark.parametrize(
    "authorization",
    (
        _basic("founder", "wrong-secret"),
        _basic("wrong-founder", "local-secret"),
        "Bearer local-secret",
        "Basic not-base64!",
        "Basic bm8tY29sb24=",
        "Basic " + "A" * 513,
    ),
)
def test_invalid_authorization_values_are_safely_rejected(
    authorization: str,
) -> None:
    response = TestClient(
        create_app(founder_username="founder", founder_password="local-secret")
    ).get("/api/v1/health", headers={"Authorization": authorization})

    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "founder_authentication_required",
        "message": "Founder authentication required",
    }


def test_valid_authorization_reaches_existing_routes_unchanged() -> None:
    client = TestClient(
        create_app(founder_username="founder", founder_password="local-secret")
    )
    headers = {"Authorization": _basic("founder", "local-secret")}

    health = client.get("/api/v1/health", headers=headers)
    strategies = client.get("/api/v1/strategies", headers=headers)

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "service": "el-psy-quant",
        "api_version": "v1",
    }
    assert strategies.status_code == 200
    assert strategies.json()["strategies"]
