"""
Script para investigar mercados adicionais (Over/Under, BTTS) na Betfair.
Navega para uma página de jogo específica e intercepta todas as requisições de API.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

class BetfairMarketsInvestigator:
    def __init__(self):
        self.api_responses = []
        self.all_urls = set()

    async def handle_response(self, response):
        """Captura TODAS as respostas de rede."""
        url = response.url
        self.all_urls.add(url)

        # Capturar respostas que possam conter dados de mercados
        keywords = ['market', 'event', 'football', 'soccer', 'odds', 'coupon', 'bet']

        if any(keyword in url.lower() for keyword in keywords):
            try:
                content_type = response.headers.get('content-type', '')

                if 'json' in content_type:
                    data = await response.json()

                    self.api_responses.append({
                        'url': url,
                        'status': response.status,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })

                    print(f"✓ Capturado: {url[:80]}...")

                    # Analisar marketTypes imediatamente
                    self._analyze_market_types(data, url)

            except Exception as e:
                print(f"  Erro ao processar {url[:60]}: {e}")

    def _analyze_market_types(self, data, url):
        """Analisa e exibe marketTypes encontrados."""
        market_types = set()

        # Buscar em diferentes estruturas possíveis
        if isinstance(data, dict):
            # Estrutura 1: eventTypes[].eventNodes[].marketNodes[]
            if 'eventTypes' in data:
                for et in data['eventTypes']:
                    for node in et.get('eventNodes', []):
                        for market in node.get('marketNodes', []):
                            mt = market.get('description', {}).get('marketType')
                            if mt:
                                market_types.add(mt)

            # Estrutura 2: markets[] diretamente
            if 'markets' in data:
                for market in data['markets']:
                    mt = market.get('marketType') or market.get('description', {}).get('marketType')
                    if mt:
                        market_types.add(mt)

            # Estrutura 3: eventType.marketCatalogue[]
            if 'marketCatalogue' in data:
                for market in data['marketCatalogue']:
                    mt = market.get('marketName') or market.get('description', {}).get('marketType')
                    if mt:
                        market_types.add(mt)

        if market_types:
            print(f"  📊 Market types: {', '.join(market_types)}")

    async def investigate(self, url: str, wait_time: int = 15):
        """
        Navega para URL e captura requisições de API.

        Args:
            url: URL da Betfair (pode ser página inicial ou jogo específico)
            wait_time: Tempo de espera em segundos para capturar requisições
        """
        async with async_playwright() as p:
            print(f"\n🚀 Iniciando investigação em: {url}\n")

            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Registrar handler para capturar respostas
            page.on('response', lambda response: asyncio.create_task(self.handle_response(response)))

            # Navegar para página
            await page.goto(url, wait_until='networkidle', timeout=60000)
            print("✓ Página carregada\n")

            # Aceitar cookies se aparecer
            try:
                cookies_btn = page.locator('#onetrust-accept-btn-handler').first
                if await cookies_btn.is_visible(timeout=3000):
                    await cookies_btn.click()
                    print("✓ Cookies aceitos\n")
            except:
                pass

            # Tentar clicar no primeiro jogo para carregar mais mercados
            try:
                print("🎯 Tentando clicar no primeiro jogo...\n")

                # Esperar a tabela de jogos carregar
                await page.wait_for_selector('tr[data-event-id], a[href*="/event/"]', timeout=10000)

                # Clicar no primeiro link de evento
                first_event = page.locator('a[href*="/event/"]').first
                await first_event.click()

                print("✓ Clicado no jogo, aguardando mercados carregarem...\n")

                # Esperar mais tempo para carregar mercados adicionais
                await page.wait_for_timeout(wait_time * 1000)

            except Exception as e:
                print(f"  ⚠ Não foi possível clicar no jogo: {e}")
                print(f"  Aguardando {wait_time}s na página inicial...\n")
                await page.wait_for_timeout(wait_time * 1000)

            await browser.close()

        return self.api_responses, self.all_urls

    def save_results(self, prefix='betfair_markets_investigation'):
        """Salva resultados da investigação."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Salvar respostas completas
        responses_file = f'data/{prefix}_responses_{timestamp}.json'
        with open(responses_file, 'w', encoding='utf-8') as f:
            json.dump(self.api_responses, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Respostas salvas: {responses_file}")

        # Salvar lista de URLs
        urls_file = f'data/{prefix}_urls_{timestamp}.txt'
        with open(urls_file, 'w', encoding='utf-8') as f:
            for url in sorted(self.all_urls):
                f.write(f"{url}\n")

        print(f"💾 URLs salvas: {urls_file}")

        # Gerar relatório
        self.generate_report()

    def generate_report(self):
        """Gera relatório de market types encontrados."""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DE INVESTIGAÇÃO")
        print("="*80)

        market_types = {}

        for resp in self.api_responses:
            data = resp.get('data', {})
            url = resp.get('url', '')

            # Analisar diferentes estruturas
            if 'eventTypes' in data:
                for et in data['eventTypes']:
                    for node in et.get('eventNodes', []):
                        for market in node.get('marketNodes', []):
                            desc = market.get('description', {})
                            mt = desc.get('marketType', 'UNKNOWN')
                            mn = desc.get('marketName', 'N/A')

                            if mt not in market_types:
                                market_types[mt] = {
                                    'count': 0,
                                    'exemplos': set(),
                                    'urls': set()
                                }

                            market_types[mt]['count'] += 1
                            market_types[mt]['exemplos'].add(mn)
                            market_types[mt]['urls'].add(url[:100])

        print(f"\nTotal de requisições capturadas: {len(self.api_responses)}")
        print(f"Total de URLs únicas: {len(self.all_urls)}")
        print(f"\nMarket Types encontrados: {len(market_types)}\n")

        for mt, details in sorted(market_types.items()):
            print(f"\n{mt}:")
            print(f"  Ocorrências: {details['count']}")
            print(f"  Exemplos: {list(details['exemplos'])[:3]}")
            print(f"  URLs: {len(details['urls'])} diferentes")

        # Verificar se Over/Under e BTTS foram encontrados
        print("\n" + "-"*80)
        print("🔍 VERIFICAÇÃO DE MERCADOS ESPECIAIS:")
        print("-"*80)

        target_markets = {
            'OVER_UNDER_25': '❌ Não encontrado',
            'OVER_UNDER_15': '❌ Não encontrado',
            'BOTH_TEAMS_TO_SCORE': '❌ Não encontrado',
            'MATCH_ODDS': '❌ Não encontrado'
        }

        for mt in market_types.keys():
            if 'OVER_UNDER' in mt:
                if '25' in mt or '2.5' in str(market_types[mt]['exemplos']):
                    target_markets['OVER_UNDER_25'] = '✅ ENCONTRADO!'
                if '15' in mt or '1.5' in str(market_types[mt]['exemplos']):
                    target_markets['OVER_UNDER_15'] = '✅ ENCONTRADO!'
            elif 'BOTH' in mt or 'BTTS' in mt:
                target_markets['BOTH_TEAMS_TO_SCORE'] = '✅ ENCONTRADO!'
            elif 'MATCH_ODDS' in mt:
                target_markets['MATCH_ODDS'] = '✅ ENCONTRADO!'

        for market, status in target_markets.items():
            print(f"  {market}: {status}")

        print("\n" + "="*80 + "\n")


async def main():
    investigator = BetfairMarketsInvestigator()

    # URL da página inicial de futebol hoje
    url = 'https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today'

    # Investigar (vai navegar e clicar no primeiro jogo)
    await investigator.investigate(url, wait_time=15)

    # Salvar resultados
    investigator.save_results()


if __name__ == '__main__':
    asyncio.run(main())
