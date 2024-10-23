# from dataclasses import make_dataclass
import datetime
from datetime import datetime, timedelta
from pathlib import Path
import json
import time
from rich import print


from betfairlightweight import APIClient
import pytz
from betfairlightweight.filters import market_filter

from bet.config import settings
from bet.files import load_json_to_dict, save_dict_to_json
from bet.models import Partida
from bet.utils import (
    markets_dict,
    converter_hora_para_datetime,
    verificar_tempo_passado,
    country_codes,
)
from bet.evolution import send_message



def get_trading():
    trading = APIClient(
        settings.username,
        settings.password,
        app_key=settings.app_key,
        certs=settings.certs_dir,
    )
    trading.login()
    return trading


class NaoExisteMercadoExcecao(Exception):
    def __init__(self, mensagem):
        super().__init__(mensagem)


def get_match_day(trading: APIClient):
    timezone = pytz.timezone("UTC")  # Define a timezone como UTC
    today = datetime.now(timezone).date()
    start_time = datetime.combine(today, datetime.min.time()).astimezone(timezone)
    end_time = datetime.combine(today, datetime.max.time()).astimezone(timezone)

    event_filter = market_filter(
        event_type_ids=["1"],  # ID 1 para Futebol
        market_start_time={"from": start_time.isoformat(), "to": end_time.isoformat()},
    )
    # Lista de eventos
    events = trading.betting.list_events(filter=event_filter)
    diferenca_fuso = timedelta(hours=3)
    # Imprimir os detalhes dos eventos
    match_day_list = []
    for event in events:
        data_hora = event.event.open_date - diferenca_fuso
        if not " v " in event.event.name:
            continue
        home_team, away_team = event.event.name.split(" v ")
        match_day_list.append(
            {
                "evento_id": event.event.id,
                "data": data_hora.date().strftime("%Y-%m-%d"),
                "hora": data_hora.time().strftime("%H:%M"),
                # "data_hora": data_hora.strftime('%d-%m-%Y %H:%M'),
                # "evento": event.event.name,
                "home_team": home_team,
                "away_team": away_team,
            }
        )
        # match_day_list.append(event.event.__dict__)
    # Fazer logout
    trading.logout()
    match_day_list_ordenada = sorted(match_day_list, key=lambda x: x["hora"])

    return match_day_list_ordenada


def get_odds_event_markets(event_id: str, market: str, trading: APIClient) -> dict:
    event_filter = market_filter(event_ids=[event_id])

    market_catalogues = trading.betting.list_market_catalogue(
        filter=event_filter,
        market_projection=["EVENT", "MARKET_START_TIME", "RUNNER_DESCRIPTION"],
        max_results="1000",
    )
    if market_catalogues == []:
        raise NaoExisteMercadoExcecao("Não há mercados para este evento.")

    runner_names = {}
    for market_catalogue in market_catalogues:
        for runner in market_catalogue.runners:
            runner_names[runner.selection_id] = runner.runner_name

    market_names_dict = {}
    market_ids_dict = {}
    for market_catalogue in market_catalogues:
        market_names_dict[market_catalogue.market_id] = market_catalogue.market_name
        market_ids_dict[market_catalogue.market_name] = market_catalogue.market_id

    if market not in market_ids_dict.keys():
        raise NaoExisteMercadoExcecao("Mercado não exste para o evento")
    market_id = market_ids_dict[market]
    market_books = trading.betting.list_market_book(
        market_ids=[market_id], price_projection={"priceData": ["EX_BEST_OFFERS"]}
    )
    market_odds_back_lay = {}
    for market_book in market_books:
        market_odds_back_lay["market"] = market_names_dict[market_book.market_id]
        market_odds_back_lay["status"] = market_book.status
        market_odds_back_lay["selections"] = []
        for runner in market_book.runners:
            selection_back_lay = {}
            selection_back_lay["name"] = runner_names[runner.selection_id]
            if (
                runner.ex is not None
                and hasattr(runner.ex, "available_to_back")
                and runner.ex.available_to_back
            ):
                # if runner.ex.available_to_back:
                # if selection_back_lay["name"] == "2 - 2":
                # print([r.price for r in runner.ex.available_to_back])
                selection_back_lay["back_odds"] = runner.ex.available_to_back[0].price
                # Primeiro preço na lista de back
            else:
                selection_back_lay[
                    "back_odds"
                ] = "Sem informação de odd para back"  # Primeiro preço na lista de back

            if (
                runner.ex is not None
                and hasattr(runner.ex, "available_to_lay")
                and runner.ex.available_to_lay
            ):
                selection_back_lay["lay_odds"] = runner.ex.available_to_lay[
                    0
                ].price  # Primeiro preço na lista de back
            else:
                selection_back_lay["lay_odds"] = "Sem informação de odd para lay"
            market_odds_back_lay["selections"].append(
                selection_back_lay
            )  # Primeiro preço na lista de back
    return market_odds_back_lay


def busca_odds_mercado(trading: APIClient):
    jogos_do_dia = get_match_day(trading)  # Busca todos os jogos do dia

    jogos = []

    for jogo in jogos_do_dia:
        hora = converter_hora_para_datetime(jogo["hora"])
        minutos_para_inicio_jogo = 4
        if verificar_tempo_passado(hora, minutos_para_inicio_jogo):
            jogos.append(jogo)

    dados_dia = {"jogos": []}
    file_name = f"{settings.data_dir}/jogos/mercados_{jogos_do_dia[0]['data']}.json"

    if Path(file_name).exists():
        dados_dia = load_json_to_dict(file_name)

    if jogos == []:
        print(f"Não existe jogos nos proximos {minutos_para_inicio_jogo} minutos")
        return

    for jogo in jogos:
        dados_jogo = Partida(**jogo)
        if dados_dia != []:
            evento_ids = [jogo["evento_id"] for jogo in dados_dia["jogos"]]

        if dados_jogo.evento_id in evento_ids:  # Jogo já foi processado
            print(f"Evento {dados_jogo.evento_id} já foi processado")
            continue

        print(
            f"Processando {dados_jogo.home_team.replace('/', '')} vs {dados_jogo.away_team.replace('/', '')}"
        )
        dados_jogo_dict = {}
        dados_jogo_dict["evento_id"] = dados_jogo.evento_id
        dados_jogo_dict[
            "times"
        ] = f"{dados_jogo.home_team.replace('/', '')} vs {dados_jogo.away_team.replace('/', '')}"
        dados_jogo_dict["mercados"] = []
        for mercado in markets_dict.values():
            nao_incluir_dados = True
            try:
                dados_market = get_odds_event_markets(dados_jogo.evento_id, mercado)
            except NaoExisteMercadoExcecao:
                print(f"Não existe dados para o jogo{dados_jogo.evento_id}")
                nao_incluir_dados = False
                continue
            # file_path = f"{settings.data_dir}/jogos/{dados_jogo.home_team.replace('/', '')}_{dados_jogo.away_team.replace('/', '')}_{dados_jogo.data}_{dados_jogo.hora}_{dados_jogo.evento_id}.json"
            if nao_incluir_dados:
                dados_jogo_dict["mercados"].append(dados_market)
                # save_dict_to_json(dados_market, file_path)
        dados_dia["jogos"].append(dados_jogo_dict)
    save_dict_to_json(dados_dia, file_name)


def get_1_gol_segundo_tempo(trading: APIClient):
    #trading.login()
    eventos_notificados = []
    print("Monitorando eventos...")
    while True:
        event_exist = False
        event_filter = market_filter(
            event_type_ids=["1"],  # ID 1 para Futebol
            in_play_only=True,
            # market_start_time={"from": start_time.isoformat(), "to": end_time.isoformat()},
        )
        # Lista de eventos
        events = trading.betting.list_events(filter=event_filter)
        event_ids = [event.event.id for event in events]
        scores = trading.in_play_service.get_scores(event_ids=event_ids)
        event_data_1_gol = []
        event_data_1_gol_ids = []
        for score in scores:
            score_home = score.score.home.score
            score_away = score.score.away.score
            if int(score_home) + int(score_away) == 1:
                score_data = {}
                score_data["home_score"] = score.score.home.score
                score_data["away_score"] = score.score.away.score
                score_data["home_name"] = score.score.home.name
                score_data["away_name"] = score.score.away.name
                score_data["event_id"] = score.event_id
                event_data_1_gol_ids.append(score.event_id)
                event_data_1_gol.append(score_data)

        if event_data_1_gol:
            for event_data in event_data_1_gol:
                event_time_line = trading.in_play_service.get_event_timeline(
                    event_id=event_data["event_id"]
                )
                for update_detail in event_time_line.update_detail:
                    if (
                        update_detail.type == "Goal"
                        and update_detail.match_time > 45
                        and update_detail.elapsed_regular_time > 45
                    ):
                        try:
                            market_data = get_odds_event_markets(
                                    str(event_data["event_id"]), 
                                    'Over/Under 1.5 Goals',
                                    trading
                            )
                        except NaoExisteMercadoExcecao:
                            continue

                        odds_lay_U15 = market_data["selections"][0]["lay_odds"]
                        odds_back_U15 = market_data["selections"][0]["back_odds"]

                        country_code = [event.event.country_code for event in events if event.event.id == str(event_data['event_id'])][0]
                        county = country_codes[country_code] if country_code != None and country_code in country_codes.keys() else "Desconhecido"
                        notification = f"{event_data['home_name']} {event_data['home_score']}"
                        notification += f" x {event_data['away_score']} {event_data['away_name']}"
                        notification += f"\n{update_detail.type} {update_detail.match_time} {update_detail.team_name}"
                        notification += f"\nId do evento: {event_data['event_id']}"
                        notification += f"\n{datetime.now().strftime('%H:%M:%S')}"
                        notification += f"\nLocal: {county}"
                        notification += f"\nOdds: back - {odds_back_U15} / lay - {odds_lay_U15}"
                        if event_data["event_id"] not in eventos_notificados:
                            print("*****************************")
                            print(f"{notification}")
                            send_message(
                                number=settings.group_number,
                                url=settings.instance_url,
                                text=notification
                            )
                            eventos_notificados.append(event_data['event_id'])
                        event_exist = True


                    else:
                        event_exist = False

        #if not event_exist:
            #print(f"Não há eventos!")
        time.sleep(60)


if __name__ == "__main__":
    # from rich.console import Console

    # console = Console()
    # id = "32955574"
    # market = "Correct Score"
    # console.print(get_odds_event_markets(id, market))
    busca_odds_mercado()
