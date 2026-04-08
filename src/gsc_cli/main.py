"""GSC CLI — Agent-first Google Search Console tool."""

from __future__ import annotations

import typer

from gsc_cli import __version__
from gsc_cli.auth.commands import app as auth_app
from gsc_cli.inspect.commands import inspect_url
from gsc_cli.query.commands import query
from gsc_cli.sites.commands import app as sites_app

app = typer.Typer(
    name="gsc",
    help="Agent-first CLI for Google Search Console SEO analytics.",
    no_args_is_help=True,
)

app.add_typer(auth_app, name="auth")
app.add_typer(sites_app, name="sites")
app.command("query")(query)
app.command("inspect")(inspect_url)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version."),
) -> None:
    if version:
        typer.echo(f"gsc-cli {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
