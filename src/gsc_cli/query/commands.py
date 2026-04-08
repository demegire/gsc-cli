"""Query CLI command — Search Analytics queries."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

import typer

from gsc_cli.auth.client import get_authenticated_service
from gsc_cli.errors import NoResultsError, UsageError, handle_errors
from gsc_cli.output import OutputFormat, detect_default_format, render, render_raw
from gsc_cli.query.pagination import MAX_ROWS_PER_REQUEST, fetch_all

VALID_DIMENSIONS = {"query", "page", "country", "device", "date", "searchAppearance"}
VALID_SEARCH_TYPES = {"web", "image", "video", "news", "discover", "googleNews"}
VALID_OPERATORS = {
    "contains": "contains",
    "equals": "equals",
    "notcontains": "notContains",
    "notequals": "notEquals",
    "includingregex": "includingRegex",
    "excludingregex": "excludingRegex",
    # Aliases
    "=": "equals",
    "!=": "notEquals",
    "~": "contains",
    "!~": "notContains",
    "re": "includingRegex",
    "!re": "excludingRegex",
}
VALID_AGGREGATION_TYPES = {"auto", "byPage", "byProperty", "byNewsShowcasePanel"}
VALID_DATA_STATES = {"all", "final"}


def _parse_dimensions(raw: str) -> list[str]:
    dims = [d.strip() for d in raw.split(",") if d.strip()]
    for d in dims:
        if d not in VALID_DIMENSIONS:
            raise UsageError(
                f"Invalid dimension: '{d}'. Valid: {', '.join(sorted(VALID_DIMENSIONS))}",
                code="INVALID_DIMENSION",
            )
    return dims


def _parse_filter(raw: str) -> dict:
    """Parse 'dimension operator value' into a GSC API filter dict.

    Examples:
        'query contains python' -> {dimension: query, operator: contains, expression: python}
        'page = /blog'          -> {dimension: page, operator: equals, expression: /blog}
    """
    parts = raw.split(None, 2)
    if len(parts) < 3:
        raise UsageError(
            f"Invalid filter: '{raw}'. Expected: 'dimension operator value'",
            code="INVALID_FILTER",
        )
    dimension, op_raw, expression = parts
    if dimension not in VALID_DIMENSIONS:
        raise UsageError(
            f"Invalid filter dimension: '{dimension}'. Valid: {', '.join(sorted(VALID_DIMENSIONS))}",
            code="INVALID_FILTER",
        )
    op = VALID_OPERATORS.get(op_raw.lower())
    if not op:
        raise UsageError(
            f"Invalid filter operator: '{op_raw}'. Valid: {', '.join(sorted(VALID_OPERATORS))}",
            code="INVALID_FILTER",
        )
    return {"dimension": dimension, "operator": op, "expression": expression}


def _format_row(row: dict, dimensions: list[str]) -> dict:
    """Flatten a GSC API row into a simple dict."""
    result: dict[str, Any] = {}
    keys = row.get("keys", [])
    for i, dim in enumerate(dimensions):
        result[dim] = keys[i] if i < len(keys) else ""
    result["clicks"] = row.get("clicks", 0)
    result["impressions"] = row.get("impressions", 0)
    result["ctr"] = round(row.get("ctr", 0), 4)
    result["position"] = round(row.get("position", 0), 1)
    return result


def query(
    site: str = typer.Option(..., "--site", "-s", help="Site URL (e.g. sc-domain:example.com)."),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="Start date YYYY-MM-DD (default: 28 days ago)."),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="End date YYYY-MM-DD (default: yesterday)."),
    dimensions: Optional[str] = typer.Option(None, "--dimensions", "-d", help="Comma-separated: query,page,country,device,date,searchAppearance."),
    filter_strs: Optional[list[str]] = typer.Option(None, "--filter", help="Filter: 'dimension operator value'. Repeatable."),
    search_type: str = typer.Option("web", "--search-type", "-t", help="web, image, video, news, discover, googleNews."),
    aggregation_type: str = typer.Option("auto", "--aggregation-type", help="auto, byPage, byProperty, byNewsShowcasePanel."),
    data_state: str = typer.Option("final", "--data-state", help="all (include fresh data) or final (default)."),
    row_limit: int = typer.Option(1000, "--row-limit", "-n", help="Rows per request (max 25000)."),
    start_row: int = typer.Option(0, "--start-row", help="Starting row offset."),
    fetch_all_flag: bool = typer.Option(False, "--all", help="Auto-paginate to fetch all results."),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Output format."),
) -> None:
    """Query Search Console analytics data.

    Examples:
      gsc query --site sc-domain:example.com --dimensions query,page
      gsc query -s sc-domain:example.com -d query --filter "query contains python"
      gsc query -s sc-domain:example.com -d date,query --all --format csv
    """
    fmt = fmt or detect_default_format()

    def _out(data, is_error=False):
        if is_error:
            render_raw(data, fmt=fmt, is_error=True)

    with handle_errors(_out):
        # Validate inputs
        dim_list = _parse_dimensions(dimensions) if dimensions else []

        if search_type not in VALID_SEARCH_TYPES:
            raise UsageError(
                f"Invalid search type: '{search_type}'. Valid: {', '.join(sorted(VALID_SEARCH_TYPES))}",
                code="INVALID_SEARCH_TYPE",
            )

        if aggregation_type not in VALID_AGGREGATION_TYPES:
            raise UsageError(
                f"Invalid aggregation type: '{aggregation_type}'. Valid: {', '.join(sorted(VALID_AGGREGATION_TYPES))}",
                code="INVALID_AGGREGATION_TYPE",
            )

        if data_state not in VALID_DATA_STATES:
            raise UsageError(
                f"Invalid data state: '{data_state}'. Valid: {', '.join(sorted(VALID_DATA_STATES))}",
                code="INVALID_DATA_STATE",
            )

        # Date defaults
        end_d = date.fromisoformat(end_date) if end_date else date.today() - timedelta(days=1)
        start_d = date.fromisoformat(start_date) if start_date else end_d - timedelta(days=27)

        # Build request body per GSC API spec
        # POST https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query
        body: dict[str, Any] = {
            "startDate": start_d.isoformat(),
            "endDate": end_d.isoformat(),
            "type": search_type,
            "aggregationType": aggregation_type,
            "dataState": data_state,
        }
        if dim_list:
            body["dimensions"] = dim_list
        if row_limit != 1000:
            body["rowLimit"] = min(row_limit, MAX_ROWS_PER_REQUEST)
        if start_row > 0:
            body["startRow"] = start_row

        # Parse filters
        filters = []
        if filter_strs:
            for f in filter_strs:
                filters.append(_parse_filter(f))
        if filters:
            body["dimensionFilterGroups"] = [{"filters": filters}]

        # Execute
        service = get_authenticated_service()

        if fetch_all_flag:
            rows = fetch_all(service, site, body)
        else:
            response = (
                service.searchanalytics()
                .query(siteUrl=site, body=body)
                .execute()
            )
            rows = response.get("rows", [])

        if not rows:
            raise NoResultsError()

        # Format output
        data = [_format_row(r, dim_list) for r in rows]
        meta = {
            "site": site,
            "date_range": [start_d.isoformat(), end_d.isoformat()],
            "dimensions": dim_list,
            "search_type": search_type,
            "has_more": len(rows) == (MAX_ROWS_PER_REQUEST if fetch_all_flag else row_limit),
        }
        render(data, meta=meta, fmt=fmt)
