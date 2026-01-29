"""Calendar command - visual monthly betting performance calendar."""

import calendar
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bet.storage.database import BettingDatabase

console = Console()


def calendar_command(
    mes: Optional[str] = typer.Option(
        None, "--mes", "-m", help="Mês específico (YYYY-MM, padrão: mês atual)"
    ),
    estrategia: Optional[str] = typer.Option(
        None, "--estrategia", "-e", help="Filtrar por estratégia"
    ),
):
    """Exibir calendário mensal visual com performance de apostas (usa stakes reais dos registros)."""
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

    # Aggregate data by day
    dados_por_dia = _aggregate_daily_data(registros)

    # Render calendar
    _render_calendar(ano, mes_num, dados_por_dia)

    # Display statistics
    _display_monthly_stats(dados_por_dia, registros, ano, mes_num)


def _aggregate_daily_data(registros: List[dict]) -> Dict[int, dict]:
    """Aggregate betting data by day of month - percentage = (total profit / stake) × 100."""
    dados_por_dia = defaultdict(
        lambda: {
            "lucro_total": 0.0,
            "count": 0,
            "lucro_acumulado": 0.0,
            "percentual_stake": 0.0,
            "stake_dia": 0.0,  # Stake for the day (same for all bets)
        }
    )

    for reg in registros:
        # Parse date
        data_str = reg["data"]
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        dia = data.day

        # Aggregate values
        lucro = reg.get("lucro_prejuizo") or 0.0
        stake = reg.get("stake", 25.0)

        dados_por_dia[dia]["lucro_total"] += lucro
        dados_por_dia[dia]["count"] += 1

        # Set stake for the day (all bets on the same day should have the same stake)
        if dados_por_dia[dia]["stake_dia"] == 0.0:
            dados_por_dia[dia]["stake_dia"] = stake

        # Use accumulated profit from last record of the day
        lucro_acum = reg.get("lucro_acumulado") or 0.0
        dados_por_dia[dia]["lucro_acumulado"] = lucro_acum

    # Calculate daily percentage: (total profit / stake) × 100
    for dia, dados in dados_por_dia.items():
        if dados["stake_dia"] > 0:
            dados["percentual_stake"] = (dados["lucro_total"] / dados["stake_dia"]) * 100

    return dados_por_dia


def _get_text_color(percentual: float) -> str:
    """Get text color based on performance percentage."""
    if percentual > 0:
        return "green"  # Profit
    elif percentual < 0:
        return "red"  # Loss
    else:
        return "white"  # Neutral


def _render_calendar(
    ano: int, mes: int, dados_por_dia: Dict[int, dict]
):
    """Render visual calendar with betting performance."""
    # Month name in Portuguese
    meses_pt = [
        "",
        "JANEIRO",
        "FEVEREIRO",
        "MARÇO",
        "ABRIL",
        "MAIO",
        "JUNHO",
        "JULHO",
        "AGOSTO",
        "SETEMBRO",
        "OUTUBRO",
        "NOVEMBRO",
        "DEZEMBRO",
    ]

    console.print(f"\n[bold cyan]📅 CALENDÁRIO DE APOSTAS - {meses_pt[mes]} {ano}[/bold cyan]\n")

    # Create calendar matrix (Monday as first day of week - ISO standard)
    calendar.setfirstweekday(calendar.MONDAY)
    cal = calendar.monthcalendar(ano, mes)

    # Create table
    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=None,
        padding=(0, 1),
        expand=True,
    )

    # Add columns for days of week (Monday first - ISO standard)
    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    for dia in dias_semana:
        table.add_column(dia, justify="center", width=12)

    # Add rows for weeks
    hoje = date.today()

    for semana in cal:
        row_cells = []

        for dia_num in semana:
            if dia_num == 0:
                # Empty cell
                row_cells.append("")
            else:
                dia_data = date(ano, mes, dia_num)
                dados = dados_por_dia.get(dia_num)

                if dados and dados["count"] > 0:
                    # Day with bets
                    percentual = dados["percentual_stake"]

                    # Get text color
                    text_color = _get_text_color(percentual)

                    # Format cell content
                    cell_text = Text()
                    cell_text.append(f"{dia_num:2d}\n", style="white")

                    # Percentage with sign
                    sign = "+" if percentual >= 0 else ""
                    cell_text.append(f"{sign}{percentual:.1f}%", style=text_color)

                    # No background, white border
                    row_cells.append(
                        Panel(
                            cell_text,
                            style="white",
                            padding=(0, 0),
                            border_style="white",
                        )
                    )

                else:
                    # Day without bets (past or future)
                    cell_text = Text()
                    cell_text.append(f"{dia_num:2d}", style="white")

                    row_cells.append(
                        Panel(
                            cell_text,
                            style="white",
                            padding=(0, 0),
                            border_style="white",
                        )
                    )

        table.add_row(*row_cells)

    console.print(table)

    # Legend
    console.print("\n[bold]🎨 LEGENDA:[/bold]")
    console.print("  [green]🟢 Verde[/green]: Lucro  |  [red]🔴 Vermelho[/red]: Prejuízo  |  [white]⚪ Branco[/white]: Sem dados")
    console.print("\n[italic]ℹ️  Percentual do dia = (lucro total do dia / stake do dia) × 100[/italic]")


def _display_monthly_stats(
    dados_por_dia: Dict[int, dict], registros: List[dict], ano: int, mes: int
):
    """Display monthly statistics summary."""
    console.print("\n[bold cyan]📊 ESTATÍSTICAS DO MÊS[/bold cyan]")

    if not dados_por_dia:
        console.print("[yellow]   Nenhum registro encontrado para este mês[/yellow]")
        return

    # Calculate statistics
    dias_com_apostas = len([d for d in dados_por_dia.values() if d["count"] > 0])
    total_apostas = sum(d["count"] for d in dados_por_dia.values())

    # Total profit/loss
    lucro_total = sum(d["lucro_total"] for d in dados_por_dia.values())

    # Get stake value (assuming all bets use the same stake)
    stake_unitaria = next((d["stake_dia"] for d in dados_por_dia.values() if d["stake_dia"] > 0), 25.0)

    # Calculate total stake invested (stake_dia × count for each day)
    stake_total = sum(d["stake_dia"] * d["count"] for d in dados_por_dia.values())

    # Best and worst days
    dias_lucro = {dia: d for dia, d in dados_por_dia.items() if d["count"] > 0}

    if dias_lucro:
        melhor_dia = max(dias_lucro.items(), key=lambda x: x[1]["lucro_total"])
        pior_dia = min(dias_lucro.items(), key=lambda x: x[1]["lucro_total"])

        # Win rate (bets won - individual operations)
        apostas_ganhas = sum(1 for reg in registros if (reg.get("lucro_prejuizo") or 0.0) > 0)
        taxa_vitoria = (apostas_ganhas / total_apostas * 100) if total_apostas > 0 else 0

        # Calculate ROI based on total stakes
        roi_pct = (lucro_total / stake_total * 100) if stake_total > 0 else 0

        # Calculate accumulated return (sum of daily percentages)
        rendimento_acumulado = sum(d["percentual_stake"] for d in dados_por_dia.values())

        # Display stats
        console.print(f"\n[bold]Período:[/bold] {mes:02d}/{ano}")
        console.print(f"[bold]Total de dias com apostas:[/bold] {dias_com_apostas}")
        console.print(f"[bold]Total de apostas:[/bold] {total_apostas}")

        # Accumulated return (sum of daily percentages)
        stakes_color = "green" if rendimento_acumulado >= 0 else "red"
        stakes_sign = "+" if rendimento_acumulado >= 0 else ""
        console.print(
            f"[bold]Rendimento Acumulado:[/bold] [{stakes_color}]{stakes_sign}{rendimento_acumulado:.1f}%[/{stakes_color}]"
        )

        # Profit/loss with color
        lucro_color = "green" if lucro_total >= 0 else "red"
        sign = "+" if lucro_total >= 0 else ""
        console.print(
            f"[bold]Lucro/Prejuízo Total:[/bold] [{lucro_color}]{sign}{lucro_total:.2f}[/{lucro_color}]"
        )

        # Best/worst days
        console.print(
            f"[bold]Melhor dia:[/bold] {melhor_dia[0]:02d}/{mes:02d} "
            f"([green]+{melhor_dia[1]['lucro_total']:.2f}[/green])"
        )
        console.print(
            f"[bold]Pior dia:[/bold] {pior_dia[0]:02d}/{mes:02d} "
            f"([red]{pior_dia[1]['lucro_total']:.2f}[/red])"
        )

        # Win rate (individual bets won)
        console.print(
            f"[bold]Taxa de vitória:[/bold] {taxa_vitoria:.0f}% ({apostas_ganhas}/{total_apostas})"
        )

        # ROI
        roi_color = "green" if roi_pct >= 0 else "red"
        roi_sign = "+" if roi_pct >= 0 else ""
        console.print(
            f"[bold]ROI:[/bold] [{roi_color}]{roi_sign}{roi_pct:.1f}%[/{roi_color}]"
        )

        # Performance indicator based on ROI
        if roi_pct > 20:
            console.print("\n[bold green]🚀 Performance: EXCELENTE (+20% ROI)[/bold green]")
        elif roi_pct > 10:
            console.print("\n[bold green]✅ Performance: MUITO BOM (+10% ROI)[/bold green]")
        elif roi_pct > 0:
            console.print("\n[bold green]📈 Performance: POSITIVO[/bold green]")
        elif roi_pct == 0:
            console.print("\n[bold yellow]➖ Performance: NEUTRO[/bold yellow]")
        elif roi_pct > -10:
            console.print("\n[bold red]⚠️ Performance: PREJUÍZO LEVE[/bold red]")
        else:
            console.print("\n[bold red]❌ Performance: PREJUÍZO SIGNIFICATIVO[/bold red]")
