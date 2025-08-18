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


if __name__ == "__main__":
    current_time = datetime.now().time()
    time_thirty_minutes_later = add_thirty_minutes_to_time_hm_only(current_time)
    print(current_time, time_thirty_minutes_later)

    hora = time(11, 00)
    print(is_time_greater_than_now(hora))
    print(is_time_greater_than_now(time_thirty_minutes_later))
