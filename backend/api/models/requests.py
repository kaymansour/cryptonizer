"""
Pydantic models for API request validation
"""

from pydantic import BaseModel
from typing import List, Optional, Dict


class PortfolioOptimizationRequest(BaseModel):
    symbols: List[str]
    total_value: float = 100000
    objective: str = "max_sharpe"
    period: str = "1y"
    ml_config: Optional[Dict] = None


class EfficientFrontierRequest(BaseModel):
    symbols: List[str]
    period: str = "1y"
    num_portfolios: int = 50


class BacktestRequest(BaseModel):
    symbols: List[str]
    weights: Dict[str, float]
    initial_investment: float = 100000
    start_date: str
    end_date: str
    rebalance_frequency: str = "monthly"


class StrategyComparisonRequest(BaseModel):
    symbols: List[str]
    optimized_weights: Dict[str, float]
    initial_investment: float = 100000
    start_date: str
    end_date: str
    rebalance_frequency: str = "monthly"
    include_benchmarks: Optional[List[str]] = None


class MLConfigRequest(BaseModel):
    """Optional ML configuration parameters that can be customized by user preferences"""

    signal_threshold: float = 2.0
    min_confidence: float = 0.5
    max_position_size: float = 0.6
    stop_loss_pct: float = 0.03
    trailing_stop_pct: float = 0.05
    trade_cooldown_periods: int = 6
    required_confirmations: int = 2
    take_profit_levels: List[float] = [0.03, 0.05, 0.08]
    take_profit_portions: List[float] = [0.3, 0.3, 0.4]
    interval: str = "4h"
    use_trend_filter: bool = True
    use_rsi_filter: bool = True
    use_volume_filter: bool = True
    rsi_oversold: float = 25
    rsi_overbought: float = 60


class MLBacktestRequest(BaseModel):
    symbols: List[str]
    weights: Dict[str, float]
    initial_investment: float = 100000
    start_date: str
    end_date: str
    interval: str = "4h"  # "1h" or "4h"
    signal_threshold: float = 2.0
    max_position_size: float = 0.6
    rsi_oversold: int = 25
    rsi_overbought: int = 60
    stop_loss_pct: float = 0.03
    trailing_stop_pct: float = 0.05
    # Optional ML config from user preferences
    ml_config: Optional[MLConfigRequest] = None
