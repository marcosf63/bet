#!/usr/bin/env python3
"""
Betfair Scraper - Interceptação de API
Captura requisições XHR/Fetch da API da Betfair para extrair dados dos jogos.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import re


class BetfairAPIScraper:
    """Scraper que intercepta chamadas de API da Betfair."""

    def __init__(self):
        self.api_responses = []
        self.jogos_extraidos = []

    async def handle_response(self, response):
        """Captura respostas de API relevantes."""
        url = response.url

        # Filtrar apenas URLs de API relevantes
        if any(keyword in url.lower() for keyword in ['event', 'market', 'football', 'soccer', 'coupon']):
            try:
                # Verificar se é JSON
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    data = await response.json()

                    print(f"📡 API: {url[:80]}...")

                    self.api_responses.append({
                        'url': url,
                        'status': response.status,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })

                    # Tentar extrair jogos diretamente
                    self._extract_games_from_api(data)

            except Exception as e:
                # Ignorar erros de parsing (nem toda resposta é JSON)
                pass

    def _extract_games_from_api(self, data):
        """Tenta extrair jogos dos dados da API."""

        # Estrutura específica da Betfair: eventTypes[].eventNodes[]
        if isinstance(data, dict) and 'eventTypes' in data:
            event_types = data.get('eventTypes', [])

            for event_type in event_types:
                if isinstance(event_type, dict):
                    event_nodes = event_type.get('eventNodes', [])

                    for node in event_nodes:
                        if isinstance(node, dict) and 'event' in node:
                            # Passar node completo para extrair odds dos marketNodes
                            self._parse_betfair_event_with_odds(node)
        else:
            # Fallback: busca recursiva genérica
            self._find_events_recursive(data)

    def _find_events_recursive(self, obj, depth=0):
        """Busca recursiva genérica para outras estruturas de API."""
        if depth > 10:
            return

        if isinstance(obj, dict):
            if 'events' in obj or 'event' in obj:
                events_data = obj.get('events') or obj.get('event')
                if isinstance(events_data, list):
                    for event in events_data:
                        self._parse_event(event)
                elif isinstance(events_data, dict):
                    self._parse_event(events_data)

            for value in obj.values():
                self._find_events_recursive(value, depth + 1)

        elif isinstance(obj, list):
            for item in obj:
                self._find_events_recursive(item, depth + 1)

    def _parse_betfair_event_with_odds(self, event_node):
        """Parse evento completo com odds dos marketNodes."""
        try:
            event = event_node.get('event', {})
            market_nodes = event_node.get('marketNodes', [])

            jogo = {}

            # EventName: "Time A x Time B" ou "Time A v Time B"
            event_name = event.get('eventName', '')

            # Tentar separar times
            if ' x ' in event_name:
                times = event_name.split(' x ')
            elif ' v ' in event_name:
                times = event_name.split(' v ')
            else:
                return  # Formato não reconhecido

            if len(times) == 2:
                jogo['mandante'] = times[0].strip()
                jogo['visitante'] = times[1].strip()

            # OpenDate: ISO format
            open_date = event.get('openDate')
            if open_date:
                try:
                    dt = datetime.fromisoformat(open_date.replace('Z', '+00:00'))
                    jogo['horario'] = dt.strftime('%H:%M')
                    jogo['data'] = dt.strftime('%Y-%m-%d')
                except:
                    pass

            # Competição
            jogo['competicao'] = event.get('countryCode', 'N/A')

            # Inicializar odds como None
            jogo['odd_home_back'] = None
            jogo['odd_draw_back'] = None
            jogo['odd_away_lay'] = None
            jogo['odd_over_25_ft_back'] = None
            jogo['odd_btts_yes_back'] = None
            jogo['odd_over_15_ft_back'] = None

            # Extrair odds do mercado MATCH_ODDS
            for market in market_nodes:
                market_type = market.get('description', {}).get('marketType')

                if market_type == 'MATCH_ODDS':
                    runners = market.get('runners', [])

                    # Identificar runners por ordem (geralmente: Home, Away, Draw)
                    for runner in runners:
                        runner_name = runner.get('description', {}).get('runnerName', '').lower()
                        exchange = runner.get('exchange', {})

                        # Odds disponíveis
                        available_back = exchange.get('availableToBack', [])
                        available_lay = exchange.get('availableToLay', [])

                        # Identificar tipo de runner
                        if jogo['mandante'].lower() in runner_name or runner_name in jogo['mandante'].lower():
                            # Home team
                            if available_back:
                                jogo['odd_home_back'] = available_back[0].get('price')

                        elif 'empate' in runner_name or 'draw' in runner_name:
                            # Draw
                            if available_back:
                                jogo['odd_draw_back'] = available_back[0].get('price')

                        elif jogo['visitante'].lower() in runner_name or runner_name in jogo['visitante'].lower():
                            # Away team
                            if available_lay:
                                jogo['odd_away_lay'] = available_lay[0].get('price')

                # Mercados Over/Under (se disponíveis)
                elif market_type == 'OVER_UNDER_25':
                    for runner in market.get('runners', []):
                        runner_name = runner.get('description', {}).get('runnerName', '').lower()
                        if 'over' in runner_name:
                            available_back = runner.get('exchange', {}).get('availableToBack', [])
                            if available_back:
                                jogo['odd_over_25_ft_back'] = available_back[0].get('price')

                elif market_type == 'OVER_UNDER_15':
                    for runner in market.get('runners', []):
                        runner_name = runner.get('description', {}).get('runnerName', '').lower()
                        if 'over' in runner_name:
                            available_back = runner.get('exchange', {}).get('availableToBack', [])
                            if available_back:
                                jogo['odd_over_15_ft_back'] = available_back[0].get('price')

                elif market_type == 'BOTH_TEAMS_TO_SCORE':
                    for runner in market.get('runners', []):
                        runner_name = runner.get('description', {}).get('runnerName', '').lower()
                        if 'yes' in runner_name or 'sim' in runner_name:
                            available_back = runner.get('exchange', {}).get('availableToBack', [])
                            if available_back:
                                jogo['odd_btts_yes_back'] = available_back[0].get('price')

            # Validar dados mínimos
            if jogo.get('mandante') and jogo.get('visitante') and jogo.get('horario'):
                chave = f"{jogo.get('horario')}|{jogo['mandante']}|{jogo['visitante']}"
                if not any(f"{j.get('horario')}|{j.get('mandante')}|{j.get('visitante')}" == chave
                          for j in self.jogos_extraidos):
                    self.jogos_extraidos.append(jogo)

                    # Log com odds
                    odds_info = f"Back: {jogo['odd_home_back']}, Draw: {jogo['odd_draw_back']}, Lay Away: {jogo['odd_away_lay']}"
                    print(f"  ✓ {jogo.get('horario')} - {jogo['mandante']} x {jogo['visitante']} ({odds_info})")

        except Exception as e:
            pass

    def _parse_betfair_event(self, event):
        """Parse evento no formato específico da Betfair."""
        try:
            jogo = {}

            # EventName: "Time A x Time B" ou "Time A v Time B"
            event_name = event.get('eventName', '')

            # Tentar separar times (x ou v como separador)
            if ' x ' in event_name:
                times = event_name.split(' x ')
            elif ' v ' in event_name:
                times = event_name.split(' v ')
            else:
                return  # Formato não reconhecido

            if len(times) == 2:
                jogo['mandante'] = times[0].strip()
                jogo['visitante'] = times[1].strip()

            # OpenDate: ISO format
            open_date = event.get('openDate')
            if open_date:
                try:
                    dt = datetime.fromisoformat(open_date.replace('Z', '+00:00'))
                    jogo['horario'] = dt.strftime('%H:%M')
                    jogo['data'] = dt.strftime('%Y-%m-%d')
                except:
                    pass

            # Competição (não vem no event, mas podemos adicionar depois)
            jogo['competicao'] = event.get('countryCode', 'N/A')

            # Validar dados mínimos
            if jogo.get('mandante') and jogo.get('visitante') and jogo.get('horario'):
                chave = f"{jogo.get('horario')}|{jogo['mandante']}|{jogo['visitante']}"
                if not any(f"{j.get('horario')}|{j.get('mandante')}|{j.get('visitante')}" == chave
                          for j in self.jogos_extraidos):
                    self.jogos_extraidos.append(jogo)
                    print(f"  ✓ {jogo.get('horario')} - {jogo['mandante']} x {jogo['visitante']}")

        except Exception as e:
            pass

    def _parse_event(self, event):
        """Parse um evento individual."""
        if not isinstance(event, dict):
            return

        try:
            # Tentar extrair informações do evento
            # Estruturas comuns: id, name, teams, startTime, etc.

            jogo = {}

            # Nome do evento (geralmente "Time A vs Time B")
            name = event.get('name') or event.get('eventName') or event.get('marketName')
            if name and ' v ' in name:
                times = name.split(' v ')
                if len(times) == 2:
                    jogo['mandante'] = times[0].strip()
                    jogo['visitante'] = times[1].strip()

            # Horário
            start_time = event.get('startTime') or event.get('openDate') or event.get('marketStartTime')
            if start_time:
                # Converter timestamp ou ISO string para horário
                if isinstance(start_time, (int, float)):
                    dt = datetime.fromtimestamp(start_time / 1000)  # Milliseconds
                    jogo['horario'] = dt.strftime('%H:%M')
                    jogo['data'] = dt.strftime('%Y-%m-%d')
                elif isinstance(start_time, str):
                    # Tentar parsear ISO format
                    try:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        jogo['horario'] = dt.strftime('%H:%M')
                        jogo['data'] = dt.strftime('%Y-%m-%d')
                    except:
                        pass

            # Competição
            competition = event.get('competition') or event.get('competitionName') or event.get('eventType')
            if competition:
                if isinstance(competition, dict):
                    jogo['competicao'] = competition.get('name', 'N/A')
                else:
                    jogo['competicao'] = str(competition)

            # Validar que temos dados mínimos
            if jogo.get('mandante') and jogo.get('visitante') and jogo.get('horario'):
                # Evitar duplicatas
                chave = f"{jogo.get('horario')}|{jogo['mandante']}|{jogo['visitante']}"
                if not any(f"{j.get('horario')}|{j.get('mandante')}|{j.get('visitante')}" == chave
                          for j in self.jogos_extraidos):
                    self.jogos_extraidos.append(jogo)
                    print(f"  ✓ Jogo: {jogo.get('horario')} - {jogo['mandante']} x {jogo['visitante']}")

        except Exception as e:
            # Ignorar erros de parsing
            pass

    async def scrape(self, url):
        """Executa o scraping interceptando APIs."""

        async with async_playwright() as p:
            print("🚀 Iniciando navegador com interceptação de API...")

            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # Registrar handler de respostas
            page.on('response', self.handle_response)

            print(f"🌐 Navegando para: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Aceitar cookies
            try:
                print("🍪 Aceitando cookies...")
                cookies_btn = page.locator('#onetrust-accept-btn-handler').first
                await cookies_btn.click(timeout=3000)
                await asyncio.sleep(2)
                print("✓ Cookies aceitos")
            except:
                print("ℹ️  Popup de cookies não encontrado")

            # Aguardar mais requisições
            print("⏳ Aguardando carregamento completo da API...")
            await asyncio.sleep(5)

            # Scroll para carregar mais conteúdo lazy-loaded
            print("📜 Scroll para carregar conteúdo adicional...")
            for _ in range(3):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(1)

            await asyncio.sleep(2)

            await browser.close()

        return self.jogos_extraidos, self.api_responses


async def main():
    """Função principal."""

    print("=" * 100)
    print("🎯 BETFAIR API SCRAPER - INTERCEPTAÇÃO DE REQUISIÇÕES")
    print("=" * 100)
    print()

    url = 'https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today'

    scraper = BetfairAPIScraper()
    jogos, api_responses = await scraper.scrape(url)

    print("\n" + "=" * 100)
    print(f"📊 RESULTADOS")
    print("=" * 100)
    print(f"Total de requisições API capturadas: {len(api_responses)}")
    print(f"Total de jogos extraídos: {len(jogos)}")
    print()

    # Salvar respostas da API para análise
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if api_responses:
        api_file = f"data/betfair_api_responses_{timestamp}.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(api_responses, f, ensure_ascii=False, indent=2)
        print(f"💾 Respostas da API salvas em: {api_file}")

    # Salvar jogos extraídos
    if jogos:
        jogos_file = f"data/betfair_jogos_api_{timestamp}.json"
        with open(jogos_file, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=2)
        print(f"💾 Jogos extraídos salvos em: {jogos_file}")

        # Exibir preview
        print("\n📋 PREVIEW DOS JOGOS:")
        print("-" * 100)
        for i, jogo in enumerate(jogos[:10], 1):
            comp = jogo.get('competicao', 'N/A')
            hora = jogo.get('horario', '??:??')
            print(f"{i:2}. {hora} | {jogo['mandante']:>30} x {jogo['visitante']:<30} | {comp[:20]}")

        if len(jogos) > 10:
            print(f"... e mais {len(jogos) - 10} jogos")
        print("-" * 100)
    else:
        print("\n⚠️  Nenhum jogo extraído via API")
        print("💡 As APIs podem usar estruturas diferentes ou não estar disponíveis")
        print("   Tente o scraper HTML como fallback")


if __name__ == "__main__":
    asyncio.run(main())
