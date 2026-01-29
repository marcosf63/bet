#!/usr/bin/env python3
"""
Script otimizado para extrair jogos da Betfair usando MCP Playwright.
Versão 2 - Extração mais precisa baseada na estrutura real da página.
"""

import json
from datetime import datetime
import subprocess
import re


def extrair_jogos_via_mcp():
    """Extrai jogos usando comandos MCP Playwright via subprocess."""

    print("🌐 Navegando para Betfair...")

    # Usar o browser do MCP que já está aberto
    # Executar JavaScript para extrair os dados
    js_code = """
    (() => {
        const jogos = [];
        const hoje = new Date().toISOString().split('T')[0];

        // Buscar todas as seções de competição
        const sections = document.querySelectorAll('[class*="coupon-section"]');

        sections.forEach(section => {
            // Nome da competição
            const competicaoEl = section.querySelector('h3, [class*="competition-name"], [class*="title"]');
            const competicao = competicaoEl ? competicaoEl.textContent.trim() : '';

            // Buscar todas as linhas de jogos dentro desta seção
            const rows = section.querySelectorAll('[class*="coupon-row"], [class*="event-row"], tr');

            rows.forEach(row => {
                try {
                    // Buscar horário (formato "Hoje às HH:MM")
                    const horaEl = row.querySelector('[class*="time"], [class*="hora"]');
                    let horario = '';

                    if (horaEl) {
                        const textoHora = horaEl.textContent.trim();
                        const match = textoHora.match(/(\d{1,2}:\d{2})/);
                        if (match) {
                            horario = match[1];
                        }
                    }

                    // Buscar nomes dos times
                    const teamEls = row.querySelectorAll('[class*="team-name"], [class*="runner-name"], .runner');

                    if (teamEls.length >= 2 && horario) {
                        const mandante = teamEls[0].textContent.trim();
                        const visitante = teamEls[1].textContent.trim();

                        // Validar que são nomes válidos (não são números/odds)
                        if (mandante.length > 2 && visitante.length > 2 &&
                            !mandante.match(/^\d+[\.,]\d+$/) &&
                            !visitante.match(/^\d+[\.,]\d+$/)) {

                            jogos.push({
                                data: hoje,
                                horario: horario,
                                competicao: competicao,
                                mandante: mandante,
                                visitante: visitante
                            });
                        }
                    }
                } catch (e) {
                    // Ignorar erros em linhas individuais
                }
            });
        });

        // Remover duplicatas
        const unique = [];
        const seen = new Set();

        jogos.forEach(jogo => {
            const key = `${jogo.horario}|${jogo.mandante}|${jogo.visitante}`;
            if (!seen.has(key)) {
                seen.add(key);
                unique.push(jogo);
            }
        });

        return unique;
    })()
    """

    return js_code


def main():
    """Função principal."""
    print("=" * 80)
    print("🎯 EXTRATOR BETFAIR - JOGOS DE HOJE")
    print("=" * 80)
    print()
    print("📋 Este script precisa ser executado via MCP Playwright.")
    print("   Use o browser_evaluate do MCP para executar o código JavaScript.")
    print()

    js_code = extrair_jogos_via_mcp()

    print("📝 Código JavaScript para usar no MCP Playwright:")
    print("-" * 80)
    print(js_code)
    print("-" * 80)
    print()
    print("💡 Instruções:")
    print("   1. Navegue para: https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today")
    print("   2. Use browser_evaluate com o código acima")
    print("   3. Salve o resultado em um arquivo JSON")


if __name__ == "__main__":
    main()
