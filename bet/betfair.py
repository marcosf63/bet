from betfairlightweight.streaming import stream
from config import settings
import requests
import json
import datetime
import betfairlightweight
from betfairlightweight import StreamListener
from betfairlightweight.resources.bettingresources import MarketBook
from betfairlightweight.filters import market_filter
from datetime import datetime, timedelta
import pytz

def get_session_token():
    payload = f"username={settings.username}&password={settings.password}"
    headers = {
        "X-Application": "settings.app_key",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    url = "https://identitysso-cert.betfair.com/api/certlogin"

    resp = requests.post(
        url,
        data=payload,
        cert=("./certs/betfair_app.crt", "./certs/betfair_app.key"),
        headers=headers,
    )

    if resp.status_code == 200:
        session_data = resp.json()
        return session_data["sessionToken"]

    return False


def get_soccer_matchs_today(session_token: str):

    endpoint = "https://api.betfair.com/exchange/betting/rest/v1.0/"

    header = {
        "X-Application": settings.app_key,
        "X-Authentication": session_token,
        "content-type": "application/json",
    }

    json_req = '{"filter": { "eventTypeIds": ["1"],"marketStartTime": {"from": "2023-07-20T00:00:00Z","to": "2023-07-20T23:59:00Z"}}}'

    url = endpoint + "listEvents/"

    response = requests.post(url, data=json_req, headers=header)

    list_event_types = json.loads(response.text)
    return list_event_types

def get_market_info_by_event(session_token: str, event_ids: list):
    endpoint = "https://api.betfair.com/exchange/betting/rest/v1.0/"

    header = {
        "X-Application": settings.app_key,
        "X-Authentication": session_token,
        "content-type": "application/json",
    }

    json_req = '{"filter": {"eventIds":' +  str(event_ids).replace("\'", "\"") + '}}'
    print(json_req)
    url = endpoint + "listMarketCatalogue/"

    response = requests.post(url, data=json_req, headers=header)

    list_market_info = json.loads(response.text)
    return list_market_info


def get_initial_odds(data_folder, date):
    """
    Função para buscar as odds iniciais de eventos de futebol em uma determinada data nos dados históricos da Betfair.

    Parâmetros:
    data_folder (str): O diretório onde os arquivos de dados históricos da Betfair estão armazenados.
    date (datetime.date): A data dos eventos de futebol que se está interessado.

    Retorna:
    None. Imprime as odds iniciais de cada seleção em cada mercado de cada evento de futebol na data especificada.

    Exemplo de uso:
    get_initial_odds("/path/to/your/data/folder", datetime.date(2023, 7, 20))
    """
    listener = StreamListener(max_latency=None)

    # Carregar dados do dia especificado
    file_path = f"{data_folder}/{date.strftime('%Y/%m/%d')}.tar"
    stream = trading.streaming.create_historical_generator_stream(
        file_path=file_path,
        listener=listener,
    )

    # Loop por todos os eventos no arquivo de dados
    # for event in listener:
        # Só estamos interessados em eventos de futebol (soccer)
        # if event.event_type == "soccer":
        #     # Loop por todos os mercados no evento
        #     for market in event.market_books:
        #         # Loop por todas as seleções no mercado
        #         for selection in market.runners:
        #             print(f"Evento: {event.event_type} Mercado: {market.market_name} Seleção: {selection.selection_name} Odd inicial: {selection.last_price_traded}")
    # for market_books in stream:
    #     # Só estamos interessados em eventos de futebol (soccer)
    #     if 'soccer' in market_books.event_type:
    #         # Loop por todos os mercados no evento
    #         for market_book in market_books:
    #             # Loop por todas as seleções no mercado
    #             for runner in market_book.runners:
    #                 print(f"Evento: {market_books.event_type} Mercado: {market_book.market_name} Seleção: {runner.selection_id} Odd inicial: {runner.last_price_traded}")

    with stream as gen:
        for market_books in gen():
            # Para cada atualização de livro de mercado
            for market_book in market_books:

                # Certificar-se de que o livro do mercado é para um evento de futebol
                if 'SOCCER' not in market_book.event_type:
                    continue
                
                # Loop por todas as seleções no mercado
                for runner in market_book.runners:
                    print(f"Evento: {market_book.event_type} Mercado: {market_book.market_id} Seleção: {runner.selection_id} Odd inicial: {runner.last_price_traded}")

def get_match_day():
    trading = betfairlightweight.APIClient(settings.username, settings.password, app_key=settings.app_key, certs=settings.certs_dir)
    trading.login()

    timezone = pytz.timezone("UTC")  # Define a timezone como UTC
    today = datetime.now(timezone).date()
    start_time = datetime.combine(today, datetime.min.time()).astimezone(timezone)
    end_time = datetime.combine(today, datetime.max.time()).astimezone(timezone)

    event_filter = market_filter(
        event_type_ids=['1'],  # ID 1 para Futebol
        market_start_time={
            'from': start_time.isoformat(),
            'to': end_time.isoformat()
        }
    )
    # Lista de eventos
    events = trading.betting.list_events(
        filter=event_filter
    )
    diferenca_fuso = timedelta(hours=3)
    # Imprimir os detalhes dos eventos
    match_day_list = []
    for event in events:
        match_day_list.append(
            {
                "Evento:", event.event.name,
                "Data e Hora:",event.event.open_date - diferenca_fuso,
                "EVENT_ID:", event.event.id,
            }

        )
    
    # Fazer logout
    trading.logout()

    return match_day_list 



if __name__ == "__main__":
    import json
    print(json.dumps(get_match_day()))
