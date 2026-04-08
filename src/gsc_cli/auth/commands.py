"""Auth CLI commands: login, service-account, status."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from gsc_cli.auth.client import SCOPES, _creds_to_dict
from gsc_cli.config import (
    get_config_dir,
    load_client_secrets,
    load_oauth_token,
    load_service_account,
    save_client_secrets,
    save_oauth_token,
    save_service_account,
)

app = typer.Typer(name="auth", help="Manage authentication credentials.")


@app.command()
def login(
    client_secrets_file: Path = typer.Option(
        None,
        "--client-secrets",
        help="Path to OAuth client_secrets.json from Google Cloud Console. "
        "Only needed on first login; cached afterwards.",
    ),
) -> None:
    """Authenticate via OAuth2 browser flow."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    secrets = None
    if client_secrets_file:
        secrets = json.loads(client_secrets_file.read_text())
        save_client_secrets(secrets)
    else:
        secrets = load_client_secrets()

    if not secrets:
        typer.echo(
            "No client_secrets.json found. Provide one with --client-secrets.\n"
            "Create OAuth credentials at: https://console.cloud.google.com/apis/credentials",
            err=True,
        )
        raise typer.Exit(3)

    flow = InstalledAppFlow.from_client_config(secrets, scopes=SCOPES)
    creds = flow.run_local_server(port=0)
    save_oauth_token(_creds_to_dict(creds))
    typer.echo("Authenticated successfully. Credentials saved.")


@app.command("service-account")
def service_account(
    key_file: Path = typer.Option(..., "--key-file", help="Path to service account JSON key file."),
) -> None:
    """Configure a service account for authentication."""
    if not key_file.exists():
        typer.echo(f"File not found: {key_file}", err=True)
        raise typer.Exit(2)

    data = json.loads(key_file.read_text())
    if "type" not in data or data["type"] != "service_account":
        msg = "Invalid service account key file (missing 'type': 'service_account')."
        typer.echo(msg, err=True)
        raise typer.Exit(2)

    save_service_account(data)
    typer.echo(f"Service account configured: {data.get('client_email', 'unknown')}")


@app.command()
def status() -> None:
    """Show current authentication status."""
    config_dir = get_config_dir()
    result: dict = {"authenticated": False, "method": None, "config_dir": str(config_dir)}

    sa = load_service_account()
    if sa:
        result["authenticated"] = True
        result["method"] = "service_account"
        result["email"] = sa.get("client_email", "unknown")
        _print_status(result)
        return

    token = load_oauth_token()
    if token:
        result["authenticated"] = True
        result["method"] = "oauth"
        result["has_refresh_token"] = bool(token.get("refresh_token"))
        _print_status(result)
        return

    _print_status(result)


def _print_status(result: dict) -> None:
    import sys
    if sys.stdout.isatty():
        if result["authenticated"]:
            typer.echo(f"Authenticated via {result['method']}")
            if result.get("email"):
                typer.echo(f"  Email: {result['email']}")
        else:
            typer.echo("Not authenticated. Run: gsc auth login")
    else:
        print(json.dumps({"ok": True, "data": result}, indent=2))
