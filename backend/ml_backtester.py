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
        signal_threshold: float = 0.5,  # % price change threshold for trades
        max_position_size: float = 0.3,  # Max 30% of portfolio in single asset
        transaction_cost: float = 0.001,  # 0.1% transaction fee
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

        # Portfolio state
        self.positions = {symbol: 0.0 for symbol in symbols}  # Number of coins held
        self.cash = initial_capital

        # Performance tracking
        self.portfolio_values = []
        self.trade_history = []
        self.predictions_log = []

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
                data = yf.download(
                    symbol,
                    start=self.start_date
                    - timedelta(days=10),  # Extra data for indicators
                    end=self.end_date,
                    interval=self.interval,
                    progress=False,
                )

                if data.empty:
                    raise ValueError(f"No data for {symbol}")

                # Add technical indicators
                data = self._add_features(data)
                historical_data[symbol] = data
                print(f"  Retrieved {len(data)} candles")

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                raise

        return historical_data

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators"""
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

        return df.dropna()

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
            prediction = predictor.predict_next(historical_slice)

            # Enhance signal based on prediction confidence
            predicted_change = float(prediction["predicted_change_percent"])

            if predicted_change > self.signal_threshold:
                signal = "BUY"
            elif predicted_change < -self.signal_threshold:
                signal = "SELL"
            else:
                signal = "HOLD"

            return {
                "signal": signal,
                "predicted_price": float(prediction["predicted_price"]),
                "predicted_change": predicted_change,
                "current_price": float(prediction["current_price"]),
                "confidence": float(
                    abs(predicted_change) / 10.0
                ),  # Normalize to 0-1 range
            }

        except Exception as e:
            print(f"  ⚠️  Prediction error for {symbol}: {str(e)}")
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
            signal = "BUY"
        elif current_price < ma_20 and ma_20 < ma_50:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "predicted_price": current_price,
            "predicted_change": 0.0,
            "current_price": current_price,
            "confidence": 0.5,
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
        Execute trade based on signal
        """
        position_size = self.calculate_position_size(symbol, signal_data)

        if abs(position_size) < 10:  # Minimum $10 trade
            return

        # Ensure current_price is a float
        current_price = float(signal_data["current_price"])

        if signal_data["signal"] == "BUY":
            # Calculate coins to buy (accounting for fees)
            coins_to_buy = (position_size * (1 - self.transaction_cost)) / current_price
            cost = position_size

            if cost <= self.cash:
                self.positions[symbol] += coins_to_buy
                self.cash -= cost

                self.trade_history.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "BUY",
                        "coins": float(coins_to_buy),
                        "price": float(current_price),
                        "value": float(cost),
                        "predicted_change": float(signal_data["predicted_change"]),
                        "confidence": float(signal_data["confidence"]),
                    }
                )

        elif signal_data["signal"] == "SELL":
            # Calculate coins to sell
            value_to_sell = position_size
            coins_to_sell = value_to_sell / current_price

            if coins_to_sell <= self.positions[symbol]:
                self.positions[symbol] -= coins_to_sell
                proceeds = value_to_sell * (1 - self.transaction_cost)
                self.cash += proceeds

                self.trade_history.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "SELL",
                        "coins": float(coins_to_sell),
                        "price": float(current_price),
                        "value": float(proceeds),
                        "predicted_change": float(signal_data["predicted_change"]),
                        "confidence": float(signal_data["confidence"]),
                    }
                )

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
        min_lookback = 168 if self.interval == "1h" else 42

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
        sell_trades = [t for t in self.trade_history if t["action"] == "SELL"]

        # Win rate (trades that were followed by price increase)
        winning_trades = sum(
            1
            for t in self.trade_history
            if t["predicted_change"] * (1 if t["action"] == "BUY" else -1) > 0
        )
        win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0

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
                "win_rate": win_rate,
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
            "config": {
                "interval": self.interval,
                "signal_threshold": self.signal_threshold,
                "max_position_size": self.max_position_size,
                "transaction_cost": self.transaction_cost,
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
  Win Rate: {trading['win_rate']:.1f}%
  Avg Trade Size: ${trading['avg_trade_size']:,.2f}

Strategy Configuration:
  Signal Threshold: {self.signal_threshold}%
  Max Position Size: {self.max_position_size*100}%
  Transaction Cost: {self.transaction_cost*100}%
"""


# Convenience function
def ml_backtest_portfolio(
    symbols: List[str],
    initial_capital: float = 100000,
    start_date: str = None,
    end_date: str = None,
    interval: str = "4h",
    signal_threshold: float = 0.5,
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
        signal_threshold=0.5,
    )

    results = backtester.run_backtest()
    print(backtester.get_performance_summary())

    print(f"\nTrade History (last 10):")
    for trade in backtester.trade_history[-10:]:
        print(
            f"  {trade['timestamp']}: {trade['action']} {trade['coins']:.6f} {trade['symbol']} @ ${trade['price']:.2f}"
        )
