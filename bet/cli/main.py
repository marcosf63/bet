"""Main CLI application entry point."""

import typer
from rich.console import Console

from bet.cli.commands.analysis import analysis_command
from bet.cli.commands.api import api_command

# Import all modular commands
from bet.cli.commands.daily import mday_command
from bet.cli.commands.diff import diff_command
from bet.cli.commands.favorites import fav_command
from bet.cli.commands.halftime import ht0x0_command
from bet.cli.commands.layaway import layaway_command
from bet.cli.commands.report import report_command
from bet.cli.commands.shell import shell_command
from bet.cli.commands.sofa import sofa_command

app = typer.Typer(name="Bet CLI", help="CLI para análise de jogos de futebol.")
console = Console()


# Register all commands
app.command(name="mday")(mday_command)
app.command(name="fav")(fav_command)
app.command(name="ht0x0")(ht0x0_command)
app.command(name="shell")(shell_command)
app.command(name="diff")(diff_command)
app.command(name="sofa")(sofa_command)
app.command(name="relatorio")(report_command)
app.command(name="layaway")(layaway_command)
app.command(name="analise")(analysis_command)
app.command(name="api")(api_command)


def main():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
