"""Profit calculation metrics for betting strategies."""

from typing import Dict, Optional


class ProfitCalculator:
    """Calculator for profit/loss in betting operations."""

    @staticmethod
    def calculate_lay_profit(
        stake: float,
        odd_lay: float,
        commission: float = 0.05,
        win: bool = True
    ) -> float:
        """
        Calculate profit/loss for a lay bet.

        Args:
            stake: Stake amount
            odd_lay: Lay odd
            commission: Commission rate (default 5%)
            win: True if lay bet won, False if lost

        Returns:
            Profit (positive) or loss (negative)
        """
        if win:
            # Lay wins: profit is the stake minus commission
            profit = stake * (1 - commission)
            return round(profit, 2)
        else:
            # Lay loses: loss is (odd - 1) * stake
            loss = -(odd_lay - 1) * stake
            return round(loss, 2)

    @staticmethod
    def calculate_back_profit(
        stake: float,
        odd_back: float,
        win: bool = True
    ) -> float:
        """
        Calculate profit/loss for a back bet.

        Args:
            stake: Stake amount
            odd_back: Back odd
            win: True if back bet won, False if lost

        Returns:
            Profit (positive) or loss (negative)
        """
        if win:
            # Back wins: profit is (odd - 1) * stake
            profit = (odd_back - 1) * stake
            return round(profit, 2)
        else:
            # Back loses: loss is the stake
            return -stake

    @staticmethod
    def calculate_green_up(
        stake_back: float,
        odd_back: float,
        odd_lay: float,
        commission: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate green up (equal profit) strategy.

        Args:
            stake_back: Initial back stake
            odd_back: Back odd
            odd_lay: Lay odd for closing position
            commission: Commission rate

        Returns:
            Dictionary with lay stake and profit calculations
        """
        # Calculate liability for back bet
        liability = stake_back * (odd_back - 1)

        # Calculate lay stake needed for green up
        stake_lay = liability / (odd_lay - 1)

        # Calculate profit if back wins
        profit_if_back_wins = liability - (stake_lay * (1 - commission))

        # Calculate profit if lay wins (back loses)
        profit_if_lay_wins = stake_lay * (1 - commission) - stake_back

        return {
            "stake_lay": round(stake_lay, 2),
            "profit_if_back_wins": round(profit_if_back_wins, 2),
            "profit_if_lay_wins": round(profit_if_lay_wins, 2),
            "average_profit": round((profit_if_back_wins + profit_if_lay_wins) / 2, 2)
        }

    @staticmethod
    def calculate_roi(profit: float, stake: float) -> float:
        """
        Calculate Return on Investment.

        Args:
            profit: Total profit
            stake: Total stake

        Returns:
            ROI as percentage
        """
        if stake == 0:
            return 0.0
        return round((profit / stake) * 100, 2)

    @staticmethod
    def calculate_kelly_criterion(
        probability: float,
        odd: float,
        bankroll: float
    ) -> Optional[float]:
        """
        Calculate optimal stake using Kelly Criterion.

        Formula: f = (bp - q) / b
        Where:
        - f = fraction of bankroll to bet
        - b = odd - 1
        - p = probability of winning
        - q = probability of losing (1 - p)

        Args:
            probability: Win probability (0-1)
            odd: Betting odd
            bankroll: Total bankroll

        Returns:
            Recommended stake or None
        """
        if probability <= 0 or probability >= 1 or odd <= 1:
            return None

        b = odd - 1
        q = 1 - probability

        # Kelly fraction
        f = (b * probability - q) / b

        # Only bet if Kelly is positive
        if f <= 0:
            return None

        # Use fractional Kelly (e.g., 0.25) for safety
        fractional_kelly = f * 0.25

        return round(bankroll * fractional_kelly, 2)
