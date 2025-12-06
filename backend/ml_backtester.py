"""
ML-Driven Trading Backtester - Enhanced Version
Uses trained LSTM models with multi-factor signal confirmation
Data Source: Pre-downloaded CSV with 11+ years of historical data
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "models"))

from intraday_predictor import IntradayPredictor

# Import CSV data loader
try:
    from services.csv_data_loader import get_symbol_data, CSV_DATA_AVAILABLE
except ImportError:
    CSV_DATA_AVAILABLE = False

warnings.filterwarnings("ignore")


class MLTradingBacktester:
    """
    Enhanced ML-driven backtester with multi-factor signal confirmation
    """

    def __init__(
        self,
        symbols: List[str],
        initial_capital: float,
        start_date: str,
        end_date: str,
        interval: str = "1d",  # Daily candles for better trend detection
        signal_threshold: float = 1.5,  # Lowered from 2.0% to allow more stable assets
        max_position_size: float = 0.6,  # Increased from 0.3
        transaction_cost: float = 0,
        # New parameters for enhanced strategy
        use_trend_filter: bool = True,
        use_rsi_filter: bool = True,
        use_volume_filter: bool = True,
        rsi_oversold: float = 25,
        rsi_overbought: float = 60,
        min_confidence: float = 0.35,  # Lowered from 0.5 to allow more trades
        trailing_stop_pct: float = 0.05,  # 5% trailing stop
        # NEW parameters for improved strategy
        stop_loss_pct: float = 0.03,  # 3% stop loss from entry
        trade_cooldown_periods: int = 6,  # 6 candles between trades
        required_confirmations: int = 2,  # Need 2 consecutive signals
        use_csv: bool = True,  # Use CSV data instead of API
    ):
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Keep dates timezone-naive to match CSV data format
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        # Remove timezone info if present (CSV data is tz-naive)
        self.start_date = (
            start_dt.tz_localize(None) if start_dt.tz is not None else start_dt
        )
        self.end_date = end_dt.tz_localize(None) if end_dt.tz is not None else end_dt

        self.interval = interval
        self.signal_threshold = signal_threshold
        self.max_position_size = max_position_size
        self.transaction_cost = transaction_cost

        # Enhanced strategy parameters
        self.use_trend_filter = use_trend_filter
        self.use_rsi_filter = use_rsi_filter
        self.use_volume_filter = use_volume_filter
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.min_confidence = min_confidence
        self.trailing_stop_pct = trailing_stop_pct

        # NEW: Stop loss and cooldown parameters
        self.stop_loss_pct = stop_loss_pct
        self.trade_cooldown_periods = trade_cooldown_periods
        self.required_confirmations = required_confirmations

        # Data source configuration
        self.use_csv = use_csv and CSV_DATA_AVAILABLE

        # Portfolio state
        self.positions = {symbol: 0.0 for symbol in symbols}
        self.entry_prices = {symbol: 0.0 for symbol in symbols}  # Track entry for P&L
        self.highest_prices = {symbol: 0.0 for symbol in symbols}  # For trailing stop

        # NEW: Trade cooldown tracking
        self.last_trade_time = {symbol: None for symbol in symbols}

        # NEW: Signal confirmation tracking
        self.signal_history = {symbol: [] for symbol in symbols}

        # NEW: Take-profit tracking
        self.take_profit_levels = [0.03, 0.05, 0.08]  # 3%, 5%, 8% profit targets
        self.take_profit_portions = [0.3, 0.3, 0.4]  # Sell 30%, 30%, 40% at each level
        self.take_profit_hit = {}  # Track which levels have been hit per symbol

        self.cash = initial_capital

        # Performance tracking
        self.portfolio_values = []
        self.trade_history = []
        self.predictions_log = []
        self.realized_pnl = []  # Track actual P&L per trade

        # DEBUG: Signal statistics per symbol
        self.signal_stats = {
            symbol: {
                "total_signals": 0,
                "raw_buy": 0,
                "raw_sell": 0,
                "raw_hold": 0,
                "final_buy": 0,
                "final_sell": 0,
                "final_hold": 0,
                "blocked_by_confidence": 0,
                "blocked_by_downtrend": 0,
                "blocked_by_confirmation": 0,
                "avg_pred_change": [],
            }
            for symbol in symbols
        }

        # ML predictors
        self.predictors = {}
        self._initialize_predictors()

    def _initialize_predictors(self):
        """Load or initialize ML predictors for each symbol"""
        print(f"Initializing ML predictors for {len(self.symbols)} assets...")

        for symbol in self.symbols:
            try:
                # Use 60 lookback periods for daily data, 168 for hourly
                lookback = (
                    60
                    if self.interval == "1d"
                    else (168 if self.interval == "1h" else 42)
                )
                predictor = IntradayPredictor(
                    symbol=symbol,
                    interval=self.interval,
                    lookback_periods=lookback,
                    use_csv=self.use_csv,
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
        """Fetch historical data for backtesting from CSV or yfinance"""
        print(f"\n{'='*60}")
        print(f"Fetching {self.interval} data for backtesting")
        print(f"Data source: {'CSV file' if self.use_csv else 'yfinance API'}")
        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print(f"{'='*60}")

        historical_data = {}

        for symbol in self.symbols:
            try:
                print(f"Fetching {symbol}...")
                extra_days = 120  # More buffer for indicators (especially daily data)

                # Use CSV data if available and interval is 1d
                if self.use_csv and self.interval == "1d":
                    data = get_symbol_data(
                        symbol,
                        start_date=self.start_date - timedelta(days=extra_days),
                        end_date=self.end_date,
                    )
                else:
                    # Fall back to yfinance API
                    data = yf.download(
                        symbol,
                        start=self.start_date - timedelta(days=extra_days),
                        end=self.end_date,
                        interval=self.interval,
                        progress=False,
                    )

                if data.empty:
                    raise ValueError(f"No data for {symbol}")

                # Flatten MultiIndex columns if present (happens with single ticker download)
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                print(f"  Retrieved {len(data)} raw candles")
                data = self._add_features(data)
                historical_data[symbol] = data
                print(f"  After feature engineering: {len(data)} periods available")

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                raise

        return historical_data

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive technical indicators"""
        # Create a deep copy to avoid issues
        df = df.copy(deep=True)

        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Moving Averages
        df["MA_10"] = df["Close"].rolling(window=10).mean()
        df["MA_20"] = df["Close"].rolling(window=20).mean()
        df["MA_50"] = df["Close"].rolling(window=50).mean()
        df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()

        # MACD
        df["MACD"] = df["EMA_12"] - df["EMA_26"]
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Histogram"] = df["MACD"] - df["MACD_Signal"]

        # RSI
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        bb_std = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (bb_std * 2)
        df["BB_Lower"] = df["BB_Middle"] - (bb_std * 2)
        df["BB_Position"] = (df["Close"] - df["BB_Lower"]) / (
            df["BB_Upper"] - df["BB_Lower"]
        )

        # Volume indicators
        df["Volume_MA"] = df["Volume"].rolling(window=20).mean()
        df["Volume_Ratio"] = df["Volume"] / df["Volume_MA"]
        df["Volume_Change"] = df["Volume"].pct_change()

        # Price action
        df["Price_Change"] = df["Close"].pct_change()
        df["Volatility"] = df["Close"].rolling(window=20).std()
        df["ATR"] = self._calculate_atr(df, period=14)

        # Trend strength
        df["ADX"] = self._calculate_adx(df, period=14)

        # Trend direction (1 = uptrend, -1 = downtrend, 0 = sideways)
        df["Trend"] = np.where(
            (df["MA_20"] > df["MA_50"]) & (df["Close"] > df["MA_20"]),
            1,
            np.where((df["MA_20"] < df["MA_50"]) & (df["Close"] < df["MA_20"]), -1, 0),
        )

        df = df.dropna()
        return df

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df["High"]
        low = df["Low"]
        close = df["Close"].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (trend strength)"""
        high = df["High"]
        low = df["Low"]
        close = df["Close"]

        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        atr = self._calculate_atr(df, period)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx.fillna(25)  # Default to moderate trend

    def _check_cooldown(self, symbol: str, current_idx: int) -> bool:
        """Check if enough time has passed since last trade"""
        if self.last_trade_time[symbol] is None:
            return True
        periods_since_last = current_idx - self.last_trade_time[symbol]
        return periods_since_last >= self.trade_cooldown_periods

    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """Check if stop loss is triggered (3% from entry)"""
        if self.positions[symbol] <= 0:
            return False

        entry_price = self.entry_prices[symbol]
        if entry_price <= 0:
            return False

        loss_pct = (entry_price - current_price) / entry_price
        return loss_pct >= self.stop_loss_pct

    def check_take_profit(self, symbol: str, current_price: float) -> Optional[float]:
        """Check if any take profit level is hit, return portion to sell"""
        if self.positions[symbol] <= 0:
            return None

        entry_price = self.entry_prices[symbol]
        if entry_price <= 0:
            return None

        profit_pct = (current_price - entry_price) / entry_price

        # Check each take profit level
        for i, (level, portion) in enumerate(
            zip(self.take_profit_levels, self.take_profit_portions)
        ):
            level_key = f"{symbol}_tp_{i}"
            if profit_pct >= level and not self.take_profit_hit.get(level_key, False):
                self.take_profit_hit[level_key] = True
                return portion  # Return portion to sell

        return None

    def _check_signal_confirmation(self, symbol: str, raw_signal: str) -> str:
        """Check if signal is confirmed by consecutive same signals"""
        self.signal_history[symbol].append(raw_signal)
        if len(self.signal_history[symbol]) > 5:
            self.signal_history[symbol].pop(0)

        recent = self.signal_history[symbol][-self.required_confirmations :]
        if len(recent) < self.required_confirmations:
            return "HOLD"

        if all(s == "BUY" for s in recent):
            if symbol in self.signal_stats:
                self.signal_stats[symbol]["final_buy"] += 1
            return "BUY"
        elif all(s == "SELL" for s in recent):
            if symbol in self.signal_stats:
                self.signal_stats[symbol]["final_sell"] += 1
            return "SELL"

        if symbol in self.signal_stats:
            self.signal_stats[symbol]["final_hold"] += 1
        return "HOLD"

    def _get_major_trend(self, data: pd.DataFrame) -> int:
        """Determine major trend using longer-term MAs"""
        if len(data) < 100:
            return 0

        ma_50 = float(data["Close"].rolling(50).mean().iloc[-1])
        ma_100 = (
            float(data["Close"].rolling(100).mean().iloc[-1])
            if len(data) >= 100
            else ma_50
        )
        current_price = float(data["Close"].iloc[-1])

        if current_price > ma_50 and ma_50 > ma_100:
            return 1  # Strong uptrend
        elif current_price < ma_50 and ma_50 < ma_100:
            return -1  # Strong downtrend
        return 0  # Sideways

    def generate_trading_signal(
        self, symbol: str, historical_slice: pd.DataFrame
    ) -> Dict:
        """
        Generate enhanced trading signal using ML prediction + technical confirmation
        """
        predictor = self.predictors.get(symbol)
        current_price = float(historical_slice["Close"].iloc[-1])

        # Get technical indicators
        rsi = (
            float(historical_slice["RSI"].iloc[-1]) if "RSI" in historical_slice else 50
        )
        trend = (
            int(historical_slice["Trend"].iloc[-1])
            if "Trend" in historical_slice
            else 0
        )
        volume_ratio = (
            float(historical_slice["Volume_Ratio"].iloc[-1])
            if "Volume_Ratio" in historical_slice
            else 1.0
        )
        macd_hist = (
            float(historical_slice["MACD_Histogram"].iloc[-1])
            if "MACD_Histogram" in historical_slice
            else 0
        )
        adx = (
            float(historical_slice["ADX"].iloc[-1]) if "ADX" in historical_slice else 25
        )
        bb_position = (
            float(historical_slice["BB_Position"].iloc[-1])
            if "BB_Position" in historical_slice
            else 0.5
        )

        if predictor is None or len(historical_slice) < 100:
            return self._technical_signal(historical_slice, symbol)

        try:
            prediction = predictor.predict_next(historical_slice)
            predicted_change = float(prediction["predicted_change_percent"])
            predicted_price = float(prediction["predicted_price"])

            # Calculate multi-factor confidence score (0-1)
            confidence = self._calculate_confidence(
                predicted_change=predicted_change,
                rsi=rsi,
                trend=trend,
                volume_ratio=volume_ratio,
                macd_hist=macd_hist,
                adx=adx,
                bb_position=bb_position,
            )

            # Get major trend for logging
            major_trend = (
                self._get_major_trend(historical_slice)
                if len(historical_slice) >= 100
                else 0
            )

            # Determine raw signal with confirmation
            raw_signal = self._determine_signal(
                predicted_change=predicted_change,
                confidence=confidence,
                rsi=rsi,
                trend=trend,
                volume_ratio=volume_ratio,
                bb_position=bb_position,
                current_position=self.positions[symbol],
                current_price=current_price,
                historical_data=historical_slice,
                symbol=symbol,  # Pass symbol for stats tracking
            )

            # NEW: Apply signal confirmation (require consecutive same signals)
            signal = self._check_signal_confirmation(symbol, raw_signal)

            # DEBUG LOGGING: Log when raw_signal differs from final signal or when BUY signals happen
            if raw_signal != signal or raw_signal == "BUY":
                print(
                    f"  [DEBUG] {symbol}: pred_change={predicted_change:+.2f}%, conf={confidence:.2f}, "
                    f"rsi={rsi:.1f}, trend={trend}, major_trend={major_trend}, "
                    f"raw={raw_signal} -> final={signal}"
                )

            return {
                "signal": signal,
                "predicted_price": predicted_price,
                "predicted_change": predicted_change,
                "current_price": current_price,
                "confidence": confidence,
                "rsi": rsi,
                "trend": trend,
                "volume_ratio": volume_ratio,
                "adx": adx,
                "raw_signal": raw_signal,  # Add raw signal for debugging
                "major_trend": major_trend,  # Add major trend for debugging
            }

        except Exception as e:
            return self._technical_signal(historical_slice, symbol)

    def _calculate_confidence(
        self,
        predicted_change: float,
        rsi: float,
        trend: int,
        volume_ratio: float,
        macd_hist: float,
        adx: float,
        bb_position: float,
    ) -> float:
        """
        Calculate multi-factor confidence score (0-1)
        Higher = more confident in the trade
        """
        score = 0.0
        max_score = 0.0

        # 1. ML Prediction strength (0-0.25) - reduced weight, lower threshold
        # Use 2% as full strength instead of 5% to account for stable assets like BTC
        pred_strength = min(abs(predicted_change) / 2.0, 1.0)  # Cap at 2%
        score += pred_strength * 0.25
        max_score += 0.25

        # 1b. Bonus for having ANY directional prediction (0-0.10)
        # This ensures even small predictions contribute to confidence
        if abs(predicted_change) > 0.5:  # At least 0.5% prediction
            score += 0.10
        max_score += 0.10

        # 2.  Trend alignment (0-0.25)
        if predicted_change > 0 and trend == 1:
            score += 0.25
        elif predicted_change < 0 and trend == -1:
            score += 0.25
        elif trend == 0:
            score += 0.1  # Neutral trend, partial credit
        max_score += 0.25

        # 3. RSI confirmation (0-0.15)
        if predicted_change > 0 and rsi < 70:  # Buy signal, not overbought
            rsi_score = (70 - rsi) / 40  # Higher score when RSI is lower
            score += min(rsi_score, 1.0) * 0.15
        elif predicted_change < 0 and rsi > 30:  # Sell signal, not oversold
            rsi_score = (rsi - 30) / 40
            score += min(rsi_score, 1.0) * 0.15
        max_score += 0.15

        # 4. Volume confirmation (0-0.10)
        if volume_ratio > 1.0:  # Above average volume
            volume_score = min((volume_ratio - 1.0) / 1.0, 1.0)
            score += volume_score * 0.10
        max_score += 0.10

        # 5. MACD alignment (0-0.10)
        if (predicted_change > 0 and macd_hist > 0) or (
            predicted_change < 0 and macd_hist < 0
        ):
            score += 0.10
        max_score += 0.10

        # 6. ADX trend strength (0-0.05)
        if adx > 25:  # Strong trend
            adx_score = min((adx - 25) / 25, 1.0)
            score += adx_score * 0.05
        max_score += 0.05

        # Cap confidence at 1.0 to ensure valid probability range
        return min(score / max_score, 1.0) if max_score > 0 else 0.0

    def _determine_signal(
        self,
        predicted_change: float,
        confidence: float,
        rsi: float,
        trend: int,
        volume_ratio: float,
        bb_position: float,
        current_position: float,
        current_price: float,
        historical_data: pd.DataFrame = None,
        symbol: str = None,  # NEW: Add symbol for stats tracking
    ) -> str:
        """
        Determine trading signal with multi-factor confirmation
        """
        # Track stats if symbol provided
        if symbol and symbol in self.signal_stats:
            self.signal_stats[symbol]["total_signals"] += 1
            self.signal_stats[symbol]["avg_pred_change"].append(predicted_change)

        # Check minimum confidence threshold
        if confidence < self.min_confidence:
            if symbol and symbol in self.signal_stats:
                self.signal_stats[symbol]["blocked_by_confidence"] += 1
            return "HOLD"

        # Get major trend (informational, not blocking)
        major_trend = 0
        if historical_data is not None:
            major_trend = self._get_major_trend(historical_data)

        # Strong BUY conditions
        if predicted_change > self.signal_threshold:
            # In strong downtrends, require higher predicted change (not complete block)
            effective_threshold = self.signal_threshold
            if major_trend == -1:
                effective_threshold = (
                    self.signal_threshold * 1.5
                )  # 50% higher threshold

            if predicted_change <= effective_threshold:
                if symbol and symbol in self.signal_stats:
                    self.signal_stats[symbol]["blocked_by_downtrend"] += 1
                return "HOLD"

            buy_confirmations = 0

            # Confirmation 1: Trend alignment (or oversold bounce)
            if self.use_trend_filter:
                if trend >= 0 or rsi < self.rsi_oversold:
                    buy_confirmations += 1
            else:
                buy_confirmations += 1

            # Confirmation 2: RSI not overbought (or momentum buy)
            if self.use_rsi_filter:
                if rsi < self.rsi_overbought or (rsi > 50 and rsi < 65 and trend == 1):
                    buy_confirmations += 1
            else:
                buy_confirmations += 1

            # Confirmation 3: Volume support
            if self.use_volume_filter:
                if volume_ratio > 0.8:  # At least 80% of average volume
                    buy_confirmations += 1
            else:
                buy_confirmations += 1

            # Need at least 2 confirmations to buy
            if buy_confirmations >= 2:
                if symbol and symbol in self.signal_stats:
                    self.signal_stats[symbol]["raw_buy"] += 1
                return "BUY"
            else:
                # Log why BUY was not generated
                if symbol and symbol in self.signal_stats:
                    self.signal_stats[symbol]["blocked_by_confirmation"] += 1

        # Strong SELL conditions
        elif predicted_change < -self.signal_threshold:
            sell_confirmations = 0

            # Confirmation 1: Trend alignment (or overbought reversal)
            if self.use_trend_filter:
                if trend <= 0 or rsi > self.rsi_overbought:
                    sell_confirmations += 1
            else:
                sell_confirmations += 1

            # Confirmation 2: RSI not oversold
            if self.use_rsi_filter:
                if rsi > self.rsi_oversold:
                    sell_confirmations += 1
            else:
                sell_confirmations += 1

            # Confirmation 3: Have position to sell
            if current_position > 0:
                sell_confirmations += 1

            if sell_confirmations >= 2:
                if symbol and symbol in self.signal_stats:
                    self.signal_stats[symbol]["raw_sell"] += 1
                return "SELL"

        # Check for RSI extremes (mean reversion opportunities)
        # Allow oversold bounce even in downtrends if RSI is very low (extreme oversold)
        if rsi < 25 and predicted_change > 0 and current_position == 0:
            # Extra caution in downtrends - require very strong oversold
            if major_trend == -1 and rsi > 20:
                return "HOLD"
            return "BUY"  # Oversold bounce
        elif rsi > 75 and current_position > 0:
            return "SELL"  # Overbought, take profit

        return "HOLD"

    def _technical_signal(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Enhanced fallback technical signal"""
        current_price = float(data["Close"].iloc[-1])

        # Get indicators
        ma_20 = float(data["MA_20"].iloc[-1]) if "MA_20" in data else current_price
        ma_50 = float(data["MA_50"].iloc[-1]) if "MA_50" in data else current_price
        rsi = float(data["RSI"].iloc[-1]) if "RSI" in data else 50
        macd_hist = (
            float(data["MACD_Histogram"].iloc[-1]) if "MACD_Histogram" in data else 0
        )

        # Multi-factor technical signal
        bullish_signals = 0
        bearish_signals = 0

        # MA crossover
        if ma_20 > ma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        # Price vs MA
        if current_price > ma_20:
            bullish_signals += 1
        else:
            bearish_signals += 1

        # RSI
        if rsi < 40:
            bullish_signals += 1
        elif rsi > 60:
            bearish_signals += 1

        # MACD
        if macd_hist > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if bullish_signals >= 3:
            signal = "BUY"
        elif bearish_signals >= 3:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "predicted_price": current_price,
            "predicted_change": 0.0,
            "current_price": current_price,
            "confidence": 0.4,
            "rsi": rsi,
            "trend": 1 if ma_20 > ma_50 else -1,
            "volume_ratio": 1.0,
            "adx": 25,
        }

    def calculate_position_size(self, symbol: str, signal_data: Dict) -> float:
        """
        Enhanced position sizing with Kelly Criterion influence
        """
        if signal_data["signal"] == "HOLD":
            return 0.0

        # Calculate current portfolio value
        total_value = self.cash
        for sym in self.symbols:
            total_value += self.positions[sym] * signal_data.get("current_price", 0)

        self.current_capital = total_value

        # Maximum position value based on confidence
        base_position = self.current_capital * self.max_position_size
        confidence = signal_data["confidence"]

        # Scale position by confidence (minimum 30% of max, maximum 100%)
        confidence_multiplier = 0.3 + (confidence * 0.7)
        max_position_value = base_position * confidence_multiplier

        current_price = signal_data["current_price"]
        current_position_value = self.positions[symbol] * current_price

        if signal_data["signal"] == "BUY":
            # Available cash to deploy
            available_cash = self.cash * 0.95  # Keep 5% reserve
            room_to_buy = max_position_value - current_position_value

            # Don't over-allocate
            position_size = min(available_cash, room_to_buy)
            return max(position_size, 0)

        elif signal_data["signal"] == "SELL":
            # Sell proportion based on confidence
            # Higher confidence = sell more
            sell_ratio = 0.3 + (confidence * 0.5)  # 30% to 80% of position
            return (
                current_position_value * sell_ratio
                if current_position_value > 0
                else 0.0
            )

        return 0.0

    def check_trailing_stop(self, symbol: str, current_price: float) -> bool:
        """Check if trailing stop is triggered"""
        if self.positions[symbol] <= 0:
            return False

        # Update highest price
        if current_price > self.highest_prices[symbol]:
            self.highest_prices[symbol] = current_price

        # Check if price dropped below trailing stop
        if self.highest_prices[symbol] > 0:
            drop_pct = (
                self.highest_prices[symbol] - current_price
            ) / self.highest_prices[symbol]
            if drop_pct > self.trailing_stop_pct:
                return True

        return False

    def execute_trade(
        self,
        symbol: str,
        signal_data: Dict,
        timestamp: pd.Timestamp,
        current_idx: int = 0,
    ):
        """Execute trade based on signal with P&L tracking"""
        current_price = float(signal_data["current_price"])

        # NEW: Check take-profit levels first (before other logic)
        take_profit_portion = self.check_take_profit(symbol, current_price)
        if take_profit_portion is not None:
            coins_to_sell = self.positions[symbol] * take_profit_portion
            if coins_to_sell > 0:
                proceeds = coins_to_sell * current_price * (1 - self.transaction_cost)

                entry_price = self.entry_prices[symbol]
                pnl = (
                    (current_price - entry_price) * coins_to_sell
                    if entry_price > 0
                    else 0
                )
                self.realized_pnl.append(
                    {"symbol": symbol, "pnl": pnl, "type": "take_profit"}
                )

                self.positions[symbol] -= coins_to_sell
                self.cash += proceeds
                self.last_trade_time[symbol] = current_idx

                # Reset take-profit tracking if position fully closed
                if self.positions[symbol] <= 0.0001:
                    self.entry_prices[symbol] = 0
                    self.highest_prices[symbol] = 0
                    for i in range(len(self.take_profit_levels)):
                        self.take_profit_hit[f"{symbol}_tp_{i}"] = False

                self.trade_history.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "SELL",
                        "coins": float(coins_to_sell),
                        "price": float(current_price),
                        "value": float(proceeds),
                        "predicted_change": signal_data.get("predicted_change", 0),
                        "confidence": signal_data.get("confidence", 0),
                        "reason": "take_profit",
                        "pnl": pnl,
                    }
                )
                return

        # NEW: Check stop loss (3% fixed)
        if self.check_stop_loss(symbol, current_price):
            if self.positions[symbol] > 0:
                coins_to_sell = self.positions[symbol]
                proceeds = coins_to_sell * current_price * (1 - self.transaction_cost)

                entry_price = self.entry_prices[symbol]
                pnl = (
                    (current_price - entry_price) * coins_to_sell
                    if entry_price > 0
                    else 0
                )
                self.realized_pnl.append(
                    {"symbol": symbol, "pnl": pnl, "type": "stop_loss"}
                )

                self.cash += proceeds
                self.positions[symbol] = 0
                self.entry_prices[symbol] = 0
                self.highest_prices[symbol] = 0
                self.last_trade_time[symbol] = current_idx
                # Reset take-profit tracking
                for i in range(len(self.take_profit_levels)):
                    self.take_profit_hit[f"{symbol}_tp_{i}"] = False

                self.trade_history.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "SELL",
                        "coins": float(coins_to_sell),
                        "price": float(current_price),
                        "value": float(proceeds),
                        "predicted_change": signal_data.get("predicted_change", 0),
                        "confidence": signal_data.get("confidence", 0),
                        "reason": "stop_loss",
                        "pnl": pnl,
                    }
                )
                return

        # Check trailing stop
        if self.check_trailing_stop(symbol, current_price):
            # Force sell on trailing stop
            if self.positions[symbol] > 0:
                coins_to_sell = self.positions[symbol]
                proceeds = coins_to_sell * current_price * (1 - self.transaction_cost)

                # Calculate P&L
                entry_price = self.entry_prices[symbol]
                pnl = (
                    (current_price - entry_price) * coins_to_sell
                    if entry_price > 0
                    else 0
                )
                self.realized_pnl.append(
                    {"symbol": symbol, "pnl": pnl, "type": "trailing_stop"}
                )

                self.cash += proceeds
                self.positions[symbol] = 0
                self.entry_prices[symbol] = 0
                self.highest_prices[symbol] = 0
                self.last_trade_time[symbol] = current_idx
                # Reset take-profit tracking
                for i in range(len(self.take_profit_levels)):
                    self.take_profit_hit[f"{symbol}_tp_{i}"] = False

                self.trade_history.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "SELL",
                        "coins": float(coins_to_sell),
                        "price": float(current_price),
                        "value": float(proceeds),
                        "predicted_change": signal_data.get("predicted_change", 0),
                        "confidence": signal_data.get("confidence", 0),
                        "reason": "trailing_stop",
                        "pnl": pnl,
                    }
                )
                return

        # NEW: Check cooldown before processing signals
        if not self._check_cooldown(symbol, current_idx):
            return

        position_size = self.calculate_position_size(symbol, signal_data)

        if abs(position_size) < 50:  # Minimum $50 trade
            return

        if signal_data["signal"] == "BUY":
            coins_to_buy = (position_size * (1 - self.transaction_cost)) / current_price
            cost = position_size

            if cost <= self.cash:
                # Update average entry price
                total_coins = self.positions[symbol] + coins_to_buy
                if total_coins > 0:
                    old_value = self.positions[symbol] * self.entry_prices[symbol]
                    new_value = coins_to_buy * current_price
                    self.entry_prices[symbol] = (old_value + new_value) / total_coins

                self.positions[symbol] += coins_to_buy
                self.cash -= cost
                self.highest_prices[symbol] = current_price  # Reset trailing stop
                self.last_trade_time[symbol] = current_idx  # NEW: Track trade time

                self.trade_history.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "BUY",
                        "coins": float(coins_to_buy),
                        "price": float(current_price),
                        "value": float(cost),
                        "predicted_change": float(
                            signal_data.get("predicted_change", 0)
                        ),
                        "confidence": float(signal_data.get("confidence", 0)),
                        "reason": "ml_signal",
                        "rsi": signal_data.get("rsi", 50),
                    }
                )

        elif signal_data["signal"] == "SELL":
            # NEW: Improve sell logic - don't sell at loss unless necessary
            if self.positions[symbol] > 0:
                entry_price = self.entry_prices[symbol]
                is_in_profit = current_price > entry_price
                is_strong_bearish = (
                    signal_data.get("confidence", 0) > 0.7
                    and signal_data.get("predicted_change", 0) < -2.0
                )

                # Don't sell at a loss without strong reason
                if not is_in_profit and not is_strong_bearish:
                    return

            value_to_sell = position_size
            coins_to_sell = min(value_to_sell / current_price, self.positions[symbol])

            if coins_to_sell > 0:
                proceeds = coins_to_sell * current_price * (1 - self.transaction_cost)

                # Calculate P&L
                entry_price = self.entry_prices[symbol]
                pnl = (
                    (current_price - entry_price) * coins_to_sell
                    if entry_price > 0
                    else 0
                )
                self.realized_pnl.append(
                    {"symbol": symbol, "pnl": pnl, "type": "signal"}
                )

                self.positions[symbol] -= coins_to_sell
                self.cash += proceeds
                self.last_trade_time[symbol] = current_idx  # NEW: Track trade time

                # Reset entry price if position closed
                if self.positions[symbol] <= 0.0001:
                    self.entry_prices[symbol] = 0
                    self.highest_prices[symbol] = 0
                    # Reset take-profit tracking
                    for i in range(len(self.take_profit_levels)):
                        self.take_profit_hit[f"{symbol}_tp_{i}"] = False

                self.trade_history.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "SELL",
                        "coins": float(coins_to_sell),
                        "price": float(current_price),
                        "value": float(proceeds),
                        "predicted_change": float(
                            signal_data.get("predicted_change", 0)
                        ),
                        "confidence": float(signal_data.get("confidence", 0)),
                        "reason": "ml_signal",
                        "pnl": pnl,
                        "rsi": signal_data.get("rsi", 50),
                    }
                )

    def run_backtest(self) -> Dict:
        """Run complete ML-driven backtest"""
        print(f"\n{'='*60}")
        print(f"Running Enhanced ML-Driven Backtest")
        print(f"Strategy: ML Predictions + Technical Confirmation")
        print(f"{'='*60}")

        historical_data = self.fetch_historical_data()

        all_timestamps = set(historical_data[self.symbols[0]].index)
        for symbol in self.symbols[1:]:
            all_timestamps &= set(historical_data[symbol].index)

        timestamps = sorted([ts for ts in all_timestamps if ts >= self.start_date])

        print(f"\nBacktesting {len(timestamps)} periods...")
        print(f"Signal threshold: {self.signal_threshold}%")
        print(f"Min confidence: {self.min_confidence}")

        min_lookback = 168 if self.interval == "1h" else 100

        for i, timestamp in enumerate(timestamps):
            if i % 100 == 0:
                print(
                    f"  Progress: {i}/{len(timestamps)} ({i/len(timestamps)*100:.1f}%)"
                )

            for symbol in self.symbols:
                try:
                    historical_slice = historical_data[symbol][
                        historical_data[symbol].index <= timestamp
                    ]

                    if len(historical_slice) < min_lookback:
                        continue

                    signal_data = self.generate_trading_signal(symbol, historical_slice)
                    self.execute_trade(symbol, signal_data, timestamp, current_idx=i)

                    # Log prediction vs actual ONLY if we have next candle data
                    if i < len(timestamps) - 1:
                        next_timestamp = timestamps[i + 1]
                        # CRITICAL: Use < not <= to get data BEFORE next timestamp
                        # We want the close price AT next_timestamp, not after it
                        next_data = historical_data[symbol][
                            historical_data[symbol].index == next_timestamp
                        ]
                        if not next_data.empty:
                            actual_next_price = float(next_data["Close"].iloc[0])

                            # Only log if we have valid future data
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

            # Calculate portfolio value
            portfolio_value = self.cash
            for symbol in self.symbols:
                current_data = historical_data[symbol][
                    historical_data[symbol].index <= timestamp
                ]
                if not current_data.empty:
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

        # DEBUG: Print signal statistics summary
        print(f"\n{'='*60}")
        print(f"📊 SIGNAL STATISTICS SUMMARY")
        print(f"{'='*60}")
        for symbol in self.symbols:
            stats = self.signal_stats[symbol]
            avg_pred = (
                sum(stats["avg_pred_change"]) / len(stats["avg_pred_change"])
                if stats["avg_pred_change"]
                else 0
            )
            print(f"\n🔹 {symbol}:")
            print(f"   Total signal evaluations: {stats['total_signals']}")
            print(f"   Avg predicted change: {avg_pred:+.2f}%")
            print(f"   Raw BUY signals: {stats['raw_buy']}")
            print(f"   Raw SELL signals: {stats['raw_sell']}")
            print(f"   Final BUY signals (confirmed): {stats['final_buy']}")
            print(f"   Final SELL signals (confirmed): {stats['final_sell']}")
            print(f"   --- Blocked by ---")
            print(
                f"   Low confidence (<{self.min_confidence}): {stats['blocked_by_confidence']}"
            )
            print(f"   Downtrend filter: {stats['blocked_by_downtrend']}")
            print(f"   Failed confirmations: {stats['blocked_by_confirmation']}")
        print(f"\n{'='*60}")

        return self._calculate_performance_metrics()

    def _calculate_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics with actual P&L"""
        if not self.portfolio_values:
            raise ValueError("No portfolio values to analyze")

        portfolio_df = pd.DataFrame(self.portfolio_values)
        portfolio_df.set_index("timestamp", inplace=True)
        portfolio_df["returns"] = portfolio_df["portfolio_value"].pct_change()

        final_value = portfolio_df["portfolio_value"].iloc[-1]
        total_return = (
            (final_value - self.initial_capital) / self.initial_capital
        ) * 100

        days = (self.end_date - self.start_date).days
        years = days / 365.0
        annualized_return = (
            ((final_value / self.initial_capital) ** (1 / years) - 1) * 100
            if years > 0
            else 0
        )

        # Handle NaN values in volatility calculation
        volatility_raw = portfolio_df["returns"].std() * np.sqrt(252) * 100
        volatility = float(volatility_raw) if not np.isnan(volatility_raw) else 0.0
        sharpe_ratio = (annualized_return - 2) / volatility if volatility > 0 else 0.0

        cumulative_returns = (1 + portfolio_df["returns"]).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = ((cumulative_returns - running_max) / running_max) * 100
        max_drawdown_raw = drawdown.min()
        max_drawdown = (
            float(max_drawdown_raw) if not np.isnan(max_drawdown_raw) else 0.0
        )

        # Actual win rate from realized P&L
        num_trades = len(self.trade_history)
        sell_trades = [t for t in self.trade_history if t["action"] == "SELL"]
        winning_sells = [t for t in sell_trades if t.get("pnl", 0) > 0]
        win_rate = (len(winning_sells) / len(sell_trades) * 100) if sell_trades else 0.0

        total_pnl = sum(p["pnl"] for p in self.realized_pnl)

        # Calculate avg_win with NaN handling
        wins = [t.get("pnl", 0) for t in sell_trades if t.get("pnl", 0) > 0]
        avg_win_raw = np.mean(wins) if wins else 0
        avg_win = float(avg_win_raw) if not np.isnan(avg_win_raw) else 0.0

        # Calculate avg_loss with NaN handling
        losses = [t.get("pnl", 0) for t in sell_trades if t.get("pnl", 0) <= 0]
        avg_loss_raw = np.mean(losses) if losses else 0
        avg_loss = float(avg_loss_raw) if not np.isnan(avg_loss_raw) else 0.0

        buy_trades = [t for t in self.trade_history if t["action"] == "BUY"]

        # NEW: Track trade outcomes by reason
        take_profit_trades = [
            t for t in self.trade_history if t.get("reason") == "take_profit"
        ]
        stop_loss_trades = [
            t for t in self.trade_history if t.get("reason") == "stop_loss"
        ]
        trailing_stop_trades = [
            t for t in self.trade_history if t.get("reason") == "trailing_stop"
        ]

        return {
            "success": True,
            "summary": {
                "initial_capital": float(self.initial_capital),
                "final_value": float(final_value),
                "total_return": float(total_return),
                "annualized_return": float(annualized_return),
                "volatility": float(volatility),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
            },
            "trading_stats": {
                "total_trades": int(num_trades),
                "buy_trades": int(len(buy_trades)),
                "sell_trades": int(len(sell_trades)),
                "win_rate": float(win_rate),
                "avg_trade_size": float(
                    np.mean([t["value"] for t in self.trade_history])
                    if num_trades > 0
                    else 0
                ),
                "total_realized_pnl": float(total_pnl),
                "avg_win": float(avg_win),
                "avg_loss": float(avg_loss),
                "take_profit_trades": int(len(take_profit_trades)),
                "stop_loss_trades": int(len(stop_loss_trades)),
                "trailing_stop_trades": int(len(trailing_stop_trades)),
            },
            "final_positions": {
                symbol: {
                    "coins": position,
                    "value": position * portfolio_df["portfolio_value"].iloc[-1],
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
                "min_confidence": self.min_confidence,
                "trailing_stop_pct": self.trailing_stop_pct,
                "stop_loss_pct": self.stop_loss_pct,
                "trade_cooldown_periods": self.trade_cooldown_periods,
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
Enhanced ML-Driven Trading Backtest Results
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
  Total Realized P&L: ${trading['total_realized_pnl']:,.2f}
  Take-Profit Trades: {trading['take_profit_trades']}
  Stop-Loss Trades: {trading['stop_loss_trades']}
  Trailing-Stop Trades: {trading['trailing_stop_trades']}

Strategy Configuration:
  Signal Threshold: {self.signal_threshold}%
  Min Confidence: {self.min_confidence}
  Max Position Size: {self.max_position_size*100}%
  Trailing Stop: {self.trailing_stop_pct*100}%
  Stop Loss: {self.stop_loss_pct*100}%
  Trade Cooldown: {self.trade_cooldown_periods} periods
  Required Confirmations: {self.required_confirmations}
"""


def ml_backtest_portfolio(
    symbols: List[str],
    initial_capital: float = 100000,
    start_date: str = None,
    end_date: str = None,
    interval: str = "1d",  # Daily candles (1d) for better results
    signal_threshold: float = 2.0,
    use_csv: bool = True,  # Use CSV data instead of API
) -> Dict:
    """Convenience function to run ML-driven backtest"""
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime(
            "%Y-%m-%d"
        )  # 1 year default for daily
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    backtester = MLTradingBacktester(
        symbols=symbols,
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        signal_threshold=signal_threshold,
        use_csv=use_csv,
    )

    return backtester.run_backtest()


if __name__ == "__main__":
    print("Enhanced ML-Driven Trading Backtest Demo")
    print("=" * 60)
    print("Using daily (1d) candles with CSV data source")
    print("=" * 60)

    symbols = ["BTC-USD", "ETH-USD"]

    backtester = MLTradingBacktester(
        symbols=symbols,
        initial_capital=100000,
        start_date="2024-01-01",  # Longer period for daily data
        end_date="2024-11-29",
        interval="1d",  # Daily candles
        signal_threshold=2.0,
        use_csv=True,  # Use CSV data
    )

    results = backtester.run_backtest()
    print(backtester.get_performance_summary())
