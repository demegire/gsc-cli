"""Sitemaps CLI commands.

Wraps the webmasters v3 sitemaps resource:
  GET    .../sites/{siteUrl}/sitemaps            -> list
  GET    .../sites/{siteUrl}/sitemaps/{feedpath} -> get
  PUT    .../sites/{siteUrl}/sitemaps/{feedpath} -> submit
  DELETE .../sites/{siteUrl}/sitemaps/{feedpath} -> delete

`submit` and `delete` need the read-write scope
(https://www.googleapis.com/auth/webmasters); `list` and `get` do not.
"""

from __future__ import annotations

from typing import Any, Optional

import typer

from gsc_cli.auth.client import get_authenticated_service
from gsc_cli.errors import handle_errors
from gsc_cli.output import OutputFormat, detect_default_format, render, render_raw

app = typer.Typer(name="sitemaps", help="List, inspect, submit, and delete sitemaps.")

SITE_OPTION = typer.Option(..., "--site", "-s", help="Site URL (e.g. sc-domain:example.com).")
FEEDPATH_ARGUMENT = typer.Argument(
    ..., help="Full sitemap URL (e.g. https://example.com/sitemap.xml)."
)


def _row(entry: dict) -> dict:
    """Flatten one sitemap resource to the fields worth acting on.

    `lastSubmitted` is the acceptance timestamp Google records for a submission;
    `lastDownloaded` is when it last actually fetched the file. A recent
    `lastDownloaded` with zero errors/warnings means Google is already reading
    the sitemap fine and resubmitting it changes nothing.
    """
    return {
        "path": entry.get("path", ""),
        "type": entry.get("type", ""),
        "last_submitted": entry.get("lastSubmitted", ""),
        "last_downloaded": entry.get("lastDownloaded", ""),
        "is_pending": entry.get("isPending", ""),
        "is_sitemaps_index": entry.get("isSitemapsIndex", ""),
        "warnings": entry.get("warnings", ""),
        "errors": entry.get("errors", ""),
    }


def _renderer(fmt: OutputFormat):
    def _out(data, is_error=False):
        if is_error:
            render_raw(data, fmt=fmt, is_error=True)

    return _out


@app.command("list")
def list_sitemaps(
    site: str = SITE_OPTION,
    sitemap_index: Optional[str] = typer.Option(
        None,
        "--sitemap-index",
        help="Only list sitemaps contained in this sitemap index URL.",
    ),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Output format."),
) -> None:
    """List the sitemaps Google has on file for a property.

    Example:
      gsc sitemaps list -s sc-domain:example.com
    """
    fmt = fmt or detect_default_format()

    with handle_errors(_renderer(fmt)):
        service = get_authenticated_service()
        kwargs: dict[str, Any] = {"siteUrl": site}
        if sitemap_index:
            kwargs["sitemapIndex"] = sitemap_index
        response = service.sitemaps().list(**kwargs).execute()
        data = [_row(entry) for entry in response.get("sitemap", [])]
        render(data, meta={"site": site}, fmt=fmt)


@app.command("get")
def get_sitemap(
    feedpath: str = FEEDPATH_ARGUMENT,
    site: str = SITE_OPTION,
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Output format."),
) -> None:
    """Show Google's record for one sitemap.

    Check this before submitting: a recent `last_downloaded` with 0 errors and
    0 warnings means Google is already reading the sitemap and a resubmission
    will not change anything.

    Example:
      gsc sitemaps get https://example.com/sitemap.xml -s sc-domain:example.com
    """
    fmt = fmt or detect_default_format()

    with handle_errors(_renderer(fmt)):
        service = get_authenticated_service()
        entry = service.sitemaps().get(siteUrl=site, feedpath=feedpath).execute()
        render(
            [_row(entry)],
            meta={"site": site, "feedpath": feedpath, "full_result": entry},
            fmt=fmt,
        )


@app.command("submit")
def submit_sitemap(
    feedpath: str = FEEDPATH_ARGUMENT,
    site: str = SITE_OPTION,
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Output format."),
) -> None:
    """Submit (or resubmit) a sitemap. Needs the read-write scope.

    The API returns an empty 204 on success, so we read the record back and
    render Google's own `last_submitted` timestamp — that is the acceptance
    time worth recording.

    Example:
      gsc sitemaps submit https://example.com/sitemap.xml -s sc-domain:example.com
    """
    fmt = fmt or detect_default_format()

    with handle_errors(_renderer(fmt)):
        service = get_authenticated_service(require_write=True)
        service.sitemaps().submit(siteUrl=site, feedpath=feedpath).execute()

        meta: dict[str, Any] = {"site": site, "feedpath": feedpath, "submitted": True}
        try:
            entry = service.sitemaps().get(siteUrl=site, feedpath=feedpath).execute()
        except Exception as exc:  # noqa: BLE001 - read-back is best effort
            # The submission itself succeeded; only the confirmation read
            # failed. Say so rather than reporting the whole command as failed.
            meta["readback_error"] = str(exc)
            render([], meta=meta, fmt=fmt)
            return
        render([_row(entry)], meta=meta, fmt=fmt)


@app.command("delete")
def delete_sitemap(
    feedpath: str = FEEDPATH_ARGUMENT,
    site: str = SITE_OPTION,
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Output format."),
) -> None:
    """Remove a sitemap from the property. Needs the read-write scope.

    This only tells Google to stop tracking the sitemap; it does not delete the
    file or de-index the URLs it listed.

    Example:
      gsc sitemaps delete https://example.com/old-sitemap.xml -s sc-domain:example.com
    """
    fmt = fmt or detect_default_format()

    with handle_errors(_renderer(fmt)):
        service = get_authenticated_service(require_write=True)
        service.sitemaps().delete(siteUrl=site, feedpath=feedpath).execute()
        render([], meta={"site": site, "feedpath": feedpath, "deleted": True}, fmt=fmt)
