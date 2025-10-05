"""Lay Away command - calculate profit/loss verifying results."""

from datetime import date

import typer
from rich.console import Console

from bet.cli.helpers import (
    filter_games,
    get_daily_games,
    print_isc_legend,
    safe_float,
    save_csv_to_file,
)
from bet.utils import buscar_resultado_partida, calcular_lucro_lay, print_table

console = Console()


def layaway_command(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    odd_home_max: float = typer.Option(
        1.70, help="Filtra jogos com odd do time da casa menor ou igual ao valor especificado."
    ),
    odd_home_min: float = typer.Option(
        1.40, help="Filtra jogos com odd do time da casa maior ou igual ao valor especificado."
    ),
    isc: str = typer.Option(
        "excelente",
        help="Filtra jogos por ISC: excelente (>75), bom (≥65), moderado (≥55), fraco (<55).",
    ),
    responsabilidade: float = typer.Option(
        100.0, help="Responsabilidade em unidades para o cálculo do lucro lay."
    ),
    primeiro_tempo: bool = typer.Option(
        False,
        "--primeiro-tempo",
        "-ht",
        help="Busca resultado do primeiro tempo (HT) ao invés do final.",
    ),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em CSV."),
):
    """Calcula profit/loss de estratégia Lay Away verificando resultados via DuckDuckGo."""
    periodo_texto = "primeiro tempo (HT)" if primeiro_tempo else "final (FT)"
    console.print(
        f"[bold cyan]🔍 LAY AWAY: Buscando jogos e resultados {periodo_texto} para {data}[/bold cyan]"
    )

    # 1. Obter jogos filtrados do mday
    jogos_do_dia = get_daily_games(data, "betfair")

    # Aplicar filtros de odd
    if odd_home_max is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia if safe_float(jogo.get("Odd_H_Back")) <= odd_home_max
        ]

    if odd_home_min is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia if safe_float(jogo.get("Odd_H_Back")) >= odd_home_min
        ]

    jogos_filtrados = filter_games(jogos_do_dia, "betfair")

    # Aplicar filtro ISC
    if isc is not None:
        isc_lower = isc.lower()
        jogos_filtrados_isc = []

        for jogo in jogos_filtrados:
            isc_value_str = jogo.get("ISC", "N/A")
            if isc_value_str != "N/A":
                try:
                    isc_value = float(isc_value_str)
                    if (
                        isc_lower == "excelente"
                        and isc_value > 75
                        or isc_lower == "bom"
                        and isc_value >= 65
                        or isc_lower == "moderado"
                        and isc_value >= 55
                        or isc_lower == "fraco"
                        and isc_value < 55
                    ):
                        jogos_filtrados_isc.append(jogo)
                except ValueError:
                    continue

        jogos_filtrados = jogos_filtrados_isc

    if not jogos_filtrados:
        console.print("[yellow]Nenhum jogo encontrado com os filtros especificados.[/yellow]")
        return

    console.print(
        f"[green]✅ Encontrados {len(jogos_filtrados)} jogos com os filtros aplicados[/green]"
    )
    console.print(f"[cyan]🔍 Buscando resultados {periodo_texto} via DuckDuckGo...[/cyan]\n")

    # 2. Buscar resultados e calcular lucros
    jogos_com_resultado = []

    for idx, jogo in enumerate(jogos_filtrados, 1):
        home_team = jogo.get("Home", "")
        away_team = jogo.get("Away", "")

        console.print(
            f"[dim]{idx}/{len(jogos_filtrados)} - Buscando: {home_team} vs {away_team}...[/dim]"
        )

        # Buscar resultado
        resultado = buscar_resultado_partida(
            home_team, away_team, data, primeiro_tempo=primeiro_tempo
        )

        if resultado["encontrado"]:
            home_score = resultado["home_score"]
            away_score = resultado["away_score"]

            # Determinar resultado da partida
            if home_score > away_score:
                resultado_partida = "home_win"
            elif home_score < away_score:
                resultado_partida = "away_win"
            else:
                resultado_partida = "draw"

            # Calcular lucro lay ao visitante
            odd_a_lay = safe_float(jogo.get("Odd_A_Lay", 0))
            lucro = calcular_lucro_lay(odd_a_lay, responsabilidade, resultado_partida)

            # Adicionar informações ao jogo
            jogo_com_resultado = jogo.copy()
            periodo_label = "HT" if primeiro_tempo else "FT"
            jogo_com_resultado[f"Gols Casa {periodo_label}"] = str(home_score)
            jogo_com_resultado[f"Gols Visitante {periodo_label}"] = str(away_score)
            jogo_com_resultado["Resultado"] = resultado_partida.replace("_", " ").title()
            jogo_com_resultado["Lucro Lay"] = f"{lucro:.3f}"

            jogos_com_resultado.append(jogo_com_resultado)

            periodo_emoji = "🕐" if primeiro_tempo else "⏰"
            console.print(
                f"[green]  ✓ {periodo_emoji} {home_score}-{away_score} | Lucro: {lucro:.3f}[/green]"
            )
        else:
            console.print("[yellow]  ⚠ Resultado não encontrado[/yellow]")

    # 3. Exibir tabela com resultados
    if jogos_com_resultado:
        periodo_label = "PRIMEIRO TEMPO (HT)" if primeiro_tempo else "FINAL (FT)"
        console.print(
            f"\n[bold green]📊 RESULTADOS VERIFICADOS - {periodo_label} ({len(jogos_com_resultado)} jogos):[/bold green]"
        )
        print_table(jogos_com_resultado)

        # 4. Calcular estatísticas
        lucros = [float(jogo["Lucro Lay"]) for jogo in jogos_com_resultado]
        lucro_total = sum(lucros)
        lucro_medio = lucro_total / len(lucros) if lucros else 0
        jogos_positivos = [l for l in lucros if l > 0]
        jogos_negativos = [l for l in lucros if l < 0]
        taxa_acerto = (len(jogos_positivos) / len(lucros) * 100) if lucros else 0

        console.print("\n[bold]📈 ESTATÍSTICAS:[/bold]")
        console.print(f"   • Jogos verificados: [green]{len(jogos_com_resultado)}[/green]")
        console.print(f"   • Lucro total: [magenta]{lucro_total:.3f}[/magenta] unidades")
        console.print(f"   • Lucro médio: [cyan]{lucro_medio:.3f}[/cyan] unidades/jogo")
        console.print(f"   • Taxa de acerto: [bold cyan]{taxa_acerto:.1f}%[/bold cyan]")
        console.print(
            f"   • Jogos com lucro: [green]{len(jogos_positivos)}[/green] | Prejuízo: [red]{len(jogos_negativos)}[/red]"
        )
        console.print(
            f"   • Responsabilidade por jogo: [yellow]{responsabilidade}[/yellow] unidades"
        )

        # 5. Salvar se solicitado
        if salvar:
            filtros_aplicados = ["betfair"]
            if odd_home_max is not None:
                filtros_aplicados.append(f"home-max-{odd_home_max}")
            if odd_home_min is not None:
                filtros_aplicados.append(f"home-min-{odd_home_min}")
            if isc is not None:
                filtros_aplicados.append(f"isc-{isc.lower()}")
            if primeiro_tempo:
                filtros_aplicados.append("HT")
            else:
                filtros_aplicados.append("FT")
            filtros_aplicados.append("layaway")

            nome_arquivo = f"{data}_" + "_".join(filtros_aplicados)
            save_csv_to_file(jogos_com_resultado, nome_arquivo)

        # Mostrar legenda do ISC
        print_isc_legend()
    else:
        console.print("[yellow]Nenhum resultado encontrado para os jogos filtrados.[/yellow]")
