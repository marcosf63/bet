#!/usr/bin/env python3
"""
Betfair - Jogos de Hoje (Script simplificado)
Extrai todos os jogos de hoje da Betfair via interceptação de API.
"""

import asyncio
import sys
from pathlib import Path

# Importar scraper unificado
sys.path.insert(0, str(Path(__file__).parent))
from betfair_scraper_unified import main

if __name__ == "__main__":
    print("\n🎯 BETFAIR - EXTRATOR DE JOGOS DE HOJE\n")

    try:
        jogos = asyncio.run(main())

        if jogos:
            print(f"\n✅ Sucesso: {len(jogos)} jogos extraídos!")
        else:
            print("\n⚠️  Nenhum jogo foi extraído")

    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
