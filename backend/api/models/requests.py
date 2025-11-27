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


class MLBacktestRequest(BaseModel):
    symbols: List[str]
    weights: Dict[str, float]
    initial_investment: float = 100000
    start_date: str
    end_date: str
    interval: str = "4h"  # "1h" or "4h"
    signal_threshold: float = 0.5
