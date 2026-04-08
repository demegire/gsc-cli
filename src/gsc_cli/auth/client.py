"""Authenticated Google API client factory."""

from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from gsc_cli.config import load_oauth_token, load_service_account, save_oauth_token
from gsc_cli.errors import AuthError

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SCOPES_WRITE = ["https://www.googleapis.com/auth/webmasters"]


def get_authenticated_service(*, readonly: bool = True):
    """Build an authenticated webmasters v3 service.

    Checks for service account first, then OAuth token.
    Returns a googleapiclient Resource.
    """
    scopes = SCOPES if readonly else SCOPES_WRITE

    # Try service account
    sa_data = load_service_account()
    if sa_data:
        creds = service_account.Credentials.from_service_account_info(sa_data, scopes=scopes)
        return build("searchconsole", "v1", credentials=creds)

    # Try OAuth token
    token_data = load_oauth_token()
    if token_data:
        creds = Credentials.from_authorized_user_info(token_data, scopes=scopes)
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
