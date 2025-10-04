from datetime import datetime, time, timedelta
from rich.console import Console
from rich.table import Table
from typing import List


markets_dict = {
    "MO": "Match Odds",
    "BTTS": "Both teams to Score?",
    "CS": "Correct Score",
    "O25": "Over/Under 2.5 Goals",
    "O15": "Over/Under 1.5 Goals",
    "HT": "Half Time",
    "HTS": "Half Time Score",
}


def calcula_saida_edge_black_lay(
    odd_entrada_back: float, odd_saida_lay: float, stake: float
):
    """
    Calcula o valor efetivo da aposta para uma estratégia de black edge em apostas.

    Esta função calcula o valor efetivo da aposta a ser usado quando se aplica uma estratégia de black edge
    em apostas. Ela determina a aposta ajustada com base nas odds de entrada para apostar (odd_entrada_back),
    nas odds de saída para encerrar a aposta (odd_saida_lay), e no valor inicial apostado.

    Parâmetros:
    odd_entrada_back (float): As odds nas quais a aposta foi feita inicialmente.
    odd_saida_lay (float): As odds nas quais a aposta será encerrada.
    stake (float): O valor inicial de dinheiro apostado.

    Retorna:
    float: O valor calculado da aposta efetiva considerando as odds fornecidas.

    Exemplo:
    >>> calcula_saida_edge_black_lay(2.0, 1.8, 100)
    111.11
    """
    return round((odd_entrada_back / odd_saida_lay) * stake, 2)


def calcula_saida_edge_lay_back(
    odd_entrada_lay: float, odd_saida_back: float, responsabilidade: float
):
    """
    Calcula o lucro de uma estratégia de apostas do tipo edge lay-back.

    Esta função é usada para calcular o lucro resultante de uma estratégia de apostas onde o usuário
    primeiro faz uma aposta lay (contra) e depois faz uma aposta back (a favor) em um evento.
    O cálculo leva em conta as odds da aposta lay e back e a responsabilidade assumida na aposta lay.

    Parâmetros:
    odd_entrada_lay (float): As odds nas quais a aposta lay foi feita.
    odd_saida_back (float): As odds nas quais a aposta back é realizada.
    responsabilidade (float): O valor da responsabilidade assumida na aposta lay.

    Retorna:
    float: O lucro calculado, arredondado para duas casas decimais.

    Exemplo:
    >>> calcula_saida_edge_lay_back(2.0, 1.8, 100)
    22.22
    """
    lucro = responsabilidade / (odd_entrada_lay - 1)
    return round((odd_entrada_lay / odd_saida_back) * lucro, 2)


def calcula_saida_freebet_lay(odd_saida_back: float, responsabilidade: float):
    return round(responsabilidade / (odd_saida_back - 1), 2)


def add_thirty_minutes_to_time_hm_only(current_time: time) -> time:
    """
    Add thirty minutes to the provided time and return a new time object with only hours and minutes.

    Args:
    current_time (time): A time object representing the current time (hours, minutes, seconds).

    Returns:
    time: A new time object representing the time thirty minutes ahead of the provided time, with only hours and minutes.

    This function takes a time object as an argument, adds thirty minutes to the original time, and returns a new time object with only hours and minutes.
    """
    # Convert the time object to a datetime object with today's date
    current_datetime = datetime.combine(datetime.today(), current_time)
    # Add thirty minutes
    new_datetime = current_datetime + timedelta(minutes=30)
    # Extract and return the time part with only hours and minutes
    return new_datetime.time().replace(second=0, microsecond=0)


def is_time_greater_than_now(other_time: time) -> bool:
    """
    Compare the provided time with the current time and return True if the provided time is later.

    Args:
    other_time (time): A time object representing the time to be compared with the current time.

    Returns:
    bool: True if the provided time is later than the current time, False otherwise.

    This function takes a time object as an argument and compares it with the current time. It returns True if the provided time is later, and False otherwise.
    """
    current_time = datetime.now().time()
    return other_time > current_time


def is_time_smaller_than_now_plus30min(other_time: time) -> bool:
    """
    Checks if a given time is before the current time plus 30 minutes.

    Parameters:
    - other_time (time): The time to compare against the current time plus 30 minutes.

    Returns:
    - bool: True if other_time is before the current time plus 30 minutes, False otherwise.
    """
    current_datetime = datetime.now().replace(second=0, microsecond=0)
    future_datetime = current_datetime + timedelta(minutes=30)

    other_datetime = datetime.combine(current_datetime.date(), other_time)
    if other_datetime < current_datetime:
        other_datetime += timedelta(days=1)

    return other_datetime < future_datetime

def converter_hora_para_datetime(hora_str):
    """
    Converte uma string no formato 'HH:MM' para um objeto datetime no dia atual.

    :param hora_str: str - Hora no formato 'HH:MM'
    :return: datetime - Objeto datetime representando a hora no dia atual
    """
    hora_datetime = datetime.strptime(hora_str, "%H:%M")
    agora = datetime.now()
    return agora.replace(
        hour=hora_datetime.hour, minute=hora_datetime.minute, second=0, microsecond=0
    )


def verificar_tempo_passado(hora_passada: datetime, minutos: int) -> bool:
    """
    Verifica se a hora atual é menos de um determinado número de minutos da hora passada como parâmetro.

    :param hora_passada: datetime - Hora passada a ser comparada
    :param minutos: int - Número de minutos para comparação
    :return: bool - True se a hora atual for menos de <minutos> minutos da hora passada, False caso contrário
    """
    hora_atual = datetime.now()
    diferenca_tempo = hora_passada - hora_atual
    return diferenca_tempo > timedelta(minutes=0) and diferenca_tempo < timedelta(
        minutes=minutos
    )


country_codes = {
    "AF": "Afeganistão",
    "AL": "Albânia",
    "DZ": "Argélia",
    "AS": "Samoa Americana",
    "AD": "Andorra",
    "AO": "Angola",
    "AI": "Anguilla",
    "AQ": "Antártida",
    "AG": "Antígua e Barbuda",
    "AR": "Argentina",
    "AM": "Armênia",
    "AW": "Aruba",
    "AU": "Austrália",
    "AT": "Áustria",
    "AZ": "Azerbaijão",
    "BS": "Bahamas",
    "BH": "Bahrein",
    "BD": "Bangladesh",
    "BB": "Barbados",
    "BY": "Bielorrússia",
    "BE": "Bélgica",
    "BZ": "Belize",
    "BJ": "Benin",
    "BM": "Bermudas",
    "BT": "Butão",
    "BO": "Bolívia",
    "BA": "Bósnia e Herzegovina",
    "BW": "Botsuana",
    "BR": "Brasil",
    "BN": "Brunei",
    "BG": "Bulgária",
    "BF": "Burkina Faso",
    "BI": "Burundi",
    "CV": "Cabo Verde",
    "KH": "Camboja",
    "CM": "Camarões",
    "CA": "Canadá",
    "KY": "Ilhas Caimã",
    "CF": "República Centro-Africana",
    "TD": "Chade",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colômbia",
    "KM": "Comores",
    "CG": "Congo",
    "CD": "Congo (República Democrática)",
    "CR": "Costa Rica",
    "CI": "Costa do Marfim",
    "HR": "Croácia",
    "CU": "Cuba",
    "CY": "Chipre",
    "CZ": "República Tcheca",
    "DK": "Dinamarca",
    "DJ": "Djibuti",
    "DM": "Dominica",
    "DO": "República Dominicana",
    "EC": "Equador",
    "EG": "Egito",
    "SV": "El Salvador",
    "GQ": "Guiné Equatorial",
    "ER": "Eritreia",
    "EE": "Estônia",
    "ET": "Etiópia",
    "FJ": "Fiji",
    "FI": "Finlândia",
    "FR": "França",
    "GA": "Gabão",
    "GM": "Gâmbia",
    "GE": "Geórgia",
    "DE": "Alemanha",
    "GH": "Gana",
    "GI": "Gibraltar",
    "GR": "Grécia",
    "GL": "Groenlândia",
    "GD": "Granada",
    "GU": "Guam",
    "GT": "Guatemala",
    "GN": "Guiné",
    "GW": "Guiné-Bissau",
    "GY": "Guiana",
    "HT": "Haiti",
    "HN": "Honduras",
    "HU": "Hungria",
    "IS": "Islândia",
    "IN": "Índia",
    "ID": "Indonésia",
    "IR": "Irã",
    "IQ": "Iraque",
    "IE": "Irlanda",
    "IL": "Israel",
    "IT": "Itália",
    "JM": "Jamaica",
    "JP": "Japão",
    "JO": "Jordânia",
    "KZ": "Cazaquistão",
    "KE": "Quênia",
    "KI": "Quiribati",
    "KP": "Coreia do Norte",
    "KR": "Coreia do Sul",
    "KW": "Kuwait",
    "KG": "Quirguistão",
    "LA": "Laos",
    "LV": "Letônia",
    "LB": "Líbano",
    "LS": "Lesoto",
    "LR": "Libéria",
    "LY": "Líbia",
    "LI": "Liechtenstein",
    "LT": "Lituânia",
    "LU": "Luxemburgo",
    "MG": "Madagáscar",
    "MW": "Malawi",
    "MY": "Malásia",
    "MV": "Maldivas",
    "ML": "Mali",
    "MT": "Malta",
    "MH": "Ilhas Marshall",
    "MR": "Mauritânia",
    "MU": "Maurício",
    "MX": "México",
    "FM": "Micronésia",
    "MD": "Moldávia",
    "MC": "Mônaco",
    "MN": "Mongólia",
    "ME": "Montenegro",
    "MA": "Marrocos",
    "MZ": "Moçambique",
    "MM": "Mianmar",
    "NA": "Namíbia",
    "NR": "Nauru",
    "NP": "Nepal",
    "NL": "Países Baixos",
    "NZ": "Nova Zelândia",
    "NI": "Nicarágua",
    "NE": "Níger",
    "NG": "Nigéria",
    "NO": "Noruega",
    "OM": "Omã",
    "PK": "Paquistão",
    "PW": "Palau",
    "PA": "Panamá",
    "PG": "Papua Nova Guiné",
    "PY": "Paraguai",
    "PE": "Peru",
    "PH": "Filipinas",
    "PL": "Polônia",
    "PT": "Portugal",
    "QA": "Catar",
    "RO": "Romênia",
    "RU": "Rússia",
    "RW": "Ruanda",
    "WS": "Samoa",
    "SM": "San Marino",
    "ST": "São Tomé e Príncipe",
    "SA": "Arábia Saudita",
    "SN": "Senegal",
    "RS": "Sérvia",
    "SC": "Seychelles",
    "SL": "Serra Leoa",
    "SG": "Singapura",
    "SK": "Eslováquia",
    "SI": "Eslovênia",
    "SB": "Ilhas Salomão",
    "SO": "Somália",
    "ZA": "África do Sul",
    "ES": "Espanha",
    "LK": "Sri Lanka",
    "SD": "Sudão",
    "SR": "Suriname",
    "SZ": "Essuatíni",
    "SE": "Suécia",
    "CH": "Suíça",
    "SY": "Síria",
    "TW": "Taiwan",
    "TJ": "Tajiquistão",
    "TZ": "Tanzânia",
    "TH": "Tailândia",
    "TL": "Timor-Leste",
    "TG": "Togo",
    "TO": "Tonga",
    "TT": "Trinidad e Tobago",
    "TN": "Tunísia",
    "TR": "Turquia",
    "TM": "Turcomenistão",
    "TV": "Tuvalu",
    "UG": "Uganda",
    "UA": "Ucrânia",
    "AE": "Emirados Árabes Unidos",
    "GB": "Reino Unido",
    "US": "Estados Unidos",
    "UY": "Uruguai",
    "UZ": "Uzbequistão",
    "VU": "Vanuatu",
    "VA": "Vaticano",
    "VE": "Venezuela",
    "VN": "Vietnã",
    "YE": "Iêmen",
    "ZM": "Zâmbia",
    "ZW": "Zimbábue",
}


def is_time_greater_than_now(time_str: str) -> bool:
    # Converte a string de hora para um objeto datetime.time
    try:
        input_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise ValueError("Formato inválido de hora. Use 'HH:MM'.")

    # Obtém a hora atual
    current_time = datetime.now().time()

    # Compara as horas
    return input_time > current_time


def print_table(lista_dicionarios: List):
    """Imprime uma lista de dicionários no formato de tabela"""
    tabela = Table(show_header=True, header_style="bold magenta")
    console = Console()

    if not lista_dicionarios:
        console.print("[yellow]Nenhum dado para exibir.[/yellow]")
        return

    for chave in lista_dicionarios[0].keys():
        tabela.add_column(chave)
    for linha in lista_dicionarios:
        tabela.add_row(*linha.values())

    console.print(tabela)
    console.print(f"[bold green]Total de jogos = {len(lista_dicionarios)}[/bold green]")


def normalizar_nome_equipe(nome: str) -> str:
    """
    Normaliza nomes de equipes para comparação.
    Remove acentos, espaços extras, e converte para minúsculas.
    """
    import unicodedata
    import re
    
    # Remover acentos
    nome_normalizado = unicodedata.normalize('NFD', nome)
    nome_normalizado = ''.join(char for char in nome_normalizado if unicodedata.category(char) != 'Mn')
    
    # Converter para minúsculas e remover espaços extras
    nome_normalizado = nome_normalizado.lower().strip()
    
    # Remover caracteres especiais e múltiplos espaços
    nome_normalizado = re.sub(r'[^\w\s]', '', nome_normalizado)
    nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado)
    
    return nome_normalizado


def extrair_palavras_chave(nome: str) -> set:
    """
    Extrai palavras-chave significativas de um nome de equipe.
    Remove palavras comuns como "FC", "Club", etc.
    """
    palavras_ignorar = {
        'fc', 'club', 'united', 'city', 'town', 'athletic', 'football', 'cf', 'ac', 
        'sc', 'if', 'bk', 'fk', 'sk', 'nk', 'rsc', 'afc', 'cfc', 'lfc', 'mufc',
        'de', 'del', 'la', 'el', 'da', 'do', 'das', 'dos', 'le', 'les', 'di',
        'cf', 'ca', 'cd', 'ad', 'sd', 'ud', 'real', 'sporting', 'atletico',
        'inter', 'union', 'rovers', 'wanderers', 'rangers', 'hotspur',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
    }
    
    palavras = set(normalizar_nome_equipe(nome).split())
    palavras_significativas = palavras - palavras_ignorar
    
    # Se restaram muito poucas palavras, manter algumas das originais
    if len(palavras_significativas) < 1:
        palavras_significativas = set(list(palavras)[:2])  # Pegar primeiras 2 palavras
    
    return palavras_significativas


def calcular_similaridade(nome1: str, nome2: str) -> float:
    """
    Calcula similaridade entre dois nomes usando múltiplas estratégias.
    Retorna um valor entre 0.0 e 1.0.
    """
    # Estratégia 1: Comparação exata normalizada
    norm1 = normalizar_nome_equipe(nome1)
    norm2 = normalizar_nome_equipe(nome2)
    
    if norm1 == norm2:
        return 1.0
    
    # Estratégia 2: Verificar se um nome está contido no outro
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    # Estratégia 3: Comparação de palavras-chave
    palavras1 = extrair_palavras_chave(nome1)
    palavras2 = extrair_palavras_chave(nome2)
    
    if not palavras1 or not palavras2:
        return 0.0
    
    intersecao = palavras1.intersection(palavras2)
    uniao = palavras1.union(palavras2)
    
    similaridade_palavras = len(intersecao) / len(uniao) if uniao else 0.0
    
    # Estratégia 4: Similaridade de substring
    def lcs_length(s1: str, s2: str) -> int:
        """Calcula o comprimento da maior subsequência comum."""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    lcs_len = lcs_length(norm1, norm2)
    max_len = max(len(norm1), len(norm2))
    similaridade_lcs = lcs_len / max_len if max_len > 0 else 0.0
    
    # Combinar as estratégias
    similaridade_final = max(similaridade_palavras, similaridade_lcs)
    
    return similaridade_final


def encontrar_correspondencias(jogos_mday: List[dict], jogos_sofa: List[dict], limiar_similaridade: float = 0.6) -> dict:
    """
    Encontra correspondências entre jogos dos comandos mday e sofa.
    
    Args:
        jogos_mday: Lista de jogos do comando mday
        jogos_sofa: Lista de jogos do comando sofa  
        limiar_similaridade: Limiar mínimo para considerar uma correspondência
    
    Returns:
        Dict com correspondências encontradas, jogos únicos do mday e únicos do sofa
    """
    correspondencias = []
    indices_sofa_usados = set()
    
    for idx_mday, jogo_mday in enumerate(jogos_mday):
        melhor_correspondencia = None
        melhor_similaridade = 0.0
        melhor_idx_sofa = -1
        
        # Extrair nomes das equipes do mday (podem variar conforme a fonte)
        home_mday = jogo_mday.get('Home', jogo_mday.get('Casa', ''))
        away_mday = jogo_mday.get('Away', jogo_mday.get('Visitante', ''))
        
        for idx_sofa, jogo_sofa in enumerate(jogos_sofa):
            if idx_sofa in indices_sofa_usados:
                continue
                
            # Extrair nomes das equipes do sofa
            home_sofa = jogo_sofa.get('Casa', '')
            away_sofa = jogo_sofa.get('Visitante', '')
            
            # Calcular similaridade para ambas as combinações (direta e inversa)
            sim_direta_home = calcular_similaridade(home_mday, home_sofa)
            sim_direta_away = calcular_similaridade(away_mday, away_sofa)
            
            sim_inversa_home = calcular_similaridade(home_mday, away_sofa)
            sim_inversa_away = calcular_similaridade(away_mday, home_sofa)
            
            # Similaridade média para cada combinação
            sim_direta = (sim_direta_home + sim_direta_away) / 2
            sim_inversa = (sim_inversa_home + sim_inversa_away) / 2
            
            # Usar a melhor das duas
            similaridade_total = max(sim_direta, sim_inversa)
            
            if similaridade_total > melhor_similaridade and similaridade_total >= limiar_similaridade:
                melhor_similaridade = similaridade_total
                melhor_correspondencia = jogo_sofa
                melhor_idx_sofa = idx_sofa
        
        if melhor_correspondencia:
            correspondencias.append({
                'mday': jogo_mday,
                'sofa': melhor_correspondencia,
                'similaridade': melhor_similaridade,
                'index_mday': idx_mday,
                'index_sofa': melhor_idx_sofa
            })
            indices_sofa_usados.add(melhor_idx_sofa)
    
    # Jogos únicos (sem correspondência)
    indices_mday_usados = {corr['index_mday'] for corr in correspondencias}
    jogos_unicos_mday = [
        jogo for idx, jogo in enumerate(jogos_mday) 
        if idx not in indices_mday_usados
    ]
    
    jogos_unicos_sofa = [
        jogo for idx, jogo in enumerate(jogos_sofa)
        if idx not in indices_sofa_usados
    ]
    
    return {
        'correspondencias': correspondencias,
        'unicos_mday': jogos_unicos_mday,
        'unicos_sofa': jogos_unicos_sofa,
        'total_mday': len(jogos_mday),
        'total_sofa': len(jogos_sofa)
    }


def gerar_relatorio_comparacao(resultado_comparacao: dict) -> None:
    """
    Gera um relatório detalhado da comparação entre mday e sofa.
    """
    console = Console()
    
    correspondencias = resultado_comparacao['correspondencias']
    unicos_mday = resultado_comparacao['unicos_mday']
    unicos_sofa = resultado_comparacao['unicos_sofa']
    total_mday = resultado_comparacao['total_mday']
    total_sofa = resultado_comparacao['total_sofa']
    
    console.print("\n[bold cyan]📊 RELATÓRIO DE COMPARAÇÃO MDAY vs SOFA[/bold cyan]\n")
    
    # Estatísticas gerais
    console.print("[bold]📈 Estatísticas Gerais:[/bold]")
    console.print(f"   • Total de jogos MDAY: [cyan]{total_mday}[/cyan]")
    console.print(f"   • Total de jogos SOFA: [cyan]{total_sofa}[/cyan]")
    console.print(f"   • Correspondências encontradas: [green]{len(correspondencias)}[/green]")
    console.print(f"   • Jogos únicos MDAY: [yellow]{len(unicos_mday)}[/yellow]")
    console.print(f"   • Jogos únicos SOFA: [yellow]{len(unicos_sofa)}[/yellow]")
    
    taxa_correspondencia = (len(correspondencias) / max(total_mday, total_sofa)) * 100 if max(total_mday, total_sofa) > 0 else 0
    console.print(f"   • Taxa de correspondência: [magenta]{taxa_correspondencia:.1f}%[/magenta]")
    
    # Correspondências encontradas
    if correspondencias:
        console.print(f"\n[bold green]✅ CORRESPONDÊNCIAS ENCONTRADAS ({len(correspondencias)})[/bold green]")
        
        tabela_corresp = Table(show_header=True, header_style="bold green")
        tabela_corresp.add_column("Similaridade", style="magenta")
        tabela_corresp.add_column("MDAY - Casa", style="cyan")
        tabela_corresp.add_column("MDAY - Visitante", style="cyan")
        tabela_corresp.add_column("SOFA - Casa", style="yellow")
        tabela_corresp.add_column("SOFA - Visitante", style="yellow")
        tabela_corresp.add_column("Liga SOFA", style="dim")
        
        for corr in sorted(correspondencias, key=lambda x: x['similaridade'], reverse=True):
            mday_home = corr['mday'].get('Home', corr['mday'].get('Casa', ''))
            mday_away = corr['mday'].get('Away', corr['mday'].get('Visitante', ''))
            sofa_home = corr['sofa'].get('Casa', '')
            sofa_away = corr['sofa'].get('Visitante', '')
            sofa_liga = corr['sofa'].get('Liga', '')
            
            tabela_corresp.add_row(
                f"{corr['similaridade']:.2f}",
                mday_home,
                mday_away,
                sofa_home,
                sofa_away,
                sofa_liga[:30] + "..." if len(sofa_liga) > 30 else sofa_liga
            )
        
        console.print(tabela_corresp)
    
    # Jogos únicos do MDAY
    if unicos_mday:
        console.print(f"\n[bold yellow]📋 JOGOS ÚNICOS DO MDAY ({len(unicos_mday)})[/bold yellow]")
        console.print("[dim]Jogos presentes no MDAY mas não encontrados no SOFA[/dim]")
        
        tabela_mday = Table(show_header=True, header_style="bold yellow")
        tabela_mday.add_column("Casa", style="cyan")
        tabela_mday.add_column("Visitante", style="cyan")
        tabela_mday.add_column("Horário", style="green")
        tabela_mday.add_column("Liga/Info", style="dim")
        
        for jogo in unicos_mday[:10]:  # Mostrar até 10
            home = jogo.get('Home', jogo.get('Casa', ''))
            away = jogo.get('Away', jogo.get('Visitante', ''))
            horario = jogo.get('Horário', jogo.get('Time', ''))
            liga = jogo.get('Liga', jogo.get('Competition', jogo.get('League', '')))
            
            tabela_mday.add_row(home, away, str(horario), str(liga))
        
        if len(unicos_mday) > 10:
            console.print(f"[dim]... e mais {len(unicos_mday) - 10} jogos[/dim]")
        
        console.print(tabela_mday)
    
    # Jogos únicos do SOFA
    if unicos_sofa:
        console.print(f"\n[bold yellow]📋 JOGOS ÚNICOS DO SOFA ({len(unicos_sofa)})[/bold yellow]")
        console.print("[dim]Jogos presentes no SOFA mas não encontrados no MDAY[/dim]")
        
        tabela_sofa = Table(show_header=True, header_style="bold yellow")
        tabela_sofa.add_column("Casa", style="cyan")
        tabela_sofa.add_column("Visitante", style="cyan")
        tabela_sofa.add_column("Horário", style="green")
        tabela_sofa.add_column("Liga", style="dim")
        
        for jogo in unicos_sofa[:10]:  # Mostrar até 10
            tabela_sofa.add_row(
                jogo.get('Casa', ''),
                jogo.get('Visitante', ''),
                jogo.get('Horário', ''),
                jogo.get('Liga', '')[:40] + "..." if len(jogo.get('Liga', '')) > 40 else jogo.get('Liga', '')
            )
        
        if len(unicos_sofa) > 10:
            console.print(f"[dim]... e mais {len(unicos_sofa) - 10} jogos[/dim]")
        
        console.print(tabela_sofa)


async def interceptar_requisicoes_http(url: str, tempo_espera: int = 10000) -> list:
    """
    Intercepta todas as requisições HTTP para uma URL específica e retorna APIs encontradas.
    
    Args:
        url: URL da página para visitar
        tempo_espera: Tempo em ms para aguardar carregamento das requisições
    
    Returns:
        Lista de URLs de APIs encontradas
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[red]❌ Playwright não disponível. Instale com: pip install playwright[/red]")
        return []
    
    apis_encontradas = []
    
    print(f"[cyan]🔍 Interceptando requisições HTTP para: {url}[/cyan]")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-dev-shm-usage',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Interceptar todas as requisições
        def capture_request(request):
            # Filtrar apenas chamadas de API (geralmente contêm /api/ no caminho)
            if '/api/' in request.url and 'sofascore.com' in request.url:
                print(f"[dim]🔍 API encontrada: {request.method} {request.url}[/dim]")
                apis_encontradas.append({
                    'method': request.method,
                    'url': request.url,
                    'headers': dict(request.headers)
                })
        
        # Interceptar respostas para validar se são APIs válidas
        async def capture_response(response):
            if ('/api/' in response.url and 
                'sofascore.com' in response.url and 
                response.status == 200):
                
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        # Tentar obter o tamanho da resposta
                        try:
                            # Para APIs pequenas, podemos verificar se têm conteúdo
                            response_size = len(str(await response.body()))
                            print(f"[green]✅ API JSON válida: {response.url} ({response_size} bytes)[/green]")
                        except:
                            print(f"[green]✅ API JSON válida: {response.url}[/green]")
                    else:
                        print(f"[yellow]⚠️  API não-JSON: {response.url} (content-type: {content_type})[/yellow]")
                except Exception as e:
                    print(f"[yellow]⚠️  Erro ao processar resposta de {response.url}: {e}[/yellow]")
        
        # Registrar os interceptadores
        page.on("request", capture_request)
        page.on("response", capture_response)
        
        try:
            print(f"[dim]🌐 Navegando para a página...[/dim]")
            await page.goto(url, wait_until="load", timeout=30000)
            
            print(f"[dim]⏱️ Aguardando {tempo_espera/1000}s para capturar todas as requisições...[/dim]")
            await page.wait_for_timeout(tempo_espera)
            
            # Rolar a página para acionar mais requisições
            print("[dim]📜 Rolando página para ativar lazy loading...[/dim]")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # Tentar clicar em abas/botões para ativar mais APIs
            try:
                # Procurar por botões/abas comuns no SofaScore
                buttons_selectors = [
                    '[data-testid="tab"]',
                    'button[class*="tab"]',
                    '[role="tab"]',
                    'a[class*="tab"]'
                ]
                
                for selector in buttons_selectors:
                    elements = await page.query_selector_all(selector)
                    for i, element in enumerate(elements[:3]):  # Máximo 3 cliques
                        try:
                            text = await element.inner_text()
                            print(f"[dim]👆 Clicando em: {text[:20]}...[/dim]")
                            await element.click()
                            await page.wait_for_timeout(1000)
                        except:
                            continue
                        if i >= 2:  # Máximo 3 cliques por seletor
                            break
            except Exception as e:
                print(f"[dim]⚠️  Erro ao clicar em elementos: {e}[/dim]")
            
            print(f"[cyan]📊 Total de APIs encontradas: {len(apis_encontradas)}[/cyan]")
            
        except Exception as e:
            print(f"[red]❌ Erro ao navegar: {e}[/red]")
        
        finally:
            await browser.close()
    
    return apis_encontradas


def testar_interceptador_sofascore(url: str = "https://www.sofascore.com/pt/football/match/fulham-chelsea/NsT#id:14025097") -> None:
    """
    Testa o interceptador de requisições HTTP com uma URL do SofaScore.
    """
    import asyncio
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print(f"[bold cyan]🧪 TESTE: Interceptando APIs do SofaScore[/bold cyan]")
    console.print(f"[dim]URL: {url}[/dim]\n")
    
    # Executar a interceptação
    apis = asyncio.run(interceptar_requisicoes_http(url, tempo_espera=8000))
    
    if not apis:
        console.print("[yellow]❌ Nenhuma API encontrada[/yellow]")
        return
    
    # Criar tabela com as APIs encontradas
    tabela = Table(show_header=True, header_style="bold magenta")
    tabela.add_column("Método", style="cyan")
    tabela.add_column("URL da API", style="green")
    tabela.add_column("Parâmetros", style="dim")
    
    # Agrupar APIs similares e extrair informações úteis
    apis_unicas = {}
    
    for api in apis:
        # Extrair o path da API (sem parâmetros de query)
        url_parts = api['url'].split('?')
        base_url = url_parts[0]
        params = url_parts[1] if len(url_parts) > 1 else ""
        
        # Criar chave única baseada no método e base URL
        key = f"{api['method']}:{base_url}"
        
        if key not in apis_unicas:
            apis_unicas[key] = {
                'method': api['method'],
                'base_url': base_url,
                'params_examples': [params] if params else [],
                'count': 1
            }
        else:
            apis_unicas[key]['count'] += 1
            if params and params not in apis_unicas[key]['params_examples']:
                apis_unicas[key]['params_examples'].append(params)
    
    # Ordenar por frequência (mais chamadas primeiro)
    apis_ordenadas = sorted(apis_unicas.values(), key=lambda x: x['count'], reverse=True)
    
    for api_info in apis_ordenadas:
        # Encurtar URL se muito longa
        base_url = api_info['base_url']
        if len(base_url) > 80:
            base_url = "..." + base_url[-77:]
        
        # Mostrar exemplos de parâmetros (máximo 2)
        params_str = ""
        if api_info['params_examples']:
            params_examples = api_info['params_examples'][:2]
            params_str = "; ".join(params_examples)
            if len(params_str) > 50:
                params_str = params_str[:47] + "..."
        
        # Adicionar contador se foi chamada múltiplas vezes
        method_display = api_info['method']
        if api_info['count'] > 1:
            method_display += f" ({api_info['count']}x)"
        
        tabela.add_row(method_display, base_url, params_str)
    
    console.print(tabela)
    console.print(f"\n[bold]📊 RESUMO:[/bold]")
    console.print(f"   • Total de requisições API: [cyan]{len(apis)}[/cyan]")
    console.print(f"   • APIs únicas: [green]{len(apis_unicas)}[/green]")
    console.print(f"   • Domínio: [yellow]sofascore.com[/yellow]")


def comparar_mday_sofa(data: str = None, fonte_mday: str = "betfair", limiar_similaridade: float = 0.6) -> dict:
    """
    Função principal que compara os resultados dos comandos mday e sofa.
    
    Args:
        data: Data no formato YYYY-MM-DD. Se None, usa data atual
        fonte_mday: Fonte de dados para mday (betfair, footystats, flashscore)
        limiar_similaridade: Limiar mínimo para considerar correspondência
    
    Returns:
        Dict com resultados da comparação
    """
    from bet.cli import _get_daily_games
    from bet.soufascore import get_scheduled_events
    
    if data is None:
        from datetime import date
        data = date.today().strftime("%Y-%m-%d")
    
    console = Console()
    console.print(f"[bold cyan]🔍 Comparando jogos para {data}[/bold cyan]")
    console.print(f"[dim]MDAY fonte: {fonte_mday} | SOFA: SofaScore API[/dim]")
    
    # Buscar dados do MDAY
    console.print("[dim]📥 Buscando dados MDAY...[/dim]")
    jogos_mday = _get_daily_games(data, fonte_mday)
    
    # Buscar dados do SOFA
    console.print("[dim]📥 Buscando dados SOFA...[/dim]")
    eventos_sofa = get_scheduled_events(data)
    
    # Converter eventos SOFA para formato de dict
    jogos_sofa = []
    for evento in eventos_sofa:
        from datetime import datetime
        dt = datetime.fromtimestamp(evento.startTimestamp)
        
        # Extrair país
        pais = ""
        if (evento.tournament.category and 
            "country" in evento.tournament.category and 
            evento.tournament.category["country"] and
            "name" in evento.tournament.category["country"]):
            pais = evento.tournament.category["country"]["name"]
        
        # Formar URL da partida
        url_partida = ""
        if evento.slug and evento.customId:
            url_partida = f"https://www.sofascore.com/pt/football/match/{evento.slug}/{evento.customId}#id:{evento.id}"
        
        jogos_sofa.append({
            "Horário": dt.strftime("%H:%M"),
            "Data": dt.strftime("%d/%m"),
            "Liga": evento.tournament.name,
            "País": pais,
            "Casa": evento.homeTeam.name,
            "Visitante": evento.awayTeam.name,
            "Status": evento.status.description,
            "CustomID": evento.customId or "",
            "Slug": evento.slug or "",
            "URL": url_partida,
            "ID": str(evento.id)
        })
    
    console.print(f"[dim]📊 MDAY: {len(jogos_mday)} jogos | SOFA: {len(jogos_sofa)} jogos[/dim]")
    
    # Fazer comparação
    resultado = encontrar_correspondencias(jogos_mday, jogos_sofa, limiar_similaridade)
    
    # Gerar relatório
    gerar_relatorio_comparacao(resultado)
    
    return resultado


def obter_apis_sofascore(url: str) -> List[str]:
    """
    Função simplificada que retorna apenas uma lista de URLs das APIs SofaScore.

    Args:
        url: URL da página SofaScore para interceptar

    Returns:
        Lista de strings com as URLs das APIs encontradas
    """
    import asyncio

    try:
        apis_completas = asyncio.run(interceptar_requisicoes_http(url, tempo_espera=8000))
        return [api['url'] for api in apis_completas] if apis_completas else []
    except Exception as e:
        print(f"[red]❌ Erro ao obter APIs: {e}[/red]")
        return []


def buscar_resultado_partida(home_team: str, away_team: str, data: str, primeiro_tempo: bool = False) -> dict:
    """
    Busca o resultado de uma partida via DuckDuckGo.

    Args:
        home_team: Nome do time da casa
        away_team: Nome do time visitante
        data: Data da partida no formato YYYY-MM-DD
        primeiro_tempo: Se True, busca apenas resultado do primeiro tempo (HT)

    Returns:
        Dict com: {'home_score': int, 'away_score': int, 'encontrado': bool, 'ht_score': bool}
    """
    try:
        from ddgs import DDGS
        import re

        # Formatar data para busca (dd/mm/yyyy)
        from datetime import datetime
        data_dt = datetime.strptime(data, "%Y-%m-%d")
        data_formatada = data_dt.strftime("%d/%m/%Y")

        # Criar query de busca
        if primeiro_tempo:
            query = f"{home_team} vs {away_team} {data_formatada} resultado intervalo HT primeiro tempo"
        else:
            query = f"{home_team} vs {away_team} {data_formatada} resultado placar"

        # Buscar no DuckDuckGo
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=10))

        if not results:
            return {'home_score': None, 'away_score': None, 'encontrado': False, 'ht_score': primeiro_tempo}

        # Padrões para buscar resultado do primeiro tempo
        if primeiro_tempo:
            # Padrões: "HT: 1-0", "Half Time: 2-1", "Intervalo: 0-0", "(1-0)"
            ht_patterns = [
                r'(?:HT|Half[\s-]?Time|Intervalo|1st Half)[\s:]*(\d{1,2})\s*[-:x×]\s*(\d{1,2})',
                r'\((\d{1,2})\s*[-:x×]\s*(\d{1,2})\)',  # Placar entre parênteses geralmente é HT
                r'(\d{1,2})\s*[-:x×]\s*(\d{1,2})(?=.*(?:intervalo|half|HT))',
            ]

            for result in results:
                text = result.get('body', '') + ' ' + result.get('title', '')

                for pattern in ht_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)

                    for match in matches:
                        home_score = int(match[0])
                        away_score = int(match[1])

                        # Validar placar razoável para primeiro tempo (máximo 10 gols)
                        if home_score <= 10 and away_score <= 10:
                            return {
                                'home_score': home_score,
                                'away_score': away_score,
                                'encontrado': True,
                                'ht_score': True,
                                'fonte': result.get('href', '')
                            }
        else:
            # Buscar placar final (FT)
            # Padrões: "2-1", "2 x 1", "2:1", "FT: 3-2"
            placar_pattern = r'\b(\d{1,2})\s*[-:x×]\s*(\d{1,2})\b'

            for result in results:
                text = result.get('body', '') + ' ' + result.get('title', '')

                # Procurar padrão de placar
                matches = re.findall(placar_pattern, text, re.IGNORECASE)

                for match in matches:
                    home_score = int(match[0])
                    away_score = int(match[1])

                    # Validar que o placar seja razoável (máximo 20 gols por time)
                    if home_score <= 20 and away_score <= 20:
                        return {
                            'home_score': home_score,
                            'away_score': away_score,
                            'encontrado': True,
                            'ht_score': False,
                            'fonte': result.get('href', '')
                        }

        return {'home_score': None, 'away_score': None, 'encontrado': False, 'ht_score': primeiro_tempo}

    except Exception as e:
        print(f"[dim]⚠️ Erro ao buscar resultado: {e}[/dim]")
        return {'home_score': None, 'away_score': None, 'encontrado': False, 'ht_score': primeiro_tempo}


def calcular_lucro_lay(odd_lay: float, responsabilidade: float, resultado: str) -> float:
    """
    Calcula o lucro em uma aposta lay ao visitante.

    Args:
        odd_lay: Odd do lay ao visitante
        responsabilidade: Valor da responsabilidade (unidades)
        resultado: 'home_win', 'draw' ou 'away_win'

    Returns:
        Lucro em unidades (positivo se ganhou, negativo se perdeu)
    """
    if resultado in ['home_win', 'draw']:
        # Lay ganhou (visitante não ganhou)
        lucro = responsabilidade / (odd_lay - 1)
        return round(lucro, 3)
    elif resultado == 'away_win':
        # Lay perdeu (visitante ganhou)
        return -responsabilidade
    else:
        return 0.0


if __name__ == "__main__":
    current_time = datetime.now().time()
    time_thirty_minutes_later = add_thirty_minutes_to_time_hm_only(current_time)
    print(current_time, time_thirty_minutes_later)

    hora = time(11, 00)
    print(is_time_greater_than_now(hora))
    print(is_time_greater_than_now(time_thirty_minutes_later))
