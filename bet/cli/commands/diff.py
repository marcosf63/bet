"""Diff command - compare MDAY and SOFA data."""

from datetime import date, datetime

import typer
from rich.console import Console

from bet.cli.helpers import (
    calculate_similarity,
    filter_games,
    get_daily_games,
    print_isc_legend,
    safe_float,
    save_diff_to_file,
)
from bet.services.sofascore.client import get_scheduled_events
from bet.utils import print_table

console = Console()


def diff_command(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    fonte: str = typer.Option(
        "betfair",
        help="Fonte dos dados: betfair, footystats ou flashscore.",
    ),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em CSV."),
    odd_home_max: float = typer.Option(
        None, help="Filtra jogos com odd do time da casa menor ou igual ao valor especificado."
    ),
    odd_home_min: float = typer.Option(
        None, help="Filtra jogos com odd do time da casa maior ou igual ao valor especificado."
    ),
    isc: str = typer.Option(
        None, help="Filtra jogos por ISC: excelente (>75), bom (≥65), moderado (≥55), fraco (<55)."
    ),
    liga: str = typer.Option(None, help="Filtra jogos por uma liga específica (busca parcial)."),
    status: str = typer.Option(
        None, help="Filtra jogos por status (ex: ended, notstarted, inprogress, postponed)."
    ),
):
    """Compara jogos entre MDAY e SOFA e gera arquivo com correspondências incluindo gols."""
    console.print("[bold cyan]Busca correspondencias entre MDAY e SOFA[/bold cyan]")

    try:
        # 1. Obter dados MDAY com filtros
        jogos_do_dia = get_daily_games(data, fonte)

        # Aplicar filtros de odd_home
        if fonte == "betfair":
            odd_home_col = "Odd_H_Back"
        else:
            odd_home_col = "Odd_H_FT"

        if odd_home_max is not None:
            jogos_do_dia = [
                j for j in jogos_do_dia if safe_float(j.get(odd_home_col)) <= odd_home_max
            ]

        if odd_home_min is not None:
            jogos_do_dia = [
                j for j in jogos_do_dia if safe_float(j.get(odd_home_col)) >= odd_home_min
            ]

        jogos_mday = filter_games(jogos_do_dia, fonte)

        # Filtro ISC
        if isc and fonte == "betfair":
            isc_lower = isc.lower()
            jogos_filtrados_isc = []
            for jogo in jogos_mday:
                isc_val_str = jogo.get("ISC", "N/A")
                if isc_val_str != "N/A":
                    try:
                        isc_val = float(isc_val_str)
                        if (
                            (isc_lower == "excelente" and isc_val > 75)
                            or (isc_lower == "bom" and isc_val >= 65)
                            or (isc_lower == "moderado" and isc_val >= 55)
                            or (isc_lower == "fraco" and isc_val < 55)
                        ):
                            jogos_filtrados_isc.append(jogo)
                    except ValueError:
                        continue
            jogos_mday = jogos_filtrados_isc

        # 2. Obter dados SOFA
        console.print(f"[cyan]Buscando jogos para {data}...[/cyan]")
        eventos_sofa = get_scheduled_events(data)

        if not eventos_sofa:
            console.print(f"[yellow]Nenhum jogo no SOFA para {data}[/yellow]")
            return

        # Filtros SOFA
        if liga:
            eventos_sofa = [e for e in eventos_sofa if liga.lower() in e.tournament.name.lower()]

        if status:
            eventos_sofa = [
                e
                for e in eventos_sofa
                if status.lower() in e.status.type.lower()
                or status.lower() in e.status.description.lower()
            ]

        # Converter eventos para formato comparacao
        data_entrada = datetime.strptime(data, "%Y-%m-%d")
        data_entrada_str = data_entrada.strftime("%d/%m")

        jogos_sofa = []
        for evento in eventos_sofa:
            dt = datetime.fromtimestamp(evento.startTimestamp)
            if dt.strftime("%d/%m") != data_entrada_str:
                continue

            jogos_sofa.append(
                {
                    "Time": dt.strftime("%H:%M"),
                    "Date": dt.strftime("%d/%m"),
                    "League": evento.tournament.name,
                    "Home": evento.homeTeam.name,
                    "Away": evento.awayTeam.name,
                    "Gols_Casa": evento.homeScore.current if evento.homeScore else 0,
                    "Gols_Visitante": evento.awayScore.current if evento.awayScore else 0,
                    "Status": evento.status.description,
                    "ID": str(evento.id),
                }
            )

        # 3. Encontrar correspondencias
        jogos_correspondentes = []
        for jogo_mday in jogos_mday:
            melhor_correspondencia = None
            melhor_score = 0

            for jogo_sofa in jogos_sofa:
                score = 0
                # Comparacao exata
                if (
                    jogo_mday.get("Home", "").lower() == jogo_sofa.get("Home", "").lower()
                    and jogo_mday.get("Away", "").lower() == jogo_sofa.get("Away", "").lower()
                    and jogo_mday.get("Time", "") == jogo_sofa.get("Time", "")
                ):
                    score = 1.0
                # Apenas times
                elif (
                    jogo_mday.get("Home", "").lower() == jogo_sofa.get("Home", "").lower()
                    and jogo_mday.get("Away", "").lower() == jogo_sofa.get("Away", "").lower()
                ):
                    score = 0.8
                # Similaridade
                else:
                    home_sim = calculate_similarity(
                        jogo_mday.get("Home", ""), jogo_sofa.get("Home", "")
                    )
                    away_sim = calculate_similarity(
                        jogo_mday.get("Away", ""), jogo_sofa.get("Away", "")
                    )
                    score = (home_sim + away_sim) / 2

                if score > melhor_score and score >= 0.6:
                    melhor_score = score
                    melhor_correspondencia = jogo_sofa

            # Criar jogo combinado com lucros
            if melhor_correspondencia:
                jogo_combinado = jogo_mday.copy()
                gols_casa = melhor_correspondencia["Gols_Casa"]
                gols_visitante = melhor_correspondencia["Gols_Visitante"]

                jogo_combinado["Gols Casa"] = str(gols_casa)
                jogo_combinado["Gols Visitante"] = str(gols_visitante)
                jogo_combinado["Status SOFA"] = melhor_correspondencia["Status"]

                # Calcular lucros
                odd_a_lay = safe_float(jogo_mday.get("Odd_A_Lay", 0))
                odd_h_back = safe_float(jogo_mday.get("Odd_H_Back", 0))

                # Lay Away
                if odd_a_lay > 1:
                    if gols_casa >= gols_visitante:
                        lucro_lay_away = 1 / (odd_a_lay - 1)
                        jogo_combinado["Lucro Lay Away"] = f"{lucro_lay_away:.3f}"
                    else:
                        jogo_combinado["Lucro Lay Away"] = "-1.000"
                else:
                    jogo_combinado["Lucro Lay Away"] = "N/A"

                # Back Home
                if odd_h_back > 0:
                    if gols_casa > gols_visitante:
                        lucro_back_home = odd_h_back - 1
                        jogo_combinado["Lucro Back Home"] = f"{lucro_back_home:.3f}"
                    else:
                        jogo_combinado["Lucro Back Home"] = "-1.000"
                else:
                    jogo_combinado["Lucro Back Home"] = "N/A"

                jogos_correspondentes.append(jogo_combinado)

        # 4. Mostrar resultados
        if jogos_correspondentes:
            console.print(
                f"\n[bold green]Encontradas {len(jogos_correspondentes)} correspondencias[/bold green]"
            )
            print_table(jogos_correspondentes)

            # Estatisticas
            lucros_lay = [
                float(j.get("Lucro Lay Away", "0"))
                for j in jogos_correspondentes
                if j.get("Lucro Lay Away", "N/A") != "N/A"
            ]
            lucros_back = [
                float(j.get("Lucro Back Home", "0"))
                for j in jogos_correspondentes
                if j.get("Lucro Back Home", "N/A") != "N/A"
            ]

            console.print("\n[bold]Estatisticas:[/bold]")
            if lucros_lay:
                console.print(
                    f"LAY AWAY: {len(lucros_lay)} jogos, lucro total: {sum(lucros_lay):.3f}"
                )
            if lucros_back:
                console.print(
                    f"BACK HOME: {len(lucros_back)} jogos, lucro total: {sum(lucros_back):.3f}"
                )

            if salvar:
                filtros = [fonte]
                if odd_home_max:
                    filtros.append(f"home-max-{odd_home_max}")
                if odd_home_min:
                    filtros.append(f"home-min-{odd_home_min}")
                if isc:
                    filtros.append(f"isc-{isc.lower()}")
                if liga:
                    filtros.append(f"liga-{liga.lower().replace(' ', '-')}")
                if status:
                    filtros.append(f"status-{status.lower()}")
                save_diff_to_file(jogos_correspondentes, data, filtros)
        else:
            console.print("[yellow]Nenhuma correspondencia encontrada[/yellow]")

        if fonte == "betfair" and jogos_correspondentes:
            print_isc_legend()

    except Exception as e:
        console.print(f"[bold red]Erro: {e}[/bold red]")
