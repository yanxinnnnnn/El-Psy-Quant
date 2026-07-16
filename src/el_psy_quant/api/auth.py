"""Minimal Founder-only authentication for the versioned local API."""

from __future__ import annotations

import base64
import binascii
import os
import secrets
from dataclasses import dataclass
from http import HTTPStatus

from fastapi import Request

from el_psy_quant.api.errors import PublicApiError

FOUNDER_USERNAME_ENV = "EL_PSY_QUANT_FOUNDER_USERNAME"
FOUNDER_PASSWORD_ENV = "EL_PSY_QUANT_FOUNDER_PASSWORD"
FOUNDER_AUTH_REALM = "El-Psy-Quant Founder"
_MAX_CREDENTIAL_LENGTH = 128
_MAX_AUTHORIZATION_LENGTH = 512


@dataclass(frozen=True, repr=False)
class FounderAuthConfig:
    """One in-memory local Founder credential pair."""

    username: str
    password: str

    def __repr__(self) -> str:
        """Keep authentication material out of logs and assertion output."""
        return "FounderAuthConfig(username=<redacted>, password=<redacted>)"


def _validate_credential(value: object, *, name: str, allow_colon: bool) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if len(value) > _MAX_CREDENTIAL_LENGTH:
        raise ValueError(f"{name} must be at most {_MAX_CREDENTIAL_LENGTH} characters")
    if any(ord(character) < 33 or ord(character) > 126 for character in value):
        raise ValueError(f"{name} must use visible ASCII characters")
    if not allow_colon and ":" in value:
        raise ValueError(f"{name} must not contain a colon")
    return value


def resolve_founder_auth_config(
    *,
    username: str | None = None,
    password: str | None = None,
) -> FounderAuthConfig | None:
    """Resolve optional paired credentials without performing any I/O."""
    if username is None and password is None:
        username = os.getenv(FOUNDER_USERNAME_ENV)
        password = os.getenv(FOUNDER_PASSWORD_ENV)
    if username is None and password is None:
        return None
    if username is None or password is None:
        raise ValueError(
            f"{FOUNDER_USERNAME_ENV} and {FOUNDER_PASSWORD_ENV} must be configured together"
        )
    return FounderAuthConfig(
        username=_validate_credential(
            username,
            name=FOUNDER_USERNAME_ENV,
            allow_colon=False,
        ),
        password=_validate_credential(
            password,
            name=FOUNDER_PASSWORD_ENV,
            allow_colon=True,
        ),
    )


def _decode_basic_credentials(value: str | None) -> tuple[str, str] | None:
    if value is None or len(value) > _MAX_AUTHORIZATION_LENGTH:
        return None
    scheme, separator, encoded = value.partition(" ")
    if separator != " " or scheme.lower() != "basic" or not encoded:
        return None
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("ascii")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    username, separator, password = decoded.partition(":")
    if separator != ":":
        return None
    return username, password


def _authentication_required() -> PublicApiError:
    return PublicApiError(
        status_code=HTTPStatus.UNAUTHORIZED,
        code="founder_authentication_required",
        message="Founder authentication required",
        headers={
            "Cache-Control": "no-store",
            "WWW-Authenticate": f'Basic realm="{FOUNDER_AUTH_REALM}", charset="UTF-8"',
        },
    )


async def require_founder_auth(request: Request) -> None:
    """Require the configured local credential pair for every versioned route."""
    config = getattr(request.app.state, "founder_auth", None)
    if config is None:
        return
    if not isinstance(config, FounderAuthConfig):
        raise _authentication_required()

    supplied = _decode_basic_credentials(request.headers.get("Authorization"))
    if supplied is None:
        raise _authentication_required()
    supplied_username, supplied_password = supplied
    username_matches = secrets.compare_digest(supplied_username, config.username)
    password_matches = secrets.compare_digest(supplied_password, config.password)
    if not (username_matches and password_matches):
        raise _authentication_required()


__all__ = [
    "FOUNDER_PASSWORD_ENV",
    "FOUNDER_USERNAME_ENV",
    "FounderAuthConfig",
    "require_founder_auth",
    "resolve_founder_auth_config",
]
