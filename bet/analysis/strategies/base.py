"""Base strategy class for betting strategies."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class BaseStrategy(ABC):
    """Base class for all betting strategies."""

    def __init__(self, name: str, description: str):
        """
        Initialize strategy.

        Args:
            name: Strategy name
            description: Strategy description
        """
        self.name = name
        self.description = description
        self.created_at = datetime.now()

    @abstractmethod
    def analyze(self, games: List[Dict]) -> List[Dict]:
        """
        Analyze games and return filtered results.

        Args:
            games: List of game dictionaries

        Returns:
            List of games that match strategy criteria
        """
        pass

    @abstractmethod
    def validate_game(self, game: Dict) -> bool:
        """
        Validate if a single game matches strategy criteria.

        Args:
            game: Game dictionary

        Returns:
            True if game matches criteria, False otherwise
        """
        pass

    def get_recommendation(self, game: Dict) -> Optional[str]:
        """
        Get betting recommendation for a game.

        Args:
            game: Game dictionary

        Returns:
            Recommendation string or None
        """
        if self.validate_game(game):
            return f"Strategy {self.name} recommends this game"
        return None

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
