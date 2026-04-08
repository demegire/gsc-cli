"""Rendering layer: JSON envelope, Rich tables, CSV. TTY-aware defaults."""

from __future__ import annotations

import csv
import json
import sys
from enum import Enum
from typing import Any


class OutputFormat(str, Enum):
    json = "json"
    table = "table"
    csv = "csv"


def detect_default_format() -> OutputFormat:
    return OutputFormat.table if sys.stdout.isatty() else OutputFormat.json


def render(
    data: list[dict],
    *,
    meta: dict[str, Any] | None = None,
    fmt: OutputFormat,
    columns: list[str] | None = None,
) -> None:
    """Render successful result in the chosen format."""
    if fmt == OutputFormat.json:
        _render_json(data, meta)
    elif fmt == OutputFormat.table:
        _render_table(data, columns)
    elif fmt == OutputFormat.csv:
        _render_csv(data, columns)


def render_raw(envelope: dict, *, fmt: OutputFormat, is_error: bool = False) -> None:
    """Render a pre-built envelope (used by handle_errors)."""
    if fmt == OutputFormat.json:
        print(json.dumps(envelope, indent=2, default=str))
    else:
        if is_error:
            err = envelope.get("error", {})
            sys.stderr.write(f"Error [{err.get('code', 'UNKNOWN')}]: {err.get('message', '')}\n")
        else:
            print(json.dumps(envelope, indent=2, default=str))


def _render_json(data: list[dict], meta: dict[str, Any] | None) -> None:
    envelope = {"ok": True, "data": data, "meta": meta or {}}
    envelope["meta"]["row_count"] = len(data)
    print(json.dumps(envelope, indent=2, default=str))


def _render_table(data: list[dict], columns: list[str] | None) -> None:
    if not data:
        from rich.console import Console
        Console(stderr=True).print("[dim]No results[/dim]")
        return

    from rich.console import Console
    from rich.table import Table

    console = Console()
    cols = columns or list(data[0].keys())

    table = Table(show_header=True, header_style="bold cyan")
    for col in cols:
        justify = "right" if _is_numeric_col(data, col) else "left"
        table.add_column(col, justify=justify)

    for row in data:
        table.add_row(*(str(row.get(c, "")) for c in cols))

    console.print(table)


def _render_csv(data: list[dict], columns: list[str] | None) -> None:
    if not data:
        return
    cols = columns or list(data[0].keys())
    writer = csv.DictWriter(sys.stdout, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for row in data:
        writer.writerow(row)


def _is_numeric_col(data: list[dict], col: str) -> bool:
    for row in data:
        v = row.get(col)
        if v is not None:
            return isinstance(v, (int, float))
    return False
