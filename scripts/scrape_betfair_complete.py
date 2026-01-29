#!/usr/bin/env python3
"""
Script para extrair TODOS os dados de jogos de hoje do site da Betfair usando Playwright.
Navega por todas as páginas usando o botão "próximo".
Extrai: data/hora, time mandante e time visitante.
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def extrair_jogos_pagina(page):
    """Extrai jogos da página atual."""

    jogos = await page.evaluate("""
        () => {
            const jogos = [];
            const hoje = new Date().toISOString().split('T')[0];

            // Buscar todos os elementos que contêm "Hoje às" ou horários
            const allElements = document.querySelectorAll('*');
            const jogosMap = new Map();

            allElements.forEach(el => {
                const texto = el.textContent || '';

                // Procurar por padrão de horário: "Hoje às HH:MM"
                const matchHoje = texto.match(/Hoje às (\\d{1,2}:\\d{2})/);
                if (matchHoje) {
                    const horario = matchHoje[1];

                    // Tentar encontrar os times próximos a este elemento
                    let parent = el.parentElement;
                    let tentativas = 0;

                    while (parent && tentativas < 5) {
                        const todosTextos = parent.innerText.split('\\n');

                        // Procurar por linhas que parecem nomes de times
                        const possiveisTimes = todosTextos.filter(linha => {
                            const l = linha.trim();
                            return l.length > 3 &&
                                   l.length < 50 &&
                                   !l.includes('Hoje às') &&
                                   !l.match(/^\\d+[:.\\d,]*$/) &&
                                   !l.includes('R$') &&
                                   !l.includes('Correspondido') &&
                                   !l.includes('Múltiplas') &&
                                   !l.includes('Ver todo');
                        });

                        if (possiveisTimes.length >= 2) {
                            // Encontrou os times
                            const mandante = possiveisTimes[0].trim();
                            const visitante = possiveisTimes[1].trim();
                            const chave = `${mandante}|${visitante}|${horario}`;

                            if (!jogosMap.has(chave)) {
                                jogosMap.set(chave, {
                                    data: hoje,
                                    horario: horario,
                                    mandante: mandante,
                                    visitante: visitante
                                });
                            }
                            break;
                        }

                        parent = parent.parentElement;
                        tentativas++;
                    }
                }
            });

            return Array.from(jogosMap.values());
        }
    """)

    return jogos


async def scrape_betfair_today():
    """Extrai dados dos jogos de hoje da Betfair navegando por todas as páginas."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False para debug
        page = await browser.new_page()

        # Configurar viewport maior para ver mais conteúdo
        await page.set_viewport_size({"width": 1920, "height": 1080})

        print("🌐 Navegando para Betfair...")
        await page.goto('https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today',
                       wait_until='domcontentloaded')

        # Aguardar carregamento inicial
        await page.wait_for_timeout(3000)

        # Aceitar cookies se aparecer
        try:
            aceitar_cookies = page.locator('text="Aceitar todos os cookies"')
            if await aceitar_cookies.is_visible(timeout=2000):
                print("🍪 Aceitando cookies...")
                await aceitar_cookies.click()
                await page.wait_for_timeout(1000)
        except:
            pass

        # Clicar no botão "Hoje" para garantir que estamos vendo os jogos de hoje
        print("📅 Clicando no botão 'Hoje'...")
        try:
            # Tentar diferentes seletores para o botão "Hoje"
            hoje_button = page.locator('text="Hoje"').first
            await hoje_button.click(timeout=5000)
            await page.wait_for_timeout(2000)
            print("✓ Botão 'Hoje' clicado")
        except Exception as e:
            print(f"⚠ Não foi possível clicar em 'Hoje': {e}")
            print("  Continuando mesmo assim...")

        todos_jogos = []
        pagina_num = 1

        while True:
            print(f"\n📄 Processando página {pagina_num}...")

            # Extrair jogos da página atual
            jogos_pagina = await extrair_jogos_pagina(page)

            if jogos_pagina:
                print(f"  ✓ Encontrados {len(jogos_pagina)} jogos nesta página")
                todos_jogos.extend(jogos_pagina)
            else:
                print(f"  ⚠ Nenhum jogo encontrado nesta página")

            # Procurar pelo botão "Próximo" ou setas de navegação
            try:
                # Tentar vários seletores possíveis para navegação
                proximo_button = None

                # Seletor 1: texto "Próximo" ou "Next"
                try:
                    proximo_button = page.locator('text=/Próximo|Next|próximo|next/i').first
                    if await proximo_button.is_visible(timeout=2000):
                        print("  → Encontrado botão 'Próximo' (texto)")
                except:
                    pass

                # Seletor 2: botão com seta para direita
                if not proximo_button:
                    try:
                        proximo_button = page.locator('button[aria-label*="próximo" i], button[aria-label*="next" i]').first
                        if await proximo_button.is_visible(timeout=1000):
                            print("  → Encontrado botão 'Próximo' (aria-label)")
                    except:
                        pass

                # Seletor 3: ícone de seta
                if not proximo_button:
                    try:
                        proximo_button = page.locator('[class*="next"], [class*="arrow-right"], [class*="chevron-right"]').first
                        if await proximo_button.is_visible(timeout=1000):
                            print("  → Encontrado botão 'Próximo' (classe)")
                    except:
                        pass

                # Se encontrou botão, clicar
                if proximo_button and await proximo_button.is_visible():
                    # Verificar se não está desabilitado
                    is_disabled = await proximo_button.is_disabled()
                    if is_disabled:
                        print("  ⏹ Botão 'Próximo' está desabilitado - última página alcançada")
                        break

                    print("  ⏭  Clicando em 'Próximo'...")
                    await proximo_button.click()
                    await page.wait_for_timeout(2000)  # Aguardar carregamento
                    pagina_num += 1
                else:
                    print("  ⏹ Botão 'Próximo' não encontrado - última página alcançada")
                    break

            except Exception as e:
                print(f"  ⏹ Erro ao procurar próxima página: {e}")
                break

            # Limite de segurança para evitar loop infinito
            if pagina_num > 50:
                print("  ⚠ Limite de 50 páginas atingido - parando por segurança")
                break

        await browser.close()

        # Remover duplicatas
        jogos_unicos = []
        vistos = set()

        for jogo in todos_jogos:
            chave = f"{jogo['mandante']}|{jogo['visitante']}|{jogo['horario']}"
            if chave not in vistos:
                vistos.add(chave)
                jogos_unicos.append(jogo)

        return jogos_unicos


async def main():
    """Função principal."""
    print("=" * 80)
    print("🎯 SCRAPER BETFAIR - JOGOS DE HOJE (COMPLETO)")
    print("=" * 80)

    jogos = await scrape_betfair_today()

    print("\n" + "=" * 80)
    print(f"✓ TOTAL DE JOGOS ENCONTRADOS: {len(jogos)}")
    print("=" * 80)

    if jogos:
        # Ordenar por horário
        jogos.sort(key=lambda x: x['horario'])

        # Salvar em JSON
        output_file = f"data/betfair_today_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Dados salvos em: {output_file}\n")

        # Exibir todos os jogos
        print("📋 LISTA COMPLETA DE JOGOS:")
        print("-" * 80)
        for i, jogo in enumerate(jogos, 1):
            print(f"{i:3}. {jogo['horario']:>8} | {jogo['mandante']:>30} x {jogo['visitante']:<30}")
        print("-" * 80)
    else:
        print("\n⚠ NENHUM JOGO ENCONTRADO")
        print("\n💡 Dicas:")
        print("  - Verifique se o site está acessível")
        print("  - A estrutura do site pode ter mudado")
        print("  - Tente executar com headless=False para ver o navegador")


if __name__ == "__main__":
    asyncio.run(main())
