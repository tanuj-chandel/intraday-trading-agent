import pandas as pd
from typing import Dict, Any, List

class CorporateAction:
    def __init__(
        self,
        symbol: str,
        ex_date: str,
        action_type: str,  # "SPLIT", "BONUS", "DIVIDEND"
        ratio: float = 1.0, # For 1:10 split, ratio = 10.0; for 1:1 bonus, ratio = 2.0
        dividend_amount: float = 0.0
    ):
        self.symbol = symbol
        self.ex_date = ex_date
        self.action_type = action_type
        self.ratio = ratio
        self.dividend_amount = dividend_amount

class CorporateActionAdjuster:
    """
    Corporate Action Price Adjuster for Indian Equities.
    Adjusts historical OHLC prices backward to prevent false breakout/breakdown signals on Split/Bonus ex-dates.
    """

    @classmethod
    def adjust_series(
        cls,
        df: pd.DataFrame,
        actions: List[CorporateAction]
    ) -> pd.DataFrame:
        df_adj = df.copy()
        df_adj["is_corporate_action_adjusted"] = True

        for act in actions:
            ex_dt = pd.to_datetime(act.ex_date)
            mask = df_adj["timestamp"] < ex_dt

            if act.action_type in ["SPLIT", "BONUS"] and act.ratio > 1.0:
                # Divide past OHLC by split ratio
                df_adj.loc[mask, ["open", "high", "low", "close"]] /= act.ratio
                # Multiply past volume by split ratio
                df_adj.loc[mask, "volume"] *= act.ratio
            elif act.action_type == "DIVIDEND" and act.dividend_amount > 0:
                df_adj.loc[mask, ["open", "high", "low", "close"]] -= act.dividend_amount

        return df_adj
