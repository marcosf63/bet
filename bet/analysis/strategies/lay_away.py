"""Lay Away strategy - based on ISC (Indice de Supremacia Casa)."""

from typing import List, Dict
from bet.analysis.strategies.base import BaseStrategy


class LayAwayStrategy(BaseStrategy):
    """Strategy for Lay Away based on home team dominance (ISC)."""

    ISC_LEVELS = {
        "excelente": 75.0,
        "bom": 65.0,
        "moderado": 55.0,
    }

    def __init__(
        self,
        min_isc: float = 65.0,
        max_home_odd: float = 1.6,
        min_home_odd: float = 1.3,
    ):
        """
        Initialize Lay Away strategy.

        Args:
            min_isc: Minimum ISC value to consider
            max_home_odd: Maximum home odd
            min_home_odd: Minimum home odd
        """
        super().__init__(
            name="Lay Away",
            description=f"Lay away team when home has ISC >= {min_isc}"
        )
        self.min_isc = min_isc
        self.max_home_odd = max_home_odd
        self.min_home_odd = min_home_odd

    def validate_game(self, game: Dict) -> bool:
        """Check if game matches Lay Away criteria."""
        try:
            isc_str = game.get("ISC", "N/A")
            if isc_str == "N/A":
                return False

            isc = float(isc_str)
            odd_home = float(game.get("Odd_H_Back", 999))

            # Check ISC threshold
            if isc < self.min_isc:
                return False

            # Check home odd range
            if self.min_home_odd and odd_home < self.min_home_odd:
                return False
            if self.max_home_odd and odd_home > self.max_home_odd:
                return False

            return True
        except (ValueError, TypeError):
            return False

    def analyze(self, games: List[Dict]) -> List[Dict]:
        """Filter games suitable for Lay Away."""
        return [game for game in games if self.validate_game(game)]

    def get_isc_level(self, isc: float) -> str:
        """Get ISC quality level."""
        if isc > 75:
            return "excelente"
        elif isc >= 65:
            return "bom"
        elif isc >= 55:
            return "moderado"
        else:
            return "fraco"

    def get_recommendation(self, game: Dict) -> str:
        """Get specific recommendation for Lay Away."""
        if not self.validate_game(game):
            return None

        try:
            isc = float(game.get("ISC", 0))
            odd_away_lay = float(game.get("Odd_A_Lay", 0))
            level = self.get_isc_level(isc)

            return f"Lay Away at {odd_away_lay:.2f} (ISC: {isc:.1f} - {level})"
        except (ValueError, TypeError):
            return None
