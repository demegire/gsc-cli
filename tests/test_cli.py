"""Integration tests for the CLI app."""


from typer.testing import CliRunner

from gsc_cli.main import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "query" in result.output
    assert "inspect" in result.output
    assert "auth" in result.output
    assert "sites" in result.output


def test_query_help():
    result = runner.invoke(app, ["query", "--help"])
    assert result.exit_code == 0
    assert "--site" in result.output
    assert "--dimensions" in result.output
    assert "--filter" in result.output


def test_query_missing_site():
    result = runner.invoke(app, ["query"])
    assert result.exit_code != 0


def test_auth_help():
    result = runner.invoke(app, ["auth", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output
    assert "service-account" in result.output
    assert "status" in result.output


def test_sites_help():
    result = runner.invoke(app, ["sites", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output


def test_inspect_help():
    result = runner.invoke(app, ["inspect", "--help"])
    assert result.exit_code == 0
    assert "--site" in result.output
