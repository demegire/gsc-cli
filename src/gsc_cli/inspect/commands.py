"""URL Inspection CLI command."""

from __future__ import annotations

from typing import Any, Optional

import typer

from gsc_cli.auth.client import get_authenticated_service
from gsc_cli.errors import handle_errors
from gsc_cli.output import OutputFormat, detect_default_format, render, render_raw


def inspect_url(
    url: str = typer.Argument(..., help="URL to inspect."),
    site: str = typer.Option(..., "--site", "-s", help="Site URL (e.g. sc-domain:example.com)."),
    language: str = typer.Option("en-US", "--language", "-l", help="Language code (BCP-47) for messages."),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Output format."),
) -> None:
    """Inspect a URL's index status, mobile usability, and rich results.

    Uses the URL Inspection API:
    POST https://searchconsole.googleapis.com/v1/urlInspection/index:inspect

    Example:
      gsc inspect https://example.com/page --site sc-domain:example.com
    """
    fmt = fmt or detect_default_format()

    def _out(data, is_error=False):
        if is_error:
            render_raw(data, fmt=fmt, is_error=True)

    with handle_errors(_out):
        service = get_authenticated_service()

        # URL Inspection API request body
        body = {
            "inspectionUrl": url,
            "siteUrl": site,
            "languageCode": language,
        }
        response = service.urlInspection().index().inspect(body=body).execute()
        result = response.get("inspectionResult", {})

        # Flatten key fields for table/csv display
        index_status = result.get("indexStatusResult", {})
        mobile = result.get("mobileUsabilityResult", {})
        rich_results = result.get("richResultsResult", {})

        data = [
            {
                "url": url,
                "verdict": index_status.get("verdict", ""),
                "coverage_state": index_status.get("coverageState", ""),
                "indexing_state": index_status.get("indexingState", ""),
                "robots_txt_state": index_status.get("robotsTxtState", ""),
                "last_crawl_time": index_status.get("lastCrawlTime", ""),
                "page_fetch_state": index_status.get("pageFetchState", ""),
                "crawled_as": index_status.get("crawledAs", ""),
                "mobile_verdict": mobile.get("verdict", ""),
                "rich_results_verdict": rich_results.get("verdict", ""),
            }
        ]

        meta: dict[str, Any] = {
            "site": site,
            "inspected_url": url,
            "full_result": result,  # Include full API response in meta for agents
        }
        render(data, meta=meta, fmt=fmt)
