"""
Script para navegar até uma página individual de jogo na Betfair
e capturar todos os mercados disponíveis (Over/Under, BTTS, etc.)
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

class BetfairMatchNavigator:
    def __init__(self):
        self.api_responses = []
        self.market_types_found = set()

    async def handle_response(self, response):
        """Captura respostas de API relevantes."""
        url = response.url
        keywords = ['market', 'event', 'football', 'soccer', 'odds', 'coupon']

        if any(keyword in url.lower() for keyword in keywords):
            try:
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    data = await response.json()
                    self.api_responses.append({
                        'url': url,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })

                    # Analisar marketTypes
                    markets = self._extract_market_types(data)
                    if markets:
                        self.market_types_found.update(markets)
                        print(f"  📊 Markets: {', '.join(markets)}")

            except Exception as e:
                pass

    def _extract_market_types(self, data):
        """Extrai market types de diferentes estruturas."""
        markets = set()

        if isinstance(data, dict):
            # Estrutura 1: eventTypes[].eventNodes[].marketNodes[]
            if 'eventTypes' in data:
                for et in data['eventTypes']:
                    for node in et.get('eventNodes', []):
                        for market in node.get('marketNodes', []):
                            mt = market.get('description', {}).get('marketType')
                            if mt:
                                markets.add(mt)

            # Estrutura 2: markets[]
            if 'markets' in data:
                for market in data.get('markets', []):
                    mt = market.get('marketType') or market.get('description', {}).get('marketType')
                    if mt:
                        markets.add(mt)

            # Estrutura 3: Procurar recursivamente por 'marketType'
            markets.update(self._search_market_types_recursive(data))

        return markets

    def _search_market_types_recursive(self, obj, depth=0, max_depth=5):
        """Busca recursiva por marketType em estruturas JSON."""
        if depth > max_depth:
            return set()

        markets = set()

        if isinstance(obj, dict):
            if 'marketType' in obj:
                markets.add(obj['marketType'])

            for value in obj.values():
                markets.update(self._search_market_types_recursive(value, depth + 1, max_depth))

        elif isinstance(obj, list):
            for item in obj:
                markets.update(self._search_market_types_recursive(item, depth + 1, max_depth))

        return markets

    async def navigate_to_match(self, base_url: str):
        """Navega para página inicial e clica no primeiro jogo."""
        async with async_playwright() as p:
            print(f"\n🚀 Iniciando navegação para jogo individual...\n")

            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Registrar handler
            page.on('response', lambda response: asyncio.create_task(self.handle_response(response)))

            # Navegar para página inicial
            print(f"📍 Navegando para: {base_url}")
            await page.goto(base_url, wait_until='networkidle', timeout=60000)

            # Aceitar cookies
            try:
                cookies_btn = page.locator('#onetrust-accept-btn-handler').first
                if await cookies_btn.is_visible(timeout=3000):
                    await cookies_btn.click()
                    print("✓ Cookies aceitos\n")
                    await page.wait_for_timeout(2000)
            except:
                pass

            # Aguardar página carregar
            await page.wait_for_timeout(3000)

            print("🎯 Procurando jogo para clicar...\n")

            # Tentar diferentes estratégias para clicar no jogo
            clicked = False

            # Estratégia 1: Link direto para evento
            try:
                print("  Tentando: Clicar em link de evento...")
                event_link = page.locator('a[href*="/football/"]').first
                if await event_link.is_visible(timeout=5000):
                    event_url = await event_link.get_attribute('href')
                    print(f"  ✓ Link encontrado: {event_url}")
                    await event_link.click()
                    clicked = True
                    print("  ✓ Clique realizado!\n")
            except Exception as e:
                print(f"  ✗ Falhou: {e}\n")

            # Estratégia 2: Clicar em linha da tabela
            if not clicked:
                try:
                    print("  Tentando: Clicar em linha da tabela...")
                    row = page.locator('tr.event-row, tr[data-event-id], div.event-holder').first
                    if await row.is_visible(timeout=5000):
                        await row.click()
                        clicked = True
                        print("  ✓ Clique realizado!\n")
                except Exception as e:
                    print(f"  ✗ Falhou: {e}\n")

            # Estratégia 3: Procurar pelo nome do time
            if not clicked:
                try:
                    print("  Tentando: Procurar elemento com nome de time...")
                    teams = page.locator('text=/Ferroviária|Coritiba|Remo/i').first
                    if await teams.is_visible(timeout=5000):
                        # Clicar no elemento pai
                        parent = teams.locator('xpath=ancestor::a | ancestor::tr | ancestor::div[@role="button"]').first
                        await parent.click()
                        clicked = True
                        print("  ✓ Clique realizado!\n")
                except Exception as e:
                    print(f"  ✗ Falhou: {e}\n")

            # Estratégia 4: JavaScript para clicar
            if not clicked:
                try:
                    print("  Tentando: JavaScript para clicar...")
                    result = await page.evaluate('''() => {
                        const links = Array.from(document.querySelectorAll('a[href*="/football/"]'));
                        if (links.length > 0) {
                            links[0].click();
                            return true;
                        }
                        return false;
                    }''')
                    if result:
                        clicked = True
                        print("  ✓ Clique realizado via JavaScript!\n")
                except Exception as e:
                    print(f"  ✗ Falhou: {e}\n")

            if clicked:
                print("⏳ Aguardando página de jogo carregar e mercados serem requisitados...\n")
                await page.wait_for_timeout(15000)  # 15 segundos para capturar todas as requisições

                # Tentar rolar a página para carregar mais mercados
                print("📜 Rolando página para carregar mercados adicionais...\n")
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(5000)

            else:
                print("⚠️  Não foi possível clicar no jogo. Aguardando na página inicial...\n")
                await page.wait_for_timeout(10000)

            await browser.close()

        return clicked

    def generate_report(self):
        """Gera relatório dos mercados encontrados."""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DE MERCADOS ENCONTRADOS")
        print("="*80)

        print(f"\nTotal de requisições capturadas: {len(self.api_responses)}")
        print(f"Market Types únicos: {len(self.market_types_found)}\n")

        if self.market_types_found:
            print("Market Types encontrados:")
            for mt in sorted(self.market_types_found):
                print(f"  • {mt}")
        else:
            print("  ⚠️  Nenhum market type encontrado")

        # Verificar mercados específicos
        print("\n" + "-"*80)
        print("🔍 VERIFICAÇÃO DE MERCADOS ALVO:")
        print("-"*80)

        targets = {
            'MATCH_ODDS': '❌',
            'OVER_UNDER_25': '❌',
            'OVER_UNDER_15': '❌',
            'BOTH_TEAMS_TO_SCORE': '❌'
        }

        for mt in self.market_types_found:
            if 'MATCH_ODDS' in mt:
                targets['MATCH_ODDS'] = '✅ ENCONTRADO!'
            if 'OVER_UNDER' in mt:
                if '25' in mt or '2.5' in mt:
                    targets['OVER_UNDER_25'] = '✅ ENCONTRADO!'
                if '15' in mt or '1.5' in mt:
                    targets['OVER_UNDER_15'] = '✅ ENCONTRADO!'
            if 'BOTH' in mt.upper() or 'BTTS' in mt.upper():
                targets['BOTH_TEAMS_TO_SCORE'] = '✅ ENCONTRADO!'

        for market, status in targets.items():
            print(f"  {market}: {status}")

        print("\n" + "="*80 + "\n")

    def save_results(self):
        """Salva respostas capturadas."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/betfair_match_page_responses_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.api_responses, f, indent=2, ensure_ascii=False)

        print(f"💾 Respostas salvas: {filename}\n")


async def main():
    navigator = BetfairMatchNavigator()

    url = 'https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today'

    clicked = await navigator.navigate_to_match(url)

    navigator.save_results()
    navigator.generate_report()

    if not clicked:
        print("\n⚠️  ATENÇÃO: Não foi possível navegar para página de jogo individual.")
        print("            Apenas mercados da página inicial foram capturados.\n")


if __name__ == '__main__':
    asyncio.run(main())
