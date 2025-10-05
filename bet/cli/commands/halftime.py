"""Halftime 0x0 command (ht0x0) - games with potential 0x0 at halftime."""

from datetime import date
import typer
from rich.console import Console

from bet.cli.helpers import get_daily_games, filter_games, safe_float
from bet.utils import print_table

console = Console()


def ht0x0_command(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    fonte: str = typer.Option(
        "betfair",
        help="Fonte dos dados: betfair, footystats ou flashscore.",
    ),
    odd_over: float = typer.Option(2.0, help="Odd mínima para o mercado Over 2.5 FT."),
    odd_btts: float = typer.Option(2.0, help="Odd mínima para o mercado BTTS (Ambos Marcam)."),
    horai: int = typer.Option(0, help="Hora inicial para filtrar os jogos."),
):
    """Busca jogos com potencial de 0x0 no intervalo (HT) baseado em odds altas de Over 2.5 e BTTS."""
    jogos_do_dia = get_daily_games(data, fonte)

    # Definir colunas baseado na fonte
    if fonte == "betfair":
        odd_over_col = "Odd_Over25_FT_Back"
        odd_btts_col = "Odd_BTTS_Yes_Back"
    else:  # footystats e flashscore
        odd_over_col = "Odd_Over05_HT"  # Over 0.5 HT para footystats/flashscore
        odd_btts_col = "Odd_BTTS_No"    # BTTS No para footystats/flashscore

    jogos_filtrados = [
        jogo for jogo in jogos_do_dia
        if (safe_float(jogo.get(odd_over_col)) > odd_over and
            safe_float(jogo.get(odd_btts_col)) > odd_btts)
        and int(jogo.get("Time", "0:0").split(":")[0]) >= horai
    ]
    jogos_filtrados = filter_games(jogos_filtrados, fonte)
    print_table(jogos_filtrados)
