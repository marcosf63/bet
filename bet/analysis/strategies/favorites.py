"""Favorites strategy - games with clear favorites."""

from bet.analysis.strategies.base import BaseStrategy


class FavoritesStrategy(BaseStrategy):
    """Strategy for finding games with clear favorites."""

    def __init__(self, max_odd: float = 1.5, fonte: str = "betfair"):
        """
        Initialize favorites strategy.

        Args:
            max_odd: Maximum odd to consider a team as favorite
            fonte: Data source (betfair, footystats, flashscore)
        """
        super().__init__(
            name="Favorites", description=f"Find games with clear favorites (odd <= {max_odd})"
        )
        self.max_odd = max_odd
        self.fonte = fonte

        # Define odd columns based on source
        if fonte == "betfair":
            self.odd_home_col = "Odd_H_Back"
            self.odd_away_col = "Odd_A_Back"
        else:
            self.odd_home_col = "Odd_H_FT"
            self.odd_away_col = "Odd_A_FT"

    def validate_game(self, game: dict) -> bool:
        """Check if game has a clear favorite."""
        try:
            odd_home = float(game.get(self.odd_home_col, 999))
            odd_away = float(game.get(self.odd_away_col, 999))
            return odd_home <= self.max_odd or odd_away <= self.max_odd
        except (ValueError, TypeError):
            return False

    def analyze(self, games: list[dict]) -> list[dict]:
        """Filter games with clear favorites."""
        return [game for game in games if self.validate_game(game)]

    def get_recommendation(self, game: dict) -> str:
        """Get specific recommendation for favorites."""
        if not self.validate_game(game):
            return None

        try:
            odd_home = float(game.get(self.odd_home_col, 999))
            odd_away = float(game.get(self.odd_away_col, 999))

            if odd_home <= self.max_odd and odd_home < odd_away:
                return f"Back Home at {odd_home}"
            elif odd_away <= self.max_odd:
                return f"Back Away at {odd_away}"
        except (ValueError, TypeError):
            pass

        return None
