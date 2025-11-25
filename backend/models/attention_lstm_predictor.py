"""
Attention-LSTM Cryptocurrency Price Predictor
Enhanced LSTM with attention mechanism for improved temporal pattern recognition
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from keras.models import Sequential, Model
from keras.layers import Dense, LSTM, Dropout, Input, Layer, Multiply, Permute, RepeatVector, Lambda
from keras import backend as K
import tensorflow as tf

from intraday_predictor import IntradayPredictor


class AttentionLayer(Layer):
    """
    Custom Attention Layer for LSTM
    Implements Bahdanau-style additive attention mechanism
    """

    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        # input_shape: (batch_size, time_steps, features)
        self.W = self.add_weight(
            name="attention_weight",
            shape=(input_shape[-1], input_shape[-1]),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.b = self.add_weight(
            name="attention_bias",
            shape=(input_shape[-1],),
            initializer="zeros",
            trainable=True,
        )
        self.u = self.add_weight(
            name="attention_context",
            shape=(input_shape[-1], 1),
            initializer="glorot_uniform",
            trainable=True,
        )
        super(AttentionLayer, self).build(input_shape)

    def call(self, inputs):
        # inputs shape: (batch_size, time_steps, features)
        
        # Compute attention scores
        # (batch, time_steps, features) @ (features, features) -> (batch, time_steps, features)
        score = K.tanh(K.dot(inputs, self.W) + self.b)
        
        # (batch, time_steps, features) @ (features, 1) -> (batch, time_steps, 1)
        attention_scores = K.dot(score, self.u)
        
        # Softmax over time dimension
        attention_weights = K.softmax(attention_scores, axis=1)
        
        # Apply attention weights
        # (batch, time_steps, features) * (batch, time_steps, 1) -> (batch, time_steps, features)
        weighted_input = inputs * attention_weights
        
        # Sum over time dimension to get context vector
        # (batch, time_steps, features) -> (batch, features)
        context = K.sum(weighted_input, axis=1)
        
        return context

    def compute_output_shape(self, input_shape):
        # Returns (batch_size, features) - removes time dimension
        return (input_shape[0], input_shape[-1])

    def get_config(self):
        return super(AttentionLayer, self).get_config()


class AttentionLSTMPredictor(IntradayPredictor):
    """
    LSTM with Attention mechanism for cryptocurrency price prediction
    Inherits from IntradayPredictor but uses attention-enhanced architecture
    """

    def __init__(self, symbol: str, interval: str = "1h", lookback_periods: int = 168, prediction_horizon: int = 1):
        # Initialize parent class
        super().__init__(symbol, interval, lookback_periods, prediction_horizon)
        
        # Override model paths to use attention-specific naming
        self.model_path = f"models/{symbol}_{interval}_attention_predictor.keras"
        self.scaler_path = f"models/{symbol}_{interval}_attention_scaler.pkl"

    def build_model(self, input_shape: Tuple) -> Model:
        """
        Build Attention-LSTM model for price prediction
        
        Architecture:
        - 2 LSTM layers with return_sequences=True (to feed into attention)
        - Custom Attention layer to focus on important time steps
        - Final LSTM layer for temporal processing
        - Dense layers for prediction
        """
        # Input layer
        inputs = Input(shape=input_shape)
        
        # First LSTM layer
        lstm1 = LSTM(128, return_sequences=True)(inputs)
        dropout1 = Dropout(0.2)(lstm1)
        
        # Second LSTM layer
        lstm2 = LSTM(64, return_sequences=True)(dropout1)
        dropout2 = Dropout(0.2)(lstm2)
        
        # Apply Attention mechanism
        attention_output = AttentionLayer()(dropout2)
        dropout3 = Dropout(0.2)(attention_output)
        
        # Dense layers for final prediction
        dense1 = Dense(32, activation="relu")(dropout3)
        dropout4 = Dropout(0.2)(dense1)
        dense2 = Dense(16, activation="relu")(dropout4)
        outputs = Dense(1)(dense2)
        
        # Create model
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        
        return model


def compare_models(
    symbol: str,
    interval: str = "4h",
    epochs: int = 50,
    batch_size: int = 32
) -> Dict:
    """
    Train and compare vanilla LSTM vs Attention-LSTM on the same data
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC-USD')
        interval: Candle interval ('1h' or '4h')
        epochs: Number of training epochs
        batch_size: Training batch size
    
    Returns:
        Dictionary with comparison metrics for both models
    """
    print(f"\n{'='*70}")
    print(f"MODEL COMPARISON: {symbol} ({interval} candles)")
    print(f"{'='*70}\n")
    
    # Train vanilla LSTM
    print("🔵 Training Vanilla LSTM...")
    vanilla_predictor = IntradayPredictor(symbol=symbol, interval=interval)
    vanilla_results = vanilla_predictor.train(epochs=epochs, batch_size=batch_size)
    
    print("\n" + "-"*70 + "\n")
    
    # Train Attention-LSTM
    print("🟢 Training Attention-LSTM...")
    attention_predictor = AttentionLSTMPredictor(symbol=symbol, interval=interval)
    attention_results = attention_predictor.train(epochs=epochs, batch_size=batch_size)
    
    # Calculate improvements
    mse_improvement = ((vanilla_results["test_loss"] - attention_results["test_loss"]) / vanilla_results["test_loss"]) * 100
    mae_improvement = ((vanilla_results["test_mae"] - attention_results["test_mae"]) / vanilla_results["test_mae"]) * 100
    
    # Comparison summary
    print(f"\n{'='*70}")
    print("COMPARISON RESULTS")
    print(f"{'='*70}")
    print(f"\n{'Metric':<20} {'Vanilla LSTM':>15} {'Attention-LSTM':>15} {'Improvement':>15}")
    print("-"*70)
    print(f"{'Test Loss (MSE)':<20} {vanilla_results['test_loss']:>15.6f} {attention_results['test_loss']:>15.6f} {mse_improvement:>14.2f}%")
    print(f"{'Test MAE':<20} {vanilla_results['test_mae']:>15.6f} {attention_results['test_mae']:>15.6f} {mae_improvement:>14.2f}%")
    print(f"{'Training Samples':<20} {vanilla_results['training_samples']:>15} {attention_results['training_samples']:>15} {'Same':>15}")
    print(f"{'Test Samples':<20} {vanilla_results['test_samples']:>15} {attention_results['test_samples']:>15} {'Same':>15}")
    print("="*70)
    
    # Determine winner
    if attention_results["test_loss"] < vanilla_results["test_loss"]:
        print(f"\n✅ Attention-LSTM performs BETTER (MSE reduced by {abs(mse_improvement):.2f}%)")
    elif attention_results["test_loss"] > vanilla_results["test_loss"]:
        print(f"\n⚠️  Vanilla LSTM performs BETTER (MSE lower by {abs(mse_improvement):.2f}%)")
    else:
        print(f"\n🟡 Models perform EQUALLY")
    
    return {
        "symbol": symbol,
        "interval": interval,
        "vanilla_lstm": vanilla_results,
        "attention_lstm": attention_results,
        "improvements": {
            "mse_improvement_percent": mse_improvement,
            "mae_improvement_percent": mae_improvement,
        },
        "winner": "attention" if attention_results["test_loss"] < vanilla_results["test_loss"] else "vanilla"
    }


def batch_compare_models(
    symbols: List[str],
    interval: str = "4h",
    epochs: int = 50,
    batch_size: int = 32
) -> Dict:
    """
    Compare vanilla LSTM vs Attention-LSTM across multiple cryptocurrencies
    
    Returns:
        Dictionary with comparison results for each symbol
    """
    results = {}
    
    for symbol in symbols:
        try:
            comparison = compare_models(symbol, interval, epochs, batch_size)
            results[symbol] = comparison
        except Exception as e:
            print(f"\n❌ {symbol} comparison failed: {str(e)}\n")
            results[symbol] = {"error": str(e)}
    
    # Overall summary
    print(f"\n{'='*70}")
    print("OVERALL COMPARISON SUMMARY")
    print(f"{'='*70}\n")
    
    vanilla_wins = 0
    attention_wins = 0
    
    for symbol, result in results.items():
        if "error" not in result:
            winner = result["winner"]
            mse_improvement = result["improvements"]["mse_improvement_percent"]
            
            if winner == "attention":
                attention_wins += 1
                icon = "🟢"
            else:
                vanilla_wins += 1
                icon = "🔵"
            
            print(f"{icon} {symbol:<15} Winner: {winner.upper():<10} MSE Change: {mse_improvement:>7.2f}%")
    
    print(f"\n{'='*70}")
    print(f"Vanilla LSTM wins: {vanilla_wins}")
    print(f"Attention-LSTM wins: {attention_wins}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    # Test symbols for comparison
    test_symbols = [
        "BTC-USD",
        "ETH-USD",
    ]
    
    print("🚀 Starting Model Comparison: Vanilla LSTM vs Attention-LSTM")
    print("="*70)
    
    # Compare models on test symbols
    results = batch_compare_models(test_symbols, interval="4h", epochs=50, batch_size=32)
    
    print("\n✅ Comparison complete! Check results above to decide which model to use.")
