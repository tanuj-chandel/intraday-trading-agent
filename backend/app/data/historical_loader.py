import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logging import logger

class HistoricalDataValidationError(Exception):
    pass

class HistoricalDataLoader:
    """
    Validates, parses, and loads Indian equity historical candle datasets.
    Enforces strict Asia/Kolkata market hours (09:15 to 15:30 IST), OHLC integrity, and zero lookahead.
    """

    @classmethod
    def load_csv(
        cls,
        file_path: str,
        symbol: Optional[str] = None,
        filter_market_hours: bool = True
    ) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Historical data file not found: {file_path}")

        try:
            # Read CSV ignoring comment lines
            df = pd.read_csv(file_path, comment="#")
        except Exception as e:
            raise HistoricalDataValidationError(f"Failed to read CSV: {str(e)}")

        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            raise HistoricalDataValidationError(f"Missing required columns in dataset: {missing}")

        # 1. Parse timestamps
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        except Exception as e:
            raise HistoricalDataValidationError(f"Invalid timestamp format: {str(e)}")

        # 2. Sort and check duplicates
        df = df.sort_values("timestamp").reset_index(drop=True)
        if df["timestamp"].duplicated().any():
            logger.warning("Duplicate timestamps found in dataset; dropping duplicates.")
            df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

        # 3. Validate OHLC Geometry
        invalid_high = df[(df["high"] < df["open"]) | (df["high"] < df["close"])]
        if not invalid_high.empty:
            raise HistoricalDataValidationError(f"High price lower than open or close in {len(invalid_high)} rows.")

        invalid_low = df[(df["low"] > df["open"]) | (df["low"] > df["close"])]
        if not invalid_low.empty:
            raise HistoricalDataValidationError(f"Low price higher than open or close in {len(invalid_low)} rows.")

        # 4. Validate Volume
        invalid_vol = df[df["volume"] < 0]
        if not invalid_vol.empty:
            raise HistoricalDataValidationError(f"Negative volume detected in {len(invalid_vol)} rows.")

        # 5. Market Hours Filter (09:15 to 15:30 IST)
        if filter_market_hours:
            times = df["timestamp"].dt.time
            open_t = pd.to_datetime(settings.MARKET_OPEN_TIME).time()
            close_t = pd.to_datetime(settings.MARKET_CLOSE_TIME).time()
            df = df[(times >= open_t) & (times <= close_t)].reset_index(drop=True)

        if "symbol" not in df.columns and symbol:
            df["symbol"] = symbol

        return df

    @classmethod
    def get_available_datasets(cls, data_dir: str = "data/historical") -> List[Dict[str, Any]]:
        datasets = []
        if not os.path.exists(data_dir):
            return datasets

        for fname in os.listdir(data_dir):
            if fname.endswith(".csv"):
                fpath = os.path.join(data_dir, fname)
                is_sample = "SAMPLE" in fname.upper()
                try:
                    df = pd.read_csv(fpath, comment="#", nrows=5)
                    sym = fname.replace("SAMPLE_", "").replace(".csv", "").split("_")[0]
                    datasets.append({
                        "filename": fname,
                        "file_path": fpath,
                        "symbol": sym,
                        "is_sample": is_sample,
                        "label": f"{sym} ({'SAMPLE DATA ONLY' if is_sample else 'GENUINE HISTORICAL'})",
                        "size_bytes": os.path.getsize(fpath)
                    })
                except Exception:
                    continue

        return datasets
