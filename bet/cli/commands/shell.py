"""Interactive shell command."""

import typer

from bet.config import settings
from bet.utils import converter_hora_para_datetime
from bet.utils.notifications import run_timer, play_sound, send_notification
from bet.cli.helpers import get_daily_games
from bet.core.constants import URL_TEMPLATES


def shell_command():
    """Abre um shell interativo (IPython) com funções úteis pré-carregadas."""
    _vars = {
        "settings": settings,
        "converter_hora_para_datetime": converter_hora_para_datetime,
        "run_timer": run_timer,
        "play_sound": play_sound,
        "send_notification": send_notification,
        "get_daily_games": get_daily_games,
        "URL_TEMPLATES": URL_TEMPLATES,
    }
    typer.echo(f"Auto imports: {list(_vars.keys())}")
    try:
        from IPython import start_ipython
        start_ipython(argv=["--ipython-dir=/tmp", "--no-banner"], user_ns=_vars)
    except ImportError:
        import code
        code.InteractiveConsole(_vars).interact()
