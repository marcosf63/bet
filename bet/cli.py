from datetime import date, datetime
from typing import List, Dict
from pathlib import Path
import csv
import requests
import typer
from rich.console import Console
import glob

from bet.files import csv_string_to_json_list
from bet.utils import (
    converter_hora_para_datetime,
    print_table,
    buscar_resultado_partida,
    calcular_lucro_lay,
)
from bet.config import settings
from bet.notification import run_timer, play_sound, send_notification
from bet.services.sofascore.client import get_scheduled_events, get_scheduled_events_demo
from bet.core.constants import URL_TEMPLATES, COLUNAS_PRINCIPAIS

# --- Constantes e Configuração ---
main = typer.Typer(name="Bet CLI", help="CLI para análise de jogos de futebol.")
console = Console()

# Analytics import
try:
    from bet.analytics import TradingAnalyzer
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False


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
    jogos_filtrados = []
    
    for d in games:
        jogo_filtrado = {k: d.get(k, '') for k in colunas}
        
        # Calcular ISC apenas para betfair
        if fonte == "betfair" and "ISC" in colunas:
            odd_a_lay = _safe_float(d.get('Odd_A_Lay', 0))
            odd_h_back = _safe_float(d.get('Odd_H_Back', 0))
            odd_d_back = _safe_float(d.get('Odd_D_Back', 0))
            
            # Calcular ISC (Índice de Supremacia Casa)
            if odd_h_back > 0 and odd_a_lay > 0:
                # PH: Probabilidade implícita do Home ganhar (1/Odd_H_Back)
                ph = 1 / odd_h_back
                
                # PAN: Probabilidade do Away não ganhar (1 - 1/Odd_A_Lay)
                pan = 1 - (1 / odd_a_lay)
                
                # FD: Força diferencial normalizada (Odd_A_Lay/Odd_H_Back)/10
                fd = (odd_a_lay / odd_h_back) / 10
                
                # FDE: Fator de desequilíbrio normalizado (Odd_D_Back/Odd_H_Back)/3
                fde = (odd_d_back / odd_h_back) / 3
                
                # ISC = (PH × 0.35 + PAN × 0.25 + FD × 0.25 + FDE × 0.15) × 100
                isc = (ph * 0.35 + pan * 0.25 + fd * 0.25 + fde * 0.15) * 100
                jogo_filtrado["ISC"] = f"{isc:.1f}"
            else:
                jogo_filtrado["ISC"] = "N/A"
        
        jogos_filtrados.append(jogo_filtrado)
    
    return jogos_filtrados

def _print_isc_legend():
    """Imprime a legenda do ISC (Índice de Supremacia Casa)."""
    console.print("\n[bold cyan]📊 LEGENDA DO ISC (Índice de Supremacia Casa):[/bold cyan]")
    console.print("[bold blue]Fórmula:[/bold blue] ISC = (PH × 0.35 + PAN × 0.25 + FD × 0.25 + FDE × 0.15) × 100")
    console.print("• [bold]PH:[/bold] Probabilidade implícita do Home ganhar (1/Odd_H_Back)")
    console.print("• [bold]PAN:[/bold] Probabilidade do Away não ganhar (1 - 1/Odd_A_Lay)")
    console.print("• [bold]FD:[/bold] Força diferencial normalizada (Odd_A_Lay/Odd_H_Back)/10")
    console.print("• [bold]FDE:[/bold] Fator de desequilíbrio normalizado (Odd_D_Back/Odd_H_Back)/3")
    console.print("\n[bold green]🎯 INTERPRETAÇÃO:[/bold green]")
    console.print("🟢 [bold green]ISC > 75[/bold green] - EXCELENTE - Forte dominância, ideal para Lay Away")
    console.print("🔵 [bold blue]ISC 65-75[/bold blue] - BOM - Boa dominância, considerar Lay Away")
    console.print("🟠 [bold yellow]ISC 55-65[/bold yellow] - MODERADO - Analisar com cautela")
    console.print("🔴 [bold red]ISC < 55[/bold red] - FRACO - Evitar Lay Away")


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


def _save_diff_to_file(data: List[Dict], date_str: str, filtros_aplicados: List[str]):
    """Save diff results to CSV file in the diff folder."""
    if not data:
        console.print("[yellow]No data to save.[/yellow]")
        return

    folder_path = Path("/home/marcos/projetos/bet/data/diff")
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Construir nome do arquivo com filtros aplicados
    nome_arquivo = f"{date_str}_" + "_".join(filtros_aplicados) if filtros_aplicados else date_str
    file_path = folder_path / f"{nome_arquivo}.csv"

    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    console.print(f"[green]Diff file saved to:[/green] {file_path}")


@main.command()
def diff(
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
    isc: str = typer.Option(None, help="Filtra jogos por ISC: excelente (>75), bom (≥65), moderado (≥55), fraco (<55)."),
    liga: str = typer.Option(None, help="Filtra jogos por uma liga específica (busca parcial)."),
    status: str = typer.Option(None, help="Filtra jogos por status (ex: ended, notstarted, inprogress, postponed)."),
):
    """Compara jogos entre MDAY e SOFA e gera arquivo com correspondências incluindo gols."""
    from datetime import datetime
    from bet.soufascore import get_scheduled_events
    
    console.print(f"[bold cyan]🔍 DIFF: Buscando correspondências entre MDAY e SOFA[/bold cyan]")
    
    try:
        # 1. Obter dados do MDAY com filtros aplicados
        jogos_do_dia = _get_daily_games(data, fonte)
        
        # Aplicar filtros de odd_home do mday
        if fonte == "betfair":
            odd_home_col = "Odd_H_Back"
        else:
            odd_home_col = "Odd_H_FT"
            
        if odd_home_max is not None:
            jogos_do_dia = [
                jogo for jogo in jogos_do_dia
                if _safe_float(jogo.get(odd_home_col)) <= odd_home_max
            ]
        
        if odd_home_min is not None:
            jogos_do_dia = [
                jogo for jogo in jogos_do_dia
                if _safe_float(jogo.get(odd_home_col)) >= odd_home_min
            ]
        
        jogos_mday = _filter_games(jogos_do_dia, fonte)
        
        # Aplicar filtro ISC se especificado
        if isc is not None and fonte == "betfair":
            isc_lower = isc.lower()
            jogos_filtrados_isc = []
            
            for jogo in jogos_mday:
                isc_value_str = jogo.get("ISC", "N/A")
                if isc_value_str != "N/A":
                    try:
                        isc_value = float(isc_value_str)
                        if isc_lower == "excelente" and isc_value > 75:
                            jogos_filtrados_isc.append(jogo)
                        elif isc_lower == "bom" and isc_value >= 65:
                            jogos_filtrados_isc.append(jogo)
                        elif isc_lower == "moderado" and isc_value >= 55:
                            jogos_filtrados_isc.append(jogo)
                        elif isc_lower == "fraco" and isc_value < 55:
                            jogos_filtrados_isc.append(jogo)
                    except ValueError:
                        continue
            
            jogos_mday = jogos_filtrados_isc
        
        # 2. Obter dados do SOFA com filtros aplicados
        console.print(f"[cyan]🔍 Buscando jogos agendados para {data}...[/cyan]")
        eventos_sofa = get_scheduled_events(data)
        
        if not eventos_sofa:
            console.print(f"[yellow]Nenhum jogo encontrado no SOFA para {data}[/yellow]")
            return
        
        # Aplicar filtros do sofa
        if liga:
            eventos_sofa = [
                evento for evento in eventos_sofa
                if liga.lower() in evento.tournament.name.lower()
            ]
        
        if status:
            eventos_sofa = [
                evento for evento in eventos_sofa
                if status.lower() in evento.status.type.lower() or 
                   status.lower() in evento.status.description.lower()
            ]
        
        # Converter eventos sofa para formato de comparação
        data_entrada = datetime.strptime(data, "%Y-%m-%d")
        data_entrada_str = data_entrada.strftime("%d/%m")
        
        jogos_sofa = []
        for evento in eventos_sofa:
            dt = datetime.fromtimestamp(evento.startTimestamp)
            data_jogo = dt.strftime("%d/%m")
            
            # Filtrar apenas jogos da data especificada
            if data_jogo != data_entrada_str:
                continue
                
            horario = dt.strftime("%H:%M")
            
            # Extrair gols
            gols_casa = evento.homeScore.current if evento.homeScore else 0
            gols_visitante = evento.awayScore.current if evento.awayScore else 0
            
            jogo_sofa = {
                "Time": horario,
                "Date": data_jogo,
                "League": evento.tournament.name,
                "Home": evento.homeTeam.name,
                "Away": evento.awayTeam.name,
                "Gols_Casa": gols_casa,
                "Gols_Visitante": gols_visitante,
                "Status": evento.status.description,
                "ID": str(evento.id)
            }
            jogos_sofa.append(jogo_sofa)
        
        # 3. Encontrar correspondências usando múltiplas estratégias
        jogos_correspondentes = []
        
        for jogo_mday in jogos_mday:
            melhor_correspondencia = None
            melhor_score = 0
            
            for jogo_sofa in jogos_sofa:
                score = 0
                
                # Estratégia 1: Comparação exata de time, horário
                if (jogo_mday.get("Home", "").lower() == jogo_sofa.get("Home", "").lower() and
                    jogo_mday.get("Away", "").lower() == jogo_sofa.get("Away", "").lower() and
                    jogo_mday.get("Time", "") == jogo_sofa.get("Time", "")):
                    score = 1.0
                
                # Estratégia 2: Comparação de times e liga
                elif (jogo_mday.get("Home", "").lower() == jogo_sofa.get("Home", "").lower() and
                      jogo_mday.get("Away", "").lower() == jogo_sofa.get("Away", "").lower() and
                      jogo_mday.get("League", "").lower() == jogo_sofa.get("League", "").lower()):
                    score = 0.9
                
                # Estratégia 3: Apenas times (mais flexível)
                elif (jogo_mday.get("Home", "").lower() == jogo_sofa.get("Home", "").lower() and
                      jogo_mday.get("Away", "").lower() == jogo_sofa.get("Away", "").lower()):
                    score = 0.8
                
                # Estratégia 4: Similaridade de nomes (usando similaridade básica)
                else:
                    home_similarity = _calculate_similarity(jogo_mday.get("Home", ""), jogo_sofa.get("Home", ""))
                    away_similarity = _calculate_similarity(jogo_mday.get("Away", ""), jogo_sofa.get("Away", ""))
                    score = (home_similarity + away_similarity) / 2
                
                if score > melhor_score and score >= 0.6:  # Limiar mínimo
                    melhor_score = score
                    melhor_correspondencia = jogo_sofa
            
            # Se encontrou correspondência, criar jogo combinado
            if melhor_correspondencia:
                jogo_combinado = jogo_mday.copy()
                gols_casa = melhor_correspondencia["Gols_Casa"]
                gols_visitante = melhor_correspondencia["Gols_Visitante"]
                
                jogo_combinado["Gols Casa"] = str(gols_casa)
                jogo_combinado["Gols Visitante"] = str(gols_visitante)
                jogo_combinado["Status SOFA"] = melhor_correspondencia["Status"]
                
                # Calcular lucros com 1 unidade
                odd_a_lay = _safe_float(jogo_mday.get('Odd_A_Lay', 0))
                odd_h_back = _safe_float(jogo_mday.get('Odd_H_Back', 0))
                
                # Lucro Lay Away
                if odd_a_lay > 1:
                    if gols_casa > gols_visitante or gols_casa == gols_visitante:
                        # Away perdeu ou empatou -> Lay Away ganha
                        lucro_lay_away = 1 / (odd_a_lay - 1)
                        jogo_combinado["Lucro Lay Away"] = f"{lucro_lay_away:.3f}"
                    elif gols_visitante > gols_casa:
                        # Away ganhou -> Lay Away perde
                        jogo_combinado["Lucro Lay Away"] = "-1.000"
                    else:
                        jogo_combinado["Lucro Lay Away"] = "N/A"
                else:
                    jogo_combinado["Lucro Lay Away"] = "N/A"
                
                # Lucro Back Home
                if odd_h_back > 0:
                    if gols_casa > gols_visitante:
                        # Home ganhou -> Back Home ganha
                        lucro_back_home = odd_h_back - 1
                        jogo_combinado["Lucro Back Home"] = f"{lucro_back_home:.3f}"
                    elif gols_visitante > gols_casa or gols_casa == gols_visitante:
                        # Home perdeu ou empatou -> Back Home perde
                        jogo_combinado["Lucro Back Home"] = "-1.000"
                    else:
                        jogo_combinado["Lucro Back Home"] = "N/A"
                else:
                    jogo_combinado["Lucro Back Home"] = "N/A"
                
                jogos_correspondentes.append(jogo_combinado)
        
        # 4. Mostrar resultados
        if jogos_correspondentes:
            console.print(f"\n[bold green]✅ Encontradas {len(jogos_correspondentes)} correspondências:[/bold green]")
            print_table(jogos_correspondentes)
            
            # Calcular estatísticas de lucro
            lucros_lay_away = []
            lucros_back_home = []
            
            for jogo in jogos_correspondentes:
                # Lucro Lay Away
                lucro_lay_str = jogo.get("Lucro Lay Away", "N/A")
                if lucro_lay_str != "N/A":
                    try:
                        lucros_lay_away.append(float(lucro_lay_str))
                    except ValueError:
                        pass
                
                # Lucro Back Home
                lucro_back_str = jogo.get("Lucro Back Home", "N/A")
                if lucro_back_str != "N/A":
                    try:
                        lucros_back_home.append(float(lucro_back_str))
                    except ValueError:
                        pass
            
            console.print(f"\n[bold]📊 ESTATÍSTICAS DE LUCRO:[/bold]")
            
            if lucros_lay_away:
                lucro_total_lay = sum(lucros_lay_away)
                lucro_medio_lay = lucro_total_lay / len(lucros_lay_away)
                
                console.print(f"[bold yellow]🔄 LAY AWAY:[/bold yellow]")
                console.print(f"   • Jogos analisados: [green]{len(lucros_lay_away)}[/green]")
                console.print(f"   • Lucro total: [magenta]{lucro_total_lay:.3f}[/magenta] unidades")
                console.print(f"   • Lucro médio por jogo: [cyan]{lucro_medio_lay:.3f}[/cyan] unidades")
            
            if lucros_back_home:
                lucro_total_back = sum(lucros_back_home)
                lucro_medio_back = lucro_total_back / len(lucros_back_home)
                
                console.print(f"[bold blue]🏠 BACK HOME:[/bold blue]")
                console.print(f"   • Jogos analisados: [green]{len(lucros_back_home)}[/green]")
                console.print(f"   • Lucro total: [magenta]{lucro_total_back:.3f}[/magenta] unidades")
                console.print(f"   • Lucro médio por jogo: [cyan]{lucro_medio_back:.3f}[/cyan] unidades")
            
            # Salvar se solicitado
            if salvar:
                filtros_aplicados = [fonte]
                if odd_home_max is not None:
                    filtros_aplicados.append(f"home-max-{odd_home_max}")
                if odd_home_min is not None:
                    filtros_aplicados.append(f"home-min-{odd_home_min}")
                if isc is not None:
                    filtros_aplicados.append(f"isc-{isc.lower()}")
                if liga is not None:
                    filtros_aplicados.append(f"liga-{liga.lower().replace(' ', '-')}")
                if status is not None:
                    filtros_aplicados.append(f"status-{status.lower()}")
                
                _save_diff_to_file(jogos_correspondentes, data, filtros_aplicados)
        else:
            console.print(f"[yellow]❌ Nenhuma correspondência encontrada entre MDAY e SOFA[/yellow]")
        
        # Mostrar legenda do ISC apenas para fonte betfair
        if fonte == "betfair" and jogos_correspondentes:
            _print_isc_legend()
            
    except Exception as e:
        console.print(f"[bold red]❌ Erro na comparação: {e}[/bold red]")


def _calculate_similarity(str1: str, str2: str) -> float:
    """Calcula similaridade básica entre duas strings."""
    if not str1 or not str2:
        return 0.0
    
    str1, str2 = str1.lower().strip(), str2.lower().strip()
    if str1 == str2:
        return 1.0
    
    # Similaridade baseada em palavras comuns
    words1 = set(str1.split())
    words2 = set(str2.split())
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)


@main.command()
def relatorio(
    pasta: str = typer.Option(
        "/home/marcos/projetos/bet/data/diff",
        help="Pasta contendo os arquivos CSV de diff.",
    ),
    periodo: str = typer.Option(None, help="Filtrar por período (formato: YYYY-MM, ex: 2025-08)."),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o relatório em CSV."),
):
    """Gera relatório consolidado dos lucros dos arquivos na pasta diff."""
    folder_path = Path(pasta)
    
    if not folder_path.exists():
        console.print(f"[bold red]❌ Pasta não encontrada: {pasta}[/bold red]")
        return
    
    # Buscar arquivos CSV na pasta
    csv_files = list(folder_path.glob("*.csv"))
    
    if not csv_files:
        console.print(f"[yellow]❌ Nenhum arquivo CSV encontrado em: {pasta}[/yellow]")
        return
    
    console.print(f"[bold cyan]📊 RELATÓRIO DE LUCROS LAY AWAY[/bold cyan]")
    console.print(f"[dim]Pasta: {pasta}[/dim]")
    
    # Consolidar dados de todos os arquivos
    todos_jogos = []
    arquivos_processados = 0
    
    for csv_file in csv_files:
        # Filtrar por período se especificado
        if periodo:
            # Extrair data do nome do arquivo (formato: YYYY-MM-DD_...)
            nome_arquivo = csv_file.stem
            if not nome_arquivo.startswith(periodo):
                continue
        
        try:
            with csv_file.open("r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                jogos_arquivo = list(reader)
                
                # Adicionar informação do arquivo origem
                for jogo in jogos_arquivo:
                    jogo["Arquivo"] = csv_file.name
                    todos_jogos.append(jogo)
                
                arquivos_processados += 1
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Erro ao processar {csv_file.name}: {e}[/yellow]")
            continue
    
    if not todos_jogos:
        console.print(f"[yellow]❌ Nenhum jogo encontrado nos arquivos{' do período ' + periodo if periodo else ''}[/yellow]")
        return
    
    console.print(f"[green]✅ Processados {arquivos_processados} arquivos, {len(todos_jogos)} jogos encontrados[/green]")
    
    # Calcular estatísticas consolidadas
    lucros_lay_away = []
    lucros_back_home = []
    jogos_com_lucro = []
    jogos_sem_lucro = 0
    
    for jogo in todos_jogos:
        jogo_adicionado = False
        
        # Processar Lucro Lay Away
        lucro_lay_str = jogo.get("Lucro Lay Away", jogo.get("Lucro", "N/A"))  # Backward compatibility
        if lucro_lay_str != "N/A" and lucro_lay_str != "":
            try:
                lucro_lay_value = float(lucro_lay_str)
                lucros_lay_away.append(lucro_lay_value)
                if not jogo_adicionado:
                    jogos_com_lucro.append(jogo)
                    jogo_adicionado = True
            except ValueError:
                pass
        
        # Processar Lucro Back Home
        lucro_back_str = jogo.get("Lucro Back Home", "N/A")
        if lucro_back_str != "N/A" and lucro_back_str != "":
            try:
                lucro_back_value = float(lucro_back_str)
                lucros_back_home.append(lucro_back_value)
                if not jogo_adicionado:
                    jogos_com_lucro.append(jogo)
                    jogo_adicionado = True
            except ValueError:
                pass
        
        if not jogo_adicionado:
            jogos_sem_lucro += 1
    
    if lucros_lay_away or lucros_back_home:
        console.print(f"\n[bold]📈 RESUMO EXECUTIVO:[/bold]")
        console.print(f"   • Total de jogos processados: [green]{len(jogos_com_lucro)}[/green]")
        
        # Estatísticas LAY AWAY
        if lucros_lay_away:
            lucro_total_lay = sum(lucros_lay_away)
            lucro_medio_lay = lucro_total_lay / len(lucros_lay_away)
            lucros_positivos_lay = [l for l in lucros_lay_away if l > 0]
            lucros_negativos_lay = [l for l in lucros_lay_away if l < 0]
            taxa_acerto_lay = (len(lucros_positivos_lay) / len(lucros_lay_away)) * 100
            
            console.print(f"\n[bold yellow]🔄 LAY AWAY:[/bold yellow]")
            console.print(f"   • Jogos analisados: [green]{len(lucros_lay_away)}[/green]")
            console.print(f"   • Lucro total: [magenta]{lucro_total_lay:.3f}[/magenta] unidades")
            console.print(f"   • Lucro médio por jogo: [cyan]{lucro_medio_lay:.3f}[/cyan] unidades")
            console.print(f"   • Taxa de acerto: [bold cyan]{taxa_acerto_lay:.1f}%[/bold cyan]")
            console.print(f"   • Jogos com lucro: [green]{len(lucros_positivos_lay)}[/green] | Jogos com prejuízo: [red]{len(lucros_negativos_lay)}[/red]")
        
        # Estatísticas BACK HOME
        if lucros_back_home:
            lucro_total_back = sum(lucros_back_home)
            lucro_medio_back = lucro_total_back / len(lucros_back_home)
            lucros_positivos_back = [l for l in lucros_back_home if l > 0]
            lucros_negativos_back = [l for l in lucros_back_home if l < 0]
            taxa_acerto_back = (len(lucros_positivos_back) / len(lucros_back_home)) * 100
            
            console.print(f"\n[bold blue]🏠 BACK HOME:[/bold blue]")
            console.print(f"   • Jogos analisados: [green]{len(lucros_back_home)}[/green]")
            console.print(f"   • Lucro total: [magenta]{lucro_total_back:.3f}[/magenta] unidades")
            console.print(f"   • Lucro médio por jogo: [cyan]{lucro_medio_back:.3f}[/cyan] unidades")
            console.print(f"   • Taxa de acerto: [bold cyan]{taxa_acerto_back:.1f}%[/bold cyan]")
            console.print(f"   • Jogos com lucro: [green]{len(lucros_positivos_back)}[/green] | Jogos com prejuízo: [red]{len(lucros_negativos_back)}[/red]")
        
        # Comparação entre estratégias
        if lucros_lay_away and lucros_back_home:
            console.print(f"\n[bold]⚖️ COMPARAÇÃO DE ESTRATÉGIAS:[/bold]")
            melhor_estrategia = "LAY AWAY" if lucro_total_lay > lucro_total_back else "BACK HOME"
            diferenca = abs(lucro_total_lay - lucro_total_back)
            console.print(f"   • Melhor estratégia: [bold green]{melhor_estrategia}[/bold green]")
            console.print(f"   • Diferença de lucro: [yellow]{diferenca:.3f}[/yellow] unidades")
        
        console.print(f"\n[bold]📁 DETALHAMENTO POR ARQUIVO:[/bold]")
        
        # Agrupar por arquivo
        dados_por_arquivo = {}
        for jogo in jogos_com_lucro:
            arquivo = jogo["Arquivo"]
            if arquivo not in dados_por_arquivo:
                dados_por_arquivo[arquivo] = {"lay_away": [], "back_home": []}
            
            # Lucro Lay Away
            lucro_lay_str = jogo.get("Lucro Lay Away", jogo.get("Lucro", "N/A"))
            if lucro_lay_str != "N/A":
                try:
                    dados_por_arquivo[arquivo]["lay_away"].append(float(lucro_lay_str))
                except ValueError:
                    pass
            
            # Lucro Back Home
            lucro_back_str = jogo.get("Lucro Back Home", "N/A")
            if lucro_back_str != "N/A":
                try:
                    dados_por_arquivo[arquivo]["back_home"].append(float(lucro_back_str))
                except ValueError:
                    pass
        
        for arquivo, dados in dados_por_arquivo.items():
            console.print(f"   • [dim]{arquivo}[/dim]:")
            
            if dados["lay_away"]:
                lucro_lay = sum(dados["lay_away"])
                media_lay = lucro_lay / len(dados["lay_away"])
                console.print(f"     🔄 Lay Away: {len(dados['lay_away'])} jogos, {lucro_lay:.3f} total, {media_lay:.3f} média")
            
            if dados["back_home"]:
                lucro_back = sum(dados["back_home"])
                media_back = lucro_back / len(dados["back_home"])
                console.print(f"     🏠 Back Home: {len(dados['back_home'])} jogos, {lucro_back:.3f} total, {media_back:.3f} média")
        
        # Salvar relatório se solicitado
        if salvar:
            relatorio_data = []
            for jogo in jogos_com_lucro:
                relatorio_data.append(jogo)
            
            # Nome do arquivo do relatório
            sufixo = f"_{periodo}" if periodo else ""
            nome_relatorio = f"relatorio_consolidado{sufixo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            relatorio_path = folder_path / nome_relatorio
            
            with relatorio_path.open("w", newline="", encoding="utf-8") as csvfile:
                if relatorio_data:
                    fieldnames = relatorio_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(relatorio_data)
                    
                    console.print(f"\n[green]💾 Relatório salvo em: {relatorio_path}[/green]")
        
        if jogos_sem_lucro > 0:
            console.print(f"\n[dim]ℹ️ {jogos_sem_lucro} jogos ignorados (sem dados de lucro)[/dim]")
            
    else:
        console.print(f"[yellow]❌ Nenhum jogo com dados de lucro válidos encontrado[/yellow]")


@main.command()
def layaway(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    odd_home_max: float = typer.Option(1.70, help="Filtra jogos com odd do time da casa menor ou igual ao valor especificado."),
    odd_home_min: float = typer.Option(1.40, help="Filtra jogos com odd do time da casa maior ou igual ao valor especificado."),
    isc: str = typer.Option("excelente", help="Filtra jogos por ISC: excelente (>75), bom (≥65), moderado (≥55), fraco (<55)."),
    responsabilidade: float = typer.Option(100.0, help="Responsabilidade em unidades para o cálculo do lucro lay."),
    primeiro_tempo: bool = typer.Option(False, "--primeiro-tempo", "-ht", help="Busca resultado do primeiro tempo (HT) ao invés do final."),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em CSV."),
):
    """Calcula profit/loss de estratégia Lay Away verificando resultados via DuckDuckGo."""
    periodo_texto = "primeiro tempo (HT)" if primeiro_tempo else "final (FT)"
    console.print(f"[bold cyan]🔍 LAY AWAY: Buscando jogos e resultados {periodo_texto} para {data}[/bold cyan]")

    # 1. Obter jogos filtrados do mday
    jogos_do_dia = _get_daily_games(data, "betfair")

    # Aplicar filtros de odd
    if odd_home_max is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia
            if _safe_float(jogo.get("Odd_H_Back")) <= odd_home_max
        ]

    if odd_home_min is not None:
        jogos_do_dia = [
            jogo for jogo in jogos_do_dia
            if _safe_float(jogo.get("Odd_H_Back")) >= odd_home_min
        ]

    jogos_filtrados = _filter_games(jogos_do_dia, "betfair")

    # Aplicar filtro ISC
    if isc is not None:
        isc_lower = isc.lower()
        jogos_filtrados_isc = []

        for jogo in jogos_filtrados:
            isc_value_str = jogo.get("ISC", "N/A")
            if isc_value_str != "N/A":
                try:
                    isc_value = float(isc_value_str)
                    if isc_lower == "excelente" and isc_value > 75:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "bom" and isc_value >= 65:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "moderado" and isc_value >= 55:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "fraco" and isc_value < 55:
                        jogos_filtrados_isc.append(jogo)
                except ValueError:
                    continue

        jogos_filtrados = jogos_filtrados_isc

    if not jogos_filtrados:
        console.print("[yellow]Nenhum jogo encontrado com os filtros especificados.[/yellow]")
        return

    console.print(f"[green]✅ Encontrados {len(jogos_filtrados)} jogos com os filtros aplicados[/green]")
    console.print(f"[cyan]🔍 Buscando resultados {periodo_texto} via DuckDuckGo...[/cyan]\n")

    # 2. Buscar resultados e calcular lucros
    jogos_com_resultado = []

    for idx, jogo in enumerate(jogos_filtrados, 1):
        home_team = jogo.get("Home", "")
        away_team = jogo.get("Away", "")

        console.print(f"[dim]{idx}/{len(jogos_filtrados)} - Buscando: {home_team} vs {away_team}...[/dim]")

        # Buscar resultado
        resultado = buscar_resultado_partida(home_team, away_team, data, primeiro_tempo=primeiro_tempo)

        if resultado['encontrado']:
            home_score = resultado['home_score']
            away_score = resultado['away_score']

            # Determinar resultado da partida
            if home_score > away_score:
                resultado_partida = 'home_win'
            elif home_score < away_score:
                resultado_partida = 'away_win'
            else:
                resultado_partida = 'draw'

            # Calcular lucro lay ao visitante
            odd_a_lay = _safe_float(jogo.get('Odd_A_Lay', 0))
            lucro = calcular_lucro_lay(odd_a_lay, responsabilidade, resultado_partida)

            # Adicionar informações ao jogo
            jogo_com_resultado = jogo.copy()
            periodo_label = "HT" if primeiro_tempo else "FT"
            jogo_com_resultado[f"Gols Casa {periodo_label}"] = str(home_score)
            jogo_com_resultado[f"Gols Visitante {periodo_label}"] = str(away_score)
            jogo_com_resultado["Resultado"] = resultado_partida.replace('_', ' ').title()
            jogo_com_resultado["Lucro Lay"] = f"{lucro:.3f}"

            jogos_com_resultado.append(jogo_com_resultado)

            periodo_emoji = "🕐" if primeiro_tempo else "⏰"
            console.print(f"[green]  ✓ {periodo_emoji} {home_score}-{away_score} | Lucro: {lucro:.3f}[/green]")
        else:
            console.print(f"[yellow]  ⚠ Resultado não encontrado[/yellow]")

    # 3. Exibir tabela com resultados
    if jogos_com_resultado:
        periodo_label = "PRIMEIRO TEMPO (HT)" if primeiro_tempo else "FINAL (FT)"
        console.print(f"\n[bold green]📊 RESULTADOS VERIFICADOS - {periodo_label} ({len(jogos_com_resultado)} jogos):[/bold green]")
        print_table(jogos_com_resultado)

        # 4. Calcular estatísticas
        lucros = [float(jogo["Lucro Lay"]) for jogo in jogos_com_resultado]
        lucro_total = sum(lucros)
        lucro_medio = lucro_total / len(lucros) if lucros else 0
        jogos_positivos = [l for l in lucros if l > 0]
        jogos_negativos = [l for l in lucros if l < 0]
        taxa_acerto = (len(jogos_positivos) / len(lucros) * 100) if lucros else 0

        console.print(f"\n[bold]📈 ESTATÍSTICAS:[/bold]")
        console.print(f"   • Jogos verificados: [green]{len(jogos_com_resultado)}[/green]")
        console.print(f"   • Lucro total: [magenta]{lucro_total:.3f}[/magenta] unidades")
        console.print(f"   • Lucro médio: [cyan]{lucro_medio:.3f}[/cyan] unidades/jogo")
        console.print(f"   • Taxa de acerto: [bold cyan]{taxa_acerto:.1f}%[/bold cyan]")
        console.print(f"   • Jogos com lucro: [green]{len(jogos_positivos)}[/green] | Prejuízo: [red]{len(jogos_negativos)}[/red]")
        console.print(f"   • Responsabilidade por jogo: [yellow]{responsabilidade}[/yellow] unidades")

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
            _save_csv_to_file(jogos_com_resultado, nome_arquivo)

        # Mostrar legenda do ISC
        _print_isc_legend()
    else:
        console.print("[yellow]Nenhum resultado encontrado para os jogos filtrados.[/yellow]")


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
    isc: str = typer.Option(None, help="Filtra jogos por ISC: excelente (>75), bom (≥65), moderado (≥55), fraco (<55)."),
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
    
    # Filtrar por ISC se especificado (apenas para betfair)
    if isc is not None and fonte == "betfair":
        isc_lower = isc.lower()
        jogos_filtrados_isc = []
        
        for jogo in jogos_filtrados:
            isc_value_str = jogo.get("ISC", "N/A")
            if isc_value_str != "N/A":
                try:
                    isc_value = float(isc_value_str)
                    # Aplicar filtro baseado na legenda:
                    # excelente: ISC > 75 (inclui apenas excelente)
                    # bom: ISC >= 65 (inclui bom e excelente)
                    # moderado: ISC >= 55 (inclui moderado, bom e excelente)
                    # fraco: ISC < 55 (inclui apenas fraco)
                    if isc_lower == "excelente" and isc_value > 75:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "bom" and isc_value >= 65:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "moderado" and isc_value >= 55:
                        jogos_filtrados_isc.append(jogo)
                    elif isc_lower == "fraco" and isc_value < 55:
                        jogos_filtrados_isc.append(jogo)
                except ValueError:
                    continue
        
        jogos_filtrados = jogos_filtrados_isc
    
    if salvar:
        # Construir nome do arquivo com filtros aplicados
        sufixos = [fonte]
        
        if odd_home_max is not None:
            sufixos.append(f"home-max-{odd_home_max}")
        if odd_home_min is not None:
            sufixos.append(f"home-min-{odd_home_min}")
        if isc is not None:
            sufixos.append(f"isc-{isc.lower()}")
        
        nome_arquivo = f"{data}_" + "_".join(sufixos)
        _save_csv_to_file(jogos_filtrados, nome_arquivo)
    
    print_table(jogos_filtrados)
    
    # Mostrar legenda do ISC apenas para fonte betfair
    if fonte == "betfair" and jogos_filtrados:
        _print_isc_legend()


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


@main.command()
def sofa(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    liga: str = typer.Option(None, help="Filtra jogos por uma liga específica (busca parcial)."),
    status: str = typer.Option(None, help="Filtra jogos por status (ex: ended, notstarted, inprogress, postponed)."),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em JSON."),
    demo: bool = typer.Option(False, help="Usar dados de demonstração (quando API não funciona)."),
):
    """Busca jogos agendados do SofaScore (comando: sofa)."""
    from datetime import datetime
    import json
    
    if demo:
        console.print(f"[cyan]🔍 Usando dados de demonstração...[/cyan]")
        eventos = get_scheduled_events_demo()
    else:
        console.print(f"[cyan]🔍 Buscando jogos agendados para {data}...[/cyan]")
        eventos = get_scheduled_events(data)
    
    if not eventos:
        console.print(f"[yellow]Nenhum jogo encontrado para {data}[/yellow]")
        return
    
    # Filtrar por liga se especificado
    if liga:
        eventos_filtrados = [
            evento for evento in eventos
            if liga.lower() in evento.tournament.name.lower()
        ]
        if eventos_filtrados:
            eventos = eventos_filtrados
            console.print(f"[green]Filtrado por liga '{liga}': {len(eventos)} jogos[/green]")
        else:
            console.print(f"[yellow]Nenhum jogo encontrado para a liga '{liga}'[/yellow]")
            return
    
    # Filtrar por status se especificado
    if status:
        eventos_filtrados = [
            evento for evento in eventos
            if status.lower() in evento.status.type.lower() or 
               status.lower() in evento.status.description.lower()
        ]
        if eventos_filtrados:
            eventos = eventos_filtrados
            console.print(f"[green]Filtrado por status '{status}': {len(eventos)} jogos[/green]")
        else:
            console.print(f"[yellow]Nenhum jogo encontrado com status '{status}'[/yellow]")
            return
    
    # Ordenar eventos por horário (startTimestamp)
    eventos = sorted(eventos, key=lambda evento: evento.startTimestamp)
    
    # Preparar dados para exibição
    jogos_para_tabela = []
    # Converter data de entrada para formato de comparação
    data_entrada = datetime.strptime(data, "%Y-%m-%d")
    data_entrada_str = data_entrada.strftime("%d/%m")
    
    for evento in eventos:
        # Converter timestamp para horário e data locais
        dt = datetime.fromtimestamp(evento.startTimestamp)
        horario = dt.strftime("%H:%M")
        data_jogo = dt.strftime("%d/%m")
        
        # Filtrar apenas jogos da data especificada
        if data_jogo != data_entrada_str:
            continue
        
        # Extrair país do torneio se disponível
        pais = ""
        if (evento.tournament.category and 
            "country" in evento.tournament.category and 
            evento.tournament.category["country"] and
            "name" in evento.tournament.category["country"]):
            pais = evento.tournament.category["country"]["name"]
        
        # Extrair placares se disponíveis
        placar_casa = evento.homeScore.current if evento.homeScore and evento.homeScore.current is not None else "-"
        placar_visitante = evento.awayScore.current if evento.awayScore and evento.awayScore.current is not None else "-"
        
        # Formar URL da partida
        url_partida = ""
        if evento.slug and evento.customId:
            url_partida = f"https://www.sofascore.com/pt/football/match/{evento.slug}/{evento.customId}#id:{evento.id}"
        
        jogo_info = {
            "Horário": horario,
            "Data": data_jogo,
            "Liga": evento.tournament.name,
            "País": pais,
            "Casa": evento.homeTeam.name,
            "Visitante": evento.awayTeam.name,
            "Gols Casa": str(placar_casa),
            "Gols Visitante": str(placar_visitante),
            "Status": evento.status.description,
            "CustomID": evento.customId or "",
            "Slug": evento.slug or "",
            "URL": url_partida,
            "ID": str(evento.id)
        }
        jogos_para_tabela.append(jogo_info)
    
    # Mostrar tabela
    console.print(f"\n[bold green]📅 Jogos encontrados para {data}: {len(jogos_para_tabela)}[/bold green]")
    print_table(jogos_para_tabela)
    
    # Salvar dados se solicitado
    if salvar:
        from pathlib import Path
        
        # Criar pasta de dados
        data_dir = Path("/home/marcos/projetos/bet/data/sofa")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo incluindo filtros aplicados para melhor identificação
        sufixos = []
        if liga:
            sufixos.append(f"liga-{liga.replace(' ', '-').lower()}")
        if status:
            sufixos.append(f"status-{status.replace(' ', '-').lower()}")
        
        sufixo = "_" + "_".join(sufixos) if sufixos else ""
        arquivo_json = data_dir / f"jogos_agendados_{data}{sufixo}.json"
        
        # Preparar dados para salvar (mesmo formato da tabela exibida)
        dados_para_salvar = {
            "metadata": {
                "data_busca": data,
                "filtro_liga": liga,
                "filtro_status": status,
                "total_jogos": len(jogos_para_tabela),
                "gerado_em": datetime.now().isoformat()
            },
            "jogos": jogos_para_tabela
        }
        
        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados_para_salvar, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]💾 Dados salvos em: {arquivo_json}[/green]")
        console.print(f"[dim]   • {len(jogos_para_tabela)} jogos no formato da tabela[/dim]")
        if sufixos:
            console.print(f"[dim]   • Filtros aplicados: {', '.join(sufixos)}[/dim]")
    
    # Estatísticas rápidas
    ligas_count = {}
    for evento in eventos:
        liga_nome = evento.tournament.name
        ligas_count[liga_nome] = ligas_count.get(liga_nome, 0) + 1
    
    console.print(f"\n[bold yellow]📊 Top 5 Ligas:[/bold yellow]")
    top_ligas = sorted(ligas_count.items(), key=lambda x: x[1], reverse=True)[:5]
    for liga_nome, count in top_ligas:
        console.print(f"  {liga_nome}: {count} jogos")


@main.command()
def api(
    url: str = typer.Argument(..., help="URL da página para descobrir APIs"),
    mostrar_detalhes: bool = typer.Option(False, "--detalhes", "-d", help="Mostra detalhes adicionais das APIs"),
    salvar: bool = typer.Option(False, "--salvar", "-s", help="Salva as APIs encontradas em arquivo JSON"),
):
    """Descobre todas as APIs de uma página web (comando: api)."""
    from bet.utils import obter_apis_sofascore, testar_interceptador_sofascore
    import json
    from urllib.parse import urlparse
    
    console.print(f"[cyan]🔍 Descobrindo APIs da URL: {url}[/cyan]\n")
    
    try:
        # Usar função específica do SofaScore se for uma URL do SofaScore, senão usar genérica
        if "sofascore.com" in url.lower():
            console.print("[dim]🎯 URL do SofaScore detectada, usando interceptador otimizado...[/dim]\n")
            
            if mostrar_detalhes:
                # Usar função detalhada que mostra tabela
                testar_interceptador_sofascore(url)
                return
            else:
                # Usar função simples que retorna só as URLs
                apis = obter_apis_sofascore(url)
        else:
            # Para outros sites, usar função genérica
            console.print("[dim]🌐 Usando interceptador genérico...[/dim]\n")
            apis = obter_apis_sofascore(url)  # Esta função já funciona para qualquer URL
        
        if not apis:
            console.print("[yellow]❌ Nenhuma API encontrada na página[/yellow]")
            return
        
        # Mostrar resultados
        console.print(f"[green]✅ Encontradas {len(apis)} APIs:[/green]\n")
        
        # Agrupar APIs por tipo/domínio para melhor organização
        apis_agrupadas = {}
        for api_url in apis:
            try:
                parsed_url = urlparse(api_url)
                dominio = parsed_url.netloc
                
                if dominio not in apis_agrupadas:
                    apis_agrupadas[dominio] = []
                apis_agrupadas[dominio].append(api_url)
            except:
                # Se não conseguir fazer parse, colocar em "outros"
                if "outros" not in apis_agrupadas:
                    apis_agrupadas["outros"] = []
                apis_agrupadas["outros"].append(api_url)
        
        # Mostrar APIs agrupadas por domínio
        for dominio, urls in apis_agrupadas.items():
            console.print(f"[bold blue]📡 {dominio} ({len(urls)} APIs):[/bold blue]")
            for i, api_url in enumerate(urls, 1):
                # Truncar URLs muito longas para melhor visualização
                url_display = api_url if len(api_url) <= 80 else api_url[:77] + "..."
                console.print(f"   {i:2d}. {url_display}")
            console.print()
        
        # Salvar em arquivo se solicitado
        if salvar:
            parsed_original = urlparse(url)
            nome_arquivo = f"apis_{parsed_original.netloc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            arquivo_path = Path(f"data/apis/{nome_arquivo}")
            arquivo_path.parent.mkdir(parents=True, exist_ok=True)
            
            dados_para_salvar = {
                "url_original": url,
                "timestamp": datetime.now().isoformat(),
                "total_apis": len(apis),
                "apis_por_dominio": apis_agrupadas,
                "todas_apis": apis
            }
            
            with open(arquivo_path, "w", encoding="utf-8") as f:
                json.dump(dados_para_salvar, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]💾 APIs salvas em: {arquivo_path}[/green]")
        
        # Mostrar resumo
        console.print(f"[bold yellow]📊 RESUMO:[/bold yellow]")
        console.print(f"   • Total de APIs: [cyan]{len(apis)}[/cyan]")
        console.print(f"   • Domínios únicos: [green]{len(apis_agrupadas)}[/green]")
        console.print(f"   • URL analisada: [dim]{url}[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Erro ao descobrir APIs: {e}[/red]")


if __name__ == "__main__":
    main()
