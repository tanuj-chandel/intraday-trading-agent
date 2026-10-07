import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

class TechnicalAnalysis:
    """
    Reusable, modular technical analysis calculations.
    Every calculation is pure and unit-testable.
    """

    @staticmethod
    def calculate_sma(series: pd.Series, period: int = 20) -> pd.Series:
        """Simple Moving Average"""
        return series.rolling(window=period, min_periods=1).mean()

    @staticmethod
    def calculate_ema(series: pd.Series, period: int = 9) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index (Wilder's RSI).
        """
        delta = close.diff()
        gain = (delta.where(delta > 0, 0.0)).copy()
        loss = (-delta.where(delta < 0, 0.0)).copy()

        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)

    @staticmethod
    def calculate_macd(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence.
        Returns (macd_line, signal_line, histogram)
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        macd_hist = macd_line - signal_line
        return macd_line, signal_line, macd_hist

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Intraday Volume Weighted Average Price.
        VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
        """
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        pv = typical_price * df["volume"]
        
        if "timestamp" in df.columns:
            dates = pd.to_datetime(df["timestamp"]).dt.date
            temp_df = pd.DataFrame({
                "pv": pv,
                "vol": df["volume"],
                "date": dates
            }, index=df.index)
            cum_pv = temp_df.groupby("date")["pv"].cumsum()
            cum_vol = temp_df.groupby("date")["vol"].cumsum()
            vwap = cum_pv / (cum_vol + 1e-10)
            return pd.Series(vwap, index=df.index)
        else:
            return pd.Series((pv.cumsum()) / (df["volume"].cumsum() + 1e-10), index=df.index)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high = df["high"]
        low = df["low"]
        close_prev = df["close"].shift(1)
        
        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        return atr.fillna(tr.mean())

    @staticmethod
    def calculate_bollinger_bands(
        close: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands.
        Returns (upper_band, middle_band, lower_band)
        """
        middle_band = close.rolling(window=period, min_periods=1).mean()
        rolling_std = close.rolling(window=period, min_periods=1).std().fillna(0.0)
        upper_band = middle_band + (std_dev * rolling_std)
        lower_band = middle_band - (std_dev * rolling_std)
        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_rvol(volume: pd.Series, period: int = 20) -> pd.Series:
        """Relative Volume (current volume / moving average of volume)"""
        vol_ma = volume.rolling(window=period, min_periods=1).mean()
        return (volume / (vol_ma + 1e-10)).fillna(1.0)

    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
        """Calculates dynamic intraday support & resistance levels."""
        recent_low = df["low"].tail(window).min()
        recent_high = df["high"].tail(window).max()
        return float(recent_low), float(recent_high)

    @classmethod
    def detect_breakout(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects if current bar is breaking out of recent range with volume confirmation.
        """
        if len(df) < 25:
            return {"breakout": False, "breakdown": False, "rvol": 1.0}
            
        current = df.iloc[-1]
        lookback = df.iloc[-25:-1]
        
        recent_high = lookback["high"].max()
        recent_low = lookback["low"].min()
        rvol = cls.calculate_rvol(df["volume"]).iloc[-1]
        
        is_breakout = (current["close"] > recent_high) and (rvol >= 1.3)
        is_breakdown = (current["close"] < recent_low) and (rvol >= 1.3)
        
        return {
            "breakout": bool(is_breakout),
            "breakdown": bool(is_breakdown),
            "recent_high": float(recent_high),
            "recent_low": float(recent_low),
            "rvol": float(rvol)
        }

    @classmethod
    def compute_all_indicators(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes all indicators and attaches them to DataFrame.
        """
        df = df.copy()
        df["sma_20"] = cls.calculate_sma(df["close"], 20)
        df["sma_50"] = cls.calculate_sma(df["close"], 50)
        df["ema_9"] = cls.calculate_ema(df["close"], 9)
        df["ema_21"] = cls.calculate_ema(df["close"], 21)
        df["rsi_14"] = cls.calculate_rsi(df["close"], 14)
        macd_line, signal_line, macd_hist = cls.calculate_macd(df["close"])
        df["macd"] = macd_line
        df["macd_signal"] = signal_line
        df["macd_hist"] = macd_hist
        df["vwap"] = cls.calculate_vwap(df)
        df["atr_14"] = cls.calculate_atr(df, 14)
        bb_u, bb_m, bb_l = cls.calculate_bollinger_bands(df["close"], 20, 2.0)
        df["bb_upper"] = bb_u
        df["bb_middle"] = bb_m
        df["bb_lower"] = bb_l
        df["rvol"] = cls.calculate_rvol(df["volume"], 20)
        return df
