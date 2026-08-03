"""Authenticated Google API client factory."""

from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from gsc_cli.config import load_oauth_token, load_service_account, save_oauth_token
from gsc_cli.errors import AuthError

READ_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
WRITE_SCOPE = "https://www.googleapis.com/auth/webmasters"

SCOPES = [READ_SCOPE]
SCOPES_WRITE = [WRITE_SCOPE]

READONLY_TOKEN_MESSAGE = (
    "This Search Console connection is read-only: the stored token was granted "
    f"{READ_SCOPE} but this command needs {WRITE_SCOPE}. Reconnect Search "
    "Console to grant write access, then retry."
)


def get_authenticated_service(*, require_write: bool = False, readonly: bool | None = None):
    """Build an authenticated webmasters v3 service.

    Checks for service account first, then OAuth token.
    Returns a googleapiclient Resource.

    Write commands pass ``require_write=True``. For OAuth tokens we check the
    scopes recorded in the token file *before* touching the network, so a
    read-only connection fails fast with AUTH_SCOPE_READONLY instead of a 403
    at call time or a "Scope has changed" RefreshError at refresh time.

    ``readonly`` is the pre-0.2 spelling, kept so existing callers and ad-hoc
    scripts keep working: readonly=False means the same as require_write=True.
    """
    if readonly is not None:
        require_write = not readonly

    # Service accounts request their scopes up front — there is no prior grant
    # to inspect, so ask for exactly what this command needs.
    sa_data = load_service_account()
    if sa_data:
        scopes = SCOPES_WRITE if require_write else SCOPES
        creds = service_account.Credentials.from_service_account_info(sa_data, scopes=scopes)
        return build("searchconsole", "v1", credentials=creds)

    token_data = load_oauth_token()
    if token_data:
        granted = [s for s in (token_data.get("scopes") or []) if s]
        if require_write and WRITE_SCOPE not in granted:
            raise AuthError(
                READONLY_TOKEN_MESSAGE,
                code="AUTH_SCOPE_READONLY",
                details={"granted_scopes": granted, "required_scope": WRITE_SCOPE},
            )
        # Build from the scopes the token was actually granted, never from a
        # hardcoded list: google-auth compares requested against granted on
        # refresh and raises RefreshError when we ask for more than we hold.
        creds = Credentials.from_authorized_user_info(token_data, scopes=granted or None)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_oauth_token(_creds_to_dict(creds))
        if not creds.valid:
            raise AuthError("OAuth token is invalid. Run: gsc auth login", code="AUTH_INVALID")
        return build("searchconsole", "v1", credentials=creds)

    raise AuthError(
        "No credentials found. Run: gsc auth login  OR  gsc auth service-account --key-file PATH",
        code="AUTH_MISSING",
    )


def _creds_to_dict(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
    }
