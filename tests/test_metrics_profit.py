"""Tests for bet.analysis.metrics.profit module."""

from bet.analysis.metrics.profit import ProfitCalculator


class TestCalculateLayProfit:
    """Tests for calculate_lay_profit method."""

    def test_lay_profit_win(self):
        """Test lay bet profit when lay wins."""
        profit = ProfitCalculator.calculate_lay_profit(
            stake=100, odd_lay=2.5, commission=0.05, win=True
        )
        # Profit = stake * (1 - commission) = 100 * 0.95 = 95
        assert profit == 95.0

    def test_lay_profit_loss(self):
        """Test lay bet loss when lay loses."""
        profit = ProfitCalculator.calculate_lay_profit(
            stake=100, odd_lay=2.5, commission=0.05, win=False
        )
        # Loss = -(odd - 1) * stake = -(2.5 - 1) * 100 = -150
        assert profit == -150.0

    def test_lay_profit_no_commission(self):
        """Test lay bet with no commission."""
        profit = ProfitCalculator.calculate_lay_profit(
            stake=100, odd_lay=2.0, commission=0.0, win=True
        )
        assert profit == 100.0

    def test_lay_profit_high_commission(self):
        """Test lay bet with high commission."""
        profit = ProfitCalculator.calculate_lay_profit(
            stake=100, odd_lay=2.0, commission=0.10, win=True
        )
        # Profit = 100 * (1 - 0.10) = 90
        assert profit == 90.0


class TestCalculateBackProfit:
    """Tests for calculate_back_profit method."""

    def test_back_profit_win(self):
        """Test back bet profit when back wins."""
        profit = ProfitCalculator.calculate_back_profit(stake=100, odd_back=2.5, win=True)
        # Profit = (odd - 1) * stake = (2.5 - 1) * 100 = 150
        assert profit == 150.0

    def test_back_profit_loss(self):
        """Test back bet loss when back loses."""
        profit = ProfitCalculator.calculate_back_profit(stake=100, odd_back=2.5, win=False)
        # Loss = -stake = -100
        assert profit == -100

    def test_back_profit_low_odd(self):
        """Test back bet with low odd."""
        profit = ProfitCalculator.calculate_back_profit(stake=100, odd_back=1.5, win=True)
        # Profit = (1.5 - 1) * 100 = 50
        assert profit == 50.0

    def test_back_profit_high_odd(self):
        """Test back bet with high odd."""
        profit = ProfitCalculator.calculate_back_profit(stake=100, odd_back=5.0, win=True)
        # Profit = (5.0 - 1) * 100 = 400
        assert profit == 400.0


class TestCalculateGreenUp:
    """Tests for calculate_green_up method."""

    def test_green_up_basic(self):
        """Test basic green up calculation."""
        result = ProfitCalculator.calculate_green_up(
            stake_back=100, odd_back=2.0, odd_lay=1.8, commission=0.05
        )
        assert "stake_lay" in result
        assert "profit_if_back_wins" in result
        assert "profit_if_lay_wins" in result
        assert "average_profit" in result
        assert result["stake_lay"] > 0

    def test_green_up_equal_odds(self):
        """Test green up with equal back and lay odds."""
        result = ProfitCalculator.calculate_green_up(
            stake_back=100, odd_back=2.0, odd_lay=2.0, commission=0.05
        )
        # stake_lay = liability / (odd_lay - 1) = 100 / 1 = 100
        assert result["stake_lay"] == 100.0

    def test_green_up_no_commission(self):
        """Test green up with no commission."""
        result = ProfitCalculator.calculate_green_up(
            stake_back=100, odd_back=2.5, odd_lay=2.0, commission=0.0
        )
        assert result["stake_lay"] > 0
        assert "profit_if_back_wins" in result

    def test_green_up_calculation_accuracy(self):
        """Test green up calculation accuracy."""
        result = ProfitCalculator.calculate_green_up(
            stake_back=100, odd_back=3.0, odd_lay=2.5, commission=0.05
        )
        # liability = 100 * (3.0 - 1) = 200
        # stake_lay = 200 / (2.5 - 1) = 200 / 1.5 = 133.33
        assert abs(result["stake_lay"] - 133.33) < 0.01


class TestCalculateROI:
    """Tests for calculate_roi method."""

    def test_roi_positive(self):
        """Test ROI with positive profit."""
        roi = ProfitCalculator.calculate_roi(profit=50, stake=100)
        # ROI = (50 / 100) * 100 = 50%
        assert roi == 50.0

    def test_roi_negative(self):
        """Test ROI with negative profit (loss)."""
        roi = ProfitCalculator.calculate_roi(profit=-30, stake=100)
        # ROI = (-30 / 100) * 100 = -30%
        assert roi == -30.0

    def test_roi_zero_profit(self):
        """Test ROI with zero profit."""
        roi = ProfitCalculator.calculate_roi(profit=0, stake=100)
        assert roi == 0.0

    def test_roi_zero_stake(self):
        """Test ROI with zero stake."""
        roi = ProfitCalculator.calculate_roi(profit=50, stake=0)
        assert roi == 0.0

    def test_roi_high_profit(self):
        """Test ROI with high profit."""
        roi = ProfitCalculator.calculate_roi(profit=200, stake=100)
        # ROI = (200 / 100) * 100 = 200%
        assert roi == 200.0


class TestCalculateKellyCriterion:
    """Tests for calculate_kelly_criterion method."""

    def test_kelly_positive_edge(self):
        """Test Kelly criterion with positive edge."""
        stake = ProfitCalculator.calculate_kelly_criterion(probability=0.6, odd=2.5, bankroll=1000)
        assert stake is not None
        assert stake > 0
        assert stake <= 1000

    def test_kelly_no_edge(self):
        """Test Kelly criterion with no edge."""
        # Fair odd for 50% probability is 2.0
        stake = ProfitCalculator.calculate_kelly_criterion(probability=0.5, odd=2.0, bankroll=1000)
        # Should return None or very small value
        assert stake is None or stake == 0

    def test_kelly_negative_edge(self):
        """Test Kelly criterion with negative edge."""
        stake = ProfitCalculator.calculate_kelly_criterion(probability=0.4, odd=2.0, bankroll=1000)
        # Negative Kelly should return None
        assert stake is None

    def test_kelly_invalid_probability_zero(self):
        """Test Kelly criterion with invalid probability (0)."""
        stake = ProfitCalculator.calculate_kelly_criterion(probability=0, odd=2.5, bankroll=1000)
        assert stake is None

    def test_kelly_invalid_probability_one(self):
        """Test Kelly criterion with invalid probability (1)."""
        stake = ProfitCalculator.calculate_kelly_criterion(probability=1, odd=2.5, bankroll=1000)
        assert stake is None

    def test_kelly_invalid_odd(self):
        """Test Kelly criterion with invalid odd (<=1)."""
        stake = ProfitCalculator.calculate_kelly_criterion(probability=0.6, odd=1.0, bankroll=1000)
        assert stake is None

        stake = ProfitCalculator.calculate_kelly_criterion(probability=0.6, odd=0.5, bankroll=1000)
        assert stake is None

    def test_kelly_fractional(self):
        """Test that Kelly uses fractional (0.25) for safety."""
        # With probability=0.7, odd=2.5, bankroll=1000
        # Full Kelly: f = (1.5 * 0.7 - 0.3) / 1.5 = 0.50
        # Fractional Kelly (0.25): 0.50 * 0.25 = 0.125
        # Stake = 1000 * 0.125 = 125
        stake = ProfitCalculator.calculate_kelly_criterion(probability=0.7, odd=2.5, bankroll=1000)
        assert stake is not None
        # Should be around 125 with fractional Kelly
        assert 100 < stake < 150

    def test_kelly_high_probability(self):
        """Test Kelly criterion with high win probability."""
        stake = ProfitCalculator.calculate_kelly_criterion(probability=0.8, odd=2.0, bankroll=1000)
        assert stake is not None
        assert stake > 0

    def test_kelly_different_bankrolls(self):
        """Test Kelly criterion scales with bankroll."""
        stake1 = ProfitCalculator.calculate_kelly_criterion(probability=0.6, odd=2.5, bankroll=1000)
        stake2 = ProfitCalculator.calculate_kelly_criterion(probability=0.6, odd=2.5, bankroll=2000)
        assert stake1 is not None
        assert stake2 is not None
        # stake2 should be approximately double stake1
        assert abs(stake2 - (stake1 * 2)) < 0.1
