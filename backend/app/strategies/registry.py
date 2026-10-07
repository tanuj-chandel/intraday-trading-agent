import pandas as pd
from typing import Dict, Any, List, Optional
from app.technical.indicators import TechnicalAnalysis

class StrategyDefinition:
    def __init__(
        self,
        strategy_id: str,
        strategy_name: str,
        version: str,
        description: str,
        default_parameters: Dict[str, Any],
        is_enabled: bool = True
    ):
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.version = version
        self.description = description
        self.default_parameters = default_parameters
        self.is_enabled = is_enabled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "version": self.version,
            "description": self.description,
            "default_parameters": self.default_parameters,
            "is_enabled": self.is_enabled
        }

class StrategyRegistry:
    """
    Central strategy registry supporting versioning, parameterization, and enable states.
    """
    _registry: Dict[str, StrategyDefinition] = {}

    @classmethod
    def register(cls, strategy: StrategyDefinition):
        cls._registry[strategy.strategy_id] = strategy

    @classmethod
    def get(cls, strategy_id: str) -> Optional[StrategyDefinition]:
        return cls._registry.get(strategy_id)

    @classmethod
    def list_strategies(cls) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in cls._registry.values()]

# Register Default VWAP_EMA_MOMENTUM_V1 (Active)
StrategyRegistry.register(
    StrategyDefinition(
        strategy_id="VWAP_EMA_MOMENTUM_V1",
        strategy_name="VWAP + EMA Dynamic Momentum & RVOL",
        version="1.0.0",
        description="Event-driven intraday trend-following strategy using VWAP filter, EMA 9/21 cross, RSI momentum range, and RVOL confirmation.",
        is_enabled=True,
        default_parameters={
            "ema_fast": 9,
            "ema_slow": 21,
            "rsi_period": 14,
            "rsi_long_min": 52.0,
            "rsi_long_max": 75.0,
            "rsi_short_min": 25.0,
            "rsi_short_max": 48.0,
            "min_rvol": 1.15,
            "atr_period": 14,
            "sl_multiplier": 1.5,
            "target_multiplier": 2.0,
            "min_risk_reward": 1.5,
            "trailing_stop": True,
            "trailing_stop_activation_r": 1.0
        }
    )
)

# Register ORB_15M_V1 (Prepared, Inactive)
StrategyRegistry.register(
    StrategyDefinition(
        strategy_id="ORB_15M_V1",
        strategy_name="Opening Range Breakout 15M",
        version="1.0.0",
        description="Intraday 15-minute Opening Range Breakout strategy with volume expansion confirmation.",
        is_enabled=False,
        default_parameters={
            "range_minutes": 15,
            "rvol_threshold": 1.2,
            "risk_reward": 2.0
        }
    )
)

# Register MEAN_REVERSION_BB_RSI_V1 (Prepared, Inactive)
StrategyRegistry.register(
    StrategyDefinition(
        strategy_id="MEAN_REVERSION_BB_RSI_V1",
        strategy_name="Mean Reversion BB + RSI",
        version="1.0.0",
        description="Mean reversion counter-trend strategy using Bollinger Band touches and RSI divergence.",
        is_enabled=False,
        default_parameters={
            "rsi_oversold": 30.0,
            "rsi_overbought": 70.0,
            "target": "BB_MIDDLE"
        }
    )
)
