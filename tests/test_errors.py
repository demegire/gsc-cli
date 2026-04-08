"""Tests for error handling."""

from gsc_cli.errors import ApiError, AuthError, GscError, NoResultsError, UsageError


def test_auth_error():
    e = AuthError("no creds")
    assert e.exit_code == 3
    assert e.code == "AUTH_ERROR"


def test_usage_error():
    e = UsageError("bad arg")
    assert e.exit_code == 2
    assert e.code == "INVALID_ARGS"


def test_api_error():
    e = ApiError("quota exceeded", code="QUOTA_EXCEEDED")
    assert e.exit_code == 4
    assert e.code == "QUOTA_EXCEEDED"


def test_no_results_error():
    e = NoResultsError()
    assert e.exit_code == 5
    assert e.code == "NO_RESULTS"


def test_custom_code():
    e = GscError("custom", code="CUSTOM", exit_code=99)
    assert e.exit_code == 99
    assert e.code == "CUSTOM"
