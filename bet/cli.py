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

# Analytics import
try:
    from bet.analytics import TradingAnalyzer
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

URL_TEMPLATES = {
    "betfair": "https://raw.githubusercontent.com/futpythontrader/Jogos_do_Dia/refs/heads/main/Betfair/Jogos_do_Dia_Betfair_Back_Lay_{data}.csv",
    "footystats": "https://github.com/futpythontrader/Jogos_do_Dia/raw/refs/heads/main/FootyStats/Jogos_do_Dia_FootyStats_{data}.csv",
    "flashscore": "https://github.com/futpythontrader/Jogos_do_Dia/raw/refs/heads/main/FlashScore/Jogos_do_Dia_FlashScore_{data}.csv"
}
COLUNAS_PRINCIPAIS = {
    "betfair": [
        "Date", "Time", "League", "Home", "Away", "Odd_H_Back", "Odd_D_Back",
        "Odd_A_Back", "Odd_Over25_FT_Back", "Odd_BTTS_Yes_Back", "Odd_Over15_FT_Back"
    ],
    "footystats": [
        "Date", "Time", "League", "Home", "Away", "Odd_H_FT", "Odd_D_FT", 
        "Odd_A_FT", "Odd_Over05_HT", "Odd_BTTS_No", "XG_Home_Pre"
    ],
    "flashscore": [
        "Date", "Time", "League", "Home", "Away", "Odd_H_FT", "Odd_D_FT", 
        "Odd_A_FT", "Odd_Over05_HT", "Odd_BTTS_No", "XG_Home_Pre"
    ]
}


# --- Funções Auxiliares ---
def _safe_float(value: any, default: float = 0.0) -> float:
    """Converte um valor para float de forma segura, retornando um padrão em caso de erro."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _get_daily_games(data: str, fonte: str = "betfair") -> List[Dict]:
    """Busca e processa os jogos do dia a partir da fonte de dados remota."""
    if fonte not in URL_TEMPLATES:
        console.print(f"[bold red]Fonte '{fonte}' não disponível. Fontes válidas: {', '.join(URL_TEMPLATES.keys())}[/bold red]")
        return []
    
    url = URL_TEMPLATES[fonte].format(data=data)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lança uma exceção para respostas 4xx/5xx
        return csv_string_to_json_list(response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Erro ao buscar dados da fonte '{fonte}' para {data}: {e}[/bold red]")
        return []


def _filter_games(games: List[Dict], fonte: str = "betfair"):
    """Filtra as colunas."""
    if not games:
        console.print("[yellow]Nenhum jogo encontrado para os critérios fornecidos.[/yellow]")
        return []

    if fonte not in COLUNAS_PRINCIPAIS:
        console.print(f"[bold red]Fonte '{fonte}' não configurada para colunas. Usando padrão betfair.[/bold red]")
        fonte = "betfair"

    colunas = COLUNAS_PRINCIPAIS[fonte]
    jogos_filtrados = [{k: d.get(k, '') for k in colunas} for d in games]
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
        "URL_TEMPLATES": URL_TEMPLATES,
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
    fonte: str = typer.Option(
        "betfair",
        help="Fonte dos dados: betfair, footystats ou flashscore.",
    ),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em CSV."),
    odd_home_max: float = typer.Option(None, help="Filtra jogos com odd do time da casa menor ou igual ao valor especificado."),
    odd_home_min: float = typer.Option(None, help="Filtra jogos com odd do time da casa maior ou igual ao valor especificado."),
):
    """Lista todas as partidas do dia."""
    jogos_do_dia = _get_daily_games(data, fonte)
    
    # Filtrar por odd do time da casa se especificado
    # Definir coluna de odd home baseado na fonte
    if fonte == "betfair":
        odd_home_col = "Odd_H_Back"
    else:  # footystats e flashscore
        odd_home_col = "Odd_H_FT"
    
    # Filtrar por odd máxima do time da casa
    if odd_home_max is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia
            if _safe_float(jogo.get(odd_home_col)) <= odd_home_max
        ]
    
    # Filtrar por odd mínima do time da casa
    if odd_home_min is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia
            if _safe_float(jogo.get(odd_home_col)) >= odd_home_min
        ]
    
    jogos_filtrados = _filter_games(jogos_do_dia, fonte)
    if salvar:
        _save_csv_to_file(jogos_filtrados, f"{data}_{fonte}")
    print_table(jogos_filtrados)


@main.command()
def fav(
    oddmax: float = typer.Option(1.5, help="Odd máxima para um time ser considerado favorito."),
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    fonte: str = typer.Option(
        "betfair",
        help="Fonte dos dados: betfair, footystats ou flashscore.",
    ),
    horai: int = typer.Option(0, help="Hora inicial para filtrar os jogos."),
    horaf: int = typer.Option(23, help="Hora final para filtrar os jogos."),
    liga: str = typer.Option(None, help="Filtra jogos por uma liga específica (busca parcial)."),
):
    """Lista jogos com um favorito claro (odd <= oddmax) em um determinado horário e liga."""
    jogos_do_dia = _get_daily_games(data, fonte)
    
    # Definir colunas de odds baseado na fonte
    if fonte == "betfair":
        odd_home_col = "Odd_H_Back"
        odd_away_col = "Odd_A_Back"
    else:  # footystats e flashscore
        odd_home_col = "Odd_H_FT"
        odd_away_col = "Odd_A_FT"

    jogos_filtrados = [
        jogo for jogo in jogos_do_dia
        if (_safe_float(jogo.get(odd_home_col)) <= oddmax or _safe_float(jogo.get(odd_away_col)) <= oddmax)
        and (horai <= int(jogo.get("Time", "0:0").split(":")[0]) <= horaf)
    ]

    if liga:
        jogos_filtrados = [
            jogo for jogo in jogos_filtrados if liga.lower() in jogo.get("League", "").lower()
        ]

    jogos_filtrados = _filter_games(jogos_filtrados, fonte)

    print_table(jogos_filtrados)


@main.command()
def ht0x0(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    fonte: str = typer.Option(
        "betfair",
        help="Fonte dos dados: betfair, footystats ou flashscore.",
    ),
    odd_over: float = typer.Option(2.0, help="Odd mínima para o mercado Over 2.5 FT."),
    odd_btts: float = typer.Option(2.0, help="Odd mínima para o mercado BTTS (Ambos Marcam)."),
    horai: int = typer.Option(0, help="Hora inicial para filtrar os jogos."),
):
    """Busca jogos com potencial de 0x0 no intervalo (HT) baseado em odds altas de Over 2.5 e BTTS."""
    jogos_do_dia = _get_daily_games(data, fonte)

    # Definir colunas baseado na fonte
    if fonte == "betfair":
        odd_over_col = "Odd_Over25_FT_Back"
        odd_btts_col = "Odd_BTTS_Yes_Back"
    else:  # footystats e flashscore
        odd_over_col = "Odd_Over05_HT"  # Over 0.5 HT para footystats/flashscore
        odd_btts_col = "Odd_BTTS_No"    # BTTS No para footystats/flashscore

    jogos_filtrados = [
        jogo for jogo in jogos_do_dia
        if (_safe_float(jogo.get(odd_over_col)) > odd_over and
            _safe_float(jogo.get(odd_btts_col)) > odd_btts)
        and int(jogo.get("Time", "0:0").split(":")[0]) >= horai
    ]
    jogos_filtrados = _filter_games(jogos_filtrados, fonte)
    print_table(jogos_filtrados)


@main.command()
def analise(
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


if __name__ == "__main__":
    main()
