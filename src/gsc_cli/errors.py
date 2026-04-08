"""Structured error handling with machine-readable exit codes."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Any, Generator

from google.auth import exceptions as auth_exceptions
from googleapiclient.errors import HttpError


class GscError(Exception):
    """Base error with structured code and exit code."""

    def __init__(
        self, message: str, code: str = "UNKNOWN", exit_code: int = 1, details: Any = None,
    ):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.details = details


class AuthError(GscError):
    def __init__(self, message: str, code: str = "AUTH_ERROR", details: Any = None):
        super().__init__(message, code=code, exit_code=3, details=details)


class UsageError(GscError):
    def __init__(self, message: str, code: str = "INVALID_ARGS", details: Any = None):
        super().__init__(message, code=code, exit_code=2, details=details)


class ApiError(GscError):
    def __init__(self, message: str, code: str = "API_ERROR", details: Any = None):
        super().__init__(message, code=code, exit_code=4, details=details)


class NoResultsError(GscError):
    def __init__(self, message: str = "No results found", details: Any = None):
        super().__init__(message, code="NO_RESULTS", exit_code=5, details=details)


def _error_envelope(code: str, message: str, details: Any = None) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, "details": details}}


@contextmanager
def handle_errors(format_func) -> Generator[None, None, None]:
    """Context manager that catches errors and renders them as structured output.

    Args:
        format_func: callable(data, is_error=False) that renders output.
                     When is_error=True, data is an error envelope dict.
    """
    try:
        yield
    except GscError as e:
        format_func(_error_envelope(e.code, str(e), e.details), is_error=True)
        sys.exit(e.exit_code)
    except auth_exceptions.DefaultCredentialsError as e:
        format_func(
            _error_envelope("AUTH_MISSING", f"No credentials found. Run: gsc auth login\n{e}"),
            is_error=True,
        )
        sys.exit(3)
    except auth_exceptions.RefreshError as e:
        format_func(
            _error_envelope("AUTH_EXPIRED", f"Token expired. Run: gsc auth login\n{e}"),
            is_error=True,
        )
        sys.exit(3)
    except HttpError as e:
        status = e.resp.status if e.resp else 0
        if status == 403:
            code = "QUOTA_EXCEEDED" if "quota" in str(e).lower() else "PERMISSION_DENIED"
        elif status == 429:
            code = "RATE_LIMITED"
        else:
            code = f"HTTP_{status}"
        format_func(_error_envelope(code, str(e)), is_error=True)
        sys.exit(4)
    except Exception as e:
        format_func(_error_envelope("UNKNOWN", str(e)), is_error=True)
        sys.exit(1)
