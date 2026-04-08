"""Shared test fixtures."""

import pytest


@pytest.fixture
def mock_service(mocker):
    """Mock the Google API service."""
    service = mocker.MagicMock()
    mocker.patch("gsc_cli.auth.client.get_authenticated_service", return_value=service)
    return service
