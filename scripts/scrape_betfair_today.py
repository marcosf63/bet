#!/usr/bin/env python3
"""
Script para extrair dados de jogos do site da Betfair usando Playwright.
Extrai: data/hora, time mandante e time visitante.
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def scrape_betfair_today():
    """Extrai dados dos jogos de hoje da Betfair."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navegando para Betfair...")
        await page.goto('https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today')

        # Aguardar carregamento
        await page.wait_for_timeout(3000)

        # Clicar no botão "Hoje" para garantir que estamos vendo os jogos de hoje
        try:
            hoje_button = await page.wait_for_selector('text="Hoje"', timeout=5000)
            await hoje_button.click()
            await page.wait_for_timeout(2000)
        except:
            print("Botão 'Hoje' não encontrado, continuando...")

        # Extrair dados dos jogos
        jogos = await page.evaluate("""
            () => {
                const jogos = [];
                const hoje = new Date().toISOString().split('T')[0];

                // Buscar todas as seções de competição
                const sections = document.querySelectorAll('[class*="section"], [class*="competition"], .coupon-section');

                sections.forEach(section => {
                    // Para cada seção, buscar os jogos
                    const rows = section.querySelectorAll('[class*="event"], [class*="market"], [data-event-id], .coupon-row');

                    rows.forEach(row => {
                        try {
                            // Buscar horário
                            const timeEl = row.querySelector('[class*="time"], [class*="start-time"], .time-col');
                            let horario = timeEl?.textContent?.trim() || '';

                            // Se encontrou horário no formato HH:MM
                            if (horario.match(/\\d{1,2}:\\d{2}/)) {
                                // Buscar nomes dos times
                                const allText = row.innerText;
                                const lines = allText.split('\\n').filter(l => l.trim());

                                // Procurar por linhas que parecem nomes de times
                                const possibleTeams = lines.filter(line => {
                                    const l = line.trim();
                                    // Não é horário, não é número/odd, tem tamanho razoável
                                    return l.length > 3 &&
                                           l.length < 50 &&
                                           !l.match(/^\\d+[:.\\d]*$/) &&
                                           !l.match(/^R\\$/) &&
                                           !l.includes('Correspondido') &&
                                           !l.match(/^[0-9.]+$/);
                                });

                                if (possibleTeams.length >= 2) {
                                    jogos.push({
                                        data: hoje,
                                        horario: horario,
                                        mandante: possibleTeams[0],
                                        visitante: possibleTeams[1]
                                    });
                                }
                            }
                        } catch (e) {
                            // Ignorar erros individuais
                        }
                    });
                });

                // Remover duplicatas baseado em mandante+visitante+horario
                const unique = [];
                const seen = new Set();

                jogos.forEach(jogo => {
                    const key = `${jogo.mandante}-${jogo.visitante}-${jogo.horario}`;
                    if (!seen.has(key)) {
                        seen.add(key);
                        unique.push(jogo);
                    }
                });

                return unique;
            }
        """)

        await browser.close()

        return jogos


async def main():
    """Função principal."""
    print("Iniciando scraping da Betfair...")

    jogos = await scrape_betfair_today()

    print(f"\n✓ Encontrados {len(jogos)} jogos\n")

    if jogos:
        # Salvar em JSON
        output_file = f"data/betfair_today_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=2)

        print(f"✓ Dados salvos em: {output_file}\n")

        # Exibir preview
        print("Preview dos jogos:")
        print("-" * 80)
        for jogo in jogos[:10]:  # Mostrar apenas os 10 primeiros
            print(f"{jogo['data']} {jogo['horario']:>8} | {jogo['mandante']:>25} x {jogo['visitante']:<25}")

        if len(jogos) > 10:
            print(f"... e mais {len(jogos) - 10} jogos")
        print("-" * 80)
    else:
        print("⚠ Nenhum jogo encontrado")


if __name__ == "__main__":
    asyncio.run(main())
