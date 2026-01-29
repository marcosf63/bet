"""Helper functions for CLI commands."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from rich.console import Console

from bet.core.constants import COLUNAS_PRINCIPAIS, URL_TEMPLATES
from bet.storage import csv_string_to_json_list

console = Console()


def safe_float(value: any, default: float = 0.0) -> float:
    """Converte um valor para float de forma segura."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_from_cache(data: str) -> Optional[list[dict]]:
    """
    Carrega dados do cache se existir.

    Args:
        data: Data no formato YYYY-MM-DD

    Returns:
        Lista de jogos do cache ou None se não existir
    """
    cache_dir = Path("/home/marcos/projetos/bet/data/betfair_cache")
    cache_file = cache_dir / f"{data}_raw.json"

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
                return cached.get("jogos", [])
        except Exception as e:
            console.print(f"[yellow]⚠ Erro ao ler cache: {e}[/yellow]")
            return None
    return None


def save_to_cache(data: str, jogos: list[dict]):
    """
    Salva dados no cache.

    Args:
        data: Data no formato YYYY-MM-DD
        jogos: Lista de jogos para cachear
    """
    cache_dir = Path("/home/marcos/projetos/bet/data/betfair_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "metadata": {
            "data_scraping": datetime.now().isoformat(),
            "total_jogos": len(jogos),
            "metodo": "scraping",
        },
        "jogos": jogos,
    }

    cache_file = cache_dir / f"{data}_raw.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[yellow]⚠ Erro ao salvar cache: {e}[/yellow]")


def get_daily_games(
    data: str, fonte: str = "betfair", use_scraper: bool = True, force_scrape: bool = False
) -> list[dict]:
    """
    Busca e processa os jogos do dia.

    Args:
        data: Data no formato YYYY-MM-DD
        fonte: Fonte dos dados (betfair, footystats, flashscore)
        use_scraper: Se True, tenta usar scraper da Betfair (apenas para fonte=betfair)
        force_scrape: Se True, ignora cache e força novo scraping

    Returns:
        Lista de jogos
    """
    if fonte not in URL_TEMPLATES:
        console.print(f"[bold red]Fonte '{fonte}' nao disponivel.[/bold red]")
        return []

    # Para fonte betfair, implementar lógica de cache + scraping
    if fonte == "betfair" and use_scraper:
        # Tentar carregar do cache primeiro (se não for force_scrape)
        if not force_scrape:
            cached_data = load_from_cache(data)
            if cached_data:
                console.print("[green]📦 Dados carregados do cache[/green]")
                console.print(f"[dim]   {len(cached_data)} jogos disponíveis[/dim]")
                return cached_data

        # Cache miss ou force_scrape: fazer scraping
        try:
            from bet.services.betfair.scraper import BetfairScraper

            if force_scrape:
                console.print("[cyan]🔄 Atualizando dados (scraping forçado)...[/cyan]")
            else:
                console.print("[cyan]🔄 Cache não encontrado, fazendo scraping...[/cyan]")

            console.print("[dim]   Isso pode levar ~15-20 segundos...[/dim]")
            scraper = BetfairScraper(headless=True)
            jogos = scraper.scrape_today()

            if jogos:
                # Salvar no cache
                save_to_cache(data, jogos)

                console.print(f"[green]✓ {len(jogos)} jogos obtidos via scraping[/green]")
                console.print("[dim]💾 Cache salvo para uso futuro[/dim]")
                return jogos
            else:
                console.print("[yellow]⚠ Scraper não retornou jogos, usando CSV...[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠ Scraper falhou ({e}), usando CSV...[/yellow]")

    # Fallback ou outras fontes: buscar CSV do GitHub
    url = URL_TEMPLATES[fonte].format(data=data)
    try:
        response = requests.get(url)
        response.raise_for_status()
        jogos = csv_string_to_json_list(response.text)
        if fonte == "betfair":
            console.print(f"[green]✓ {len(jogos)} jogos obtidos via CSV[/green]")
        return jogos
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Erro ao buscar dados: {e}[/bold red]")
        return []


def filter_games(games: list[dict], fonte: str = "betfair"):
    """Filtra as colunas e calcula ISC."""
    if not games:
        console.print("[yellow]Nenhum jogo encontrado.[/yellow]")
        return []

    if fonte not in COLUNAS_PRINCIPAIS:
        fonte = "betfair"

    colunas = COLUNAS_PRINCIPAIS[fonte]
    jogos_filtrados = []

    for d in games:
        jogo_filtrado = {k: d.get(k, "") for k in colunas}

        if fonte == "betfair" and "ISC" in colunas:
            odd_a_lay = safe_float(d.get("Odd_A_Lay", 0))
            odd_h_back = safe_float(d.get("Odd_H_Back", 0))
            odd_d_back = safe_float(d.get("Odd_D_Back", 0))

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


def save_csv_to_file(data: list[dict], date_str: str, folder_name: str = "mday"):
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


def save_diff_to_file(data: list[dict], date_str: str, filtros_aplicados: list[str]):
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
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + cost
            )

    distance = matrix[len1][len2]
    max_len = max(len1, len2)

    return 1.0 - (distance / max_len)
