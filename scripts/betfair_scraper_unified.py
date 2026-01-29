#!/usr/bin/env python3
"""
Betfair Scraper Unificado
Tenta interceptar API primeiro, se falhar usa extração HTML como fallback.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# Importar o scraper de API
sys.path.insert(0, str(Path(__file__).parent))
from betfair_scraper_api import BetfairAPIScraper


async def main():
    """Executa scraping unificado."""

    print("=" * 100)
    print("🎯 BETFAIR SCRAPER UNIFICADO - API + HTML FALLBACK")
    print("=" * 100)
    print()

    url = 'https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today'

    # ===========================================
    # FASE 1: Tentar via API (método preferido)
    # ===========================================
    print("📡 FASE 1: Tentando extração via API...")
    print("-" * 100)

    try:
        api_scraper = BetfairAPIScraper()
        jogos, api_responses = await api_scraper.scrape(url)

        if len(jogos) > 0:
            print(f"\n✅ SUCESSO via API: {len(jogos)} jogos extraídos")

            # Salvar dados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/betfair_jogos_final_{timestamp}.json"

            # Adicionar metadados
            dados_completos = {
                'metadata': {
                    'data_extracao': datetime.now().isoformat(),
                    'metodo': 'API',
                    'total_jogos': len(jogos),
                    'url': url
                },
                'jogos': jogos
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dados_completos, f, ensure_ascii=False, indent=2)

            print(f"💾 Dados salvos em: {output_file}")

            # Exibir resumo
            print("\n" + "=" * 100)
            print("📊 RESUMO DOS JOGOS EXTRAÍDOS")
            print("=" * 100)

            # Agrupar por horário
            jogos_por_hora = {}
            for jogo in jogos:
                hora = jogo.get('horario', '??:??')
                if hora not in jogos_por_hora:
                    jogos_por_hora[hora] = []
                jogos_por_hora[hora].append(jogo)

            print(f"\nTotal: {len(jogos)} jogos")
            print(f"Horários diferentes: {len(jogos_por_hora)}")
            print("\nDistribuição por horário:")
            for hora in sorted(jogos_por_hora.keys()):
                print(f"  {hora}: {len(jogos_por_hora[hora])} jogos")

            print("\n📋 JOGOS:")
            print("-" * 100)
            print(f"{'#':<4} {'HORÁRIO':<10} {'MANDANTE':<35} {'VISITANTE':<35}")
            print("-" * 100)

            # Ordenar por horário
            jogos_ordenados = sorted(jogos, key=lambda x: x.get('horario', '99:99'))

            for i, jogo in enumerate(jogos_ordenados, 1):
                hora = jogo.get('horario', '??:??')
                mandante = jogo.get('mandante', 'N/A')[:33]
                visitante = jogo.get('visitante', 'N/A')[:33]
                print(f"{i:<4} {hora:<10} {mandante:<35} {visitante:<35}")

            print("-" * 100)
            print("\n✅ Extração concluída com sucesso!")

            return jogos

        else:
            print("\n⚠️  API não retornou jogos, tentando fallback HTML...")
            raise Exception("Fallback para HTML")

    except Exception as e:
        print(f"\n❌ Erro na extração via API: {str(e)[:100]}")

        # ===========================================
        # FASE 2: Fallback - Extração HTML
        # ===========================================
        print("\n" + "=" * 100)
        print("📄 FASE 2: Fallback - Extração HTML")
        print("=" * 100)
        print("\n⚠️  A extração HTML ainda não foi implementada.")
        print("   Por enquanto, apenas a extração via API está disponível.")
        print("\n💡 Sugestão: Execute novamente o script para tentar via API.")

        return []


if __name__ == "__main__":
    jogos = asyncio.run(main())

    if jogos:
        print(f"\n🎉 Processo concluído: {len(jogos)} jogos extraídos")
        sys.exit(0)
    else:
        print("\n❌ Nenhum jogo foi extraído")
        sys.exit(1)
