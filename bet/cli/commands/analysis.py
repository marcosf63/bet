"""Analysis command - statistical trading strategy analysis."""

from datetime import date
from pathlib import Path
import typer
from rich.console import Console

console = Console()

# Analytics import
try:
    from bet.analysis.analytics import TradingAnalyzer
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False


def analysis_command(
    arquivo: str = typer.Option(
        "notebooks/dados/lucro_por_operacao.csv",
        help="Caminho para o arquivo de dados CSV."
    ),
    coluna: str = typer.Option(
        "Lucro_Lay",
        help="Nome da coluna com os retornos/lucros."
    ),
    salvar_graficos: bool = typer.Option(
        False,
        "--salvar",
        help="Salvar gráficos em arquivo PNG."
    ),
    simulacoes: int = typer.Option(
        10000,
        help="Número de simulações Monte Carlo."
    ),
    operacoes_futuras: int = typer.Option(
        500,
        help="Número de operações para simular no futuro."
    ),
):
    """Executa análise estatística completa de uma estratégia de trading."""

    if not ANALYTICS_AVAILABLE:
        console.print("[red]❌ Funcionalidade de análise não disponível.[/red]")
        console.print("[yellow]💡 Instale as dependências: pip install scipy matplotlib seaborn[/yellow]")
        return

    console.print(f"[bold blue]📊 Iniciando análise da estratégia...[/bold blue]")
    console.print(f"📁 Arquivo: {arquivo}")
    console.print(f"📈 Coluna: {coluna}")
    console.print("=" * 60)

    try:
        # Verificar se arquivo existe
        arquivo_path = Path(arquivo)
        if not arquivo_path.exists():
            console.print(f"[red]❌ Arquivo não encontrado: {arquivo}[/red]")
            # Tentar caminhos alternativos
            arquivo_path = Path("data") / Path(arquivo).name
            if arquivo_path.exists():
                arquivo = str(arquivo_path)
                console.print(f"[yellow]📁 Usando arquivo alternativo: {arquivo}[/yellow]")
            else:
                console.print("[yellow]💡 Verifique o caminho do arquivo ou use o comando com --help[/yellow]")
                return

        # Carregar dados
        import pandas as pd
        df = pd.read_csv(arquivo)

        if coluna not in df.columns:
            console.print(f"[red]❌ Coluna '{coluna}' não encontrada.[/red]")
            console.print(f"[yellow]📊 Colunas disponíveis: {', '.join(df.columns)}[/yellow]")
            return

        # Preparar dados
        returns = df[coluna].dropna().values

        if len(returns) == 0:
            console.print(f"[red]❌ Nenhum dado válido encontrado na coluna '{coluna}'.[/red]")
            return

        console.print(f"[green]✅ Dados carregados: {len(returns)} operações[/green]")

        # Criar analisador
        analyzer = TradingAnalyzer(returns)

        # Gerar relatório
        console.print("\n[bold cyan]📈 RELATÓRIO DE ANÁLISE[/bold cyan]")
        console.print("=" * 70)

        # Estatísticas básicas
        basic_stats = analyzer.basic_stats()
        console.print(f"[blue]📊 Operações:[/blue] {basic_stats['count']}")
        console.print(f"[blue]💰 Retorno médio:[/blue] {basic_stats['mean']:.4f}")
        console.print(f"[blue]📐 Desvio padrão:[/blue] {basic_stats['std']:.4f}")
        console.print(f"[blue]📈 Mínimo/Máximo:[/blue] {basic_stats['min']:.4f} / {basic_stats['max']:.4f}")

        # Métricas de performance
        perf_metrics = analyzer.performance_metrics()
        console.print(f"\n[green]🎯 Taxa de acerto:[/green] {perf_metrics['win_rate']*100:.1f}%")
        console.print(f"[green]💎 Profit Factor:[/green] {perf_metrics['profit_factor']:.2f}")
        console.print(f"[green]⚡ Índice Sharpe:[/green] {perf_metrics['sharpe_ratio']:.2f}")
        console.print(f"[green]🎯 Expectância:[/green] {perf_metrics['expectancy']:.4f}")

        # Análise de risco
        max_dd = analyzer.max_drawdown()
        var_5, cvar_5 = analyzer.value_at_risk()
        kelly = analyzer.kelly_criterion()

        console.print(f"\n[red]⚠️  Drawdown máximo:[/red] {max_dd:.4f}")
        console.print(f"[red]📉 VaR (5%):[/red] {var_5:.4f}")
        console.print(f"[red]💥 CVaR (5%):[/red] {cvar_5:.4f}")
        console.print(f"[yellow]🎰 Kelly %:[/yellow] {kelly*100:.1f}%")

        # Simulação Monte Carlo
        console.print(f"\n[bold magenta]🎲 SIMULAÇÃO MONTE CARLO[/bold magenta]")
        console.print("=" * 50)

        with console.status("[bold green]Executando simulações..."):
            mc_results = analyzer.monte_carlo_simulation(
                n_simulations=simulacoes,
                n_periods=operacoes_futuras
            )

        console.print(f"[cyan]📊 Simulações:[/cyan] {simulacoes:,}")
        console.print(f"[cyan]🔮 Operações futuras:[/cyan] {operacoes_futuras}")
        console.print(f"[green]📈 Prob. de lucro:[/green] {mc_results['prob_positive']*100:.1f}%")
        console.print(f"[blue]💰 Retorno médio esperado:[/blue] {mc_results['mean_return']:.2f}")
        console.print(f"[yellow]📊 Cenário otimista (95%):[/yellow] {mc_results['percentile_95']:.2f}")
        console.print(f"[red]📊 Cenário pessimista (5%):[/red] {mc_results['percentile_5']:.2f}")

        # Recomendações
        console.print(f"\n[bold yellow]💡 RECOMENDAÇÕES[/bold yellow]")
        console.print("=" * 40)

        if perf_metrics['expectancy'] > 0:
            console.print("[green]✅ Estratégia com expectância positiva - continuar execução[/green]")
        else:
            console.print("[red]❌ Estratégia com expectância negativa - revisar urgentemente[/red]")

        if perf_metrics['sharpe_ratio'] > 1.0:
            console.print("[green]✅ Boa relação risco-retorno (Sharpe > 1.0)[/green]")
        else:
            console.print("[yellow]⚠️  Relação risco-retorno pode ser melhorada[/yellow]")

        if perf_metrics['win_rate'] > 0.6:
            console.print("[green]✅ Taxa de acerto satisfatória[/green]")
        else:
            console.print("[yellow]⚠️  Considerar melhorar filtros de entrada[/yellow]")

        if abs(max_dd) < 0.1:
            console.print("[green]✅ Drawdown controlado[/green]")
        else:
            console.print("[red]⚠️  Implementar gestão de risco mais rigorosa[/red]")

        console.print(f"[cyan]🎯 Sugestão de sizing: {kelly*100:.1f}% do capital por operação[/cyan]")

        # Gerar gráficos se solicitado
        if salvar_graficos:
            try:
                console.print(f"\n[bold blue]📈 Gerando visualizações...[/bold blue]")

                import matplotlib
                matplotlib.use('Agg')  # Backend não-interativo

                fig = analyzer.plot_analysis()

                # Salvar gráfico
                output_path = f"analise_{coluna.lower()}_{date.today().strftime('%Y%m%d')}.png"
                fig.savefig(output_path, dpi=300, bbox_inches='tight')
                console.print(f"[green]💾 Gráficos salvos em: {output_path}[/green]")

                # Limpar memória
                import matplotlib.pyplot as plt
                plt.close(fig)

            except Exception as e:
                console.print(f"[red]❌ Erro ao gerar gráficos: {e}[/red]")

        console.print(f"\n[bold green]✅ Análise concluída com sucesso![/bold green]")
        console.print("[dim]💡 Use --salvar para gerar gráficos ou --help para mais opções[/dim]")

    except FileNotFoundError:
        console.print(f"[red]❌ Arquivo não encontrado: {arquivo}[/red]")
        console.print("[yellow]💡 Verifique o caminho do arquivo[/yellow]")
    except KeyError as e:
        console.print(f"[red]❌ Coluna não encontrada: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Erro na análise: {e}[/red]")
        console.print("[yellow]💡 Verifique se o arquivo está no formato correto[/yellow]")
