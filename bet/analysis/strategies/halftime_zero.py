"""Halftime 0x0 strategy - games likely to be 0-0 at halftime."""

from bet.analysis.strategies.base import BaseStrategy


class HalftimeZeroStrategy(BaseStrategy):
    """Strategy for finding games with potential 0x0 at halftime."""

    def __init__(
        self, min_odd_over: float = 2.0, min_odd_btts: float = 2.0, fonte: str = "betfair"
    ):
        """
        Initialize halftime zero strategy.

        Args:
            min_odd_over: Minimum odd for Over 2.5 market
            min_odd_btts: Minimum odd for BTTS market
            fonte: Data source
        """
        super().__init__(
            name="Halftime 0x0", description="Find games with high probability of 0-0 at halftime"
        )
        self.min_odd_over = min_odd_over
        self.min_odd_btts = min_odd_btts
        self.fonte = fonte

        # Define columns based on source
        if fonte == "betfair":
            self.odd_over_col = "Odd_Over25_FT_Back"
            self.odd_btts_col = "Odd_BTTS_Yes_Back"
        else:
            self.odd_over_col = "Odd_Over05_HT"
            self.odd_btts_col = "Odd_BTTS_No"

    def validate_game(self, game: dict) -> bool:
        """Check if game matches halftime 0x0 criteria."""
        try:
            odd_over = float(game.get(self.odd_over_col, 0))
            odd_btts = float(game.get(self.odd_btts_col, 0))
            return odd_over > self.min_odd_over and odd_btts > self.min_odd_btts
        except (ValueError, TypeError):
            return False

    def analyze(self, games: list[dict]) -> list[dict]:
        """Filter games with halftime 0x0 potential."""
        return [game for game in games if self.validate_game(game)]

    def get_recommendation(self, game: dict) -> str:
        """Get specific recommendation for halftime 0x0."""
        if not self.validate_game(game):
            return None

        return "Consider betting 0x0 at halftime or Under 0.5 HT"
