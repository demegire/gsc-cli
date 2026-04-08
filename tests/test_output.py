"""Tests for output rendering."""

import json

from gsc_cli.output import OutputFormat, render


def test_json_output(capsys):
    data = [{"query": "test", "clicks": 10}]
    render(data, meta={"site": "example.com"}, fmt=OutputFormat.json)
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["data"] == data
    assert out["meta"]["site"] == "example.com"
    assert out["meta"]["row_count"] == 1


def test_json_empty(capsys):
    render([], meta={}, fmt=OutputFormat.json)
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["data"] == []
    assert out["meta"]["row_count"] == 0


def test_csv_output(capsys):
    data = [
        {"query": "foo", "clicks": 5},
        {"query": "bar", "clicks": 3},
    ]
    render(data, fmt=OutputFormat.csv)
    lines = [line.strip() for line in capsys.readouterr().out.strip().split("\n")]
    assert lines[0] == "query,clicks"
    assert lines[1] == "foo,5"
    assert lines[2] == "bar,3"


def test_csv_empty(capsys):
    render([], fmt=OutputFormat.csv)
    assert capsys.readouterr().out == ""


def test_table_output(capsys):
    data = [{"query": "test", "clicks": 42}]
    render(data, fmt=OutputFormat.table)
    out = capsys.readouterr().out
    assert "test" in out
    assert "42" in out
