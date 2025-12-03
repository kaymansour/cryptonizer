"""
Hybrid Model Predictor - Automatically selects best model per cryptocurrency
Uses market characteristics to determine optimal architecture
"""

import argparse
import os
import numpy as np
import pandas as pd
from typing import Dict, Literal
import yfinance as yf
from datetime import datetime, timedelta

from intraday_predictor import IntradayPredictor
from attention_lstm_predictor import OptimizedAttentionLSTMPredictor


class HybridPredictor:
    """
    Intelligent predictor that selects the best model architecture
    based on cryptocurrency market characteristics
    """

    # Pre-configured optimal models based on your training results
    MODEL_SELECTION = {
        "BTC-USD": "optimized",
        "ETH-USD": "optimized",
        "SOL-USD": "optimized",
        "AVAX-USD": "optimized",
        "LINK-USD": "optimized",
        "ADA-USD": "vanilla",
        "DOT-USD": "vanilla",
        "MATIC-USD": "vanilla",
        "ATOM-USD": "vanilla",
        "XRP-USD": "vanilla",
    }

    def __init__(
        self,
        symbol: str,
        interval: str = "4h",
        lookback_periods: int = 168,
        auto_select: bool = True,
    ):
        """
        Initialize hybrid predictor

        Args:
            symbol: Crypto symbol (e.g., 'BTC-USD')
            interval: Candle interval
            lookback_periods: Lookback window
            auto_select: If True, automatically select best model based on market cap
        """
        self.symbol = symbol
        self.interval = interval
        self.lookback_periods = lookback_periods
        self.auto_select = auto_select
        self.predictor = None
        self.selected_model = None

        # Select and initialize the appropriate model
        self._select_model()

    def _select_model(self):
        """Select the best model architecture for this cryptocurrency"""

        if self.symbol in self.MODEL_SELECTION and not self.auto_select:
            # Use pre-configured selection
            model_type = self.MODEL_SELECTION[self.symbol]
            print(f"📊 Using pre-configured {model_type} model for {self.symbol}")
        else:
            # Auto-select based on market characteristics
            model_type = self._auto_select_model()

        # Initialize the selected model
        if model_type == "optimized":
            self.predictor = OptimizedAttentionLSTMPredictor(
                symbol=self.symbol,
                interval=self.interval,
                lookback_periods=self.lookback_periods,
            )
            self.selected_model = "Optimized Attention-LSTM"
        else:
            self.predictor = IntradayPredictor(
                symbol=self.symbol,
                interval=self.interval,
                lookback_periods=self.lookback_periods,
            )
            self.selected_model = "Vanilla LSTM"

        print(f"✅ Selected: {self.selected_model} for {self.symbol}")

    def _auto_select_model(self) -> Literal["vanilla", "optimized"]:
        """
        Automatically select model based on market characteristics

        Criteria:
        - High market cap (>$100B) → Optimized Attention
        - High volume/volatility → Optimized Attention
        - Lower cap/volume → Vanilla LSTM
        """
        try:
            print(f"🔍 Analyzing market characteristics for {self.symbol}...")

            # Fetch recent market data
            ticker = yf.Ticker(self.symbol)
            info = ticker.info

            # Get historical data for volatility analysis
            hist = yf.download(self.symbol, period="30d", interval="1d", progress=False)

            # Market cap (in billions)
            market_cap = info.get("marketCap", 0) / 1e9

            # Average volume (last 30 days)
            avg_volume = hist["Volume"].mean() if not hist.empty else 0

            # Price volatility (30-day std)
            volatility = hist["Close"].pct_change().std() if not hist.empty else 0

            print(f"   Market Cap: ${market_cap:.1f}B")
            print(f"   Avg Volume: {avg_volume:,.0f}")
            print(f"   Volatility: {volatility:.4f}")

            # Decision logic based on your training results
            # High-cap, high-volume coins benefit from attention
            if market_cap > 100 or avg_volume > 10_000_000:
                print(f"   → High market cap/volume detected")
                return "optimized"
            elif volatility > 0.05:  # High volatility coins
                print(f"   → High volatility detected")
                return "optimized"
            else:
                print(f"   → Using vanilla LSTM for stability")
                return "vanilla"

        except Exception as e:
            print(f"⚠️  Auto-selection failed: {e}")
            print(f"   Defaulting to vanilla LSTM")
            return "vanilla"

    def train(
        self,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.0002,
        patience: int = 15,
    ) -> Dict:
        """
        Train the selected model with configurable hyperparameters

        Args:
            epochs: Maximum number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for optimizer
            patience: Early stopping patience
        """
        print(f"\n{'='*70}")
        print(f"HYBRID TRAINING: {self.symbol}")
        print(f"Selected Architecture: {self.selected_model}")
        print(f"{'='*70}\n")

        result = self.predictor.train(
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            patience=patience,
        )
        result["model_type"] = self.selected_model

        return result

    def predict_next(self, recent_data: pd.DataFrame) -> Dict:
        """Make prediction using the selected model"""
        prediction = self.predictor.predict_next(recent_data)
        prediction["model_used"] = self.selected_model
        return prediction

    def load_model(self):
        """Load pre-trained model"""
        self.predictor.load_model()

    def save_model(self):
        """Save trained model"""
        self.predictor.save_model()


class EnsemblePredictor:
    """
    Ensemble predictor that combines predictions from both models
    Uses weighted average based on model confidence
    """

    def __init__(
        self,
        symbol: str,
        interval: str = "4h",
        lookback_periods: int = 168,
    ):
        self.symbol = symbol
        self.interval = interval
        self.lookback_periods = lookback_periods

        # Initialize both models
        self.vanilla = IntradayPredictor(
            symbol=symbol,
            interval=interval,
            lookback_periods=lookback_periods,
        )

        self.attention = OptimizedAttentionLSTMPredictor(
            symbol=symbol,
            interval=interval,
            lookback_periods=lookback_periods,
        )

        # Load pre-trained models
        self.models_loaded = False

    def load_models(self):
        """Load both pre-trained models"""
        try:
            self.vanilla.load_model()
            print(f"✅ Loaded vanilla model for {self.symbol}")
        except:
            print(f"⚠️  Vanilla model not found for {self.symbol}")

        try:
            self.attention.load_model()
            print(f"✅ Loaded attention model for {self.symbol}")
        except:
            print(f"⚠️  Attention model not found for {self. symbol}")

        self.models_loaded = True

    def predict_next(
        self,
        recent_data: pd.DataFrame,
        vanilla_weight: float = 0.5,
    ) -> Dict:
        """
        Make ensemble prediction

        Args:
            recent_data: Recent price data
            vanilla_weight: Weight for vanilla model (0-1)
        """
        if not self.models_loaded:
            self.load_models()

        # Get predictions from both models
        vanilla_pred = self.vanilla.predict_next(recent_data)
        attention_pred = self.attention.predict_next(recent_data)

        # Weighted ensemble
        attention_weight = 1 - vanilla_weight
        ensemble_price = (
            vanilla_pred["predicted_price"] * vanilla_weight
            + attention_pred["predicted_price"] * attention_weight
        )

        current_price = vanilla_pred["current_price"]
        ensemble_change = ((ensemble_price - current_price) / current_price) * 100

        return {
            "current_price": current_price,
            "predicted_price": float(ensemble_price),
            "predicted_change_percent": float(ensemble_change),
            "signal": (
                "BUY"
                if ensemble_change > 0.5
                else ("SELL" if ensemble_change < -0.5 else "HOLD")
            ),
            "vanilla_prediction": vanilla_pred["predicted_price"],
            "attention_prediction": attention_pred["predicted_price"],
            "vanilla_weight": vanilla_weight,
            "attention_weight": attention_weight,
        }


def train_hybrid_portfolio(
    symbols: list,
    interval: str = "4h",
    epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 0.0002,
    patience: int = 15,
):
    """
    Train hybrid models for a portfolio of cryptocurrencies
    Automatically selects best architecture for each

    Args:
        symbols: List of cryptocurrency symbols
        interval: Candle interval
        epochs: Maximum training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate for optimizer
        patience: Early stopping patience
    """
    print(f"\n{'='*80}")
    print("HYBRID PORTFOLIO TRAINING CONFIGURATION")
    print(f"{'='*80}")
    print(f"Symbols: {symbols}")
    print(f"Interval: {interval}")
    print(f"Epochs: {epochs}")
    print(f"Batch Size: {batch_size}")
    print(f"Learning Rate: {learning_rate}")
    print(f"Patience: {patience}")
    print(f"{'='*80}\n")

    results = {}

    for symbol in symbols:
        try:
            print(f"\n{'='*70}")
            print(f"Training {symbol}")
            print(f"{'='*70}")

            predictor = HybridPredictor(
                symbol=symbol,
                interval=interval,
                auto_select=False,  # Use pre-configured selections
            )

            result = predictor.train(
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                patience=patience,
            )
            results[symbol] = {
                "success": True,
                "model_type": result["model_type"],
                "test_loss": result["test_loss"],
                "test_mae": result["test_mae"],
                "epochs_trained": result.get("epochs_trained", "N/A"),
                "overfit_ratio": result.get("final_overfit_ratio", "N/A"),
            }

            print(f"\n✅ {symbol} training complete")
            print(f"   Model: {result['model_type']}")
            print(f"   MSE: {result['test_loss']:.6f}")
            print(f"   MAE: {result['test_mae']:.6f}")

        except Exception as e:
            print(f"\n❌ {symbol} training failed: {str(e)}")
            results[symbol] = {"success": False, "error": str(e)}

    # Summary
    print(f"\n{'='*80}")
    print("TRAINING SUMMARY")
    print(f"{'='*80}")
    print(
        f"\n{'Symbol':<12} {'Model':<15} {'MSE':<12} {'MAE':<12} {'Epochs':<8} {'Overfit':<8}"
    )
    print("-" * 80)

    for symbol, result in results.items():
        if result["success"]:
            epochs_str = str(result.get("epochs_trained", "N/A"))
            overfit_str = (
                f"{result.get('overfit_ratio', 'N/A'):.2f}"
                if isinstance(result.get("overfit_ratio"), float)
                else str(result.get("overfit_ratio", "N/A"))
            )
            print(
                f"{symbol:<12} {result['model_type']:<15} {result['test_loss']:<12.6f} {result['test_mae']:<12.6f} {epochs_str:<8} {overfit_str:<8}"
            )
        else:
            print(f"{symbol:<12} {'FAILED':<15}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train Hybrid models for cryptocurrency prediction"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=["BTC-USD"],
        help="Cryptocurrency symbols to train (e.g., BTC-USD ETH-USD)",
    )
    parser.add_argument(
        "--interval", type=str, default="4h", help="Candle interval (1h, 4h, etc.)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Maximum number of training epochs (default: 100)",
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
        "--patience", type=int, default=15, help="Early stopping patience (default: 15)"
    )
    parser.add_argument(
        "--all", action="store_true", help="Train all default cryptocurrencies"
    )

    args = parser.parse_args()

    if args.all:
        symbols = [
            "BTC-USD",
            "ETH-USD",
            "SOL-USD",
            "AVAX-USD",
            "LINK-USD",
            "ADA-USD",
            "DOT-USD",
            "ATOM-USD",
            "XRP-USD",
            "BNB-USD",
            "TRX-USD",
        ]
    else:
        symbols = args.symbols

    print("🚀 Training Hybrid Portfolio with Optimal Model Selection")
    print("=" * 80)

    results = train_hybrid_portfolio(
        symbols=symbols,
        interval=args.interval,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        patience=args.patience,
    )

    print("\n✅ Portfolio training complete!")
    print(f"\nUsage examples:")
    print(
        f"  python hybrid_predictor.py --symbols BTC-USD ETH-USD --epochs 100 --learning-rate 0.0001"
    )
    print(f"  python hybrid_predictor.py --all --epochs 50 --batch-size 64")
    print(
        f"  python hybrid_predictor.py --symbols SOL-USD --learning-rate 0.0005 --patience 20"
    )
