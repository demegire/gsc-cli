"""Tests for query command logic."""

import pytest

from gsc_cli.errors import UsageError
from gsc_cli.query.commands import _format_row, _parse_dimensions, _parse_filter


class TestParseDimensions:
    def test_single(self):
        assert _parse_dimensions("query") == ["query"]

    def test_multiple(self):
        assert _parse_dimensions("query,page,date") == ["query", "page", "date"]

    def test_with_spaces(self):
        assert _parse_dimensions("query, page") == ["query", "page"]

    def test_invalid(self):
        with pytest.raises(UsageError, match="Invalid dimension"):
            _parse_dimensions("query,invalid")

    def test_all_valid(self):
        dims = _parse_dimensions("query,page,country,device,date,searchAppearance")
        assert len(dims) == 6


class TestParseFilter:
    def test_contains(self):
        f = _parse_filter("query contains python")
        assert f == {"dimension": "query", "operator": "contains", "expression": "python"}

    def test_equals(self):
        f = _parse_filter("page equals /blog")
        assert f == {"dimension": "page", "operator": "equals", "expression": "/blog"}

    def test_alias_equals(self):
        f = _parse_filter("page = /blog")
        assert f["operator"] == "equals"

    def test_alias_not_equals(self):
        f = _parse_filter("query != test")
        assert f["operator"] == "notEquals"

    def test_alias_tilde(self):
        f = _parse_filter("query ~ python")
        assert f["operator"] == "contains"

    def test_regex(self):
        f = _parse_filter("query includingRegex ^how to")
        assert f == {
            "dimension": "query",
            "operator": "includingRegex",
            "expression": "^how to",
        }

    def test_excluding_regex(self):
        f = _parse_filter("query excludingRegex spam")
        assert f["operator"] == "excludingRegex"

    def test_case_insensitive_operator(self):
        f = _parse_filter("query CONTAINS test")
        assert f["operator"] == "contains"

    def test_invalid_dimension(self):
        with pytest.raises(UsageError, match="Invalid filter dimension"):
            _parse_filter("invalid contains test")

    def test_invalid_operator(self):
        with pytest.raises(UsageError, match="Invalid filter operator"):
            _parse_filter("query badop test")

    def test_too_few_parts(self):
        with pytest.raises(UsageError, match="Invalid filter"):
            _parse_filter("query contains")

    def test_expression_with_spaces(self):
        f = _parse_filter("query contains hello world")
        assert f["expression"] == "hello world"


class TestFormatRow:
    def test_basic(self):
        row = {
            "keys": ["python", "/blog"],
            "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 3.5,
        }
        result = _format_row(row, ["query", "page"])
        assert result == {
            "query": "python",
            "page": "/blog",
            "clicks": 10,
            "impressions": 100,
            "ctr": 0.1,
            "position": 3.5,
        }

    def test_no_dimensions(self):
        row = {"keys": [], "clicks": 5, "impressions": 50, "ctr": 0.1, "position": 2.0}
        result = _format_row(row, [])
        assert result["clicks"] == 5
        assert "query" not in result

    def test_missing_keys(self):
        row = {"keys": ["val1"], "clicks": 1, "impressions": 10, "ctr": 0.1, "position": 1.0}
        result = _format_row(row, ["dim1", "dim2"])
        assert result["dim1"] == "val1"
        assert result["dim2"] == ""
