"""Analysis package for betting strategies and metrics."""

# Import analytics module (if available)
try:
    from bet.analysis.analytics import TradingAnalyzer

    ANALYTICS_AVAILABLE = True
except ImportError:
    TradingAnalyzer = None
    ANALYTICS_AVAILABLE = False

# Import strategies
# Import metrics
from bet.analysis.metrics import ISCCalculator, ProfitCalculator
from bet.analysis.strategies import (
    BaseStrategy,
    FavoritesStrategy,
    HalftimeZeroStrategy,
    LayAwayStrategy,
)

__all__ = [
    "TradingAnalyzer",
    "ANALYTICS_AVAILABLE",
    "BaseStrategy",
    "FavoritesStrategy",
    "HalftimeZeroStrategy",
    "LayAwayStrategy",
    "ISCCalculator",
    "ProfitCalculator",
]
