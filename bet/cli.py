from datetime import date, datetime
from typing import List, Dict
from pathlib import Path
import csv
import requests
import typer
from rich.console import Console

from bet.files import csv_string_to_json_list
from bet.utils import (
    converter_hora_para_datetime,
    print_table,
)
from bet.config import settings
from bet.notification import run_timer, play_sound, send_notification

# --- Constantes e Configuração ---
main = typer.Typer(name="Bet CLI", help="CLI para análise de jogos de futebol.")
console = Console()

URL_TEMPLATE = "https://raw.githubusercontent.com/futpythontrader/Jogos_do_Dia/refs/heads/main/Betfair/Jogos_do_Dia_Betfair_Back_Lay_{data}.csv"
COLUNAS_PRINCIPAIS = [
    "Date", "Time", "League", "Home", "Away", "Odd_H_Back", "Odd_D_Back",
    "Odd_A_Back", "Odd_Over25_FT_Back", "Odd_BTTS_Yes_Back", "Odd_Over15_FT_Back"
]


# --- Funções Auxiliares ---
def _safe_float(value: any, default: float = 0.0) -> float:
    """Converte um valor para float de forma segura, retornando um padrão em caso de erro."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _get_daily_games(data: str) -> List[Dict]:
    """Busca e processa os jogos do dia a partir da fonte de dados remota."""
    url = URL_TEMPLATE.format(data=data)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lança uma exceção para respostas 4xx/5xx
        return csv_string_to_json_list(response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Erro ao buscar dados para {data}: {e}[/bold red]")
        return []


def _filter_games(games: List[Dict]):
    """Filtra as colunas."""
    if not games:
        console.print("[yellow]Nenhum jogo encontrado para os critérios fornecidos.[/yellow]")
        return

    jogos_filtrados = [{k: d.get(k, '') for k in COLUNAS_PRINCIPAIS} for d in games]
    return jogos_filtrados

def _save_csv_to_file(data: List[Dict], date_str: str):
    """Save the list of game dictionaries to a CSV file in the mday folder."""
    if not data:
        console.print("[yellow]No data to save.[/yellow]")
        return

    folder_path = Path("/home/marcos/projetos/bet/data/mday")
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = folder_path / f"{date_str}.csv"

    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    console.print(f"[green]File saved to:[/green] {file_path}")


# --- Comandos da CLI ---
@main.command()
def shell():
    """Abre um shell interativo (IPython) com funções úteis pré-carregadas."""
    _vars = {
        "settings": settings,
        "converter_hora_para_datetime": converter_hora_para_datetime,
        "run_timer": run_timer,
        "play_sound": play_sound,
        "send_notification": send_notification,
        "get_daily_games": _get_daily_games,
    }
    typer.echo(f"Auto imports: {list(_vars.keys())}")
    try:
        from IPython import start_ipython
        start_ipython(argv=["--ipython-dir=/tmp", "--no-banner"], user_ns=_vars)
    except ImportError:
        import code
        code.InteractiveConsole(_vars).interact()


@main.command()
def mday(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em CSV."),
):
    """Lista todas as partidas do dia."""
    jogos_do_dia = _get_daily_games(data)
    jogos_filtrados = _filter_games(jogos_do_dia)
    if salvar:
        _save_csv_to_file(jogos_filtrados, data)
    print_table(jogos_filtrados)


@main.command()
def fav(
    oddmax: float = typer.Option(1.5, help="Odd máxima para um time ser considerado favorito."),
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    horai: int = typer.Option(0, help="Hora inicial para filtrar os jogos."),
    horaf: int = typer.Option(23, help="Hora final para filtrar os jogos."),
    liga: str = typer.Option(None, help="Filtra jogos por uma liga específica (busca parcial)."),
):
    """Lista jogos com um favorito claro (odd <= oddmax) em um determinado horário e liga."""
    jogos_do_dia = _get_daily_games(data)
    
    jogos_filtrados = [
        jogo for jogo in jogos_do_dia
        if (_safe_float(jogo.get("Odd_H_Back")) <= oddmax or _safe_float(jogo.get("Odd_A_Back")) <= oddmax)
        and (horai <= int(jogo.get("Time", "0:0").split(":")[0]) <= horaf)
    ]

    if liga:
        jogos_filtrados = [
            jogo for jogo in jogos_filtrados if liga.lower() in jogo.get("League", "").lower()
        ]

    jogos_filtrados = _filter_games(jogos_filtrados)

    print_table(jogos_filtrados)


@main.command()
def ht0x0(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    odd_over: float = typer.Option(2.0, help="Odd mínima para o mercado Over 2.5 FT."),
    odd_btts: float = typer.Option(2.0, help="Odd mínima para o mercado BTTS (Ambos Marcam)."),
    horai: int = typer.Option(0, help="Hora inicial para filtrar os jogos."),
):
    """Busca jogos com potencial de 0x0 no intervalo (HT) baseado em odds altas de Over 2.5 e BTTS."""
    jogos_do_dia = _get_daily_games(data)

    jogos_filtrados = [
        jogo for jogo in jogos_do_dia
        if (_safe_float(jogo.get("Odd_Over25_FT_Back")) > odd_over and
            _safe_float(jogo.get("Odd_BTTS_Yes_Back")) > odd_btts)
        and int(jogo.get("Time", "0:0").split(":")[0]) >= horai
    ]
    jogos_filtrados = _filter_games(jogos_filtrados)
    print_table(jogos_filtrados)


if __name__ == "__main__":
    main()
