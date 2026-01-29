"""
Betfair Scraper - Web scraping com Playwright para extrair jogos e odds.
Intercepta requisições de API da Betfair para obter dados estruturados.
"""

import asyncio
from datetime import datetime
from typing import Optional

import pytz
from playwright.async_api import async_playwright


class BetfairScraper:
    """Scraper que intercepta APIs da Betfair para extrair jogos com odds."""

    BASE_URL = "https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today"

    def __init__(self, headless: bool = True, timeout: int = 20000):
        """
        Inicializa o scraper.

        Args:
            headless: Se True, executa navegador em modo headless
            timeout: Timeout em milissegundos para operações
        """
        self.headless = headless
        self.timeout = timeout
        self.api_responses = []
        self.jogos_extraidos = []

    async def handle_response(self, response):
        """Captura respostas de API relevantes."""
        url = response.url

        # Filtrar apenas APIs com dados de eventos/mercados
        if any(kw in url.lower() for kw in ["event", "market", "football", "soccer"]):
            try:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    self.api_responses.append(data)
                    self._extract_games_from_api(data)
            except Exception:
                pass

    def _extract_games_from_api(self, data):
        """Extrai jogos dos dados da API."""
        if isinstance(data, dict) and "eventTypes" in data:
            event_types = data.get("eventTypes", [])

            for event_type in event_types:
                if isinstance(event_type, dict):
                    event_nodes = event_type.get("eventNodes", [])

                    for node in event_nodes:
                        if isinstance(node, dict) and "event" in node:
                            self._parse_betfair_event(node)

    def _parse_betfair_event(self, event_node):
        """Parse evento com odds do marketNodes."""
        try:
            event = event_node.get("event", {})
            market_nodes = event_node.get("marketNodes", [])

            # Capturar eventId do nó
            event_id = event_node.get("eventId")

            jogo = {}

            # Extrair nome do evento: "Time A x Time B"
            event_name = event.get("eventName", "")
            if " x " in event_name:
                times = event_name.split(" x ")
            elif " v " in event_name:
                times = event_name.split(" v ")
            else:
                return

            if len(times) != 2:
                return

            jogo["mandante"] = times[0].strip()
            jogo["visitante"] = times[1].strip()

            # Extrair data/hora e converter para horário de Brasília
            open_date = event.get("openDate")
            if open_date:
                try:
                    # Parse timestamp UTC
                    dt_utc = datetime.fromisoformat(open_date.replace("Z", "+00:00"))

                    # Converter para horário de Brasília (America/Sao_Paulo)
                    tz_brasilia = pytz.timezone("America/Sao_Paulo")
                    dt_brasilia = dt_utc.astimezone(tz_brasilia)

                    jogo["horario"] = dt_brasilia.strftime("%H:%M")
                    jogo["data"] = dt_brasilia.strftime("%Y-%m-%d")
                except Exception:
                    return

            # Competição
            jogo["competicao"] = event.get("countryCode", "N/A")

            # Adicionar eventId e URL da Betfair
            if event_id:
                jogo["event_id"] = event_id
                jogo["betfair_url"] = (
                    f"https://www.betfair.bet.br/exchange/plus/pt/football/event/{event_id}"
                )
            else:
                jogo["event_id"] = None
                jogo["betfair_url"] = None

            # Inicializar odds
            jogo["odd_home_back"] = None
            jogo["odd_draw_back"] = None
            jogo["odd_away_lay"] = None
            jogo["odd_over_25_ft_back"] = None
            jogo["odd_btts_yes_back"] = None
            jogo["odd_over_15_ft_back"] = None

            # Extrair odds dos marketNodes
            for market in market_nodes:
                market_type = market.get("description", {}).get("marketType")

                if market_type == "MATCH_ODDS":
                    runners = market.get("runners", [])

                    for runner in runners:
                        runner_name = runner.get("description", {}).get("runnerName", "").lower()
                        exchange = runner.get("exchange", {})
                        available_back = exchange.get("availableToBack", [])
                        available_lay = exchange.get("availableToLay", [])

                        # Identificar runner por nome
                        if jogo["mandante"].lower() in runner_name:
                            if available_back:
                                jogo["odd_home_back"] = available_back[0].get("price")
                        elif "empate" in runner_name or "draw" in runner_name:
                            if available_back:
                                jogo["odd_draw_back"] = available_back[0].get("price")
                        elif jogo["visitante"].lower() in runner_name:
                            if available_lay:
                                jogo["odd_away_lay"] = available_lay[0].get("price")

                # Over/Under 2.5
                elif market_type == "OVER_UNDER_25":
                    for runner in market.get("runners", []):
                        runner_name = runner.get("description", {}).get("runnerName", "").lower()
                        if "over" in runner_name:
                            available_back = runner.get("exchange", {}).get("availableToBack", [])
                            if available_back:
                                jogo["odd_over_25_ft_back"] = available_back[0].get("price")

                # Over/Under 1.5
                elif market_type == "OVER_UNDER_15":
                    for runner in market.get("runners", []):
                        runner_name = runner.get("description", {}).get("runnerName", "").lower()
                        if "over" in runner_name:
                            available_back = runner.get("exchange", {}).get("availableToBack", [])
                            if available_back:
                                jogo["odd_over_15_ft_back"] = available_back[0].get("price")

                # Both Teams To Score
                elif market_type == "BOTH_TEAMS_TO_SCORE":
                    for runner in market.get("runners", []):
                        runner_name = runner.get("description", {}).get("runnerName", "").lower()
                        if "yes" in runner_name or "sim" in runner_name:
                            available_back = runner.get("exchange", {}).get("availableToBack", [])
                            if available_back:
                                jogo["odd_btts_yes_back"] = available_back[0].get("price")

            # Validar dados mínimos
            if jogo.get("mandante") and jogo.get("visitante") and jogo.get("horario"):
                # Evitar duplicatas
                chave = f"{jogo['horario']}|{jogo['mandante']}|{jogo['visitante']}"
                if not any(
                    f"{j.get('horario')}|{j.get('mandante')}|{j.get('visitante')}" == chave
                    for j in self.jogos_extraidos
                ):
                    self.jogos_extraidos.append(jogo)

        except Exception:
            pass

    async def _extract_event_urls(self, page):
        """
        Extrai as URLs reais dos eventos navegando pela página.

        Estratégia: Para cada jogo extraído via API, busca na página o link correspondente
        clicando no evento e capturando a URL da nova página.

        Args:
            page: Página do Playwright já carregada
        """
        for jogo in self.jogos_extraidos:
            try:
                event_id = jogo.get('event_id')
                if not event_id:
                    continue

                mandante = jogo.get('mandante', '')
                visitante = jogo.get('visitante', '')

                # Procurar por link que contenha ambos os times
                # A página geralmente mostra "Time A x Time B" nos links de eventos
                search_text = f"{mandante} x {visitante}"

                # Tentar localizar o link do evento pelo texto
                try:
                    # Procurar link que contenha o nome do mandante OU visitante
                    # (caso o formato seja diferente)
                    event_link = page.locator(f'a:has-text("{mandante}")').first

                    if await event_link.count() > 0:
                        # Capturar href antes de clicar
                        href = await event_link.get_attribute('href')

                        if href and ('apostas-' in href or str(event_id) in href):
                            # Construir URL completa
                            if href.startswith('/'):
                                full_url = f"https://www.betfair.bet.br{href}"
                            elif href.startswith('http'):
                                full_url = href
                            elif href.startswith('pt/'):
                                # Links relativos precisam do prefixo /exchange/plus/
                                full_url = f"https://www.betfair.bet.br/exchange/plus/{href}"
                            else:
                                full_url = f"https://www.betfair.bet.br/exchange/plus/{href}"

                            # Atualizar URL do jogo
                            jogo['betfair_url'] = full_url

                except Exception:
                    # Se não encontrar pelo texto, manter URL padrão
                    pass

            except Exception:
                pass

    async def scrape(self, url: Optional[str] = None, wait_time: int = 15) -> list[dict]:
        """
        Realiza scraping da página da Betfair.

        Args:
            url: URL para scraping (padrão: página de jogos de hoje)
            wait_time: Tempo de espera em segundos para capturar requisições

        Returns:
            Lista de jogos extraídos
        """
        url = url or self.BASE_URL

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            # Registrar handler para capturar respostas
            page.on("response", lambda response: asyncio.create_task(self.handle_response(response)))

            # Navegar
            await page.goto(url, wait_until="networkidle", timeout=self.timeout)

            # Aceitar cookies
            try:
                cookies_btn = page.locator("#onetrust-accept-btn-handler").first
                if await cookies_btn.is_visible(timeout=3000):
                    await cookies_btn.click()
                    await page.wait_for_timeout(2000)
            except Exception:
                pass

            # Aguardar requisições serem capturadas
            await page.wait_for_timeout(wait_time * 1000)

            # Extrair URLs reais dos eventos
            await self._extract_event_urls(page)

            await browser.close()

        return self.jogos_extraidos

    def scrape_today(self) -> list[dict]:
        """
        Scraping síncrono dos jogos de hoje.

        Returns:
            Lista de jogos no formato CLI
        """
        jogos = asyncio.run(self.scrape())
        return self._map_to_cli_format(jogos)

    def _map_to_cli_format(self, jogos: list[dict]) -> list[dict]:
        """
        Mapeia formato do scraper para formato esperado pela CLI.

        Args:
            jogos: Lista de jogos no formato do scraper

        Returns:
            Lista de jogos no formato CLI
        """
        cli_jogos = []

        for jogo in jogos:
            # Converter odds para string (print_table requer strings)
            def format_odd(value):
                if value is None or value == "":
                    return ""
                return str(value)

            cli_jogo = {
                "Date": jogo.get("data", ""),
                "Time": jogo.get("horario", ""),
                "League": jogo.get("competicao", ""),
                "Home": jogo.get("mandante", ""),
                "Away": jogo.get("visitante", ""),
                "Odd_H_Back": format_odd(jogo.get("odd_home_back")),
                "Odd_D_Back": format_odd(jogo.get("odd_draw_back")),
                "Odd_A_Lay": format_odd(jogo.get("odd_away_lay")),
                "Odd_Over25_FT_Back": format_odd(jogo.get("odd_over_25_ft_back")),
                "Odd_BTTS_Yes_Back": format_odd(jogo.get("odd_btts_yes_back")),
                "Odd_Over15_FT_Back": format_odd(jogo.get("odd_over_15_ft_back")),
                "Event_ID": str(jogo.get("event_id", "")),
                "Betfair_URL": jogo.get("betfair_url", ""),
            }
            cli_jogos.append(cli_jogo)

        return cli_jogos
