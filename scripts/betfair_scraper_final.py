#!/usr/bin/env python3
"""
Script final para extrair jogos da Betfair.
Usa Playwright async para navegar e extrair dados de forma eficiente.
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright


async def scrape_betfair():
    """Scrape jogos da Betfair."""

    async with async_playwright() as p:
        print("🚀 Iniciando navegador...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("🌐 Navegando para Betfair...")
        await page.goto('https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today',
                       wait_until='domcontentloaded')

        # Aguardar um pouco para o popup de cookies aparecer
        await asyncio.sleep(2)

        # Aceitar cookies PRIMEIRO
        try:
            print("🍪 Procurando popup de cookies...")
            cookies_btn = page.locator('text="Aceitar todos os cookies"').first
            await cookies_btn.wait_for(state='visible', timeout=5000)
            print("🍪 Clicando em 'Aceitar todos os cookies'...")
            await cookies_btn.click()
            await asyncio.sleep(2)  # Aguardar após aceitar cookies
            print("✓ Cookies aceitos - popup fechado")
        except Exception as e:
            print(f"ℹ️  Erro ao aceitar cookies: {str(e)[:100]}")

        # AGORA aguardar o carregamento do conteúdo principal
        print("⏳ Aguardando carregamento do conteúdo dos jogos...")

        # Aguardar mais tempo para conteúdo dinâmico carregar
        await asyncio.sleep(5)

        try:
            # Aguardar por elementos específicos que indicam jogos carregados
            await page.wait_for_selector('text=/Ferroviária|Coritiba|Remo|Brasileirão/i', timeout=15000)
            print("✓ Jogos carregados")
        except:
            print("⚠️  Timeout aguardando jogos específicos - tentando extrair...")

        # Clicar em "Hoje" se necessário
        try:
            hoje_btn = page.locator('button:has-text("Hoje"), a:has-text("Hoje")').first
            if await hoje_btn.is_visible(timeout=2000):
                print("📅 Clicando em 'Hoje'...")
                await hoje_btn.click()
                await asyncio.sleep(3)  # Aguardar recarregar após o clique
        except:
            print("ℹ️  Botão 'Hoje' não encontrado ou já selecionado")

        print("\n📊 Extraindo dados dos jogos...")

        # DEBUG: Tirar screenshot
        await page.screenshot(path='data/debug_screenshot.png')
        print(f"🐛 Debug: Screenshot salvo em data/debug_screenshot.png")

        # Extrair jogos usando diferentes estratégias
        jogos = []

        # Estratégia 1: Buscar por padrão de texto
        page_text = await page.content()

        # Estratégia 2: Analisar o texto da página linha por linha
        all_text = await page.evaluate('() => document.body.innerText')

        # DEBUG: Salvar conteúdo da página para análise
        with open('data/debug_page_content.txt', 'w', encoding='utf-8') as f:
            f.write(all_text)
        print(f"🐛 Debug: Conteúdo da página salvo em data/debug_page_content.txt")
        print(f"🐛 Debug: Total de linhas: {len(all_text.split(chr(10)))}")

        # DEBUG: Salvar HTML também
        with open('data/debug_page_html.html', 'w', encoding='utf-8') as f:
            f.write(page_text)
        print(f"�� Debug: HTML salvo em data/debug_page_html.html")

        lines = all_text.split('\n')
        current_competition = ''

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Detectar nome de competição
            if any(keyword in line for keyword in ['Brasileirão', 'Série', 'Europa', 'Eliminatórias',
                                                     'Premier', 'La Liga', 'Champions', 'Amistosos',
                                                     'Copa', 'Mundial', 'Libertadores']):
                if len(line) < 100 and not re.search(r'\d+[,\.]\d+', line):
                    current_competition = line

            # Procurar por horário no formato "Hoje às HH:MM" ou "HH:MM"
            hora_match = re.search(r'(?:Hoje às )?(\d{1,2}:\d{2})', line)

            if hora_match:
                horario = hora_match.group(1)

                # As próximas linhas devem conter os times
                mandante = ''
                visitante = ''

                # Procurar nas próximas 5 linhas
                for j in range(i+1, min(i+6, len(lines))):
                    next_line = lines[j].strip()

                    # Validar se é um nome de time válido
                    if (len(next_line) > 2 and
                        len(next_line) < 50 and
                        not re.match(r'^\d+[,\.]?\d*$', next_line) and  # Não é apenas número
                        not re.search(r'R\$', next_line) and  # Não contém R$
                        not 'Correspondido' in next_line and
                        not 'Ver todo' in next_line and
                        not 'Múltiplas' in next_line):

                        if not mandante:
                            mandante = next_line
                        elif not visitante:
                            visitante = next_line
                            break

                if mandante and visitante:
                    jogo = {
                        'data': datetime.now().strftime('%Y-%m-%d'),
                        'horario': horario,
                        'competicao': current_competition if current_competition else 'N/A',
                        'mandante': mandante,
                        'visitante': visitante
                    }

                    # Evitar duplicatas
                    jogo_key = f"{horario}|{mandante}|{visitante}"
                    if not any(f"{j['horario']}|{j['mandante']}|{j['visitante']}" == jogo_key for j in jogos):
                        jogos.append(jogo)
                        print(f"  ✓ {horario} | {mandante} x {visitante}")

            i += 1

        # Ordenar por horário
        jogos.sort(key=lambda x: x['horario'])

        await browser.close()

        return jogos


async def main():
    """Função principal."""
    print("=" * 80)
    print("🎯 BETFAIR SCRAPER - JOGOS DE HOJE")
    print("=" * 80)
    print()

    try:
        jogos = await scrape_betfair()

        print("\n" + "=" * 80)
        print(f"✅ TOTAL: {len(jogos)} jogos encontrados")
        print("=" * 80)

        if jogos:
            # Salvar em JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/betfair_jogos_{timestamp}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jogos, f, ensure_ascii=False, indent=2)

            print(f"\n💾 Dados salvos em: {output_file}")

            # Exibir tabela
            print("\n📋 JOGOS ENCONTRADOS:")
            print("-" * 100)
            print(f"{'#':<4} {'HORÁRIO':<10} {'MANDANTE':<35} {'VISITANTE':<35} {'COMPETIÇÃO':<20}")
            print("-" * 100)

            for i, jogo in enumerate(jogos, 1):
                print(f"{i:<4} {jogo['horario']:<10} {jogo['mandante']:<35} "
                      f"{jogo['visitante']:<35} {jogo['competicao'][:18]:<20}")

            print("-" * 100)

        else:
            print("\n⚠️  Nenhum jogo encontrado!")
            print("💡 Verifique se:")
            print("   - O site está acessível")
            print("   - Há jogos programados para hoje")
            print("   - A estrutura do site não mudou")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
