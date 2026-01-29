"""Add command - register and manage betting records."""

from datetime import date, datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from bet.storage.database import BettingDatabase

console = Console()
app = typer.Typer(help="Gerenciar registros de apostas")


@app.command(name="registro")
def adicionar_registro(
    aposta: str = typer.Option(..., "--aposta", "-a", help="Descrição da aposta"),
    lucro: Optional[float] = typer.Option(
        None, "--lucro", "-l", help="Valor do lucro/prejuízo"
    ),
    estrategia: str = typer.Option(
        "Under Limite", "--estrategia", "-e", help="Estratégia de aposta"
    ),
    data_aposta: Optional[str] = typer.Option(
        None, "--data", "-d", help="Data da aposta (YYYY-MM-DD, padrão: hoje)"
    ),
    stake: Optional[float] = typer.Option(
        None, "--stake", "-s", help="Stake da aposta (padrão: 5% da banca atual)"
    ),
):
    """Adicionar novo registro de aposta."""
    # Parse data
    data_obj = None
    if data_aposta:
        try:
            data_obj = datetime.strptime(data_aposta, "%Y-%m-%d").date()
        except ValueError:
            console.print(
                "[bold red]❌ Erro: formato de data inválido. Use YYYY-MM-DD[/bold red]"
            )
            raise typer.Exit(code=1)

    # Add record
    db = BettingDatabase()
    try:
        # Set date if not provided
        if data_obj is None:
            data_obj = date.today()

        # Get current bankroll for display
        banca_atual = db.obter_banca_atual()

        # If stake provided manually, show info
        if stake is not None:
            console.print(
                f"\n[bold cyan]ℹ️  Banca atual: {banca_atual:.2f} | Stake manual: {stake:.2f}[/bold cyan]"
            )
        else:
            # Calculate automatic stake (5% of bankroll)
            stake_calculada = db.calcular_stake_da_banca(banca_atual)
            console.print(
                f"\n[bold cyan]ℹ️  Banca atual: {banca_atual:.2f} | Stake automática (5%): {stake_calculada:.2f}[/bold cyan]"
            )

        registro_id = db.adicionar_registro(
            aposta=aposta,
            lucro_prejuizo=lucro,
            estrategia=estrategia,
            data=data_obj,
            stake=stake,
        )

        # Get the added record to show accumulated profit
        registros = db.buscar_registros()
        registro_adicionado = next((r for r in registros if r["id"] == registro_id), None)

        console.print(f"[green]✅ Registro adicionado com sucesso! ID: {registro_id}[/green]")

        # Show record details
        console.print("\n[bold cyan]📝 DETALHES DO REGISTRO:[/bold cyan]")
        console.print(f"   • Data: {data_obj or date.today()}")
        console.print(f"   • Estratégia: {estrategia}")
        console.print(f"   • Aposta: {aposta}")
        if registro_adicionado and registro_adicionado.get("banca") is not None:
            console.print(f"   • Banca: {registro_adicionado['banca']:.2f}")
        if registro_adicionado and registro_adicionado.get("stake") is not None:
            console.print(f"   • Stake: {registro_adicionado['stake']:.2f}")
        if lucro is not None:
            console.print(f"   • Lucro/Prejuízo: {lucro:.2f}")
        if registro_adicionado and registro_adicionado.get("lucro_acumulado") is not None:
            lucro_acum = registro_adicionado["lucro_acumulado"]
            cor_acum = "green" if lucro_acum >= 0 else "red"
            console.print(f"   • Lucro Acumulado: [{cor_acum}]{lucro_acum:.2f}[/{cor_acum}]")
            # Calculate new bankroll after this bet
            nova_banca = registro_adicionado['banca'] + lucro_acum
            cor_banca = "green" if nova_banca >= 427.0 else "red"
            console.print(f"   • Nova Banca: [{cor_banca}]{nova_banca:.2f}[/{cor_banca}]")

    except Exception as e:
        console.print(f"[bold red]❌ Erro ao adicionar registro: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="listar")
def listar_registros(
    hoje: bool = typer.Option(True, "--hoje", help="Mostrar registros de hoje"),
    semana: bool = typer.Option(True, "--semana", help="Mostrar registros da semana"),
    mes: bool = typer.Option(True, "--mes", help="Mostrar registros do mês"),
    inicio: Optional[str] = typer.Option(
        None, "--inicio", help="Data de início (YYYY-MM-DD)"
    ),
    fim: Optional[str] = typer.Option(None, "--fim", help="Data de fim (YYYY-MM-DD)"),
    ultimos_dias: Optional[int] = typer.Option(
        None, "--ultimos-dias", help="Últimos N dias"
    ),
    estrategia: Optional[str] = typer.Option(
        None, "--estrategia", "-e", help="Filtrar por estratégia"
    ),
):
    """Listar registros de apostas com filtros de período."""
    db = BettingDatabase()

    # Determine query mode
    if inicio or fim:
        # Custom range
        try:
            data_inicio = datetime.strptime(inicio, "%Y-%m-%d").date() if inicio else None
            data_fim = datetime.strptime(fim, "%Y-%m-%d").date() if fim else None
            registros = db.buscar_registros(
                data_inicio=data_inicio, data_fim=data_fim, estrategia=estrategia
            )
            periodo_label = f"Período: {inicio or '...'} até {fim or '...'}"
        except ValueError:
            console.print(
                "[bold red]❌ Erro: formato de data inválido. Use YYYY-MM-DD[/bold red]"
            )
            raise typer.Exit(code=1)

    elif ultimos_dias:
        # Last N days
        data_inicio = date.today() - __import__("datetime").timedelta(days=ultimos_dias)
        registros = db.buscar_registros(
            data_inicio=data_inicio, data_fim=date.today(), estrategia=estrategia
        )
        periodo_label = f"Últimos {ultimos_dias} dias"

    else:
        # Default: show all enabled periods (hoje, semana, mes)
        registros_por_periodo = {}

        if hoje:
            registros_por_periodo["Hoje"] = db.buscar_por_periodo("hoje")
        if semana:
            registros_por_periodo["Semana"] = db.buscar_por_periodo("semana")
        if mes:
            registros_por_periodo["Mês"] = db.buscar_por_periodo("mes")

        # Display each period separately
        for periodo_nome, regs in registros_por_periodo.items():
            if estrategia:
                regs = [r for r in regs if r["estrategia"] == estrategia]

            console.print(f"\n[bold cyan]📊 REGISTROS - {periodo_nome.upper()}[/bold cyan]")

            if not regs:
                console.print(f"[yellow]   Nenhum registro encontrado para {periodo_nome}[/yellow]")
                continue

            # Display table
            _display_records_table(regs)

            # Display statistics
            stats = db.calcular_estatisticas(regs)
            _display_statistics(stats)

        return

    # Single period display
    console.print(f"\n[bold cyan]📊 REGISTROS - {periodo_label.upper()}[/bold cyan]")

    if not registros:
        console.print("[yellow]   Nenhum registro encontrado[/yellow]")
        return

    # Display table
    _display_records_table(registros)

    # Display statistics
    stats = db.calcular_estatisticas(registros)
    _display_statistics(stats)


@app.command(name="banca")
def atualizar_banca(
    nova_banca: float = typer.Option(..., "--valor", "-v", help="Novo valor da banca"),
    motivo: Optional[str] = typer.Option(
        "Ajuste de banca", "--motivo", "-m", help="Motivo do ajuste"
    ),
):
    """Atualizar a banca manualmente (cria registro especial de ajuste)."""
    db = BettingDatabase()

    # Get current bankroll
    banca_atual = db.obter_banca_atual()

    # Calculate adjustment amount
    ajuste = nova_banca - banca_atual

    # Show info
    console.print(f"\n[bold cyan]💰 ATUALIZAÇÃO DE BANCA[/bold cyan]")
    console.print(f"   • Banca atual: {banca_atual:.2f}")
    console.print(f"   • Nova banca: {nova_banca:.2f}")

    ajuste_color = "green" if ajuste >= 0 else "red"
    ajuste_sign = "+" if ajuste >= 0 else ""
    console.print(f"   • Ajuste: [{ajuste_color}]{ajuste_sign}{ajuste:.2f}[/{ajuste_color}]")
    console.print(f"   • Motivo: {motivo}")

    # Confirm
    confirmar = typer.confirm("\nDeseja confirmar a atualização da banca?")
    if not confirmar:
        console.print("[yellow]❌ Operação cancelada[/yellow]")
        raise typer.Exit(code=0)

    try:
        # Add special record for bankroll adjustment
        registro_id = db.adicionar_registro(
            aposta=f"AJUSTE DE BANCA: {motivo}",
            lucro_prejuizo=ajuste,
            estrategia="Ajuste Manual",
            stake=0.0,  # No stake for adjustments
        )

        console.print(f"\n[green]✅ Banca atualizada com sucesso! ID: {registro_id}[/green]")

        # Show new bankroll (recalculate from database)
        nova_banca_final = db.obter_banca_atual()
        console.print(f"\n[bold green]💰 Nova banca: {nova_banca_final:.2f}[/bold green]")
        console.print(f"   • Próxima stake automática (5%): {db.calcular_stake_da_banca(nova_banca_final):.2f}")

    except Exception as e:
        console.print(f"[bold red]❌ Erro ao atualizar banca: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="resumo")
def resumo_registros(
    hoje: bool = typer.Option(False, "--hoje", help="Resumo de hoje"),
    semana: bool = typer.Option(False, "--semana", help="Resumo da semana"),
    mes: bool = typer.Option(True, "--mes", help="Resumo do mês"),
    inicio: Optional[str] = typer.Option(
        None, "--inicio", help="Data de início (YYYY-MM-DD)"
    ),
    fim: Optional[str] = typer.Option(None, "--fim", help="Data de fim (YYYY-MM-DD)"),
    ultimos_dias: Optional[int] = typer.Option(
        None, "--ultimos-dias", help="Últimos N dias"
    ),
):
    """Mostrar resumo estatístico dos registros."""
    db = BettingDatabase()

    # Determine query mode
    if inicio or fim:
        # Custom range
        try:
            data_inicio = datetime.strptime(inicio, "%Y-%m-%d").date() if inicio else None
            data_fim = datetime.strptime(fim, "%Y-%m-%d").date() if fim else None
            registros = db.buscar_registros(data_inicio=data_inicio, data_fim=data_fim)
            periodo_label = f"Período: {inicio or '...'} até {fim or '...'}"
        except ValueError:
            console.print(
                "[bold red]❌ Erro: formato de data inválido. Use YYYY-MM-DD[/bold red]"
            )
            raise typer.Exit(code=1)

    elif ultimos_dias:
        # Last N days
        data_inicio = date.today() - __import__("datetime").timedelta(days=ultimos_dias)
        registros = db.buscar_registros(data_inicio=data_inicio, data_fim=date.today())
        periodo_label = f"Últimos {ultimos_dias} dias"

    elif hoje:
        registros = db.buscar_por_periodo("hoje")
        periodo_label = "Hoje"

    elif semana:
        registros = db.buscar_por_periodo("semana")
        periodo_label = "Semana"

    elif mes:
        registros = db.buscar_por_periodo("mes")
        periodo_label = "Mês"

    else:
        # Default: month
        registros = db.buscar_por_periodo("mes")
        periodo_label = "Mês"

    console.print(f"\n[bold cyan]📈 RESUMO ESTATÍSTICO - {periodo_label.upper()}[/bold cyan]")

    if not registros:
        console.print("[yellow]   Nenhum registro encontrado[/yellow]")
        return

    # Calculate and display statistics
    stats = db.calcular_estatisticas(registros)

    console.print(f"\n[bold]Total de Registros:[/bold] {stats['total']}")

    # Profit/Loss
    lucro_color = "green" if stats["lucro_total"] >= 0 else "red"
    console.print(
        f"[bold]Lucro/Prejuízo Total:[/bold] [{lucro_color}]{stats['lucro_total']:.2f}[/{lucro_color}]"
    )
    console.print(f"[bold]Lucro Médio por Aposta:[/bold] [cyan]{stats['lucro_medio']:.2f}[/cyan]")

    # Performance indicator
    if stats["lucro_total"] > 0:
        console.print("\n[bold green]✅ Performance: LUCRO[/bold green]")
    elif stats["lucro_total"] == 0:
        console.print("\n[bold yellow]⚠️ Performance: NEUTRO[/bold yellow]")
    else:
        console.print("\n[bold red]❌ Performance: PREJUÍZO[/bold red]")


def _display_records_table(registros: list):
    """Display records in a formatted table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Data", width=12)
    table.add_column("Estratégia", width=15)
    table.add_column("Aposta", width=30)
    table.add_column("Banca", width=10, justify="right")
    table.add_column("Stake", width=10, justify="right")
    table.add_column("Lucro/Prej", width=12, justify="right")
    table.add_column("Acum.", width=12, justify="right")

    for reg in registros:
        # Format banca
        banca = reg.get("banca", 427.0)
        banca_fmt = f"{banca:.2f}"

        # Format stake
        stake = reg.get("stake", 25.0)
        stake_fmt = f"{stake:.2f}"

        # Format lucro with color
        lucro = reg["lucro_prejuizo"]
        if lucro is not None:
            if lucro >= 0:
                lucro_fmt = f"[green]+{lucro:.2f}[/green]"
            else:
                lucro_fmt = f"[red]{lucro:.2f}[/red]"
        else:
            lucro_fmt = "-"

        # Format accumulated profit with color
        lucro_acum = reg.get("lucro_acumulado")
        if lucro_acum is not None:
            if lucro_acum >= 0:
                acum_fmt = f"[green]{lucro_acum:.2f}[/green]"
            else:
                acum_fmt = f"[red]{lucro_acum:.2f}[/red]"
        else:
            acum_fmt = "-"

        # Truncate estrategia if too long
        estrategia = reg.get("estrategia", "N/A")
        estrategia_fmt = estrategia[:12] + "..." if len(estrategia) > 15 else estrategia

        table.add_row(
            str(reg["id"]),
            reg["data"],
            estrategia_fmt,
            reg["aposta"][:27] + "..." if len(reg["aposta"]) > 30 else reg["aposta"],
            banca_fmt,
            stake_fmt,
            lucro_fmt,
            acum_fmt,
        )

    console.print(table)


def _display_statistics(stats: dict):
    """Display statistics summary."""
    console.print("\n[bold]📊 Estatísticas:[/bold]")
    console.print(f"   • Total: {stats['total']}")

    lucro_color = "green" if stats["lucro_total"] >= 0 else "red"
    console.print(
        f"   • Lucro Total: [{lucro_color}]{stats['lucro_total']:.2f}[/{lucro_color}] | Média: [cyan]{stats['lucro_medio']:.2f}[/cyan]"
    )


# Entry point for the command
def add_command():
    """Main entry point for the add command."""
    app()
