"""Helper functions for CLI commands."""

from datetime import date
from typing import List, Dict
from pathlib import Path
import csv
import requests
from rich.console import Console

from bet.storage import csv_string_to_json_list
from bet.core.constants import URL_TEMPLATES, COLUNAS_PRINCIPAIS

console = Console()


def safe_float(value: any, default: float = 0.0) -> float:
    """Converte um valor para float de forma segura."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_daily_games(data: str, fonte: str = "betfair") -> List[Dict]:
    """Busca e processa os jogos do dia."""
    if fonte not in URL_TEMPLATES:
        console.print(f"[bold red]Fonte '{fonte}' nao disponivel.[/bold red]")
        return []

    url = URL_TEMPLATES[fonte].format(data=data)
    try:
        response = requests.get(url)
        response.raise_for_status()
        return csv_string_to_json_list(response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Erro ao buscar dados: {e}[/bold red]")
        return []


def filter_games(games: List[Dict], fonte: str = "betfair"):
    """Filtra as colunas e calcula ISC."""
    if not games:
        console.print("[yellow]Nenhum jogo encontrado.[/yellow]")
        return []

    if fonte not in COLUNAS_PRINCIPAIS:
        fonte = "betfair"

    colunas = COLUNAS_PRINCIPAIS[fonte]
    jogos_filtrados = []

    for d in games:
        jogo_filtrado = {k: d.get(k, '') for k in colunas}

        if fonte == "betfair" and "ISC" in colunas:
            odd_a_lay = safe_float(d.get('Odd_A_Lay', 0))
            odd_h_back = safe_float(d.get('Odd_H_Back', 0))
            odd_d_back = safe_float(d.get('Odd_D_Back', 0))

            if odd_h_back > 0 and odd_a_lay > 0:
                ph = 1 / odd_h_back
                pan = 1 - (1 / odd_a_lay)
                fd = (odd_a_lay / odd_h_back) / 10
                fde = (odd_d_back / odd_h_back) / 3
                isc = (ph * 0.35 + pan * 0.25 + fd * 0.25 + fde * 0.15) * 100
                jogo_filtrado["ISC"] = f"{isc:.1f}"
            else:
                jogo_filtrado["ISC"] = "N/A"

        jogos_filtrados.append(jogo_filtrado)

    return jogos_filtrados


def print_isc_legend():
    """Imprime a legenda do ISC."""
    console.print("\n[bold cyan]ISC Legend:[/bold cyan]")
    console.print("Excelente: ISC > 75")
    console.print("Bom: ISC 65-75")
    console.print("Moderado: ISC 55-65")
    console.print("Fraco: ISC < 55")


def save_csv_to_file(data: List[Dict], date_str: str, folder_name: str = "mday"):
    """Save data to CSV file."""
    if not data:
        console.print("[yellow]No data to save.[/yellow]")
        return

    folder_path = Path(f"/home/marcos/projetos/bet/data/{folder_name}")
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = folder_path / f"{date_str}.csv"

    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    console.print(f"[green]File saved to:[/green] {file_path}")


def save_diff_to_file(data: List[Dict], date_str: str, filtros_aplicados: List[str]):
    """Save diff results to CSV file."""
    if not data:
        return

    folder_path = Path("/home/marcos/projetos/bet/data/diff")
    folder_path.mkdir(parents=True, exist_ok=True)

    nome_arquivo = f"{date_str}_" + "_".join(filtros_aplicados) if filtros_aplicados else date_str
    file_path = folder_path / f"{nome_arquivo}.csv"

    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    console.print(f"[green]File saved to:[/green] {file_path}")


def calculate_similarity(str1: str, str2: str) -> float:
    """Calcula similaridade entre duas strings."""
    if str1 == str2:
        return 1.0

    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,
                matrix[i][j-1] + 1,
                matrix[i-1][j-1] + cost
            )

    distance = matrix[len1][len2]
    max_len = max(len1, len2)

    return 1.0 - (distance / max_len)
