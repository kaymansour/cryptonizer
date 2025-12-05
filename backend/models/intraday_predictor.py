"""
Cryptocurrency Price Predictor using LSTM
Trains models on daily (1d) candle data for trading signals

Data Source: Pre-downloaded CSV with 11+ years of historical data
Interval: Daily (1d) candles for better trend detection
"""

import argparse
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from keras.models import Sequential, load_model
from keras.layers import Dense, LSTM, Dropout, Input
from keras.regularizers import l2
from keras.callbacks import EarlyStopping, Callback
from keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
import pickle
import os
import sys
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import CSV data loader
try:
    from services.csv_data_loader import get_symbol_data, get_available_symbols

    CSV_DATA_AVAILABLE = True
except ImportError:
    CSV_DATA_AVAILABLE = False
    print("⚠️  CSV data loader not available, using yfinance API")


class TrainingLogger(Callback):
    """Custom callback to log training progress per epoch"""

    def __init__(self, symbol: str = ""):
        super().__init__()
        self.symbol = symbol

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        train_loss = logs.get("loss", 0)
        val_loss = logs.get("val_loss", 0)
        train_mae = logs.get("mae", 0)
        val_mae = logs.get("val_mae", 0)

        # Calculate if model is overfitting (train much better than val)
        overfit_ratio = val_loss / train_loss if train_loss > 0 else 1
        overfit_warning = " ⚠️ OVERFITTING" if overfit_ratio > 1.5 else ""

        print(
            f"Epoch {epoch + 1:3d} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f} | "
            f"Train MAE: {train_mae:.6f} | Val MAE: {val_mae:.6f} | "
            f"Ratio: {overfit_ratio:.2f}{overfit_warning}"
        )


class IntradayPredictor:
    """
    LSTM-based price predictor for intraday trading (1h or 4h candles)
    """

    # Feature columns used for prediction (defined once as class constant)
    FEATURE_COLUMNS = [
        "Close",
        "Volume",
        "MA_20",
        "MA_50",
        "RSI",
        "Price_Change",
        "Volatility",
    ]

    def __init__(
        self,
        symbol: str,
        interval: str = "1d",  # Daily candles (1d) - primary interval
        lookback_periods: int = 60,  # 60 days (~2 months) of daily data
        prediction_horizon: int = 1,  # Predict next candle
        use_csv: bool = True,  # Use CSV data instead of API
    ):
        self.symbol = symbol
        self.interval = interval
        self.lookback_periods = lookback_periods
        self.prediction_horizon = prediction_horizon
        self.use_csv = use_csv and CSV_DATA_AVAILABLE
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model_path = f"models/{symbol}_{interval}_predictor.keras"
        self.scaler_path = f"models/{symbol}_{interval}_scaler.pkl"

    def fetch_intraday_data(self, days_back: int = 2000) -> pd.DataFrame:
        """
        Fetch price data from CSV or yfinance API

        CSV data: Up to 11+ years of daily data (preferred)
        yfinance API: Limited to ~2 years for intraday intervals

        Args:
            days_back: Number of days of historical data to fetch
                      Default: 2000 (use more data from CSV for better training)
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            print(f"Fetching {self.interval} data for {self.symbol}...")
            print(f"Period: {start_date.date()} to {end_date.date()}")

            # Use CSV data if available (preferred for 1d interval)
            if self.use_csv and self.interval == "1d":
                print("📂 Using CSV data source (faster, more data)")
                data = get_symbol_data(
                    self.symbol, start_date=start_date, end_date=end_date
                )
            else:
                # Fall back to yfinance API for non-daily intervals
                print("🌐 Using yfinance API")
                data = yf.download(
                    self.symbol,
                    start=start_date,
                    end=end_date,
                    interval=self.interval,
                    progress=False,
                )

            if data.empty:
                raise ValueError(f"No data retrieved for {self.symbol}")

            print(f"✅ Retrieved {len(data)} {self.interval} candles")

            # Verify the interval by checking time differences
            if len(data) > 1:
                time_diff = data.index[1] - data.index[0]
                print(
                    f"✅ Verified interval: First candle time difference = {time_diff}"
                )

                # Calculate expected candles for verification
                days_diff = (end_date - start_date).days
                if self.interval == "4h":
                    expected_candles = days_diff * 6  # 6 candles per day for 4h
                    print(
                        f"   Expected ~{expected_candles} candles for {days_diff} days at 4h interval"
                    )
                elif self.interval == "1h":
                    expected_candles = days_diff * 24  # 24 candles per day for 1h
                    print(
                        f"   Expected ~{expected_candles} candles for {days_diff} days at 1h interval"
                    )
                elif self.interval == "1d":
                    expected_candles = days_diff  # 1 candle per day
                    print(
                        f"   Expected ~{expected_candles} candles for {days_diff} days at 1d interval"
                    )

            # Return raw data - features will be added when needed
            return data

        except Exception as e:
            raise Exception(f"Error fetching data: {str(e)}")

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators as features for better predictions
        """
        # Work with a copy to avoid SettingWithCopyWarning
        df = df.copy()

        # Moving averages
        df["MA_20"] = df["Close"].rolling(window=20).mean()
        df["MA_50"] = df["Close"].rolling(window=50).mean()

        # RSI
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # Volume change
        df["Volume_Change"] = df["Volume"].pct_change()

        # Price change
        df["Price_Change"] = df["Close"].pct_change()

        # Volatility (rolling std)
        df["Volatility"] = df["Close"].rolling(window=20).std()

        # Drop NaN values and reset index to ensure clean integer index
        df = df.dropna().reset_index(drop=True)

        return df

    def prepare_training_data(
        self, data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare data for LSTM training with multiple features
        FIXED: Split data BEFORE scaling to prevent data leakage
        FIXED: Predict returns (% change) instead of absolute prices to avoid autocorrelation
        """
        # Add technical indicators first
        data = self._add_features(data)

        # Select features for prediction using class constant
        features = data[self.FEATURE_COLUMNS].values

        # Create sequences BEFORE scaling and splitting
        X, y = [], []
        for i in range(self.lookback_periods, len(features) - self.prediction_horizon):
            X.append(features[i - self.lookback_periods : i])
            # Predict PERCENTAGE CHANGE instead of absolute price
            # This avoids the autocorrelation problem
            current_price = features[i, 0]  # Close price at current timestep
            future_price = features[
                i + self.prediction_horizon, 0
            ]  # Close price at future timestep
            percentage_change = (future_price - current_price) / current_price
            y.append(percentage_change)

        X, y = np.array(X), np.array(y)

        # Split into train and test FIRST
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Fit scaler ONLY on training data for X
        # Reshape for scaling: (samples * timesteps, features)
        X_train_reshaped = X_train.reshape(-1, X_train.shape[2])
        self.scaler.fit(X_train_reshaped)

        # Transform both train and test X
        X_train_scaled = self.scaler.transform(X_train_reshaped).reshape(X_train.shape)
        X_test_reshaped = X_test.reshape(-1, X_test.shape[2])
        X_test_scaled = self.scaler.transform(X_test_reshaped).reshape(X_test.shape)

        # For y (percentage returns), we DON'T scale - they're already normalized
        # Returns are naturally bounded (typically -10% to +10% for most candles)
        # and scaling them would lose interpretability
        y_train_scaled = y_train
        y_test_scaled = y_test

        print(f"Training data shape: {X_train_scaled.shape}")
        print(f"Test data shape: {X_test_scaled.shape}")
        print(f"Predicting returns (not absolute prices)")

        return X_train_scaled, y_train_scaled, X_test_scaled, y_test_scaled

    def build_model(
        self, input_shape: Tuple, learning_rate: float = 0.0002
    ) -> Sequential:
        """
        Build LSTM model for price prediction with regularization
        Output: Predicted percentage return (not absolute price)

        Args:
            input_shape: Shape of input data (timesteps, features)
            learning_rate: Learning rate for Adam optimizer (default: 0.0002)
        """
        model = Sequential(
            [
                Input(shape=input_shape),
                LSTM(128, return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
                Dropout(0.2),
                LSTM(64, return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
                Dropout(0.2),
                LSTM(32, dropout=0.2, recurrent_dropout=0.2),
                Dropout(0.2),
                Dense(16, activation="relu", kernel_regularizer=l2(0.001)),
                Dense(1),  # Output: percentage return (e.g., 0.02 for +2%)
            ]
        )

        optimizer = Adam(learning_rate=learning_rate)
        model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])
        print(f"Model compiled with learning rate: {learning_rate}")
        return model

    def train(
        self,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.0002,
        patience: int = 10,
    ) -> Dict:
        """
        Train the LSTM model with early stopping and detailed logging

        Args:
            epochs: Maximum number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for Adam optimizer
            patience: Early stopping patience (epochs without improvement)
        """
        print(f"\n{'='*80}")
        print(f"Training model for {self.symbol} ({self.interval} candles)")
        print(f"{'='*80}")
        print(f"Hyperparameters:")
        print(f"  - Epochs: {epochs}")
        print(f"  - Batch Size: {batch_size}")
        print(f"  - Learning Rate: {learning_rate}")
        print(f"  - Early Stop Patience: {patience}")
        print(f"{'='*80}\n")

        # Fetch and prepare data
        data = self.fetch_intraday_data()
        X_train, y_train, X_test, y_test = self.prepare_training_data(data)

        # Build model with configurable learning rate
        self.model = self.build_model(
            (X_train.shape[1], X_train.shape[2]), learning_rate=learning_rate
        )

        # Callbacks
        early_stop = EarlyStopping(
            monitor="val_loss", patience=patience, restore_best_weights=True, verbose=1
        )

        training_logger = TrainingLogger(symbol=self.symbol)

        print(
            f"\n{'Epoch':>5} | {'Train Loss':>12} | {'Val Loss':>12} | {'Train MAE':>12} | {'Val MAE':>12} | {'Ratio':>6}"
        )
        print("-" * 80)

        # Train with verbose=0 since we have custom logging
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, training_logger],
            verbose=0,  # Disabled default logging, using custom logger
        )

        # Training summary
        print(f"\n{'='*80}")
        print("TRAINING SUMMARY")
        print(f"{'='*80}")

        epochs_trained = len(history.history["loss"])
        final_train_loss = history.history["loss"][-1]
        final_val_loss = history.history["val_loss"][-1]
        best_val_loss = min(history.history["val_loss"])
        best_epoch = history.history["val_loss"].index(best_val_loss) + 1

        print(f"Total Epochs Trained: {epochs_trained}")
        print(f"Best Validation Loss: {best_val_loss:.6f} (Epoch {best_epoch})")
        print(f"Final Train Loss: {final_train_loss:.6f}")
        print(f"Final Val Loss: {final_val_loss:.6f}")

        # Enhanced overfitting detection metrics
        overfit_ratio = final_val_loss / final_train_loss if final_train_loss > 0 else 1
        
        # 1. Validation degradation: how much val_loss increased from best
        val_degradation = final_val_loss / best_val_loss if best_val_loss > 0 else 1
        
        # 2. Loss trajectory: is val_loss trending up in recent epochs?
        recent_val_losses = history.history["val_loss"][-10:] if epochs_trained >= 10 else history.history["val_loss"]
        is_val_increasing = recent_val_losses[-1] > recent_val_losses[0] if len(recent_val_losses) > 1 else False
        
        # 3. Absolute gap between train and val loss
        absolute_gap = final_val_loss - final_train_loss
        
        print(f"\n📊 OVERFITTING ANALYSIS:")
        print(f"   Val/Train Ratio: {overfit_ratio:.3f}")
        print(f"   Val Degradation: {val_degradation:.3f} (final/best, ideal: 1.0)")
        print(f"   Absolute Gap: {absolute_gap:.6f} (val - train)")
        print(f"   Val Trending Up: {'⚠️ YES' if is_val_increasing else '✅ NO'}")
        
        # Improved overfitting evaluation that accounts for dropout effects
        # Note: Val < Train is NORMAL with dropout (dropout is off during validation)
        if overfit_ratio > 1.5:
            print(f"\n⚠️  WARNING: Model may be OVERFITTING (Val/Train ratio: {overfit_ratio:.2f})")
            print("   Consider: Lower learning rate, more regularization, or more data")
        elif overfit_ratio < 0.6 and val_degradation > 1.2:
            # Only warn if val loss is also degrading significantly
            print(f"\n⚠️  WARNING: Unusual training dynamics (Val/Train ratio: {overfit_ratio:.2f})")
            print("   This may indicate data leakage or distribution issues")
        elif overfit_ratio < 1.0:
            # This is actually normal with dropout!
            print(f"\n✅ Model generalizing well (Val/Train ratio: {overfit_ratio:.2f})")
            print("   (Val < Train is normal due to dropout being off during validation)")
        else:
            print(f"\n✅ Model appears to be learning well (Val/Train ratio: {overfit_ratio:.2f})")
        
        # Additional check: is validation loss stable at the end?
        if val_degradation > 1.1:
            print(f"   ⚠️  Note: Val loss degraded {((val_degradation-1)*100):.1f}% from best")
        
        # Check for val loss trending up (potential overfitting starting)
        if is_val_increasing and epochs_trained > 15:
            print(f"   ⚠️  Note: Val loss trending upward in recent epochs")

        # Evaluate
        test_loss, test_mae = self.model.evaluate(X_test, y_test, verbose=0)
        print(f"\nFinal Test Loss (MSE): {test_loss:.6f}")
        print(f"Final Test MAE: {test_mae:.6f}")

        # Save model and scaler
        self.save_model()

        return {
            "test_loss": float(test_loss),
            "test_mae": float(test_mae),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "epochs_trained": epochs_trained,
            "best_val_loss": float(best_val_loss),
            "best_epoch": best_epoch,
            "final_overfit_ratio": float(overfit_ratio),
            "val_degradation": float(val_degradation),
            "absolute_gap": float(absolute_gap),
            "val_trending_up": is_val_increasing,
        }

    def predict_next(self, recent_data: pd.DataFrame) -> Dict:
        """
        Predict next candle price

        Args:
            recent_data: DataFrame with recent price data (at least lookback_periods rows)

        Returns:
            Dictionary with prediction and confidence
        """
        if self.model is None:
            self.load_model()

        # Add features (creates copy internally, drops ~50-60 rows)
        recent_data = self._add_features(recent_data)

        # Validate sufficient data after feature engineering
        if len(recent_data) < self.lookback_periods:
            raise ValueError(
                f"Need at least {self.lookback_periods} periods after feature engineering. "
                f"Got {len(recent_data)} periods."
            )

        # Prepare and scale features
        features = (
            recent_data[self.FEATURE_COLUMNS].iloc[-self.lookback_periods :].values
        )
        scaled = self.scaler.transform(features)
        X = scaled.reshape(1, self.lookback_periods, len(self.FEATURE_COLUMNS))

        # Get prediction (this is now a percentage return, not a price)
        predicted_return = self.model.predict(X, verbose=0)[0][0]

        # Convert return to actual price
        current_price = float(recent_data["Close"].iloc[-1])
        predicted_price = current_price * (1 + predicted_return)
        predicted_change = predicted_return * 100  # Convert to percentage

        return {
            "current_price": current_price,
            "predicted_price": float(predicted_price),
            "predicted_change_percent": float(predicted_change),
            "signal": (
                "BUY"
                if predicted_change > 0.5
                else ("SELL" if predicted_change < -0.5 else "HOLD")
            ),
        }

    def save_model(self):
        """Save model and scaler with explicit build to ensure Keras 3.x compatibility"""
        os.makedirs("models", exist_ok=True)

        # DELETE old scaler file if it exists (critical when switching from price to return prediction)
        if os.path.exists(self.scaler_path):
            os.remove(self.scaler_path)
            print(f"🗑️  Deleted old scaler: {self.scaler_path}")

        # CRITICAL: Ensure model is fully built before saving in Keras 3.x
        # This prevents "Layer was never built" errors during loading
        if not self.model.built:
            print("⚠️  Model not built, building explicitly...")
            # Build with the input shape the model was trained on
            input_shape = self.model.input_shape
            if input_shape[0] is None:
                # Get from first layer
                input_shape = self.model.layers[0].input_shape
            self.model.build(input_shape)

        self.model.save(self.model_path)
        with open(self.scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)
        print(f"✅ Model saved to {self.model_path}")
        print(f"✅ Scaler saved to {self.scaler_path}")

    def load_model(self):
        """Load pre-trained model and scaler - tries multiple naming conventions"""
        # Try different model naming conventions
        model_paths_to_try = [
            f"models/{self.symbol}_{self.interval}_optimized_attention.keras",  # Try optimized attention first
            f"models/{self.symbol}_{self.interval}_predictor.keras",  # Then standard predictor
        ]

        scaler_paths_to_try = [
            f"models/{self.symbol}_{self.interval}_optimized_attention_scaler.pkl",
            f"models/{self.symbol}_{self.interval}_scaler.pkl",
        ]

        # Find which model exists
        model_found = None
        scaler_found = None

        for model_path, scaler_path in zip(model_paths_to_try, scaler_paths_to_try):
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                model_found = model_path
                scaler_found = scaler_path
                break

        if not model_found:
            raise FileNotFoundError(f"Model not found. Tried: {model_paths_to_try}")

        # Import custom layers for models that use them
        try:
            from attention_lstm_predictor import (
                MultiHeadAttentionLayer,
                TemporalAttentionLayer,
            )

            custom_objects = {
                "MultiHeadAttentionLayer": MultiHeadAttentionLayer,
                "TemporalAttentionLayer": TemporalAttentionLayer,
            }
            self.model = load_model(model_found, custom_objects=custom_objects)
        except ImportError:
            # Vanilla LSTM doesn't need custom layers
            self.model = load_model(model_found)

        with open(scaler_found, "rb") as f:
            self.scaler = pickle.load(f)
        print(f"✅ Model loaded from {model_found}")

    def calculate_directional_accuracy(
        self, y_true: np.ndarray, y_pred: np.ndarray, y_prev: np.ndarray
    ) -> float:
        """
        Calculate percentage of correctly predicted price directions.

        Args:
            y_true: Actual future prices
            y_pred: Predicted future prices
            y_prev: Previous prices (to calculate direction from)

        Returns:
            Directional accuracy as a percentage (0-100)
        """
        # Calculate price changes
        true_change = y_true - y_prev
        pred_change = y_pred - y_prev

        # Use a small threshold to avoid treating noise as direction
        # For financial data, changes < 0.0001% are typically considered noise
        threshold = 1e-6

        # Get directions: 1 for up, -1 for down, 0 for no significant change
        true_direction = np.where(
            np.abs(true_change) < threshold, 0, np.sign(true_change)
        )
        pred_direction = np.where(
            np.abs(pred_change) < threshold, 0, np.sign(pred_change)
        )

        # Only count cases where there was a significant actual direction change
        significant_changes = np.abs(true_direction) > 0

        if np.sum(significant_changes) == 0:
            return 0.0  # No significant changes to evaluate

        # Calculate accuracy only on significant changes
        correct = (
            true_direction[significant_changes] == pred_direction[significant_changes]
        )
        return float(np.mean(correct) * 100)


def train_all_crypto_models(
    symbols: List[str],
    interval: str = "1d",
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.0002,
    patience: int = 10,
    use_csv: bool = True,
):
    """
    Train models for all specified cryptocurrencies

    Args:
        symbols: List of cryptocurrency symbols to train
        interval: Candle interval (1d recommended for best results)
        epochs: Maximum number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate for optimizer
        patience: Early stopping patience
        use_csv: Use CSV data instead of yfinance API
    """
    results = {}

    print(f"\n{'='*80}")
    print("BATCH TRAINING CONFIGURATION")
    print(f"{'='*80}")
    print(f"Symbols: {symbols}")
    print(f"Interval: {interval}")
    print(f"Data Source: {'CSV file' if use_csv else 'yfinance API'}")
    print(f"Epochs: {epochs}")
    print(f"Batch Size: {batch_size}")
    print(f"Learning Rate: {learning_rate}")
    print(f"Early Stop Patience: {patience}")
    print(f"{'='*80}\n")

    for symbol in symbols:
        try:
            predictor = IntradayPredictor(
                symbol=symbol, interval=interval, use_csv=use_csv
            )
            result = predictor.train(
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                patience=patience,
            )
            results[symbol] = result
            print(f"✅ {symbol} training complete")
        except Exception as e:
            print(f"❌ {symbol} training failed: {str(e)}")
            results[symbol] = {"error": str(e)}

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train LSTM models for cryptocurrency prediction"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=["BTC-USD"],
        help="Cryptocurrency symbols to train (e.g., BTC-USD ETH-USD)",
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        help="Candle interval (1d recommended, 4h, 1h)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Maximum number of training epochs (default: 50)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for training (default: 32)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.0002,
        help="Learning rate for optimizer (default: 0.0002)",
    )
    parser.add_argument(
        "--patience", type=int, default=10, help="Early stopping patience (default: 10)"
    )
    parser.add_argument(
        "--all", action="store_true", help="Train all default cryptocurrencies"
    )
    parser.add_argument(
        "--use-api", action="store_true", help="Use yfinance API instead of CSV data"
    )

    args = parser.parse_args()

    if args.all:
        symbols = [
            "BTC-USD",
            "ETH-USD",
            "ADA-USD",
            "SOL-USD",
            "DOT-USD",
            "MATIC-USD",
            "AVAX-USD",
            "LINK-USD",
            "ATOM-USD",
            "XRP-USD",
        ]
    else:
        symbols = args.symbols

    print("🚀 Training Daily Prediction Models")
    print("=" * 80)
    print(
        f"Data source: {'yfinance API' if args.use_api else 'CSV file (faster, more data)'}"
    )
    print("=" * 80)

    results = train_all_crypto_models(
        symbols=symbols,
        interval=args.interval,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        patience=args.patience,
        use_csv=not args.use_api,
    )

    print("\n" + "=" * 80)
    print("FINAL TRAINING SUMMARY")
    print("=" * 80)
    for symbol, result in results.items():
        if "error" not in result:
            print(
                f"{symbol}: MSE={result['test_loss']:.6f}, MAE={result['test_mae']:.6f}, "
                f"Epochs={result.get('epochs_trained', 'N/A')}"
            )
        else:
            print(f"{symbol}: FAILED - {result['error']}")

    print("\n✅ Training complete!")
    print(f"\nUsage examples:")
    print(f"  python intraday_predictor.py --symbols BTC-USD ETH-USD --epochs 100")
    print(f"  python intraday_predictor.py --all --epochs 50 --batch-size 64")
    print(
        f"  python intraday_predictor.py --symbols SOL-USD --use-api  # Force yfinance API"
    )
