"""Main CLI application entry point."""

import typer
from rich.console import Console

# Import new modular commands
from bet.cli.commands.daily import mday_command
from bet.cli.commands.favorites import fav_command
from bet.cli.commands.halftime import ht0x0_command
from bet.cli.commands.shell import shell_command
from bet.cli.commands.diff import diff_command

# For now, we'll import complex commands from the old cli module
# These will be migrated in future phases
import sys
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("old_cli", Path(__file__).parent.parent / "cli.py")
old_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_cli)

app = typer.Typer(name="Bet CLI", help="CLI para análise de jogos de futebol.")
console = Console()


# Register migrated modular commands
app.command(name="mday")(mday_command)
app.command(name="fav")(fav_command)
app.command(name="ht0x0")(ht0x0_command)
app.command(name="shell")(shell_command)
app.command(name="diff")(diff_command)

# Register remaining commands from old CLI (to be migrated)
app.command(name="relatorio")(old_cli.relatorio)
app.command(name="layaway")(old_cli.layaway)
app.command(name="analise")(old_cli.analise)
app.command(name="sofa")(old_cli.sofa)
app.command(name="api")(old_cli.api)


def main():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
