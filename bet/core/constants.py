"""Constantes do projeto."""

# URLs de fontes de dados
URL_TEMPLATES = {
    "betfair": "https://raw.githubusercontent.com/futpythontrader/Jogos_do_Dia/refs/heads/main/Betfair/Jogos_do_Dia_Betfair_Back_Lay_{data}.csv",
    "footystats": "https://github.com/futpythontrader/Jogos_do_Dia/raw/refs/heads/main/FootyStats/Jogos_do_Dia_FootyStats_{data}.csv",
    "flashscore": "https://github.com/futpythontrader/Jogos_do_Dia/raw/refs/heads/main/FlashScore/Jogos_do_Dia_FlashScore_{data}.csv",
}

# Colunas principais por fonte de dados
COLUNAS_PRINCIPAIS = {
    "betfair": [
        "Date",
        "Time",
        "League",
        "Home",
        "Away",
        "Odd_H_Back",
        "Odd_D_Back",
        "Odd_A_Lay",
        "Odd_Over25_FT_Back",
        "Odd_BTTS_Yes_Back",
        "Odd_Over15_FT_Back",
        "ISC",
    ],
    "footystats": [
        "Date",
        "Time",
        "League",
        "Home",
        "Away",
        "Odd_H_FT",
        "Odd_D_FT",
        "Odd_A_FT",
        "Odd_Over05_HT",
        "Odd_BTTS_No",
        "XG_Home_Pre",
    ],
    "flashscore": [
        "Date",
        "Time",
        "League",
        "Home",
        "Away",
        "Odd_H_FT",
        "Odd_D_FT",
        "Odd_A_FT",
        "Odd_Over05_HT",
        "Odd_BTTS_No",
        "XG_Home_Pre",
    ],
}

# Fontes de dados disponíveis
AVAILABLE_SOURCES = list(URL_TEMPLATES.keys())

# Configurações padrão
DEFAULT_SOURCE = "betfair"
