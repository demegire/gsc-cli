"""Sites CLI commands."""

from __future__ import annotations

from typing import Optional

import typer

from gsc_cli.auth.client import get_authenticated_service
from gsc_cli.errors import handle_errors
from gsc_cli.output import OutputFormat, detect_default_format, render, render_raw

app = typer.Typer(name="sites", help="Manage Search Console sites/properties.")


@app.command("list")
def list_sites(
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Output format."),
) -> None:
    """List all verified sites/properties."""
    fmt = fmt or detect_default_format()

    def _out(data, is_error=False):
        if is_error:
            render_raw(data, fmt=fmt, is_error=True)
        else:
            render(data, fmt=fmt)

    with handle_errors(_out):
        service = get_authenticated_service()
        # sites.list uses the webmasters v3 API endpoint
        # GET https://www.googleapis.com/webmasters/v3/sites
        response = service.sites().list().execute()
        entries = response.get("siteEntry", [])
        data = [
            {"site_url": e["siteUrl"], "permission": e["permissionLevel"]}
            for e in entries
        ]
        render(data, meta={"count": len(data)}, fmt=fmt)
