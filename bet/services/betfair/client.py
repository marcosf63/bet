import betfairlightweight
from betfairlightweight.filters import market_filter
import time
import logging
import pytz
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from rich import print
from bet.utils import (
    converter_hora_para_datetime,
    verificar_tempo_passado,
    country_codes,
)
from bet.storage import load_json_to_dict, save_dict_to_json

# from bet.services.messaging import send_message
from bet.utils.notifications import start_timer, send_notification
from bet.core.exceptions import NaoExisteMercadoExcecao

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="\033[92m%(asctime)s - %(levelname)s - %(message)s\033[0m",
)


class BetfairCliente:
    def __init__(self, username, password, app_key, certs):
        # Inicializa o cliente Betfair
        self.username = username
        self.password = password
        self.app_key = app_key
        self.certs = certs
        self.trading = betfairlightweight.APIClient(
            username, password, app_key=app_key, certs=certs
        )
        self.session_active = False

        # Configuração do logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def login(self):
        try:
            # Realiza login no Betfair
            self.trading.login()
            self.session_active = True
            logging.info("Login realizado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao tentar fazer login: {e}")
            self.session_active = False

    def logout(self):
        if self.session_active:
            try:
                # Faz logout da sessão atual
                self.trading.logout()
                logging.info("Logout realizado com sucesso.")
            except Exception as e:
                logging.error(f"Erro ao tentar fazer logout: {e}")
        else:
            logging.warning("Não há sessão ativa para realizar logout.")


class BetfairEventos:
    def __init__(self, cliente):
        self.cliente = cliente

    def listar_eventos_futebol(self, in_live=False):
        """
        Lista eventos de futebol. Se 'in_live' for True, retorna apenas eventos ao vivo.
        """
        filtro_evento = market_filter(
            event_type_ids=["1"],  # O ID do esporte "Futebol" é geralmente 1
            in_play_only=in_live,  # Filtrar eventos ao vivo, se solicitado
        )

        try:
            eventos = self.cliente.trading.betting.list_events(filter=filtro_evento)
            if not eventos:
                logging.info("Nenhum evento encontrado.")
                return []
            return eventos
        except Exception as e:
            logging.error(f"Erro ao listar eventos: {e}")
            return []

    def get_match_day(self):
        timezone = pytz.timezone("UTC")  # Define a timezone como UTC
        today = datetime.now(timezone).date()
        start_time = datetime.combine(today, datetime.min.time()).astimezone(timezone)
        end_time = datetime.combine(today, datetime.max.time()).astimezone(timezone)

        event_filter = market_filter(
            event_type_ids=["1"],  # ID 1 para Futebol
            market_start_time={
                "from": start_time.isoformat(),
                "to": end_time.isoformat(),
            },
        )
        # Lista de eventos
        events = self.cliente.trading.betting.list_events(filter=event_filter)
        diferenca_fuso = timedelta(hours=3)
        # Imprimir os detalhes dos eventos
        match_day_list = []
        for event in events:
            data_hora = event.event.open_date - diferenca_fuso
            if " v " not in event.event.name:
                continue
            home_team, away_team = event.event.name.split(" v ")
            match_day_list.append(
                {
                    "evento_id": event.event.id,
                    "data": data_hora.date().strftime("%Y-%m-%d"),
                    "hora": data_hora.time().strftime("%H:%M"),
                    "home_team": home_team,
                    "away_team": away_team,
                }
            )
        match_day_list_ordenada = sorted(match_day_list, key=lambda x: x["hora"])

        return match_day_list_ordenada


class BetfairMercados:
    def __init__(self, cliente):
        self.cliente = cliente

    def extrair_nomes_corredores(self, market_catalogues):
        runner_names = {}
        for market_catalogue in market_catalogues:
            for runner in market_catalogue.runners:
                runner_names[runner.selection_id] = runner.runner_name
        return runner_names

    def verificar_disponibilidade_odd(self, runner, tipo):
        if tipo == "back":
            if (
                runner.ex is not None
                and hasattr(runner.ex, "available_to_back")
                and runner.ex.available_to_back
            ):
                return runner.ex.available_to_back[0].price
            else:
                return "Sem informação de odd para back"
        elif tipo == "lay":
            if (
                runner.ex is not None
                and hasattr(runner.ex, "available_to_lay")
                and runner.ex.available_to_lay
            ):
                return runner.ex.available_to_lay[0].price
            else:
                return "Sem informação de odd para lay"

    def get_odds_event_markets(self, event_id: str, market: str) -> dict:
        event_filter = market_filter(event_ids=[event_id])

        market_catalogues = self.cliente.trading.betting.list_market_catalogue(
            filter=event_filter,
            market_projection=["EVENT", "MARKET_START_TIME", "RUNNER_DESCRIPTION"],
            max_results="1000",
        )
        if market_catalogues == []:
            raise NaoExisteMercadoExcecao("Não há mercados para este evento.")
            # print("Não há mercados para este evento.")

        runner_names = self.extrair_nomes_corredores(market_catalogues)

        market_names_dict = {}
        market_ids_dict = {}
        for market_catalogue in market_catalogues:
            market_names_dict[market_catalogue.market_id] = market_catalogue.market_name
            market_ids_dict[market_catalogue.market_name] = market_catalogue.market_id

        if market not in market_ids_dict.keys():
            raise NaoExisteMercadoExcecao(f"Mercado {market} não existe para o evento")
            # print(f"Mercado {market} não existe para o evento")
        market_id = market_ids_dict[market]
        market_books = self.cliente.trading.betting.list_market_book(
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
                selection_back_lay["back_odds"] = self.verificar_disponibilidade_odd(
                    runner, "back"
                )
                selection_back_lay["lay_odds"] = self.verificar_disponibilidade_odd(
                    runner, "lay"
                )
                market_odds_back_lay["selections"].append(selection_back_lay)
        return market_odds_back_lay

    def processar_mercados_para_jogo(self, dados_jogo, markets_dict):
        dados_jogo_dict = {
            "evento_id": dados_jogo.evento_id,
            "times": f"{dados_jogo.home_team.replace('/', '')} vs {dados_jogo.away_team.replace('/', '')}",
            "mercados": [],
        }
        for mercado in markets_dict.values():
            nao_incluir_dados = True
            try:
                dados_market = self.get_odds_event_markets(
                    dados_jogo.evento_id, mercado
                )
            except NaoExisteMercadoExcecao:
                print(f"Não existe dados para o jogo {dados_jogo.evento_id}")
                nao_incluir_dados = False
                continue
            if nao_incluir_dados:
                dados_jogo_dict["mercados"].append(dados_market)
        return dados_jogo_dict

    def busca_odds_mercado(self):
        eventos = BetfairEventos(self.cliente)
        jogos_do_dia = eventos.get_match_day()  # Busca todos os jogos do dia

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
            print(f"Não existe jogos nos próximos {minutos_para_inicio_jogo} minutos")
            return

        def jogo_ja_processado(dados_dia, evento_id):
            if dados_dia != []:
                evento_ids = [jogo["evento_id"] for jogo in dados_dia["jogos"]]
                return evento_id in evento_ids
            return False

        for jogo in jogos:
            dados_jogo = Partida(**jogo)

            if jogo_ja_processado(
                dados_dia, dados_jogo.evento_id
            ):  # Jogo já foi processado
                print(f"Evento {dados_jogo.evento_id} já foi processado")
                continue

            print(
                f"Processando {dados_jogo.home_team.replace('/', '')} vs {dados_jogo.away_team.replace('/', '')}"
            )
            dados_jogo_dict = self.processar_mercados_para_jogo(
                dados_jogo, markets_dict
            )
            dados_dia["jogos"].append(dados_jogo_dict)
        save_dict_to_json(dados_dia, file_name)


class BetfairMonitor:
    def __init__(self, cliente, eventos):
        self.cliente = cliente
        self.eventos = eventos

    def monitorar_gols_segundo_tempo(self, intervalo=60):
        """
        Monitora os eventos ao vivo para detectar o primeiro gol no segundo tempo.
        O intervalo entre as verificações é configurável (em segundos).
        """
        logging.info(
            "Monitorando eventos ao vivo para detectar gols no segundo tempo..."
        )

        eventos_notificados = []

        # try:
        while self.cliente.session_active:
            eventos_ao_vivo = self.eventos.listar_eventos_futebol(in_live=True)

            for evento in eventos_ao_vivo:
                event_id = evento.event.id
                nome_evento = evento.event.name

                # Obter o status do mercado e placar do evento ao vivo
                scores = self.cliente.trading.in_play_service.get_scores(
                    event_ids=[event_id]
                )

                if scores == []:
                    continue

                score = scores[0]
                score_home = score.score.home.score
                score_away = score.score.away.score
                home_name = score.score.home.name
                away_name = score.score.away.name

                event_time_line = (
                    self.cliente.trading.in_play_service.get_event_timeline(
                        event_id=event_id
                    )
                )
                # Checa se houve golno segunfo tempo para o evento
                for update_detail in event_time_line.update_detail:
                    conditions = []
                    conditions.append(int(score_home) + int(score_away) == 1)
                    conditions.append(update_detail.type == "Goal")
                    conditions.append(update_detail.match_time > 45)
                    conditions.append(update_detail.elapsed_regular_time > 45)
                    if all(conditions):
                        country_code = evento.event.country_code
                        county = (
                            country_codes[country_code]
                            if country_code != None
                            and country_code in country_codes.keys()
                            else "Desconhecido"
                        )
                        notification = f"{home_name} {score_home}"
                        notification += f" x {score_away} {away_name}"
                        notification += f"\n{update_detail.type} {update_detail.match_time} {update_detail.team_name}"
                        notification += f"\nId do evento: {event_id}"
                        notification += f"\n{datetime.now().strftime('%H:%M:%S')}"
                        notification += f"\nLocal: {county}"
                        if event_id not in eventos_notificados:
                            # print("*****************************")
                            # print(f"{notification}")
                            send_notification(notification, "Alerta de Gooool!!!", 60)
                            # play_sound("/home/marcos/Música/senna8s.mp3")
                            # send_message(
                            #     number=settings.group_number,
                            #     url=settings.instance_url,
                            #     text=notification
                            # )
                            start_timer(7, notification, "O Tempo Acabou!!!", 10)
                            logging.info(f"Contando 10 minutos para {nome_evento}")
                            eventos_notificados.append(event_id)
            # Esperar o intervalo definido antes de verificar novamente
            time.sleep(intervalo)
        # except KeyboardInterrupt:
        #     logging.info("Monitoramento interrompido pelo usuário.")
        # except Exception as e:
        #     logging.error(f"Erro durante o monitoramento: {e}")
        # finally:
        #     self.cliente.logout()


class BetfairResulados:
    def __init__(self, cliente: BetfairCliente):
        self.cliente = cliente

    def get_lucros_perdas(
        self, data_inicio: str, data_fim: str
    ) -> List[Dict[str, float]]:
        """
        Obtém os lucros e perdas de apostas liquidadas em um período.

        Args:
            client (APIClient): Cliente autenticado da API Betfair.
            data_inicio (str): Data de início no formato "DD/MM/YYYY".
            data_fim (str): Data de fim no formato "DD/MM/YYYY".

        Returns:
            List[Dict[str, float]]: Lista de dicionários contendo informações de lucros e perdas por mercado.
        """
        # Converter datas para o formato ISO8601 com início e fim do dia
        inicio_iso = datetime.strptime(data_inicio, "%d/%m/%Y").strftime(
            "%Y-%m-%dT00:00:00"
        )
        fim_iso = datetime.strptime(data_fim, "%d/%m/%Y").strftime("%Y-%m-%dT23:59:59")

        resultados = []

        try:
            # Solicita os dados de ordens liquidadas
            response = self.cliente.trading.betting.list_cleared_orders(
                bet_status="SETTLED",
                from_record=0,
                record_count=1000,
                settled_date_range={"from": inicio_iso, "to": fim_iso},
            )

            # Processa os resultados retornados
            if response.orders:
                for order in response.orders:
                    # print(dir(order))
                    # return []
                    resultados.append(
                        {
                            "evento": order.event_id,
                            "mercado": order.market_id,
                            "selecao": order.selection_id,
                            "lado": order.side,
                            "bet_outcome": order.bet_outcome,
                            "bet_id": order.bet_id,
                            "odd": order.price_matched,
                            "lucro_prejuizo": order.profit,
                            "data_liquidacao": order.settled_date.isoformat()
                            if order.settled_date
                            else None,
                        }
                    )
            else:
                print("Nenhuma ordem encontrada no período especificado.")

        except Exception as e:
            print(f"Erro ao buscar lucros e perdas: {e}")

        return resultados


# Exemplo de uso das classes
if __name__ == "__main__":
    from config import settings

    # Inicializa a classe BetfairCliente
    cliente = BetfairCliente(
        username=settings.username,
        password=settings.password,
        app_key=settings.app_key,
        certs=settings.certs_dir,
    )

    # Login
    cliente.login()

    # Inicializa a classe BetfairEventos
    eventos = BetfairEventos(cliente)
    # Inicializa a classe BetfairMonitor
    monitor = BetfairMonitor(cliente, eventos)
    # # Monitorar eventos ao vivo para detectar o primeiro gol no segundo tempo
    monitor.monitorar_gols_segundo_tempo(intervalo=60)

    # # Inicializa a classe BetfairMercados
    # mercados = BetfairMercados(cliente)

    # # Buscar odds do mercado
    # mercados.busca_odds_mercado()
