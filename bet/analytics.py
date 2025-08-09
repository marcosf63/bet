"""
Módulo de análise estatística e financeira para estratégias de trading.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import skew, kurtosis, gaussian_kde, jarque_bera
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class TradingAnalyzer:
    """Classe para análise completa de estratégias de trading."""
    
    def __init__(self, returns: np.ndarray, rf_rate: float = 0.02):
        """
        Inicializa o analisador.
        
        Args:
            returns: Array com os retornos das operações
            rf_rate: Taxa livre de risco anual (default: 2%)
        """
        self.returns = np.array(returns)
        self.rf_rate = rf_rate
        self.daily_rf = rf_rate / 252
        
    def basic_stats(self) -> Dict:
        """Calcula estatísticas básicas."""
        return {
            'count': len(self.returns),
            'mean': self.returns.mean(),
            'median': np.median(self.returns),
            'std': self.returns.std(ddof=1),
            'min': self.returns.min(),
            'max': self.returns.max(),
            'skewness': skew(self.returns),
            'kurtosis': kurtosis(self.returns),
            'q1': np.percentile(self.returns, 25),
            'q3': np.percentile(self.returns, 75)
        }
    
    def performance_metrics(self) -> Dict:
        """Calcula métricas de performance de trading."""
        wins = self.returns[self.returns > 0]
        losses = self.returns[self.returns < 0]
        
        return {
            'total_trades': len(self.returns),
            'win_rate': len(wins) / len(self.returns),
            'avg_win': wins.mean() if len(wins) > 0 else 0,
            'avg_loss': losses.mean() if len(losses) > 0 else 0,
            'profit_factor': abs(wins.sum() / losses.sum()) if len(losses) > 0 else np.inf,
            'expectancy': self.returns.mean(),
            'sharpe_ratio': self.sharpe_ratio(),
            'sortino_ratio': self.sortino_ratio(),
            'calmar_ratio': self.calmar_ratio(),
        }
    
    def sharpe_ratio(self) -> float:
        """Calcula o Índice de Sharpe."""
        excess_return = self.returns.mean() - self.daily_rf
        return excess_return / self.returns.std() * np.sqrt(252) if self.returns.std() > 0 else 0
    
    def sortino_ratio(self) -> float:
        """Calcula o Índice de Sortino."""
        excess_return = self.returns.mean() - self.daily_rf
        downside_returns = self.returns[self.returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        return excess_return / downside_std * np.sqrt(252) if downside_std > 0 else 0
    
    def calmar_ratio(self) -> float:
        """Calcula o Índice de Calmar."""
        annual_return = self.returns.mean() * 252
        max_dd = self.max_drawdown()
        return annual_return / abs(max_dd) if max_dd != 0 else 0
    
    def max_drawdown(self) -> float:
        """Calcula o drawdown máximo."""
        cumulative = np.cumsum(self.returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = cumulative - peak
        return drawdown.min()
    
    def value_at_risk(self, confidence: float = 0.05) -> Tuple[float, float]:
        """
        Calcula Value at Risk e Conditional VaR.
        
        Args:
            confidence: Nível de confiança (default: 5%)
            
        Returns:
            Tuple com (VaR, CVaR)
        """
        var = np.percentile(self.returns, confidence * 100)
        cvar = self.returns[self.returns <= var].mean()
        return var, cvar
    
    def kelly_criterion(self) -> float:
        """Calcula o critério de Kelly para sizing."""
        if self.returns.var() == 0:
            return 0
        return self.returns.mean() / self.returns.var()
    
    def monte_carlo_simulation(self, n_simulations: int = 10000, 
                             n_periods: int = 252) -> Dict:
        """
        Executa simulação Monte Carlo.
        
        Args:
            n_simulations: Número de simulações
            n_periods: Períodos por simulação
            
        Returns:
            Dicionário com resultados da simulação
        """
        # Usar KDE para resample mais realista
        kde = gaussian_kde(self.returns)
        simulations = kde.resample(n_simulations * n_periods).reshape(n_simulations, n_periods)
        
        final_returns = simulations.sum(axis=1)
        
        return {
            'prob_positive': (final_returns > 0).mean(),
            'mean_return': final_returns.mean(),
            'std_return': final_returns.std(),
            'percentile_5': np.percentile(final_returns, 5),
            'percentile_95': np.percentile(final_returns, 95),
            'worst_case': final_returns.min(),
            'best_case': final_returns.max()
        }
    
    def generate_report(self) -> str:
        """Gera relatório completo da análise."""
        basic = self.basic_stats()
        perf = self.performance_metrics()
        var_5, cvar_5 = self.value_at_risk()
        kelly = self.kelly_criterion()
        
        report = f"""
═══════════════════════════════════════════════════════════════════════
                    RELATÓRIO DE ANÁLISE DE TRADING
═══════════════════════════════════════════════════════════════════════

📊 ESTATÍSTICAS BÁSICAS:
   • Número de operações: {basic['count']}
   • Retorno médio: {basic['mean']:.4f}
   • Mediana: {basic['median']:.4f}
   • Desvio padrão: {basic['std']:.4f}
   • Assimetria: {basic['skewness']:.3f}
   • Curtose: {basic['kurtosis']:.3f}

🎯 MÉTRICAS DE PERFORMANCE:
   • Taxa de acerto: {perf['win_rate']*100:.1f}%
   • Ganho médio: {perf['avg_win']:.4f}
   • Perda média: {perf['avg_loss']:.4f}
   • Profit Factor: {perf['profit_factor']:.2f}
   • Expectância: {perf['expectancy']:.4f}
   • Sharpe Ratio: {perf['sharpe_ratio']:.2f}
   • Sortino Ratio: {perf['sortino_ratio']:.2f}
   • Calmar Ratio: {perf['calmar_ratio']:.2f}

⚠️  ANÁLISE DE RISCO:
   • Drawdown máximo: {self.max_drawdown():.4f}
   • VaR (5%): {var_5:.4f}
   • CVaR (5%): {cvar_5:.4f}
   • Kelly %: {kelly*100:.1f}%

💡 RECOMENDAÇÕES:
"""
        
        # Adicionar recomendações baseadas nas métricas
        if perf['expectancy'] > 0:
            report += "   ✅ Estratégia com expectância positiva\n"
        else:
            report += "   ❌ Estratégia com expectância negativa - revisar\n"
            
        if perf['sharpe_ratio'] > 1.0:
            report += "   ✅ Boa relação risco-retorno (Sharpe > 1.0)\n"
        else:
            report += "   ⚠️  Relação risco-retorno pode melhorar\n"
            
        if perf['win_rate'] > 0.6:
            report += "   ✅ Taxa de acerto satisfatória\n"
        else:
            report += "   ⚠️  Considerar melhorar filtros de entrada\n"
            
        if abs(self.max_drawdown()) < 0.1:
            report += "   ✅ Drawdown controlado\n"
        else:
            report += "   ⚠️  Implementar gestão de risco mais rigorosa\n"
        
        report += "\n═══════════════════════════════════════════════════════════════════════"
        
        return report
    
    def plot_analysis(self, figsize: Tuple[int, int] = (16, 12)):
        """Gera dashboard visual completo."""
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle('📈 Dashboard de Análise da Estratégia', fontsize=16, fontweight='bold')
        
        # 1. Histograma
        axes[0,0].hist(self.returns, bins=30, density=True, alpha=0.7, color='skyblue')
        axes[0,0].axvline(self.returns.mean(), color='red', linestyle='--', 
                         label=f'Média: {self.returns.mean():.3f}')
        axes[0,0].set_title('Distribuição dos Retornos')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Q-Q Plot
        stats.probplot(self.returns, dist="norm", plot=axes[0,1])
        axes[0,1].set_title('Q-Q Plot')
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. Boxplot
        axes[0,2].boxplot(self.returns, patch_artist=True)
        axes[0,2].set_title('Box Plot')
        axes[0,2].grid(True, alpha=0.3)
        
        # 4. Curva de capital
        capital = np.cumsum(self.returns)
        axes[1,0].plot(capital, color='green', linewidth=2)
        axes[1,0].fill_between(range(len(capital)), capital, alpha=0.3, color='green')
        axes[1,0].set_title('Curva de Capital')
        axes[1,0].grid(True, alpha=0.3)
        
        # 5. Drawdown
        peak = np.maximum.accumulate(capital)
        drawdown = (capital - peak) / peak * 100
        axes[1,1].fill_between(range(len(drawdown)), drawdown, 0, alpha=0.7, color='red')
        axes[1,1].set_title('Drawdown (%)')
        axes[1,1].grid(True, alpha=0.3)
        
        # 6. Rolling Sharpe
        window = min(30, len(self.returns)//4)
        if window >= 10:
            rolling_sharpe = pd.Series(self.returns).rolling(window).apply(
                lambda x: (x.mean() - self.daily_rf) / x.std() * np.sqrt(252) if x.std() > 0 else 0
            )
            axes[1,2].plot(rolling_sharpe, color='purple', linewidth=2)
            axes[1,2].axhline(0, color='red', linestyle='--', alpha=0.7)
            axes[1,2].set_title(f'Sharpe Móvel ({window})')
            axes[1,2].grid(True, alpha=0.3)
        else:
            axes[1,2].text(0.5, 0.5, 'Dados insuficientes\npara Sharpe móvel', 
                          ha='center', va='center', transform=axes[1,2].transAxes)
            axes[1,2].set_title('Sharpe Móvel')
        
        plt.tight_layout()
        return fig


def analyze_strategy(data_path: str, returns_column: str = 'Lucro_Lay') -> TradingAnalyzer:
    """
    Função utilitária para análise rápida de estratégia.
    
    Args:
        data_path: Caminho para o arquivo de dados
        returns_column: Nome da coluna com os retornos
        
    Returns:
        Instância do TradingAnalyzer
    """
    try:
        df = pd.read_csv(data_path)
        returns = df[returns_column].dropna().values
        return TradingAnalyzer(returns)
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {data_path}")
    except KeyError:
        raise KeyError(f"Coluna '{returns_column}' não encontrada no arquivo")