#!/usr/bin/env python3
"""
Script para análise rápida de estratégias de trading.
Uso: python scripts/analisar_estrategia.py [caminho_dados] [coluna_retornos]
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from bet.analytics import analyze_strategy
import matplotlib.pyplot as plt


def main():
    """Executa análise completa de estratégia."""
    
    # Parâmetros padrão
    data_path = "notebooks/dados/lucro_por_operacao.csv"
    returns_column = "Lucro_Lay"
    
    # Permitir argumentos de linha de comando
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    if len(sys.argv) > 2:
        returns_column = sys.argv[2]
    
    print(f"📊 Analisando estratégia...")
    print(f"📁 Arquivo: {data_path}")
    print(f"📈 Coluna: {returns_column}")
    print("=" * 60)
    
    try:
        # Criar analisador
        analyzer = analyze_strategy(data_path, returns_column)
        
        # Gerar e exibir relatório
        report = analyzer.generate_report()
        print(report)
        
        # Executar simulação Monte Carlo
        print("\n🎲 SIMULAÇÃO MONTE CARLO (1000 operações):")
        print("=" * 50)
        mc_results = analyzer.monte_carlo_simulation(n_periods=1000)
        
        print(f"   • Probabilidade de lucro: {mc_results['prob_positive']*100:.1f}%")
        print(f"   • Retorno médio esperado: {mc_results['mean_return']:.2f}")
        print(f"   • Cenário otimista (95%): {mc_results['percentile_95']:.2f}")
        print(f"   • Cenário pessimista (5%): {mc_results['percentile_5']:.2f}")
        print(f"   • Pior caso: {mc_results['worst_case']:.2f}")
        print(f"   • Melhor caso: {mc_results['best_case']:.2f}")
        
        # Gerar gráficos
        print("\n📈 Gerando visualizações...")
        fig = analyzer.plot_analysis()
        
        # Salvar gráfico
        output_path = f"analise_{returns_column.lower()}.png"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 Gráficos salvos em: {output_path}")
        
        # Mostrar gráficos (se disponível)
        try:
            plt.show()
        except:
            print("⚠️  Interface gráfica não disponível")
            
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        return 1
    
    print("\n✅ Análise concluída com sucesso!")
    return 0


if __name__ == "__main__":
    exit(main())