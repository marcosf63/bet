"""Tests for bet.analysis.strategies module."""

from datetime import datetime

from bet.analysis.strategies.base import BaseStrategy
from bet.analysis.strategies.favorites import FavoritesStrategy


class ConcreteStrategy(BaseStrategy):
    """Concrete implementation of BaseStrategy for testing."""

    def __init__(self):
        super().__init__(name="Test Strategy", description="A test strategy")

    def analyze(self, games):
        return [g for g in games if self.validate_game(g)]

    def validate_game(self, game):
        return game.get("valid", False)


class TestBaseStrategy:
    """Tests for BaseStrategy abstract class."""

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = ConcreteStrategy()
        assert strategy.name == "Test Strategy"
        assert strategy.description == "A test strategy"
        assert isinstance(strategy.created_at, datetime)

    def test_validate_game(self):
        """Test validate_game method."""
        strategy = ConcreteStrategy()
        assert strategy.validate_game({"valid": True}) is True
        assert strategy.validate_game({"valid": False}) is False
        assert strategy.validate_game({}) is False

    def test_analyze(self):
        """Test analyze method."""
        strategy = ConcreteStrategy()
        games = [{"valid": True}, {"valid": False}, {"valid": True}]
        result = strategy.analyze(games)
        assert len(result) == 2
        assert all(g["valid"] for g in result)

    def test_get_recommendation_valid(self):
        """Test get_recommendation for valid game."""
        strategy = ConcreteStrategy()
        game = {"valid": True}
        recommendation = strategy.get_recommendation(game)
        assert recommendation is not None
        assert "Test Strategy" in recommendation

    def test_get_recommendation_invalid(self):
        """Test get_recommendation for invalid game."""
        strategy = ConcreteStrategy()
        game = {"valid": False}
        recommendation = strategy.get_recommendation(game)
        assert recommendation is None

    def test_strategy_repr(self):
        """Test strategy string representation."""
        strategy = ConcreteStrategy()
        repr_str = repr(strategy)
        assert "ConcreteStrategy" in repr_str
        assert "Test Strategy" in repr_str


class TestFavoritesStrategy:
    """Tests for FavoritesStrategy class."""

    def test_favorites_initialization_betfair(self):
        """Test favorites strategy initialization with Betfair source."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        assert strategy.name == "Favorites"
        assert strategy.max_odd == 1.5
        assert strategy.fonte == "betfair"
        assert strategy.odd_home_col == "Odd_H_Back"
        assert strategy.odd_away_col == "Odd_A_Back"

    def test_favorites_initialization_footystats(self):
        """Test favorites strategy initialization with FootyStats source."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="footystats")
        assert strategy.odd_home_col == "Odd_H_FT"
        assert strategy.odd_away_col == "Odd_A_FT"

    def test_favorites_initialization_default(self):
        """Test favorites strategy initialization with defaults."""
        strategy = FavoritesStrategy()
        assert strategy.max_odd == 1.5
        assert strategy.fonte == "betfair"

    def test_validate_game_home_favorite(self):
        """Test validation with home team as favorite."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": 1.4, "Odd_A_Back": 3.5}
        assert strategy.validate_game(game) is True

    def test_validate_game_away_favorite(self):
        """Test validation with away team as favorite."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": 3.5, "Odd_A_Back": 1.3}
        assert strategy.validate_game(game) is True

    def test_validate_game_no_favorite(self):
        """Test validation with no clear favorite."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": 2.5, "Odd_A_Back": 2.8}
        assert strategy.validate_game(game) is False

    def test_validate_game_missing_odds(self):
        """Test validation with missing odds."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        # With only home odd that is a favorite, it should pass
        game = {"Odd_H_Back": 1.4}
        assert strategy.validate_game(game) is True
        # With both missing, should fail
        game_empty = {}
        assert strategy.validate_game(game_empty) is False

    def test_validate_game_invalid_odds(self):
        """Test validation with invalid odds."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": "invalid", "Odd_A_Back": 3.5}
        assert strategy.validate_game(game) is False

    def test_validate_game_boundary_odd(self):
        """Test validation at max_odd boundary."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game1 = {"Odd_H_Back": 1.5, "Odd_A_Back": 3.5}
        game2 = {"Odd_H_Back": 1.51, "Odd_A_Back": 3.5}
        assert strategy.validate_game(game1) is True
        assert strategy.validate_game(game2) is False

    def test_analyze_multiple_games(self):
        """Test analyzing multiple games."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        games = [
            {"Odd_H_Back": 1.4, "Odd_A_Back": 3.5},  # Home favorite
            {"Odd_H_Back": 2.5, "Odd_A_Back": 2.8},  # No favorite
            {"Odd_H_Back": 3.5, "Odd_A_Back": 1.3},  # Away favorite
            {"Odd_H_Back": 1.6, "Odd_A_Back": 3.0},  # No favorite (above max)
        ]
        result = strategy.analyze(games)
        assert len(result) == 2
        assert result[0]["Odd_H_Back"] == 1.4
        assert result[1]["Odd_A_Back"] == 1.3

    def test_analyze_empty_list(self):
        """Test analyzing empty games list."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        result = strategy.analyze([])
        assert result == []

    def test_get_recommendation_home_favorite(self):
        """Test recommendation for home favorite."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": 1.4, "Odd_A_Back": 3.5}
        recommendation = strategy.get_recommendation(game)
        assert recommendation is not None
        assert "Back Home" in recommendation
        assert "1.4" in recommendation

    def test_get_recommendation_away_favorite(self):
        """Test recommendation for away favorite."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": 3.5, "Odd_A_Back": 1.3}
        recommendation = strategy.get_recommendation(game)
        assert recommendation is not None
        assert "Back Away" in recommendation
        assert "1.3" in recommendation

    def test_get_recommendation_both_favorites(self):
        """Test recommendation when both teams could be favorites."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": 1.4, "Odd_A_Back": 1.5}
        recommendation = strategy.get_recommendation(game)
        # Should recommend home since it has lower odd
        assert recommendation is not None
        assert "Back Home" in recommendation

    def test_get_recommendation_no_favorite(self):
        """Test recommendation when no favorite exists."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": 2.5, "Odd_A_Back": 2.8}
        recommendation = strategy.get_recommendation(game)
        assert recommendation is None

    def test_get_recommendation_invalid_data(self):
        """Test recommendation with invalid data."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")
        game = {"Odd_H_Back": "invalid", "Odd_A_Back": 3.5}
        recommendation = strategy.get_recommendation(game)
        assert recommendation is None

    def test_different_max_odd(self):
        """Test strategy with different max_odd values."""
        strategy_strict = FavoritesStrategy(max_odd=1.3, fonte="betfair")
        strategy_loose = FavoritesStrategy(max_odd=2.0, fonte="betfair")

        game = {"Odd_H_Back": 1.5, "Odd_A_Back": 3.5}

        assert strategy_strict.validate_game(game) is False
        assert strategy_loose.validate_game(game) is True

    def test_footystats_source(self):
        """Test strategy with FootyStats data source."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="footystats")
        game = {"Odd_H_FT": 1.4, "Odd_A_FT": 3.5}
        assert strategy.validate_game(game) is True
        recommendation = strategy.get_recommendation(game)
        assert "Back Home" in recommendation

    def test_flashscore_source(self):
        """Test strategy with FlashScore data source."""
        strategy = FavoritesStrategy(max_odd=1.5, fonte="flashscore")
        game = {"Odd_H_FT": 1.4, "Odd_A_FT": 3.5}
        assert strategy.validate_game(game) is True
