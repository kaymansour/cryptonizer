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
        interval: str = "1h",  # "1h" or "4h"
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

            print(f"Retrieved {len(data)} candles")

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
        """
        # Add technical indicators first
        data = self._add_features(data)

        # Select features for prediction using class constant
        features = data[self.FEATURE_COLUMNS].values

        # Scale the features
        scaled_data = self.scaler.fit_transform(features)

        # Create sequences
        X, y = [], []
        for i in range(
            self.lookback_periods, len(scaled_data) - self.prediction_horizon
        ):
            X.append(scaled_data[i - self.lookback_periods : i])
            # Predict only the close price (first feature)
            y.append(scaled_data[i + self.prediction_horizon, 0])

        X, y = np.array(X), np.array(y)

        # Split into train and test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        print(f"Training data shape: {X_train.shape}")
        print(f"Test data shape: {X_test.shape}")

        return X_train, y_train, X_test, y_test

    def build_model(self, input_shape: Tuple) -> Sequential:
        """
        Build LSTM model for price prediction
        """
        model = Sequential(
            [
                Input(shape=input_shape),
                LSTM(128, return_sequences=True),
                Dropout(0.2),
                LSTM(64, return_sequences=True),
                Dropout(0.2),
                LSTM(32),
                Dropout(0.2),
                Dense(16, activation="relu"),
                Dense(1),  # Predict next close price
            ]
        )

        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        return model

    def train(self, epochs: int = 50, batch_size: int = 32) -> Dict:
        """
        Train the LSTM model
        """
        print(f"\n{'='*60}")
        print(f"Training model for {self.symbol} ({self.interval} candles)")
        print(f"{'='*60}")

        # Fetch and prepare data
        data = self.fetch_intraday_data()
        X_train, y_train, X_test, y_test = self.prepare_training_data(data)

        # Build model
        self.model = self.build_model((X_train.shape[1], X_train.shape[2]))

        # Train
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
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
        """Save model and scaler"""
        os.makedirs("models", exist_ok=True)
        self.model.save(self.model_path)
        with open(self.scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        """Load pre-trained model and scaler"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        self.model = load_model(self.model_path)
        with open(self.scaler_path, "rb") as f:
            self.scaler = pickle.load(f)
        print(f"Model loaded from {self.model_path}")


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
