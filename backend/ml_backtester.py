"""
ML-Driven Trading Backtester
Uses trained LSTM models to generate trading signals and backtest strategy performance
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
import sys
import os

# Add models directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "models"))

from intraday_predictor import IntradayPredictor

warnings.filterwarnings("ignore")


class MLTradingBacktester:
    """
    Backtester that uses ML predictions to make trading decisions
    """

    def __init__(
        self,
        symbols: List[str],
        initial_capital: float,
        start_date: str,
        end_date: str,
        interval: str = "4h",  # "1h" or "4h"
        signal_threshold: float = 2.0,  # Increased from 0.5% to 2.0%
        max_position_size: float = 0.3,  # Max 30% of portfolio in single asset
        transaction_cost: float = 0.001,  # 0.1% transaction fee
        min_confidence: float = 0.5,  # Minimum confidence to trade (increased from 0.3)
    ):
        """
        Initialize ML-driven backtester

        Args:
            symbols: List of crypto symbols (e.g., ['BTC-USD', 'ETH-USD'])
            initial_capital: Starting capital in USD
            start_date: Backtest start date
            end_date: Backtest end date
            interval: Candle interval ("1h" or "4h")
            signal_threshold: Minimum predicted % change to trigger trade
            max_position_size: Maximum % of portfolio per asset
            transaction_cost: Trading fee as decimal (0.001 = 0.1%)
            min_confidence: Minimum confidence level to execute a trade
        """
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        # Make dates timezone-aware (UTC) to match yfinance data
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        # Only localize if timezone-naive
        self.start_date = (
            start_dt if start_dt.tz is not None else start_dt.tz_localize("UTC")
        )
        self.end_date = end_dt if end_dt.tz is not None else end_dt.tz_localize("UTC")
        self.interval = interval
        self.signal_threshold = signal_threshold
        self.max_position_size = max_position_size
        self.transaction_cost = transaction_cost
        self.min_confidence = min_confidence

        # Portfolio state
        self.positions = {symbol: 0.0 for symbol in symbols}  # Number of coins held
        self.cash = initial_capital
        self.entry_prices = {symbol: 0.0 for symbol in symbols}  # Track entry prices

        # Trade cooldown tracking
        self.last_trade_time = {symbol: None for symbol in symbols}
        self.trade_cooldown_periods = 6  # Minimum 6 candles (24h for 4h interval) between trades

        # Take-profit tracking
        self.take_profit_levels = [0.03, 0.05, 0.08]  # 3%, 5%, 8% profit targets
        self.take_profit_portions = [0.3, 0.3, 0.4]  # Sell 30%, 30%, 40% at each level
        self.take_profit_hit = {}  # Track which take-profit levels have been hit

        # Stop loss
        self.stop_loss_pct = 0.03  # 3% stop loss from entry

        # Signal confirmation tracking
        self.signal_history = {symbol: [] for symbol in symbols}
        self.required_confirmations = 2  # Need 2 consecutive same signals
        
        # Confidence normalization factor (predicted_change / factor to get 0-1 range)
        self.confidence_normalization_factor = 10.0

        # Performance tracking
        self.portfolio_values = []
        self.trade_history = []
        self.predictions_log = []
        
        # Actual win/loss tracking based on trade outcomes
        self.trade_outcomes = []  # Track actual profit/loss per trade

        # ML predictors
        self.predictors = {}
        self._initialize_predictors()

    def _initialize_predictors(self):
        """Load or initialize ML predictors for each symbol"""
        print(f"Initializing ML predictors for {len(self.symbols)} assets...")

        for symbol in self.symbols:
            try:
                predictor = IntradayPredictor(
                    symbol=symbol,
                    interval=self.interval,
                    lookback_periods=(
                        168 if self.interval == "1h" else 42
                    ),  # 1 week of data
                )
                predictor.load_model()
                self.predictors[symbol] = predictor
                print(f"✅ Loaded model for {symbol}")
            except FileNotFoundError:
                print(f"⚠️  No pre-trained model for {symbol}, will train on-the-fly")
                self.predictors[symbol] = None
            except Exception as e:
                print(f"❌ Error loading {symbol}: {str(e)}")
                self.predictors[symbol] = None

    def fetch_historical_data(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch intraday historical data for backtesting

        Note: yfinance limitations apply (max 730 days for hourly)
        """
        print(f"\n{'='*60}")
        print(f"Fetching {self.interval} data for backtesting")
        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print(f"{'='*60}")

        historical_data = {}

        for symbol in self.symbols:
            try:
                print(f"Fetching {symbol}...")
                # Need extra data for feature engineering + LSTM lookback
                # 4h interval: needs 42 lookback + 60 for features = ~30 days buffer
                # 1h interval: needs 168 lookback + 60 for features = ~15 days buffer
                extra_days = 30 if self.interval == "4h" else 15
                data = yf.download(
                    symbol,
                    start=self.start_date - timedelta(days=extra_days),
                    end=self.end_date,
                    interval=self.interval,
                    progress=False,
                )

                if data.empty:
                    raise ValueError(f"No data for {symbol}")

                print(f"  Retrieved {len(data)} raw candles")

                # Add technical indicators
                data = self._add_features(data)
                historical_data[symbol] = data
                print(f"  After feature engineering: {len(data)} periods available")

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                raise

        return historical_data

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators"""
        # Work with a copy
        df = df.copy()

        df["MA_20"] = df["Close"].rolling(window=20).mean()
        df["MA_50"] = df["Close"].rolling(window=50).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        df["Volume_Change"] = df["Volume"].pct_change()
        df["Price_Change"] = df["Close"].pct_change()
        df["Volatility"] = df["Close"].rolling(window=20).std()

        # Drop NaN values but keep datetime index for backtesting
        df = df.dropna()

        return df

    def _get_major_trend(self, data: pd.DataFrame) -> int:
        """Determine major trend using longer-term MAs
        
        Returns:
            1: Strong uptrend
            -1: Strong downtrend
            0: Sideways/neutral
        """
        if len(data) < 100:
            return 0
        
        ma_50 = data["Close"].rolling(50).mean().iloc[-1]
        ma_100 = data["Close"].rolling(100).mean().iloc[-1] if len(data) >= 100 else ma_50
        current_price = data["Close"].iloc[-1]
        
        if current_price > ma_50 > ma_100:
            return 1  # Strong uptrend
        elif current_price < ma_50 < ma_100:
            return -1  # Strong downtrend
        return 0  # Sideways

    def _check_cooldown(self, symbol: str, timestamp: pd.Timestamp) -> bool:
        """Check if cooldown period has passed since last trade
        
        Returns:
            True if can trade (cooldown passed), False otherwise
        """
        if self.last_trade_time[symbol] is None:
            return True
        
        # Calculate periods since last trade based on interval
        interval_hours = {"4h": 4, "1h": 1}.get(self.interval, 4)  # Default to 4h
        period_delta = timedelta(hours=interval_hours)
        
        periods_since_trade = (timestamp - self.last_trade_time[symbol]) / period_delta
        return periods_since_trade >= self.trade_cooldown_periods

    def check_take_profit(self, symbol: str, current_price: float, timestamp: pd.Timestamp) -> Optional[float]:
        """Check if take-profit levels are hit
        
        Returns:
            Portion to sell (0.0 to 1.0) or None if no take-profit hit
        """
        if self.positions[symbol] <= 0:
            return None
        
        entry_price = self.entry_prices[symbol]
        if entry_price <= 0:
            return None
        
        profit_pct = (current_price - entry_price) / entry_price
        
        # Check each take profit level
        for i, (level, portion) in enumerate(zip(self.take_profit_levels, self.take_profit_portions)):
            level_key = f"{symbol}_tp_{i}"
            if profit_pct >= level and not self.take_profit_hit.get(level_key, False):
                self.take_profit_hit[level_key] = True
                return portion  # Return portion to sell
        
        return None

    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """Check if stop loss is triggered
        
        Returns:
            True if stop loss hit, False otherwise
        """
        if self.positions[symbol] <= 0:
            return False
        
        entry_price = self.entry_prices[symbol]
        if entry_price <= 0:
            return False
        
        loss_pct = (entry_price - current_price) / entry_price
        return loss_pct > self.stop_loss_pct

    def _should_sell_at_loss(self, signal_data: Dict) -> bool:
        """Determine if we should sell at a loss (only with strong bearish signal)
        
        Returns:
            True if strong bearish signal justifies selling at loss
        """
        return signal_data["confidence"] > 0.7 and signal_data["predicted_change"] < -2.0

    def _get_confirmed_signal(self, symbol: str, raw_signal: str) -> str:
        """Apply signal confirmation - require consecutive same signals
        
        Returns:
            Confirmed signal or 'HOLD' if not confirmed
        """
        # Add to history
        self.signal_history[symbol].append(raw_signal)
        if len(self.signal_history[symbol]) > 5:
            self.signal_history[symbol].pop(0)
        
        # Check for confirmation
        recent = self.signal_history[symbol][-self.required_confirmations:]
        if len(recent) < self.required_confirmations:
            return "HOLD"
        
        if all(s == "BUY" for s in recent):
            return "BUY"
        elif all(s == "SELL" for s in recent):
            return "SELL"
        return "HOLD"

    def _reset_take_profit_tracking(self, symbol: str):
        """Reset take-profit tracking when position is closed"""
        for i in range(len(self.take_profit_levels)):
            level_key = f"{symbol}_tp_{i}"
            self.take_profit_hit[level_key] = False

    def generate_trading_signal(
        self, symbol: str, historical_slice: pd.DataFrame
    ) -> Dict:
        """
        Generate trading signal using ML prediction

        Returns:
            Dict with signal ('BUY', 'SELL', 'HOLD'), confidence, and predicted price
        """
        predictor = self.predictors.get(symbol)

        if predictor is None:
            # Fallback to simple momentum strategy
            return self._momentum_signal(symbol, historical_slice)

        try:
            # Make sure we have enough data
            if len(historical_slice) < 100:  # Need buffer for feature engineering
                return self._momentum_signal(symbol, historical_slice)

            prediction = predictor.predict_next(historical_slice)

            # Enhance signal based on prediction confidence
            predicted_change = float(prediction["predicted_change_percent"])
            confidence = float(abs(predicted_change) / self.confidence_normalization_factor)  # Normalize to 0-1 range

            # Determine raw signal based on threshold
            if predicted_change > self.signal_threshold:
                raw_signal = "BUY"
            elif predicted_change < -self.signal_threshold:
                raw_signal = "SELL"
            else:
                raw_signal = "HOLD"
            
            # Apply signal confirmation (require consecutive same signals)
            confirmed_signal = self._get_confirmed_signal(symbol, raw_signal)
            
            # Check minimum confidence threshold
            if confirmed_signal != "HOLD" and confidence < self.min_confidence:
                confirmed_signal = "HOLD"
            
            # Apply trend filter
            major_trend = self._get_major_trend(historical_slice)
            
            # Trend filter: Only allow buys in uptrend/neutral, sells in downtrend/neutral
            if confirmed_signal == "BUY" and major_trend == -1:
                confirmed_signal = "HOLD"  # Don't buy in downtrend
            # Note: In uptrends, SELL signals are kept but execute_trade() will only
            # execute if in profit, stop-loss hit, or strong bearish signal
            
            return {
                "signal": confirmed_signal,
                "predicted_price": float(prediction["predicted_price"]),
                "predicted_change": predicted_change,
                "current_price": float(prediction["current_price"]),
                "confidence": confidence,
                "raw_signal": raw_signal,  # Keep raw signal for reference
                "major_trend": major_trend,
            }

        except Exception as e:
            # Fallback to momentum on any prediction error
            return self._momentum_signal(symbol, historical_slice)

    def _momentum_signal(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Fallback momentum-based signal"""
        # Extract scalar values to avoid Series comparison ambiguity
        current_price = float(data["Close"].iloc[-1])
        ma_20 = (
            float(data["MA_20"].iloc[-1])
            if not pd.isna(data["MA_20"].iloc[-1])
            else current_price
        )
        ma_50 = (
            float(data["MA_50"].iloc[-1])
            if not pd.isna(data["MA_50"].iloc[-1])
            else current_price
        )

        if current_price > ma_20 and ma_20 > ma_50:
            raw_signal = "BUY"
        elif current_price < ma_20 and ma_20 < ma_50:
            raw_signal = "SELL"
        else:
            raw_signal = "HOLD"
        
        # Apply confirmation
        confirmed_signal = self._get_confirmed_signal(symbol, raw_signal)
        
        # Get major trend
        major_trend = self._get_major_trend(data)

        return {
            "signal": confirmed_signal,
            "predicted_price": current_price,
            "predicted_change": 0.0,
            "current_price": current_price,
            "confidence": 0.5,
            "raw_signal": raw_signal,
            "major_trend": major_trend,
        }

    def calculate_position_size(self, symbol: str, signal_data: Dict) -> float:
        """
        Calculate optimal position size based on signal confidence and risk management

        Returns:
            Dollar amount to invest/divest
        """
        if signal_data["signal"] == "HOLD":
            return 0.0

        # Maximum position value
        max_position_value = self.current_capital * self.max_position_size

        # Current position value
        current_price = signal_data["current_price"]
        current_position_value = self.positions[symbol] * current_price

        # Confidence-adjusted sizing
        confidence = signal_data["confidence"]

        if signal_data["signal"] == "BUY":
            # Can buy up to max position size
            available_to_buy = min(
                self.cash * 0.9, max_position_value - current_position_value
            )
            return available_to_buy * confidence if available_to_buy > 0 else 0.0

        elif signal_data["signal"] == "SELL":
            # Sell portion based on confidence
            return (
                current_position_value * confidence
                if current_position_value > 0
                else 0.0
            )

        return 0.0

    def execute_trade(self, symbol: str, signal_data: Dict, timestamp: pd.Timestamp):
        """
        Execute trade based on signal with improved position management
        """
        # Ensure current_price is a float
        current_price = float(signal_data["current_price"])
        entry_price = self.entry_prices[symbol]
        
        # Check cooldown period
        if not self._check_cooldown(symbol, timestamp):
            return
        
        # Check for take-profit before processing regular signals
        take_profit_portion = self.check_take_profit(symbol, current_price, timestamp)
        if take_profit_portion is not None and take_profit_portion > 0:
            # Execute take-profit sell
            current_position_value = self.positions[symbol] * current_price
            value_to_sell = current_position_value * take_profit_portion
            coins_to_sell = value_to_sell / current_price
            
            if coins_to_sell > 0 and coins_to_sell <= self.positions[symbol]:
                self.positions[symbol] -= coins_to_sell
                proceeds = value_to_sell * (1 - self.transaction_cost)
                self.cash += proceeds
                
                # Track trade outcome
                profit_loss = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                self.trade_outcomes.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": "TAKE_PROFIT",
                    "profit_loss_pct": profit_loss * 100,
                    "is_profitable": profit_loss > 0,
                })
                
                self.trade_history.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": "TAKE_PROFIT",
                    "coins": float(coins_to_sell),
                    "price": float(current_price),
                    "value": float(proceeds),
                    "predicted_change": float(signal_data.get("predicted_change", 0)),
                    "confidence": float(signal_data.get("confidence", 0)),
                    "profit_loss_pct": profit_loss * 100,
                })
                
                self.last_trade_time[symbol] = timestamp
                
                # Reset take-profit tracking if position fully closed
                if self.positions[symbol] <= 0:
                    self._reset_take_profit_tracking(symbol)
                    self.entry_prices[symbol] = 0.0
                return
        
        # Check for stop-loss
        if self.check_stop_loss(symbol, current_price):
            # Execute stop-loss sell (sell entire position)
            coins_to_sell = self.positions[symbol]
            if coins_to_sell > 0:
                value_to_sell = coins_to_sell * current_price
                proceeds = value_to_sell * (1 - self.transaction_cost)
                
                # Track trade outcome
                profit_loss = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                self.trade_outcomes.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": "STOP_LOSS",
                    "profit_loss_pct": profit_loss * 100,
                    "is_profitable": False,  # Stop loss is always a loss
                })
                
                self.positions[symbol] = 0.0
                self.cash += proceeds
                
                self.trade_history.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": "STOP_LOSS",
                    "coins": float(coins_to_sell),
                    "price": float(current_price),
                    "value": float(proceeds),
                    "predicted_change": float(signal_data.get("predicted_change", 0)),
                    "confidence": float(signal_data.get("confidence", 0)),
                    "profit_loss_pct": profit_loss * 100,
                })
                
                self.last_trade_time[symbol] = timestamp
                self._reset_take_profit_tracking(symbol)
                self.entry_prices[symbol] = 0.0
                return
        
        # Process regular signals
        position_size = self.calculate_position_size(symbol, signal_data)

        if abs(position_size) < 10:  # Minimum $10 trade
            return

        if signal_data["signal"] == "BUY":
            # Calculate coins to buy (accounting for fees)
            coins_to_buy = (position_size * (1 - self.transaction_cost)) / current_price
            cost = position_size

            if cost <= self.cash:
                # Track if this is a new position or adding to existing
                is_new_position = self.positions[symbol] == 0
                
                self.positions[symbol] += coins_to_buy
                self.cash -= cost
                
                # Set entry price for new positions, use weighted average for additions
                if is_new_position:
                    self.entry_prices[symbol] = current_price
                else:
                    # Weighted average entry price (with defensive check for division by zero)
                    total_coins = self.positions[symbol]
                    if total_coins > 0:
                        old_coins = total_coins - coins_to_buy
                        self.entry_prices[symbol] = (
                            (entry_price * old_coins + current_price * coins_to_buy) / total_coins
                        )

                self.trade_history.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": "BUY",
                    "coins": float(coins_to_buy),
                    "price": float(current_price),
                    "value": float(cost),
                    "predicted_change": float(signal_data.get("predicted_change", 0)),
                    "confidence": float(signal_data.get("confidence", 0)),
                })
                
                self.last_trade_time[symbol] = timestamp

        elif signal_data["signal"] == "SELL":
            # Improved sell logic: only sell if in profit OR strong bearish signal
            if self.positions[symbol] > 0 and entry_price > 0:
                is_in_profit = current_price > entry_price
                is_strong_bearish = self._should_sell_at_loss(signal_data)
                
                # Don't sell at a loss without strong reason
                if not is_in_profit and not is_strong_bearish:
                    return
            
            # Calculate coins to sell
            value_to_sell = position_size
            coins_to_sell = value_to_sell / current_price

            if coins_to_sell > 0 and coins_to_sell <= self.positions[symbol]:
                self.positions[symbol] -= coins_to_sell
                proceeds = value_to_sell * (1 - self.transaction_cost)
                self.cash += proceeds

                # Track trade outcome
                profit_loss = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                self.trade_outcomes.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": "SELL",
                    "profit_loss_pct": profit_loss * 100,
                    "is_profitable": profit_loss > 0,
                })

                self.trade_history.append({
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": "SELL",
                    "coins": float(coins_to_sell),
                    "price": float(current_price),
                    "value": float(proceeds),
                    "predicted_change": float(signal_data.get("predicted_change", 0)),
                    "confidence": float(signal_data.get("confidence", 0)),
                    "profit_loss_pct": profit_loss * 100,
                })
                
                self.last_trade_time[symbol] = timestamp
                
                # Reset take-profit tracking if position fully closed
                if self.positions[symbol] <= 0:
                    self._reset_take_profit_tracking(symbol)
                    self.entry_prices[symbol] = 0.0

    def run_backtest(self) -> Dict:
        """
        Run complete ML-driven backtest

        Returns:
            Comprehensive performance report
        """
        print(f"\n{'='*60}")
        print(f"Running ML-Driven Backtest")
        print(f"{'='*60}")

        # Fetch data
        historical_data = self.fetch_historical_data()

        # Get common timestamps across all symbols
        all_timestamps = set(historical_data[self.symbols[0]].index)
        for symbol in self.symbols[1:]:
            all_timestamps &= set(historical_data[symbol].index)

        timestamps = sorted([ts for ts in all_timestamps if ts >= self.start_date])

        print(f"\nBacktesting {len(timestamps)} periods...")

        # Minimum data needed for predictions
        min_lookback = 168 if self.interval == "1h" else 100

        for i, timestamp in enumerate(timestamps):
            if i % 100 == 0:
                print(
                    f"  Progress: {i}/{len(timestamps)} ({i/len(timestamps)*100:.1f}%)"
                )

            # Get historical slice for predictions (up to current timestamp)
            period_signals = {}

            for symbol in self.symbols:
                try:
                    # Get data up to current timestamp
                    historical_slice = historical_data[symbol][
                        historical_data[symbol].index <= timestamp
                    ]

                    if len(historical_slice) < min_lookback:
                        continue

                    # Generate signal
                    signal_data = self.generate_trading_signal(symbol, historical_slice)
                    period_signals[symbol] = signal_data

                    # Execute trade
                    self.execute_trade(symbol, signal_data, timestamp)

                    # Get actual next price (if available) for comparison
                    actual_next_price = signal_data[
                        "current_price"
                    ]  # Default to current
                    if i < len(timestamps) - 1:
                        next_timestamp = timestamps[i + 1]
                        next_data = historical_data[symbol][
                            historical_data[symbol].index <= next_timestamp
                        ]
                        if not next_data.empty:
                            actual_next_price = float(next_data["Close"].iloc[-1])

                    # Log prediction with actual outcome
                    self.predictions_log.append(
                        {
                            "timestamp": timestamp,
                            "symbol": symbol,
                            "current_price": signal_data["current_price"],
                            "predicted_price": signal_data["predicted_price"],
                            "actual_next_price": actual_next_price,
                            "predicted_change": signal_data["predicted_change"],
                            "confidence": signal_data["confidence"],
                            "signal": signal_data["signal"],
                        }
                    )

                except Exception as e:
                    print(f"  ⚠️  Error processing {symbol} at {timestamp}: {str(e)}")
                    continue

            # Calculate portfolio value at this timestamp
            portfolio_value = self.cash
            for symbol in self.symbols:
                current_data = historical_data[symbol][
                    historical_data[symbol].index <= timestamp
                ]
                if not current_data.empty:
                    # Ensure we get a scalar float value, not a Series
                    current_price = float(current_data["Close"].iloc[-1])
                    portfolio_value += self.positions[symbol] * current_price

            self.portfolio_values.append(
                {
                    "timestamp": timestamp,
                    "portfolio_value": float(portfolio_value),
                    "cash": float(self.cash),
                    "positions": self.positions.copy(),
                }
            )

        # Calculate final metrics
        return self._calculate_performance_metrics()

    def _calculate_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not self.portfolio_values:
            raise ValueError("No portfolio values to analyze")

        # Convert to DataFrame for easier analysis
        portfolio_df = pd.DataFrame(self.portfolio_values)
        portfolio_df.set_index("timestamp", inplace=True)

        # Calculate returns
        portfolio_df["returns"] = portfolio_df["portfolio_value"].pct_change()

        final_value = portfolio_df["portfolio_value"].iloc[-1]
        total_return = (
            (final_value - self.initial_capital) / self.initial_capital
        ) * 100

        # Annualized metrics
        days = (self.end_date - self.start_date).days
        years = days / 365.0
        annualized_return = (
            ((final_value / self.initial_capital) ** (1 / years) - 1) * 100
            if years > 0
            else 0
        )

        # Risk metrics
        volatility = portfolio_df["returns"].std() * np.sqrt(252) * 100  # Annualized
        sharpe_ratio = (
            (annualized_return - 2) / volatility if volatility > 0 else 0
        )  # Assuming 2% risk-free rate

        # Drawdown analysis
        cumulative_returns = (1 + portfolio_df["returns"]).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = ((cumulative_returns - running_max) / running_max) * 100
        max_drawdown = drawdown.min()

        # Trading statistics
        num_trades = len(self.trade_history)
        buy_trades = [t for t in self.trade_history if t["action"] == "BUY"]
        sell_trades = [t for t in self.trade_history if t["action"] in ["SELL", "TAKE_PROFIT", "STOP_LOSS"]]
        take_profit_trades = [t for t in self.trade_history if t["action"] == "TAKE_PROFIT"]
        stop_loss_trades = [t for t in self.trade_history if t["action"] == "STOP_LOSS"]

        # Win rate based on ACTUAL trade outcomes (profit/loss)
        if self.trade_outcomes:
            profitable_trades = sum(1 for t in self.trade_outcomes if t["is_profitable"])
            actual_win_rate = (profitable_trades / len(self.trade_outcomes) * 100) if self.trade_outcomes else 0
        else:
            # Fallback to old method if no outcomes tracked
            winning_trades = sum(
                1
                for t in self.trade_history
                if t["predicted_change"] * (1 if t["action"] == "BUY" else -1) > 0
            )
            actual_win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0

        return {
            "success": True,
            "summary": {
                "initial_capital": self.initial_capital,
                "final_value": final_value,
                "total_return": total_return,
                "annualized_return": annualized_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
            },
            "trading_stats": {
                "total_trades": num_trades,
                "buy_trades": len(buy_trades),
                "sell_trades": len(sell_trades),
                "take_profit_trades": len(take_profit_trades),
                "stop_loss_trades": len(stop_loss_trades),
                "win_rate": actual_win_rate,
                "avg_trade_size": (
                    np.mean([t["value"] for t in self.trade_history])
                    if num_trades > 0
                    else 0
                ),
            },
            "final_positions": {
                symbol: {
                    "coins": position,
                    "value": position
                    * portfolio_df["portfolio_value"].iloc[-1],  # Approximation
                }
                for symbol, position in self.positions.items()
            },
            "portfolio_history": portfolio_df["portfolio_value"].to_dict(),
            "trade_history": self.trade_history,
            "trade_outcomes": self.trade_outcomes,
            "config": {
                "interval": self.interval,
                "signal_threshold": self.signal_threshold,
                "max_position_size": self.max_position_size,
                "transaction_cost": self.transaction_cost,
                "min_confidence": self.min_confidence,
                "trade_cooldown_periods": self.trade_cooldown_periods,
                "stop_loss_pct": self.stop_loss_pct,
                "required_confirmations": self.required_confirmations,
            },
        }

    def get_performance_summary(self) -> str:
        """Get formatted performance summary"""
        if not self.portfolio_values:
            return "No backtest run yet"

        metrics = self._calculate_performance_metrics()
        summary = metrics["summary"]
        trading = metrics["trading_stats"]

        return f"""
ML-Driven Trading Backtest Results
{'='*60}
Period: {self.start_date.date()} to {self.end_date.date()}
Interval: {self.interval} candles
Symbols: {', '.join(self.symbols)}

Portfolio Performance:
  Initial Capital: ${summary['initial_capital']:,.2f}
  Final Value: ${summary['final_value']:,.2f}
  Total Return: {summary['total_return']:.2f}%
  Annualized Return: {summary['annualized_return']:.2f}%
  Volatility: {summary['volatility']:.2f}%
  Sharpe Ratio: {summary['sharpe_ratio']:.3f}
  Max Drawdown: {summary['max_drawdown']:.2f}%

Trading Statistics:
  Total Trades: {trading['total_trades']}
  Buy Trades: {trading['buy_trades']}
  Sell Trades: {trading['sell_trades']}
  Take-Profit Trades: {trading['take_profit_trades']}
  Stop-Loss Trades: {trading['stop_loss_trades']}
  Win Rate (Actual): {trading['win_rate']:.1f}%
  Avg Trade Size: ${trading['avg_trade_size']:,.2f}

Strategy Configuration:
  Signal Threshold: {self.signal_threshold}%
  Min Confidence: {self.min_confidence}
  Max Position Size: {self.max_position_size*100}%
  Transaction Cost: {self.transaction_cost*100}%
  Trade Cooldown: {self.trade_cooldown_periods} periods
  Stop Loss: {self.stop_loss_pct*100}%
  Signal Confirmations Required: {self.required_confirmations}
"""


# Convenience function
def ml_backtest_portfolio(
    symbols: List[str],
    initial_capital: float = 100000,
    start_date: str = None,
    end_date: str = None,
    interval: str = "4h",
    signal_threshold: float = 2.0,  # Increased from 0.5 to 2.0
) -> Dict:
    """
    Convenience function to run ML-driven backtest
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    backtester = MLTradingBacktester(
        symbols=symbols,
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        signal_threshold=signal_threshold,
    )

    return backtester.run_backtest()


if __name__ == "__main__":
    # Example usage
    print("ML-Driven Trading Backtest Demo")
    print("=" * 60)

    symbols = ["BTC-USD", "ETH-USD"]

    backtester = MLTradingBacktester(
        symbols=symbols,
        initial_capital=100000,
        start_date="2024-10-01",
        end_date="2024-10-29",
        interval="4h",
        signal_threshold=2.0,  # Increased from 0.5 to 2.0
    )

    results = backtester.run_backtest()
    print(backtester.get_performance_summary())

    print(f"\nTrade History (last 10):")
    for trade in backtester.trade_history[-10:]:
        print(
            f"  {trade['timestamp']}: {trade['action']} {trade['coins']:.6f} {trade['symbol']} @ ${trade['price']:.2f}"
        )
