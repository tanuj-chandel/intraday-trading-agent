"""
Parquet Data Storage Engine for NSE Tick & Candle Historical Persistence.
Enables high-performance, compressed, columnar storage of streaming market data
partitioned by timeframe, symbol, and date for robust future backtesting.
"""

import os
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from app.live.data_types import LiveTick, LiveCandle
from app.core.logging import logger

STORAGE_ROOT = Path(__file__).resolve().parent / "storage"
CANDLE_STORAGE_DIR = STORAGE_ROOT / "candles"
TICK_STORAGE_DIR = STORAGE_ROOT / "ticks"

class ParquetStorageEngine:
    """
    Columnar Parquet storage engine for ticks and multi-timeframe candles.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or STORAGE_ROOT
        self.candle_dir = self.base_dir / "candles"
        self.tick_dir = self.base_dir / "ticks"
        self._ensure_directories()

    def _ensure_directories(self):
        self.candle_dir.mkdir(parents=True, exist_ok=True)
        self.tick_dir.mkdir(parents=True, exist_ok=True)

    def save_candles(self, candles: List[LiveCandle], timeframe: str = "5m"):
        """
        Saves a batch of completed candles to Parquet, partitioned by timeframe, symbol, and date.
        """
        if not candles:
            return

        groups: Dict[tuple, List[Dict[str, Any]]] = {}
        for c in candles:
            date_str = c.timestamp.strftime("%Y-%m-%d")
            key = (c.symbol, date_str)
            if key not in groups:
                groups[key] = []
            groups[key].append({
                "timestamp": pd.to_datetime(c.timestamp),
                "symbol": c.symbol,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": int(c.volume)
            })

        for (sym, date_str), records in groups.items():
            sym_dir = self.candle_dir / timeframe / sym
            sym_dir.mkdir(parents=True, exist_ok=True)
            file_path = sym_dir / f"{date_str}.parquet"

            new_df = pd.DataFrame(records)
            if file_path.exists():
                try:
                    existing_df = pd.read_parquet(file_path)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=["timestamp", "symbol"]).sort_values("timestamp")
                    combined_df.to_parquet(file_path, index=False, compression="snappy")
                except Exception as e:
                    logger.warning(f"Error appending to {file_path}: {e}. Overwriting with new batch.")
                    new_df.to_parquet(file_path, index=False, compression="snappy")
            else:
                new_df.to_parquet(file_path, index=False, compression="snappy")

    def save_ticks(self, ticks: List[LiveTick]):
        """
        Saves streaming ticks to Parquet partitioned by symbol and date.
        """
        if not ticks:
            return

        groups: Dict[tuple, List[Dict[str, Any]]] = {}
        for t in ticks:
            date_str = t.timestamp.strftime("%Y-%m-%d")
            key = (t.symbol, date_str)
            if key not in groups:
                groups[key] = []
            groups[key].append({
                "timestamp": pd.to_datetime(t.timestamp),
                "symbol": t.symbol,
                "ltp": float(t.ltp),
                "bid": float(t.bid),
                "ask": float(t.ask),
                "spread": float(t.spread),
                "volume": int(t.volume)
            })

        for (sym, date_str), records in groups.items():
            sym_dir = self.tick_dir / sym
            sym_dir.mkdir(parents=True, exist_ok=True)
            file_path = sym_dir / f"{date_str}.parquet"

            new_df = pd.DataFrame(records)
            if file_path.exists():
                try:
                    existing_df = pd.read_parquet(file_path)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=["timestamp", "symbol"]).sort_values("timestamp")
                    combined_df.to_parquet(file_path, index=False, compression="snappy")
                except Exception as e:
                    logger.warning(f"Error appending ticks to {file_path}: {e}")
                    new_df.to_parquet(file_path, index=False, compression="snappy")
            else:
                new_df.to_parquet(file_path, index=False, compression="snappy")

    def load_candles(
        self,
        symbol: str,
        timeframe: str = "5m",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Loads historical candles from Parquet storage for backtesting.
        """
        sym_dir = self.candle_dir / timeframe / symbol
        if not sym_dir.exists():
            return pd.DataFrame()

        parquet_files = sorted(list(sym_dir.glob("*.parquet")))
        if not parquet_files:
            return pd.DataFrame()

        dfs = []
        for pf in parquet_files:
            file_date = pf.stem
            if start_date and file_date < start_date:
                continue
            if end_date and file_date > end_date:
                continue
            try:
                df = pd.read_parquet(pf)
                dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to read parquet file {pf}: {e}")

        if not dfs:
            return pd.DataFrame()

        final_df = pd.concat(dfs, ignore_index=True)
        final_df["timestamp"] = pd.to_datetime(final_df["timestamp"])
        final_df = final_df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        return final_df

    def load_ticks(self, symbol: str, date: str) -> pd.DataFrame:
        """
        Loads tick data for a given symbol and date.
        """
        file_path = self.tick_dir / symbol / f"{date}.parquet"
        if not file_path.exists():
            return pd.DataFrame()
        try:
            df = pd.read_parquet(file_path)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.sort_values("timestamp").reset_index(drop=True)
        except Exception as e:
            logger.error(f"Failed to load ticks from {file_path}: {e}")
            return pd.DataFrame()

parquet_storage = ParquetStorageEngine()
