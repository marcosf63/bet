"""ISC (Indice de Supremacia Casa) calculator."""


class ISCCalculator:
    """Calculator for ISC - Home Supremacy Index."""

    # ISC formula weights
    WEIGHT_PH = 0.35  # Home win probability
    WEIGHT_PAN = 0.25  # Away not win probability
    WEIGHT_FD = 0.25  # Differential force
    WEIGHT_FDE = 0.15  # Imbalance factor

    @staticmethod
    def calculate(odd_home_back: float, odd_away_lay: float, odd_draw_back: float) -> float | None:
        """
        Calculate ISC value.

        Formula: ISC = (PH × 0.35 + PAN × 0.25 + FD × 0.25 + FDE × 0.15) × 100

        Where:
        - PH: Home win implied probability (1/Odd_H_Back)
        - PAN: Away not win probability (1 - 1/Odd_A_Lay)
        - FD: Normalized differential force (Odd_A_Lay/Odd_H_Back)/10
        - FDE: Normalized imbalance factor (Odd_D_Back/Odd_H_Back)/3

        Args:
            odd_home_back: Home team back odd
            odd_away_lay: Away team lay odd
            odd_draw_back: Draw back odd

        Returns:
            ISC value or None if calculation not possible
        """
        if odd_home_back <= 0 or odd_away_lay <= 0:
            return None

        try:
            # PH: Home win implied probability
            ph = 1 / odd_home_back

            # PAN: Away not win probability
            pan = 1 - (1 / odd_away_lay)

            # FD: Normalized differential force
            fd = (odd_away_lay / odd_home_back) / 10

            # FDE: Normalized imbalance factor
            fde = (odd_draw_back / odd_home_back) / 3

            # Calculate ISC
            isc = (
                ph * ISCCalculator.WEIGHT_PH
                + pan * ISCCalculator.WEIGHT_PAN
                + fd * ISCCalculator.WEIGHT_FD
                + fde * ISCCalculator.WEIGHT_FDE
            ) * 100

            return round(isc, 1)
        except (ZeroDivisionError, ValueError):
            return None

    @staticmethod
    def get_level(isc: float) -> str:
        """
        Get ISC quality level.

        Args:
            isc: ISC value

        Returns:
            Quality level string
        """
        if isc > 75:
            return "excelente"
        elif isc >= 65:
            return "bom"
        elif isc >= 55:
            return "moderado"
        else:
            return "fraco"

    @staticmethod
    def get_description(isc: float) -> str:
        """
        Get ISC level description.

        Args:
            isc: ISC value

        Returns:
            Description string
        """
        level = ISCCalculator.get_level(isc)
        descriptions = {
            "excelente": "Forte dominância, ideal para Lay Away",
            "bom": "Boa dominância, considerar Lay Away",
            "moderado": "Analisar com cautela",
            "fraco": "Evitar Lay Away",
        }
        return descriptions.get(level, "Desconhecido")

    @staticmethod
    def add_to_game(game: dict) -> dict:
        """
        Add ISC calculation to game dictionary.

        Args:
            game: Game dictionary with odds

        Returns:
            Game dictionary with ISC added
        """
        odd_h = game.get("Odd_H_Back")
        odd_a_lay = game.get("Odd_A_Lay")
        odd_d = game.get("Odd_D_Back")

        if odd_h and odd_a_lay and odd_d:
            try:
                isc = ISCCalculator.calculate(float(odd_h), float(odd_a_lay), float(odd_d))
                if isc is not None:
                    game["ISC"] = f"{isc:.1f}"
                    game["ISC_Level"] = ISCCalculator.get_level(isc)
                else:
                    game["ISC"] = "N/A"
                    game["ISC_Level"] = "N/A"
            except (ValueError, TypeError):
                game["ISC"] = "N/A"
                game["ISC_Level"] = "N/A"
        else:
            game["ISC"] = "N/A"
            game["ISC_Level"] = "N/A"

        return game
