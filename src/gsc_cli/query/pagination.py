"""Auto-pagination for Search Analytics queries."""

from __future__ import annotations

MAX_ROWS_PER_REQUEST = 25000
MAX_TOTAL_ROWS = 50000


def fetch_all(service, site_url: str, request_body: dict) -> list[dict]:
    """Fetch all rows by paginating with startRow.

    The GSC API returns at most 25,000 rows per request.
    We paginate until we get fewer rows than requested or hit 50k total.
    """
    all_rows: list[dict] = []
    start_row = 0
    body = {**request_body, "rowLimit": MAX_ROWS_PER_REQUEST}

    while start_row < MAX_TOTAL_ROWS:
        body["startRow"] = start_row
        response = (
            service.searchanalytics()
            .query(siteUrl=site_url, body=body)
            .execute()
        )
        rows = response.get("rows", [])
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < MAX_ROWS_PER_REQUEST:
            break
        start_row += len(rows)

    return all_rows
