"""Odds command - calculate Under Limite odds table using correction factor formula."""

from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def calcular_odd_minuto(odd_inicial: float, minuto: int) -> float:
    """
    Calcula a odd para um minuto específico usando a fórmula oficial do Excel.

    Fórmula: Odd(t) = Odd_Inicial × [(Odd_Final / Odd_Inicial)^(1/45)]^t

    Simplificando:
        Fator_Decaimento = (Odd_Final / Odd_Inicial)^(1/45)
        Odd(t) = Odd_Inicial × (Fator_Decaimento)^t

    Onde:
    - Odd_Final = 1.0 (valor quando a aposta liquida aos 90 minutos)
    - 1/45 = taxa de decaimento por minuto ao longo de um tempo de jogo
    - t = minuto relativo (0 a 35 para cada tempo)

    Args:
        odd_inicial: Valor da odd no início do tempo (ex: 3.2, 3.9, 4.6)
        minuto: Minuto relativo do tempo (0 a 35)

    Returns:
        Valor calculado da odd para o minuto especificado

    Nota:
        Esta fórmula foi extraída do arquivo Excel oficial "Precificação BLOCOS
        DE TEMPO - CURSO PRIORI.xlsx" e calcula o fator de decaimento
        dinamicamente baseado na odd inicial fornecida.
    """
    # Constantes do modelo
    ODD_FINAL = 1.0  # Valor quando a aposta liquida (aos 90 min do jogo)
    EXPOENTE = 0.02  # Taxa por minuto (valor EXATO do Excel L6 = 0.02, não 1/45!)

    # Calcular fator de decaimento específico para esta odd inicial
    # Fórmula do Excel: N6 = (I5/E10)^L6 onde:
    #   I5 = odd_final (1.0)
    #   E10 = odd_inicial (fornecida)
    #   L6 = 0.02 (IMPORTANTE: não é 1/45 = 0.0222..., é exatamente 0.02)
    fator_decaimento = (ODD_FINAL / odd_inicial) ** EXPOENTE

    # Aplicar decaimento para o minuto específico
    # Fórmula do Excel: E(n) = E10 * (fator_decaimento)^n
    odd_calculada = odd_inicial * (fator_decaimento ** minuto)

    return round(odd_calculada, 2)


def gerar_tabela_odds(odd_inicial: float, tempo: int) -> list[dict]:
    """
    Gera uma lista de dicionários com as odds calculadas para cada minuto.

    Args:
        odd_inicial: Valor da odd inicial
        tempo: 1 para primeiro tempo (0-35min), 2 para segundo tempo (45-80min)

    Returns:
        Lista de dicionários com campos: minuto, tempo_label, odd
    """
    dados_tabela = []

    if tempo == 1:
        # Primeiro tempo: 0min a 35min
        inicio_minuto = 0
        fim_minuto = 35
        offset_calculo = 0  # Cálculo começa em 0
    else:
        # Segundo tempo: 45min a 80min
        inicio_minuto = 45
        fim_minuto = 80
        offset_calculo = 45  # Ajuste para continuar o cálculo de onde parou

    for minuto_jogo in range(inicio_minuto, fim_minuto + 1):
        # Minuto relativo para cálculo (0-45 no primeiro tempo, 0-35 no segundo)
        minuto_calc = minuto_jogo - offset_calculo

        # Calcular odd
        odd_calculada = calcular_odd_minuto(odd_inicial, minuto_calc)

        # Formatar label do tempo
        if minuto_jogo == 0:
            tempo_label = "TEMPO FT"
        else:
            tempo_label = f"{minuto_jogo}min"

        dados_tabela.append({
            "minuto": minuto_jogo,
            "tempo_label": tempo_label,
            "odd": odd_calculada
        })

    return dados_tabela


def exibir_tabela_odds(dados: list[dict], odd_inicial: float, tempo: int):
    """
    Exibe a tabela de odds formatada usando Rich.

    Args:
        dados: Lista de dicionários com os dados calculados
        odd_inicial: Valor da odd inicial (para título)
        tempo: 1 ou 2 (para título)
    """
    # Criar tabela Rich
    tabela = Table(show_header=True, header_style="bold magenta")
    tabela.add_column("TEMPO", style="cyan", justify="center")
    tabela.add_column("ODD", style="white", justify="right")

    # Título da tabela
    tempo_label = "1º TEMPO" if tempo == 1 else "2º TEMPO"
    console.print(f"\n[bold cyan]📊 TABELA DE ODDS - UNDER LIMITE[/bold cyan]")
    console.print(f"[dim]Odd Inicial: {odd_inicial} | {tempo_label}[/dim]\n")

    # Adicionar linha inicial destacada
    primeira_linha = dados[0]
    tabela.add_row(
        f"[bold yellow]{tempo_label}[/bold yellow]",
        f"[bold yellow]{primeira_linha['odd']:.2f}[/bold yellow]"
    )

    # Adicionar demais linhas
    for idx, linha in enumerate(dados):
        minuto = linha["minuto"]
        tempo_label_linha = linha["tempo_label"]
        odd = linha["odd"]

        # Destacar linhas de 5 em 5 minutos (exceto linha 0)
        if minuto > 0 and minuto % 5 == 0:
            tabela.add_row(
                f"[green]{tempo_label_linha}[/green]",
                f"[green]{odd:.2f}[/green]"
            )
        else:
            # Linha normal (pular linha 0 que já foi adicionada)
            if idx > 0:
                tabela.add_row(tempo_label_linha, f"{odd:.2f}")

    console.print(tabela)

    # Legenda
    console.print("\n[bold]🎨 LEGENDA:[/bold]")
    console.print("  [green]🟢 Verde[/green]: Intervalos de 5 minutos")
    console.print("  [yellow]🟡 Amarelo[/yellow]: Linha inicial do tempo")

    # Informações adicionais
    odd_final = dados[-1]["odd"]
    decaimento_total = odd_inicial - odd_final
    percentual_decaimento = (decaimento_total / odd_inicial) * 100

    console.print(f"\n[bold]📉 ANÁLISE:[/bold]")
    console.print(f"  • Odd Inicial: [cyan]{odd_inicial:.2f}[/cyan]")
    console.print(f"  • Odd Final (último minuto): [cyan]{odd_final:.2f}[/cyan]")
    console.print(f"  • Decaimento Total: [yellow]{decaimento_total:.2f}[/yellow] ({percentual_decaimento:.1f}%)")


def salvar_tabela_csv(dados: list[dict], odd_inicial: float, tempo: int):
    """
    Salva a tabela de odds em arquivo CSV.

    Args:
        dados: Lista de dicionários com os dados calculados
        odd_inicial: Valor da odd inicial (para nome do arquivo)
        tempo: 1 ou 2 (para nome do arquivo)
    """
    # Criar diretório se não existir
    diretorio = Path("data/odds")
    diretorio.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo
    data_atual = date.today().strftime("%Y-%m-%d")
    nome_arquivo = f"under_limite_{odd_inicial}_{tempo}t_{data_atual}.csv"
    caminho_arquivo = diretorio / nome_arquivo

    # Escrever CSV
    import csv

    with open(caminho_arquivo, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Minuto", "Tempo_Label", "Odd"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for linha in dados:
            writer.writerow({
                "Minuto": linha["minuto"],
                "Tempo_Label": linha["tempo_label"],
                "Odd": f"{linha['odd']:.2f}"
            })

    console.print(f"\n[green]✅ Tabela salva em: {caminho_arquivo}[/green]")


def odds_command(
    odd_inicial: float = typer.Option(
        ...,
        "--odd-inicial",
        "-o",
        help="Valor da odd inicial (ex: 4.6)"
    ),
    tempo: int = typer.Option(
        ...,
        "--tempo",
        "-t",
        help="Tempo do jogo: 1 (primeiro tempo: 0-35min) ou 2 (segundo tempo: 45-80min)"
    ),
    salvar: bool = typer.Option(
        False,
        "--salvar",
        "-s",
        help="Se verdadeiro, salva o resultado em CSV no diretório data/odds/"
    ),
):
    """
    Calcula e exibe tabela de odds do Under Limite usando a fórmula do Fator de Correção.

    A fórmula utilizada é: Fator de Correção (%) = [1 - (Odd Inicial / Odd Final)^(1/45)] × 100

    Exemplos de uso:

        bet odds --odd-inicial 4.6 --tempo 1

        bet odds -o 3.2 -t 2 --salvar
    """
    # Validações
    if odd_inicial <= 1.0:
        console.print("[bold red]❌ Erro: odd inicial deve ser maior que 1.0[/bold red]")
        raise typer.Exit(code=1)

    if tempo not in [1, 2]:
        console.print("[bold red]❌ Erro: tempo deve ser 1 (primeiro tempo) ou 2 (segundo tempo)[/bold red]")
        raise typer.Exit(code=1)

    # Gerar dados da tabela
    dados_tabela = gerar_tabela_odds(odd_inicial, tempo)

    # Exibir tabela
    exibir_tabela_odds(dados_tabela, odd_inicial, tempo)

    # Salvar se solicitado
    if salvar:
        salvar_tabela_csv(dados_tabela, odd_inicial, tempo)
