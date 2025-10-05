"""CLI commands package."""

from bet.cli.commands.daily import mday_command
from bet.cli.commands.favorites import fav_command
from bet.cli.commands.halftime import ht0x0_command
from bet.cli.commands.shell import shell_command
from bet.cli.commands.diff import diff_command

__all__ = [
    "mday_command",
    "fav_command",
    "ht0x0_command",
    "shell_command",
    "diff_command",
]
