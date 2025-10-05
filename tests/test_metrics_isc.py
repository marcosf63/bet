"""Tests for bet.analysis.metrics.isc module."""

from bet.analysis.metrics.isc import ISCCalculator


class TestISCCalculator:
    """Tests for ISCCalculator class."""

    def test_calculate_basic(self):
        """Test basic ISC calculation."""
        isc = ISCCalculator.calculate(odd_home_back=1.5, odd_away_lay=3.5, odd_draw_back=3.8)
        assert isc is not None
        assert isinstance(isc, float)
        assert isc > 0

    def test_calculate_high_isc(self):
        """Test ISC calculation with clear favorite."""
        isc = ISCCalculator.calculate(odd_home_back=1.3, odd_away_lay=5.0, odd_draw_back=4.5)
        assert isc is not None
        assert isc >= 70  # Should be at least good or excellent

    def test_calculate_low_isc(self):
        """Test ISC calculation with balanced odds."""
        isc = ISCCalculator.calculate(odd_home_back=2.5, odd_away_lay=2.8, odd_draw_back=3.2)
        assert isc is not None
        assert isc < 60  # Should be weak or moderate

    def test_calculate_zero_odd_home(self):
        """Test ISC calculation with zero home odd."""
        isc = ISCCalculator.calculate(odd_home_back=0, odd_away_lay=3.5, odd_draw_back=3.8)
        assert isc is None

    def test_calculate_zero_odd_away(self):
        """Test ISC calculation with zero away odd."""
        isc = ISCCalculator.calculate(odd_home_back=1.5, odd_away_lay=0, odd_draw_back=3.8)
        assert isc is None

    def test_calculate_negative_odd(self):
        """Test ISC calculation with negative odd."""
        isc = ISCCalculator.calculate(odd_home_back=-1.5, odd_away_lay=3.5, odd_draw_back=3.8)
        assert isc is None

    def test_get_level_excellent(self):
        """Test ISC level classification for excellent."""
        assert ISCCalculator.get_level(80) == "excelente"
        assert ISCCalculator.get_level(76) == "excelente"

    def test_get_level_good(self):
        """Test ISC level classification for good."""
        assert ISCCalculator.get_level(75) == "bom"
        assert ISCCalculator.get_level(70) == "bom"
        assert ISCCalculator.get_level(65) == "bom"

    def test_get_level_moderate(self):
        """Test ISC level classification for moderate."""
        assert ISCCalculator.get_level(64) == "moderado"
        assert ISCCalculator.get_level(60) == "moderado"
        assert ISCCalculator.get_level(55) == "moderado"

    def test_get_level_weak(self):
        """Test ISC level classification for weak."""
        assert ISCCalculator.get_level(54) == "fraco"
        assert ISCCalculator.get_level(50) == "fraco"
        assert ISCCalculator.get_level(30) == "fraco"

    def test_get_description_excellent(self):
        """Test ISC description for excellent level."""
        description = ISCCalculator.get_description(80)
        assert description == "Forte dominância, ideal para Lay Away"

    def test_get_description_good(self):
        """Test ISC description for good level."""
        description = ISCCalculator.get_description(70)
        assert description == "Boa dominância, considerar Lay Away"

    def test_get_description_moderate(self):
        """Test ISC description for moderate level."""
        description = ISCCalculator.get_description(60)
        assert description == "Analisar com cautela"

    def test_get_description_weak(self):
        """Test ISC description for weak level."""
        description = ISCCalculator.get_description(50)
        assert description == "Evitar Lay Away"

    def test_add_to_game_valid(self):
        """Test adding ISC to game dictionary with valid odds."""
        game = {
            "Home": "Team A",
            "Away": "Team B",
            "Odd_H_Back": 1.5,
            "Odd_A_Lay": 3.5,
            "Odd_D_Back": 3.8,
        }
        result = ISCCalculator.add_to_game(game)
        assert "ISC" in result
        assert "ISC_Level" in result
        assert result["ISC"] != "N/A"
        assert result["ISC_Level"] in ["excelente", "bom", "moderado", "fraco"]

    def test_add_to_game_missing_odds(self):
        """Test adding ISC to game with missing odds."""
        game = {"Home": "Team A", "Away": "Team B", "Odd_H_Back": 1.5}
        result = ISCCalculator.add_to_game(game)
        assert result["ISC"] == "N/A"
        assert result["ISC_Level"] == "N/A"

    def test_add_to_game_invalid_odds(self):
        """Test adding ISC to game with invalid odds."""
        game = {
            "Home": "Team A",
            "Away": "Team B",
            "Odd_H_Back": "invalid",
            "Odd_A_Lay": 3.5,
            "Odd_D_Back": 3.8,
        }
        result = ISCCalculator.add_to_game(game)
        assert result["ISC"] == "N/A"
        assert result["ISC_Level"] == "N/A"

    def test_add_to_game_zero_odds(self):
        """Test adding ISC to game with zero odds."""
        game = {
            "Home": "Team A",
            "Away": "Team B",
            "Odd_H_Back": 0,
            "Odd_A_Lay": 3.5,
            "Odd_D_Back": 3.8,
        }
        result = ISCCalculator.add_to_game(game)
        assert result["ISC"] == "N/A"
        assert result["ISC_Level"] == "N/A"

    def test_calculate_formula_components(self):
        """Test ISC formula components calculation."""
        # Known values for testing
        odd_home_back = 1.5
        odd_away_lay = 3.5
        odd_draw_back = 3.8

        # Calculate components manually
        ph = 1 / odd_home_back  # ~0.667
        pan = 1 - (1 / odd_away_lay)  # ~0.714
        fd = (odd_away_lay / odd_home_back) / 10  # ~0.233
        fde = (odd_draw_back / odd_home_back) / 3  # ~0.844

        expected_isc = (
            ph * ISCCalculator.WEIGHT_PH
            + pan * ISCCalculator.WEIGHT_PAN
            + fd * ISCCalculator.WEIGHT_FD
            + fde * ISCCalculator.WEIGHT_FDE
        ) * 100

        calculated_isc = ISCCalculator.calculate(odd_home_back, odd_away_lay, odd_draw_back)

        assert calculated_isc is not None
        assert abs(calculated_isc - round(expected_isc, 1)) < 0.1

    def test_weights_sum_to_one(self):
        """Test that ISC weights sum to 1.0."""
        total_weight = (
            ISCCalculator.WEIGHT_PH
            + ISCCalculator.WEIGHT_PAN
            + ISCCalculator.WEIGHT_FD
            + ISCCalculator.WEIGHT_FDE
        )
        assert abs(total_weight - 1.0) < 0.001
