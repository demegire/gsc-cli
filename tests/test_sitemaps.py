"""Tests for the sitemaps command group and the write-scope pre-check."""

import json

import pytest
from typer.testing import CliRunner

from gsc_cli.auth.client import READ_SCOPE, WRITE_SCOPE, get_authenticated_service
from gsc_cli.errors import AuthError
from gsc_cli.main import app
from gsc_cli.sitemaps.commands import _row

runner = CliRunner()

READONLY_TOKEN = {
    "token": "at",
    "refresh_token": "rt",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "cid",
    "client_secret": "cs",
    "scopes": [READ_SCOPE, "openid"],
}
WRITE_TOKEN = {**READONLY_TOKEN, "scopes": [WRITE_SCOPE, "openid"]}

SITEMAP_ENTRY = {
    "path": "https://example.com/sitemap.xml",
    "lastSubmitted": "2026-04-27T11:50:07.390Z",
    "lastDownloaded": "2026-07-26T23:56:11.991Z",
    "isPending": False,
    "isSitemapsIndex": False,
    "type": "sitemap",
    "warnings": "0",
    "errors": "0",
}


def _stub_credentials(mocker):
    """Patch out credential construction so no test touches the network.

    A live token is already valid, so get_authenticated_service skips the
    refresh-and-persist branch entirely; what these tests assert is our scope
    handling, not google-auth's refresh behaviour.
    """
    creds = mocker.MagicMock(expired=False, valid=True)
    return mocker.patch(
        "gsc_cli.auth.client.Credentials.from_authorized_user_info", return_value=creds
    )


class TestWriteScopePreCheck:
    """A read-only token must fail fast, before any network call.

    Most connections in the wild predate write access, so this is the common
    path, not an edge case. Building credentials with a hardcoded write scope
    instead would surface as a 403 at call time or a "Scope has changed"
    RefreshError at refresh time — both far harder to act on.
    """

    def test_readonly_token_rejects_write(self, mocker):
        mocker.patch("gsc_cli.auth.client.load_service_account", return_value=None)
        mocker.patch("gsc_cli.auth.client.load_oauth_token", return_value=READONLY_TOKEN)
        build = mocker.patch("gsc_cli.auth.client.build")

        with pytest.raises(AuthError) as exc:
            get_authenticated_service(require_write=True)

        assert exc.value.code == "AUTH_SCOPE_READONLY"
        assert exc.value.exit_code == 3
        build.assert_not_called()

    def test_readonly_token_allows_read(self, mocker):
        mocker.patch("gsc_cli.auth.client.load_service_account", return_value=None)
        mocker.patch("gsc_cli.auth.client.load_oauth_token", return_value=READONLY_TOKEN)
        _stub_credentials(mocker)
        build = mocker.patch("gsc_cli.auth.client.build")

        get_authenticated_service()

        build.assert_called_once()

    def test_write_token_allows_write(self, mocker):
        mocker.patch("gsc_cli.auth.client.load_service_account", return_value=None)
        mocker.patch("gsc_cli.auth.client.load_oauth_token", return_value=WRITE_TOKEN)
        _stub_credentials(mocker)
        build = mocker.patch("gsc_cli.auth.client.build")

        get_authenticated_service(require_write=True)

        build.assert_called_once()

    def test_credentials_use_granted_scopes(self, mocker):
        """Never request more than the token holds, or refresh raises."""
        mocker.patch("gsc_cli.auth.client.load_service_account", return_value=None)
        mocker.patch("gsc_cli.auth.client.load_oauth_token", return_value=READONLY_TOKEN)
        mocker.patch("gsc_cli.auth.client.build")
        from_info = _stub_credentials(mocker)

        get_authenticated_service()

        assert from_info.call_args.kwargs["scopes"] == [READ_SCOPE, "openid"]

    def test_readonly_kwarg_still_maps_to_write(self, mocker):
        """Pre-0.2 spelling: readonly=False meant "I need write"."""
        mocker.patch("gsc_cli.auth.client.load_service_account", return_value=None)
        mocker.patch("gsc_cli.auth.client.load_oauth_token", return_value=READONLY_TOKEN)
        mocker.patch("gsc_cli.auth.client.build")

        with pytest.raises(AuthError) as exc:
            get_authenticated_service(readonly=False)

        assert exc.value.code == "AUTH_SCOPE_READONLY"


class TestRow:
    def test_flattens_known_fields(self):
        row = _row(SITEMAP_ENTRY)
        assert row["path"] == "https://example.com/sitemap.xml"
        assert row["last_submitted"] == "2026-04-27T11:50:07.390Z"
        assert row["last_downloaded"] == "2026-07-26T23:56:11.991Z"
        assert row["errors"] == "0"
        assert row["warnings"] == "0"

    def test_missing_fields_become_empty(self):
        assert _row({}) == {
            "path": "",
            "type": "",
            "last_submitted": "",
            "last_downloaded": "",
            "is_pending": "",
            "is_sitemaps_index": "",
            "warnings": "",
            "errors": "",
        }


class TestCommands:
    def test_list_renders_rows(self, mocker):
        service = mocker.MagicMock()
        service.sitemaps().list().execute.return_value = {"sitemap": [SITEMAP_ENTRY]}
        mocker.patch(
            "gsc_cli.sitemaps.commands.get_authenticated_service", return_value=service
        )

        result = runner.invoke(
            app, ["sitemaps", "list", "-s", "sc-domain:example.com", "-f", "json"]
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"][0]["last_downloaded"] == "2026-07-26T23:56:11.991Z"

    def test_submit_reads_back_the_acceptance_timestamp(self, mocker):
        """PUT returns an empty 204, so we re-read to report lastSubmitted."""
        service = mocker.MagicMock()
        service.sitemaps().get().execute.return_value = SITEMAP_ENTRY
        get_service = mocker.patch(
            "gsc_cli.sitemaps.commands.get_authenticated_service", return_value=service
        )

        result = runner.invoke(
            app,
            [
                "sitemaps",
                "submit",
                "https://example.com/sitemap.xml",
                "-s",
                "sc-domain:example.com",
                "-f",
                "json",
            ],
        )

        assert result.exit_code == 0
        assert get_service.call_args.kwargs == {"require_write": True}
        service.sitemaps().submit.assert_called_with(
            siteUrl="sc-domain:example.com", feedpath="https://example.com/sitemap.xml"
        )
        payload = json.loads(result.output)
        assert payload["meta"]["submitted"] is True
        assert payload["data"][0]["last_submitted"] == "2026-04-27T11:50:07.390Z"

    def test_submit_survives_a_failed_readback(self, mocker):
        """The submission landed; only the confirmation read failed."""
        service = mocker.MagicMock()
        service.sitemaps().get().execute.side_effect = RuntimeError("boom")
        mocker.patch(
            "gsc_cli.sitemaps.commands.get_authenticated_service", return_value=service
        )

        result = runner.invoke(
            app,
            [
                "sitemaps",
                "submit",
                "https://example.com/sitemap.xml",
                "-s",
                "sc-domain:example.com",
                "-f",
                "json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["meta"]["submitted"] is True
        assert "boom" in payload["meta"]["readback_error"]

    def test_submit_on_readonly_token_exits_3(self, mocker):
        mocker.patch("gsc_cli.auth.client.load_service_account", return_value=None)
        mocker.patch("gsc_cli.auth.client.load_oauth_token", return_value=READONLY_TOKEN)
        build = mocker.patch("gsc_cli.auth.client.build")

        result = runner.invoke(
            app,
            [
                "sitemaps",
                "submit",
                "https://example.com/sitemap.xml",
                "-s",
                "sc-domain:example.com",
                "-f",
                "json",
            ],
        )

        assert result.exit_code == 3
        payload = json.loads(result.output)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "AUTH_SCOPE_READONLY"
        build.assert_not_called()

    def test_delete_requires_write(self, mocker):
        service = mocker.MagicMock()
        get_service = mocker.patch(
            "gsc_cli.sitemaps.commands.get_authenticated_service", return_value=service
        )

        result = runner.invoke(
            app,
            [
                "sitemaps",
                "delete",
                "https://example.com/old.xml",
                "-s",
                "sc-domain:example.com",
                "-f",
                "json",
            ],
        )

        assert result.exit_code == 0
        assert get_service.call_args.kwargs == {"require_write": True}
        assert json.loads(result.output)["meta"]["deleted"] is True

    def test_submit_without_site_fails(self):
        result = runner.invoke(app, ["sitemaps", "submit", "https://example.com/sitemap.xml"])
        assert result.exit_code != 0
