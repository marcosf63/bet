"""Favorites command (fav) - games with clear favorites."""

from datetime import date

import typer
from rich.console import Console

from bet.cli.helpers import filter_games, get_daily_games, safe_float
from bet.utils import print_table

console = Console()


def fav_command(
    oddmax: float = typer.Option(1.5, help="Odd máxima para um time ser considerado favorito."),
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    fonte: str = typer.Option(
        "betfair",
        help="Fonte dos dados: betfair, footystats ou flashscore.",
    ),
    horai: int = typer.Option(0, help="Hora inicial para filtrar os jogos."),
    horaf: int = typer.Option(23, help="Hora final para filtrar os jogos."),
    liga: str = typer.Option(None, help="Filtra jogos por uma liga específica (busca parcial)."),
):
    """Lista jogos com um favorito claro (odd <= oddmax) em um determinado horário e liga."""
    jogos_do_dia = get_daily_games(data, fonte)

    # Definir colunas de odds baseado na fonte
    if fonte == "betfair":
        odd_home_col = "Odd_H_Back"
        odd_away_col = "Odd_A_Back"
    else:  # footystats e flashscore
        odd_home_col = "Odd_H_FT"
        odd_away_col = "Odd_A_FT"

    jogos_filtrados = [
        jogo
        for jogo in jogos_do_dia
        if (
            safe_float(jogo.get(odd_home_col)) <= oddmax
            or safe_float(jogo.get(odd_away_col)) <= oddmax
        )
        and (horai <= int(jogo.get("Time", "0:0").split(":")[0]) <= horaf)
    ]

    if liga:
        jogos_filtrados = [
            jogo for jogo in jogos_filtrados if liga.lower() in jogo.get("League", "").lower()
        ]

    jogos_filtrados = filter_games(jogos_filtrados, fonte)

    print_table(jogos_filtrados)
