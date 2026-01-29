"""Graph command - visual bar chart of monthly betting performance."""

from datetime import date, datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from bet.storage.database import BettingDatabase

console = Console()


def graph_command(
    mes: Optional[str] = typer.Option(
        None, "--mes", "-m", help="Mês específico (YYYY-MM, padrão: mês atual)"
    ),
    estrategia: Optional[str] = typer.Option(
        None, "--estrategia", "-e", help="Filtrar por estratégia"
    ),
):
    """Exibir gráfico de barras mensal com percentuais da stake."""
    # Parse month
    if mes:
        try:
            target_date = datetime.strptime(mes, "%Y-%m").date()
            ano = target_date.year
            mes_num = target_date.month
        except ValueError:
            console.print(
                "[bold red]❌ Erro: formato de mês inválido. Use YYYY-MM[/bold red]"
            )
            raise typer.Exit(code=1)
    else:
        hoje = date.today()
        ano = hoje.year
        mes_num = hoje.month

    # Get records for the month
    db = BettingDatabase()
    primeiro_dia = date(ano, mes_num, 1)

    # Calculate last day of month
    if mes_num == 12:
        ultimo_dia = date(ano, 12, 31)
    else:
        ultimo_dia = date(ano, mes_num + 1, 1)
        ultimo_dia = ultimo_dia.replace(day=1) - __import__("datetime").timedelta(days=1)

    registros = db.buscar_registros(
        data_inicio=primeiro_dia, data_fim=ultimo_dia, estrategia=estrategia
    )

    if not registros:
        console.print(f"\n[yellow]📊 Nenhum registro encontrado para {mes_num:02d}/{ano}[/yellow]\n")
        return

    # Aggregate data by day
    dados_por_dia = {}
    for reg in registros:
        data_str = reg["data"]
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        dia = data.day

        if dia not in dados_por_dia:
            dados_por_dia[dia] = {
                "lucro_total": 0.0,
                "stake_dia": reg.get("stake", 25.0),
                "count": 0,
            }

        dados_por_dia[dia]["lucro_total"] += reg.get("lucro_prejuizo") or 0.0
        dados_por_dia[dia]["count"] += 1

    # Calculate percentages
    for dia, dados in dados_por_dia.items():
        stake = dados["stake_dia"]
        if stake > 0:
            dados["percentual"] = (dados["lucro_total"] / stake) * 100
        else:
            dados["percentual"] = 0.0

    # Display graph
    _render_bar_chart(dados_por_dia, ano, mes_num)


def _render_bar_chart(dados_por_dia: dict, ano: int, mes: int):
    """Render vertical ASCII bar chart - positive bars up, negative bars down."""
    # Month name in Portuguese
    meses_pt = [
        "",
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]

    console.print(f"\n[bold cyan]📊 GRÁFICO DE BARRAS - {meses_pt[mes]} {ano}[/bold cyan]\n")

    # Sort by day
    dias_ordenados = sorted(dados_por_dia.keys())

    # Find max positive and negative for scaling
    max_pos = max((d["percentual"] for d in dados_por_dia.values() if d["percentual"] > 0), default=0)
    max_neg = abs(min((d["percentual"] for d in dados_por_dia.values() if d["percentual"] < 0), default=0))
    max_pct = max(max_pos, max_neg)

    # Scale factor: max 10 rows for bars
    max_height = 10
    if max_pct > 0:
        scale = max_height / max_pct
    else:
        scale = 1.0

    # Prepare data with bar heights
    bars_data = []
    for dia in dias_ordenados:
        dados = dados_por_dia[dia]
        pct = dados["percentual"]
        height = int(abs(pct) * scale)
        if height < 1 and pct != 0:
            height = 1

        bars_data.append({
            "dia": dia,
            "pct": pct,
            "height": height,
            "count": dados["count"],
            "is_positive": pct >= 0
        })

    # Render positive bars (top section)
    for row in range(max_height, 0, -1):
        line_parts = []
        for bar in bars_data:
            if bar["is_positive"] and bar["height"] >= row:
                line_parts.append("[green]██[/green]")
            else:
                line_parts.append("  ")
        console.print("     " + " ".join(line_parts))

    # Zero line
    console.print("─────" + "───".join(["──"] * len(bars_data)))

    # Render negative bars (bottom section)
    for row in range(1, max_height + 1):
        line_parts = []
        for bar in bars_data:
            if not bar["is_positive"] and bar["height"] >= row:
                line_parts.append("[red]██[/red]")
            else:
                line_parts.append("  ")
        console.print("     " + " ".join(line_parts))

    # Day labels
    day_labels = "     " + " ".join(f"{bar['dia']:2d}" for bar in bars_data)
    console.print("\n" + day_labels)

    # Percentage values
    pct_labels_parts = []
    for bar in bars_data:
        sign = "+" if bar["pct"] >= 0 else ""
        color = "green" if bar["pct"] >= 0 else "red"
        pct_labels_parts.append(f"[{color}]{sign}{bar['pct']:.0f}%[/{color}]")

    console.print("     " + " ".join(f"{label:>3}" for label in pct_labels_parts))

    # Summary statistics
    total_dias = len(dados_por_dia)
    total_apostas = sum(d["count"] for d in dados_por_dia.values())
    rendimento_total = sum(d["percentual"] for d in dados_por_dia.values())
    dias_positivos = len([d for d in dados_por_dia.values() if d["percentual"] > 0])
    taxa_vitoria = (dias_positivos / total_dias * 100) if total_dias > 0 else 0

    # Display summary
    console.print("\n" + "─" * 80)
    console.print(f"\n[bold]📈 RESUMO DO PERÍODO[/bold]")
    console.print(f"Total de dias: {total_dias}")
    console.print(f"Total de apostas: {total_apostas}")

    # Rendimento total
    rend_color = "green" if rendimento_total >= 0 else "red"
    rend_sign = "+" if rendimento_total >= 0 else ""
    console.print(
        f"Rendimento acumulado: [{rend_color}]{rend_sign}{rendimento_total:.1f}%[/{rend_color}]"
    )

    # Taxa de vitória
    console.print(f"Taxa de vitória: {taxa_vitoria:.0f}% ({dias_positivos}/{total_dias} dias)")

    # Best and worst days
    melhor_dia = max(dados_por_dia.items(), key=lambda x: x[1]["percentual"])
    pior_dia = min(dados_por_dia.items(), key=lambda x: x[1]["percentual"])

    console.print(
        f"Melhor dia: {melhor_dia[0]:02d}/{mes:02d} "
        f"([green]+{melhor_dia[1]['percentual']:.1f}%[/green])"
    )
    console.print(
        f"Pior dia: {pior_dia[0]:02d}/{mes:02d} "
        f"([red]{pior_dia[1]['percentual']:.1f}%[/red])"
    )

    console.print("")
