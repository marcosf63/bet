import json
from datetime import date
from pathlib import Path
import time
import os

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from bet.files import load_json_to_dict, save_dict_to_json
from bet.utils import (
        markets_dict, 
        calcula_saida_edge_black_lay,
        calcula_saida_edge_lay_back,
        calcula_saida_freebet_lay,
        add_thirty_minutes_to_time_hm_only,
        is_time_greater_than_now,
        is_time_smaller_than_now_plus30min,
        converter_hora_para_datetime,
        verificar_tempo_passado,
)  

from .betfair import busca_odds_mercado, get_match_day, get_odds_event_markets, get_1_gol_segundo_tempo, get_trading
from .config import settings
from .utils import (calcula_saida_edge_black_lay, calcula_saida_edge_lay_back,
                    calcula_saida_freebet_lay, markets_dict)
from bet.soufascore import get_live_events, get_live_no_gol_events, check_events
# from rich.table import Table


main = typer.Typer(name="Bet CLI")
console = Console()
trading = get_trading()

@main.command()
def shell():
    """Opens interactive shell"""
    _vars = {
        "settings": settings,
        "calcula_saida_edge_black_lay": calcula_saida_edge_black_lay,
        "calcula_saida_edge_lay_back": calcula_saida_edge_lay_back,
        "calcula_saida_freebet_lay": calcula_saida_freebet_lay,
        "add_thirty_minutes_to_time_hm_only": add_thirty_minutes_to_time_hm_only,
        "is_time_smaller_than_now_plus30min": is_time_smaller_than_now_plus30min,
        "is_time_greater_than_now": is_time_greater_than_now,
        "verificar_tempo_passado": verificar_tempo_passado,
        "converter_hora_para_datetime": converter_hora_para_datetime,
        "get_match_day": get_match_day,
        "get_live_events": get_live_events,
        "get_live_no_gol_events": get_live_no_gol_events,
        "check_events": check_events,
        "markets_dict": markets_dict,
        "get_odds_event_markets": get_odds_event_markets,
        "get_trading": get_trading,
    }
    typer.echo(f"Auto imports: {list(_vars.keys())}")
    try:
        from IPython import start_ipython

        start_ipython(argv=["--ipython-dir=/tmp", "--no-banner"], user_ns=_vars)
    except ImportError:
        import code

        code.InteractiveConsole(_vars).interact()


@main.command()
def cbl(odd_entrada_back: float, odd_saida_lay: float, stake: float):
    """Calcula o valor da saída em edge, entrando back e saindo em lay"""
    print(calcula_saida_edge_black_lay(odd_entrada_back, odd_saida_lay, stake))


@main.command()
def lbl(odd_entrada_back: float, odd_saida_lay: float, stake: float):
    """Calcula o lucro da saida em edge entrando em back e saindo em lay"""
    print(calcula_saida_edge_black_lay(odd_entrada_back, odd_saida_lay, stake) - stake)


@main.command()
def clb(odd_entrada_lay: float, odd_saida_back: float, responsabilidade: float):
    """Calcula o valor da saída em edge, entrando lay e saindo em back"""
    print(
        calcula_saida_edge_lay_back(odd_entrada_lay, odd_saida_back, responsabilidade)
    )


@main.command()
def llb(odd_entrada_lay: float, responsabilidade: float):
    """Calcula o lucro da saida em edge entrando em lay e saindo em back"""
    print(round(responsabilidade / (odd_entrada_lay - 1), 2))


@main.command()
def mday(no_print: bool = False):
    """Lista as partidas do dia com data/hora e id do evento"""
    tabela = Table(show_header=True, header_style="bold magenta")
    data = date.today()
    file_path = f"{settings.data_dir}/jogos/{data.day}-{data.month}-{data.year}.json"
    if Path(file_path).exists():
        lista_jogos = load_json_to_dict(file_path)
        print("Dados carregados.")
    else:
        print("Buscado dados na Betfair...")
        lista_jogos = get_match_day()
        save_dict_to_json(lista_jogos, file_path)
        print("Dados salvos.")
    if not no_print:
        for chave in lista_jogos[0].keys():
            tabela.add_column(chave)
        for jogo in lista_jogos:
            tabela.add_row(*jogo.values())

        console.print(tabela)
        console.print(f"[bold green]Total de jogos = {len(lista_jogos)}[/bold green]")



@main.command()
def godds(
    event_id: str,
    market: str,
    ord: bool = typer.Option(False, help="Ordena CS por da menor para maior odd."),
):
    """
    lista as odds para um evento que seja indormado o event_id e o mercado"
    """

    result = get_odds_event_markets(event_id, markets_dict[market], trading)
    tabela = Table(
        title=f"Market: {result['market']}",
        show_header=True,
        header_style="bold magenta",
    )
    for chave in result["selections"][0].keys():
        tabela.add_column(chave)

    if ord and market == "CS":
        selections_list = sorted(result["selections"], key=lambda x: x["back_odds"])
    else:
        selections_list = result["selections"]

    for selection in selections_list:
        tabela.add_row(
            selection["name"],
            str(selection["back_odds"]),
            str(selection["lay_odds"]),
        )
    console.print(tabela)


@main.command()
def l2b(odd_lay: str) -> None:
    """Converte a odd do lay para equivalente em back"""
    file_path = Path(f"{settings.data_dir}") / "lay_to_back.json"
    with file_path.open("r") as json_file:
        lay_to_back_dict = json.load(json_file)

    console.print(lay_to_back_dict[odd_lay])


@main.command()
def bom():
    busca_odds_mercado()


@main.command()
def all(
    event_id: str,
):
    """
    lista as odds para um evento que seja indormado o event_id e o mercado"
    """
    for market in ["MO", "BTTS", "O25", "CS"]:
        result = get_odds_event_markets(event_id, markets_dict[market], trading)

        tabela = Table(
            title=f"Market: {result['market']}",
            show_header=True,
            header_style="bold magenta",
        )
        for chave in result["selections"][0].keys():
            tabela.add_column(chave)

        if market == "CS":
            selections_list = sorted(result["selections"], key=lambda x: x["back_odds"])
        else:
            selections_list = result["selections"]

        for selection in selections_list:
            tabela.add_row(
                selection["name"],
                str(selection["back_odds"]),
                str(selection["lay_odds"]),
            )
        console.print(tabela)


@main.command()
def gzebra():
    data = date.today()
    file_path = f"{settings.data_dir}/jogos/{data.day}-{data.month}-{data.year}.json"
    lista_jogos: list = []
    if Path(file_path).exists():
        lista_jogos = load_json_to_dict(file_path)
    print(lista_jogos)

@main.command()
def check_gol():
    """Verifica se em algum jogo 0x0 saiu gol no segundo tempo"""
    get_1_gol_segundo_tempo(trading)
        
        
