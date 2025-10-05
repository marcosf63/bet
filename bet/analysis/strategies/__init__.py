"""Betting strategies package."""

from bet.analysis.strategies.base import BaseStrategy
from bet.analysis.strategies.favorites import FavoritesStrategy
from bet.analysis.strategies.halftime_zero import HalftimeZeroStrategy
from bet.analysis.strategies.lay_away import LayAwayStrategy

__all__ = [
    "BaseStrategy",
    "FavoritesStrategy",
    "HalftimeZeroStrategy",
    "LayAwayStrategy",
]
