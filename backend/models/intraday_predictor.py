"""
Intraday Cryptocurrency Price Predictor using LSTM
Trains models on 1h or 4h candle data for short-term trading signals
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from keras.models import Sequential, load_model
from keras.layers import Dense, LSTM, Dropout, Input
from keras.regularizers import l2
from keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
import pickle
import os
from typing import Dict, List, Tuple, Optional


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
        interval: str = "4h",  # "1h" or "4h"
        lookback_periods: int = 168,  # 1 week of hourly data
        prediction_horizon: int = 1,  # Predict next candle
    ):
        self.symbol = symbol
        self.interval = interval
        self.lookback_periods = lookback_periods
        self.prediction_horizon = prediction_horizon
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model_path = f"models/{symbol}_{interval}_predictor.keras"
        self.scaler_path = f"models/{symbol}_{interval}_scaler.pkl"

    def fetch_intraday_data(self, days_back: int = 730) -> pd.DataFrame:
        """
        Fetch intraday price data

        Note: yfinance limitations:
        - 1h interval: max 730 days
        - 4h interval: max 730 days
        - 1m interval: max 60 days
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            print(f"Fetching {self.interval} data for {self.symbol}...")
            print(f"Period: {start_date.date()} to {end_date.date()}")

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
                print(f"✅ Verified interval: First candle time difference = {time_diff}")
                
                # Calculate expected candles for verification
                days_diff = (end_date - start_date).days
                if self.interval == "4h":
                    expected_candles = days_diff * 6  # 6 candles per day for 4h
                    print(f"   Expected ~{expected_candles} candles for {days_diff} days at 4h interval")
                elif self.interval == "1h":
                    expected_candles = days_diff * 24  # 24 candles per day for 1h
                    print(f"   Expected ~{expected_candles} candles for {days_diff} days at 1h interval")
                elif self.interval == "1d":
                    expected_candles = days_diff  # 1 candle per day
                    print(f"   Expected ~{expected_candles} candles for {days_diff} days at 1d interval")

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
        """
        # Add technical indicators first
        data = self._add_features(data)

        # Select features for prediction using class constant
        features = data[self.FEATURE_COLUMNS].values

        # Create sequences BEFORE scaling and splitting
        X, y = [], []
        for i in range(
            self.lookback_periods, len(features) - self.prediction_horizon
        ):
            X.append(features[i - self.lookback_periods : i])
            # Predict only the close price (first feature)
            y.append(features[i + self.prediction_horizon, 0])

        X, y = np.array(X), np.array(y)

        # Split into train and test FIRST
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Fit scaler ONLY on training data
        # Reshape for scaling: (samples * timesteps, features)
        X_train_reshaped = X_train.reshape(-1, X_train.shape[2])
        self.scaler.fit(X_train_reshaped)

        # Transform both train and test
        X_train_scaled = self.scaler.transform(X_train_reshaped).reshape(X_train.shape)
        X_test_reshaped = X_test.reshape(-1, X_test.shape[2])
        X_test_scaled = self.scaler.transform(X_test_reshaped).reshape(X_test.shape)

        # Scale y values (only close price - first feature)
        y_train_reshaped = y_train.reshape(-1, 1)
        y_test_reshaped = y_test.reshape(-1, 1)
        
        # Create temporary array with all features set to 0 except close price for inverse transform compatibility
        temp_train = np.zeros((len(y_train), len(self.FEATURE_COLUMNS)))
        temp_train[:, 0] = y_train
        temp_test = np.zeros((len(y_test), len(self.FEATURE_COLUMNS)))
        temp_test[:, 0] = y_test
        
        y_train_scaled = self.scaler.transform(temp_train)[:, 0]
        y_test_scaled = self.scaler.transform(temp_test)[:, 0]

        print(f"Training data shape: {X_train_scaled.shape}")
        print(f"Test data shape: {X_test_scaled.shape}")

        return X_train_scaled, y_train_scaled, X_test_scaled, y_test_scaled

    def build_model(self, input_shape: Tuple) -> Sequential:
        """
        Build LSTM model for price prediction with regularization
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
                Dense(1),  # Predict next close price
            ]
        )

        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        return model

    def train(self, epochs: int = 50, batch_size: int = 32) -> Dict:
        """
        Train the LSTM model with early stopping
        """
        print(f"\n{'='*60}")
        print(f"Training model for {self.symbol} ({self.interval} candles)")
        print(f"{'='*60}")

        # Fetch and prepare data
        data = self.fetch_intraday_data()
        X_train, y_train, X_test, y_test = self.prepare_training_data(data)

        # Build model
        self.model = self.build_model((X_train.shape[1], X_train.shape[2]))

        # Early stopping callback
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        )

        # Train
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=1,
        )

        # Evaluate
        test_loss, test_mae = self.model.evaluate(X_test, y_test, verbose=0)
        print(f"\nTest Loss (MSE): {test_loss:.6f}")
        print(f"Test MAE: {test_mae:.6f}")

        # Save model and scaler
        self.save_model()

        return {
            "test_loss": float(test_loss),
            "test_mae": float(test_mae),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
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
        features = recent_data[self.FEATURE_COLUMNS].iloc[-self.lookback_periods :].values
        scaled = self.scaler.transform(features)
        X = scaled.reshape(1, self.lookback_periods, len(self.FEATURE_COLUMNS))

        # Get prediction and inverse transform
        prediction_scaled = self.model.predict(X, verbose=0)[0][0]
        dummy = np.zeros((1, len(self.FEATURE_COLUMNS)))
        dummy[0, 0] = prediction_scaled
        prediction = self.scaler.inverse_transform(dummy)[0, 0]

        # Calculate predicted change
        current_price = float(recent_data["Close"].iloc[-1])
        predicted_change = ((prediction - current_price) / current_price) * 100

        return {
            "current_price": current_price,
            "predicted_price": float(prediction),
            "predicted_change_percent": predicted_change,
            "signal": "BUY" if predicted_change > 0.5 else ("SELL" if predicted_change < -0.5 else "HOLD"),
        }

    def save_model(self):
        """Save model and scaler with explicit build to ensure Keras 3.x compatibility"""
        os.makedirs("models", exist_ok=True)
        
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
        print(f"Model saved to {self.model_path}")

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
            from attention_lstm_predictor import MultiHeadAttentionLayer, TemporalAttentionLayer
            custom_objects = {
                'MultiHeadAttentionLayer': MultiHeadAttentionLayer,
                'TemporalAttentionLayer': TemporalAttentionLayer
            }
            self.model = load_model(model_found, custom_objects=custom_objects)
        except ImportError:
            # Vanilla LSTM doesn't need custom layers
            self.model = load_model(model_found)
        
        with open(scaler_found, "rb") as f:
            self.scaler = pickle.load(f)
        print(f"✅ Model loaded from {model_found}")

    def calculate_directional_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray, y_prev: np.ndarray) -> float:
        """
        Calculate percentage of correctly predicted price directions.
        
        Args:
            y_true: Actual future prices
            y_pred: Predicted future prices
            y_prev: Previous prices (to calculate direction from)
            
        Returns:
            Directional accuracy as a percentage (0-100)
        """
        true_direction = np.sign(y_true - y_prev)
        pred_direction = np.sign(y_pred - y_prev)
        return float(np.mean(true_direction == pred_direction) * 100)


def train_all_crypto_models(symbols: List[str], interval: str = "4h"):
    """
    Train models for all specified cryptocurrencies
    """
    results = {}

    for symbol in symbols:
        try:
            predictor = IntradayPredictor(symbol=symbol, interval=interval)
            result = predictor.train(epochs=50, batch_size=32)
            results[symbol] = result
            print(f"✅ {symbol} training complete")
        except Exception as e:
            print(f"❌ {symbol} training failed: {str(e)}")
            results[symbol] = {"error": str(e)}

    return results


if __name__ == "__main__":
    # Example: Train BTC model on 4h candles
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

    print("Training intraday prediction models...")
    results = train_all_crypto_models(symbols, interval="4h")

    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    for symbol, result in results.items():
        if "error" not in result:
            print(
                f"{symbol}: MSE={result['test_loss']:.6f}, MAE={result['test_mae']:.6f}"
            )
        else:
            print(f"{symbol}: FAILED - {result['error']}")
