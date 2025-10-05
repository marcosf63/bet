"""Report command - generate consolidated profit reports from diff files."""

from datetime import datetime
from pathlib import Path
import csv
import typer
from rich.console import Console

console = Console()


def report_command(
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
