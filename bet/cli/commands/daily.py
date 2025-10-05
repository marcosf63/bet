"""Daily matches command (mday)."""

from datetime import date
import typer
from rich.console import Console

from bet.cli.helpers import (
    get_daily_games,
    filter_games,
    save_csv_to_file,
    print_isc_legend,
    safe_float,
)
from bet.utils import print_table

console = Console()


def mday_command(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    fonte: str = typer.Option(
        "betfair",
        help="Fonte dos dados: betfair, footystats ou flashscore.",
    ),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em CSV."),
    odd_home_max: float = typer.Option(None, help="Filtra jogos com odd do time da casa menor ou igual ao valor especificado."),
    odd_home_min: float = typer.Option(None, help="Filtra jogos com odd do time da casa maior ou igual ao valor especificado."),
    isc: str = typer.Option(None, help="Filtra jogos por ISC: excelente (>75), bom (≥65), moderado (≥55), fraco (<55)."),
):
    """Lista todas as partidas do dia."""
    jogos_do_dia = get_daily_games(data, fonte)

    # Filtrar por odd do time da casa se especificado
    # Definir coluna de odd home baseado na fonte
    if fonte == "betfair":
        odd_home_col = "Odd_H_Back"
    else:  # footystats e flashscore
        odd_home_col = "Odd_H_FT"

    # Filtrar por odd máxima do time da casa
    if odd_home_max is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia
            if safe_float(jogo.get(odd_home_col)) <= odd_home_max
        ]

    # Filtrar por odd mínima do time da casa
    if odd_home_min is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia
            if safe_float(jogo.get(odd_home_col)) >= odd_home_min
        ]

    jogos_filtrados = filter_games(jogos_do_dia, fonte)

    # Filtrar por ISC se especificado (apenas para betfair)
    if isc is not None and fonte == "betfair":
        isc_lower = isc.lower()
        jogos_filtrados_isc = []

        for jogo in jogos_filtrados:
            isc_value_str = jogo.get("ISC", "N/A")
            if isc_value_str != "N/A":
                try:
                    isc_value = float(isc_value_str)
                    # Aplicar filtro baseado na legenda:
                    # excelente: ISC > 75 (inclui apenas excelente)
                    # bom: ISC >= 65 (inclui bom e excelente)
                    # moderado: ISC >= 55 (inclui moderado, bom e excelente)
                    # fraco: ISC < 55 (inclui apenas fraco)
                    if isc_lower == "excelente" and isc_value > 75:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "bom" and isc_value >= 65:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "moderado" and isc_value >= 55:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "fraco" and isc_value < 55:
                        jogos_filtrados_isc.append(jogo)
                except ValueError:
                    continue

        jogos_filtrados = jogos_filtrados_isc

    if salvar:
        # Construir nome do arquivo com filtros aplicados
        sufixos = [fonte]

        if odd_home_max is not None:
            sufixos.append(f"home-max-{odd_home_max}")
        if odd_home_min is not None:
            sufixos.append(f"home-min-{odd_home_min}")
        if isc is not None:
            sufixos.append(f"isc-{isc.lower()}")

        nome_arquivo = f"{data}_" + "_".join(sufixos)
        save_csv_to_file(jogos_filtrados, nome_arquivo)

    print_table(jogos_filtrados)

    # Mostrar legenda do ISC apenas para fonte betfair
    if fonte == "betfair" and jogos_filtrados:
        print_isc_legend()
