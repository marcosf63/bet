"""
Navega diretamente para uma página de evento/jogo específico
para capturar todos os mercados disponíveis (Over/Under, BTTS, etc.)
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

class BetfairDirectEventNavigator:
    def __init__(self):
        self.api_responses = []
        self.market_types_found = set()
        self.market_details = {}

    async def handle_response(self, response):
        """Captura respostas de API."""
        url = response.url

        # Capturar APIs relevantes
        if any(kw in url.lower() for kw in ['market', 'event', 'odds', 'readonly']):
            try:
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    data = await response.json()

                    self.api_responses.append({
                        'url': url,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })

                    # Extrair e exibir market types
                    markets = self._extract_markets(data)
                    if markets:
                        print(f"✓ API: {url[:70]}...")
                        for mt, details in markets.items():
                            self.market_types_found.add(mt)
                            print(f"  📊 {mt}: {details['marketName']}")

                            if mt not in self.market_details:
                                self.market_details[mt] = details

            except Exception as e:
                pass

    def _extract_markets(self, data):
        """Extrai informações detalhadas dos mercados."""
        markets = {}

        if isinstance(data, dict):
            # Estrutura: eventTypes[].eventNodes[].marketNodes[]
            if 'eventTypes' in data:
                for et in data['eventTypes']:
                    for node in et.get('eventNodes', []):
                        for market in node.get('marketNodes', []):
                            desc = market.get('description', {})
                            mt = desc.get('marketType', 'UNKNOWN')
                            mn = desc.get('marketName', 'N/A')
                            market_id = market.get('marketId', 'N/A')

                            if mt and mt != 'UNKNOWN':
                                markets[mt] = {
                                    'marketName': mn,
                                    'marketId': market_id,
                                    'runners': len(market.get('runners', []))
                                }

        return markets

    async def navigate_and_capture(self, event_url: str, wait_time: int = 20):
        """Navega para URL de evento e captura mercados."""
        async with async_playwright() as p:
            print(f"\n🚀 Navegando para evento específico...\n")
            print(f"📍 URL: {event_url}\n")

            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Registrar handler
            page.on('response', lambda response: asyncio.create_task(self.handle_response(response)))

            # Navegar
            await page.goto(event_url, wait_until='networkidle', timeout=60000)

            # Aceitar cookies
            try:
                cookies_btn = page.locator('#onetrust-accept-btn-handler').first
                if await cookies_btn.is_visible(timeout=3000):
                    await cookies_btn.click()
                    await page.wait_for_timeout(2000)
            except:
                pass

            print("\n⏳ Aguardando carregamento completo da página...\n")
            await page.wait_for_timeout(wait_time * 1000)

            # Rolar página para ativar lazy loading de mercados
            print("📜 Rolando página para carregar todos os mercados...\n")
            for i in range(3):
                await page.evaluate('window.scrollBy(0, 500)')
                await page.wait_for_timeout(2000)

            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(5000)

            # Tentar clicar em abas de mercados adicionais
            print("🔍 Procurando abas de mercados adicionais...\n")
            try:
                # Procurar abas como "Mais Mercados", "Over/Under", "Goals", etc.
                tabs = page.locator('text=/mais|over|under|goals|gols|btts|ambos/i')
                count = await tabs.count()

                if count > 0:
                    print(f"  ✓ Encontradas {count} abas de mercados")
                    for i in range(min(count, 3)):  # Clicar nas primeiras 3 abas
                        try:
                            tab = tabs.nth(i)
                            tab_text = await tab.inner_text()
                            print(f"    Clicando em: {tab_text}")
                            await tab.click()
                            await page.wait_for_timeout(3000)
                        except:
                            pass
                else:
                    print("  ℹ️  Nenhuma aba adicional encontrada")
            except Exception as e:
                print(f"  ⚠️  Erro ao procurar abas: {e}")

            print("\n⏳ Aguardando requisições finais...\n")
            await page.wait_for_timeout(5000)

            await browser.close()

    def generate_report(self):
        """Gera relatório detalhado."""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DETALHADO - MERCADOS ENCONTRADOS")
        print("="*80)

        print(f"\nTotal de requisições: {len(self.api_responses)}")
        print(f"Market Types únicos: {len(self.market_types_found)}\n")

        if self.market_details:
            print("Mercados encontrados:\n")
            for mt, details in sorted(self.market_details.items()):
                print(f"  • {mt}")
                print(f"    Nome: {details['marketName']}")
                print(f"    ID: {details['marketId']}")
                print(f"    Runners: {details['runners']}")
                print()
        else:
            print("  ⚠️  Nenhum mercado capturado\n")

        # Verificação de mercados alvo
        print("-"*80)
        print("🎯 VERIFICAÇÃO DE MERCADOS ALVO:")
        print("-"*80 + "\n")

        targets = {
            'MATCH_ODDS': '❌ Não encontrado',
            'OVER_UNDER_25': '❌ Não encontrado',
            'OVER_UNDER_15': '❌ Não encontrado',
            'BOTH_TEAMS_TO_SCORE': '❌ Não encontrado',
            'OVER_UNDER (qualquer)': '❌ Não encontrado'
        }

        for mt in self.market_types_found:
            if 'MATCH_ODDS' in mt.upper():
                targets['MATCH_ODDS'] = f'✅ ENCONTRADO! ({mt})'

            if 'OVER' in mt.upper() and 'UNDER' in mt.upper():
                targets['OVER_UNDER (qualquer)'] = f'✅ ENCONTRADO! ({mt})'

                if '25' in mt or '2.5' in mt or '2,5' in mt:
                    targets['OVER_UNDER_25'] = f'✅ ENCONTRADO! ({mt})'
                if '15' in mt or '1.5' in mt or '1,5' in mt:
                    targets['OVER_UNDER_15'] = f'✅ ENCONTRADO! ({mt})'

            if 'BOTH' in mt.upper() or 'BTTS' in mt.upper() or 'AMBOS' in mt.upper():
                targets['BOTH_TEAMS_TO_SCORE'] = f'✅ ENCONTRADO! ({mt})'

        for market, status in targets.items():
            print(f"  {market:30s}: {status}")

        print("\n" + "="*80 + "\n")

    def save_results(self):
        """Salva resultados."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/betfair_direct_event_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': timestamp,
                    'total_requests': len(self.api_responses),
                    'market_types_found': list(self.market_types_found)
                },
                'market_details': self.market_details,
                'api_responses': self.api_responses
            }, f, indent=2, ensure_ascii=False)

        print(f"💾 Resultados salvos: {filename}\n")


async def main():
    navigator = BetfairDirectEventNavigator()

    # Primeiro, buscar URL de um jogo para testar
    # Vamos usar uma URL genérica e tentar encontrar um jogo
    print("🔍 Buscando URL de jogo para testar...\n")

    # Opção 1: Navegar pela página inicial e pegar URL real de um jogo
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto('https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today',
                       wait_until='networkidle')

        # Aceitar cookies
        try:
            cookies_btn = page.locator('#onetrust-accept-btn-handler').first
            if await cookies_btn.is_visible(timeout=3000):
                await cookies_btn.click()
                await page.wait_for_timeout(2000)
        except:
            pass

        # Esperar e pegar href do primeiro jogo
        try:
            # Procurar link que contenha "/event/" na URL
            event_link = page.locator('a[href*="/event/"]').first
            await event_link.wait_for(timeout=10000)
            event_url = await event_link.get_attribute('href')

            if not event_url.startswith('http'):
                event_url = 'https://www.betfair.bet.br' + event_url

            print(f"✓ URL de jogo encontrada: {event_url}\n")

        except Exception as e:
            print(f"⚠️  Não foi possível encontrar URL de jogo: {e}")
            print("  Usando URL de exemplo (pode não funcionar)...\n")
            event_url = 'https://www.betfair.bet.br/exchange/plus/pt/football/event/34815527'

        await browser.close()

    # Navegar para o jogo e capturar mercados
    await navigator.navigate_and_capture(event_url, wait_time=20)

    # Gerar relatório e salvar
    navigator.save_results()
    navigator.generate_report()


if __name__ == '__main__':
    asyncio.run(main())
