"""
Optimized Attention-LSTM Cryptocurrency Price Predictor
Enhanced LSTM with multi-head attention mechanism for improved temporal pattern recognition
"""

import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from keras.models import Model
from keras.layers import (
    Dense,
    LSTM,
    Dropout,
    Input,
    Layer,
    Bidirectional,
    BatchNormalization,
    Concatenate,
    GlobalAveragePooling1D,
    Add,
)
from keras.regularizers import l2
from keras.callbacks import EarlyStopping, ReduceLROnPlateau, Callback
from keras.optimizers import Adam
from keras import backend as K
import tensorflow as tf

from intraday_predictor import IntradayPredictor, TrainingLogger


@tf.keras.utils.register_keras_serializable(package="CustomLayers")
class MultiHeadAttentionLayer(Layer):
    """
    Multi-Head Attention Layer optimized for time series
    Uses multiple attention heads to capture different temporal patterns
    """

    def __init__(
        self, num_heads: int = 4, key_dim: int = 32, dropout_rate: float = 0.1, **kwargs
    ):
        super(MultiHeadAttentionLayer, self).__init__(**kwargs)
        self.num_heads = num_heads
        self.key_dim = key_dim
        self.dropout_rate = dropout_rate

        # Initialize sub-layers in __init__ instead of build()
        # This ensures they are properly tracked for serialization
        self.query_dense = None
        self.key_dense = None
        self.value_dense = None
        self.output_dense = None
        self.attention_dropout = None

    def build(self, input_shape):
        # input_shape: (batch_size, time_steps, features)
        self.features = input_shape[-1]

        # Create Dense layers with unique names
        self.query_dense = Dense(
            self.num_heads * self.key_dim, use_bias=False, name=f"{self.name}_query"
        )
        self.key_dense = Dense(
            self.num_heads * self.key_dim, use_bias=False, name=f"{self.name}_key"
        )
        self.value_dense = Dense(
            self.num_heads * self.key_dim, use_bias=False, name=f"{self.name}_value"
        )
        self.output_dense = Dense(self.features, name=f"{self.name}_output")
        self.attention_dropout = Dropout(self.dropout_rate, name=f"{self.name}_dropout")

        # Explicitly build the Dense layers
        self.query_dense.build(input_shape)
        self.key_dense.build(input_shape)
        self.value_dense.build(input_shape)
        self.output_dense.build(
            (input_shape[0], input_shape[1], self.num_heads * self.key_dim)
        )

        # Store input shape for serialization
        self._build_input_shape = input_shape

        super(MultiHeadAttentionLayer, self).build(input_shape)

    def call(self, inputs, training=None):
        batch_size = tf.shape(inputs)[0]
        time_steps = tf.shape(inputs)[1]

        # Project to Q, K, V
        query = self.query_dense(inputs)  # (batch, time, num_heads * key_dim)
        key = self.key_dense(inputs)
        value = self.value_dense(inputs)

        # Reshape for multi-head attention
        query = tf.reshape(
            query, (batch_size, time_steps, self.num_heads, self.key_dim)
        )
        key = tf.reshape(key, (batch_size, time_steps, self.num_heads, self.key_dim))
        value = tf.reshape(
            value, (batch_size, time_steps, self.num_heads, self.key_dim)
        )

        # Transpose for attention: (batch, num_heads, time, key_dim)
        query = tf.transpose(query, perm=[0, 2, 1, 3])
        key = tf.transpose(key, perm=[0, 2, 1, 3])
        value = tf.transpose(value, perm=[0, 2, 1, 3])

        # Scaled dot-product attention
        scale = tf.math.sqrt(tf.cast(self.key_dim, tf.float32))
        attention_scores = tf.matmul(query, key, transpose_b=True) / scale

        # Apply causal mask (only attend to past and present, not future)
        # This is crucial for time series prediction
        causal_mask = tf.linalg.band_part(tf.ones((time_steps, time_steps)), -1, 0)
        causal_mask = tf.cast(causal_mask, tf.float32)
        attention_scores = attention_scores * causal_mask - 1e9 * (1 - causal_mask)

        attention_weights = tf.nn.softmax(attention_scores, axis=-1)
        attention_weights = self.attention_dropout(attention_weights, training=training)

        # Apply attention to values
        attention_output = tf.matmul(attention_weights, value)

        # Reshape back: (batch, time, num_heads * key_dim)
        attention_output = tf.transpose(attention_output, perm=[0, 2, 1, 3])
        attention_output = tf.reshape(
            attention_output, (batch_size, time_steps, self.num_heads * self.key_dim)
        )

        # Project back to original dimension
        output = self.output_dense(attention_output)

        return output

    def compute_output_shape(self, input_shape):
        return input_shape

    def get_config(self):
        config = super(MultiHeadAttentionLayer, self).get_config()
        config.update(
            {
                "num_heads": self.num_heads,
                "key_dim": self.key_dim,
                "dropout_rate": self.dropout_rate,
            }
        )
        return config

    def get_build_config(self):
        return {"input_shape": self._build_input_shape}

    def build_from_config(self, config):
        self.build(config["input_shape"])

    def _set_save_spec(self, inputs_spec, args_spec=None, kwargs_spec=None):
        super()._set_save_spec(inputs_spec, args_spec, kwargs_spec)
        self._build_input_shape = inputs_spec.shape


@tf.keras.utils.register_keras_serializable(package="CustomLayers")
class TemporalAttentionLayer(Layer):
    """
    Temporal attention that preserves sequence information
    Produces attention-weighted features while keeping temporal dimension
    """

    def __init__(self, use_causal_mask: bool = True, **kwargs):
        super(TemporalAttentionLayer, self).__init__(**kwargs)
        self.use_causal_mask = use_causal_mask

        # Initialize weight attributes
        self.W_query = None
        self.W_key = None
        self.W_value = None

    def build(self, input_shape):
        self.features = input_shape[-1]

        self.W_query = self.add_weight(
            name=f"{self.name}_query_weight",
            shape=(self.features, self.features),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.W_key = self.add_weight(
            name=f"{self.name}_key_weight",
            shape=(self.features, self.features),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.W_value = self.add_weight(
            name=f"{self.name}_value_weight",
            shape=(self.features, self.features),
            initializer="glorot_uniform",
            trainable=True,
        )

        # Store input shape for serialization
        self._build_input_shape = input_shape

        super(TemporalAttentionLayer, self).build(input_shape)

    def call(self, inputs):
        # inputs: (batch, time_steps, features)
        query = tf.matmul(inputs, self.W_query)
        key = tf.matmul(inputs, self.W_key)
        value = tf.matmul(inputs, self.W_value)

        # Attention scores
        scale = tf.math.sqrt(tf.cast(self.features, tf.float32))
        attention_scores = tf.matmul(query, key, transpose_b=True) / scale

        # Apply causal mask for time series
        if self.use_causal_mask:
            time_steps = tf.shape(inputs)[1]
            causal_mask = tf.linalg.band_part(tf.ones((time_steps, time_steps)), -1, 0)
            attention_scores = attention_scores * causal_mask - 1e9 * (1 - causal_mask)

        attention_weights = tf.nn.softmax(attention_scores, axis=-1)

        # Apply attention - preserves temporal dimension
        output = tf.matmul(attention_weights, value)

        return output

    def compute_output_shape(self, input_shape):
        return input_shape

    def get_config(self):
        config = super(TemporalAttentionLayer, self).get_config()
        config.update({"use_causal_mask": self.use_causal_mask})
        return config

    def get_build_config(self):
        return {"input_shape": self._build_input_shape}

    def build_from_config(self, config):
        self.build(config["input_shape"])

    def _set_save_spec(self, inputs_spec, args_spec=None, kwargs_spec=None):
        super()._set_save_spec(inputs_spec, args_spec, kwargs_spec)
        self._build_input_shape = inputs_spec.shape


class OptimizedAttentionLSTMPredictor(IntradayPredictor):
    """
    Optimized LSTM with Attention mechanism for cryptocurrency price prediction

    Key improvements over basic attention:
    1.  Bidirectional LSTM for richer feature extraction
    2. Multi-head attention with causal masking
    3. Residual connections to prevent gradient degradation
    4.  Layer normalization for training stability
    5. Proper regularization for financial data
    """

    def __init__(
        self,
        symbol: str,
        interval: str = "1d",  # Daily candles for better trend detection
        lookback_periods: int = 60,  # 60 days (~2 months) of daily data
        prediction_horizon: int = 1,
        num_attention_heads: int = 4,
        use_bidirectional: bool = True,
        use_csv: bool = True,  # Use CSV data instead of API
    ):
        super().__init__(symbol, interval, lookback_periods, prediction_horizon, use_csv)

        self.num_attention_heads = num_attention_heads
        self.use_bidirectional = use_bidirectional

        # Override model paths
        self.model_path = f"models/{symbol}_{interval}_optimized_attention.keras"
        self.scaler_path = f"models/{symbol}_{interval}_optimized_attention_scaler.pkl"

    def build_model(self, input_shape: Tuple, learning_rate: float = 0.0002) -> Model:
        """
        Build Optimized Attention-LSTM model

        Architecture:
        - Bidirectional LSTM for rich temporal features
        - Multi-head attention with causal masking
        - Residual connections
        - Gradual dimension reduction

        Args:
            input_shape: Shape of input data (timesteps, features)
            learning_rate: Learning rate for Adam optimizer (default: 0.0002)
        """
        inputs = Input(shape=input_shape)

        # === Encoder Block 1: Feature Extraction ===
        if self.use_bidirectional:
            lstm1 = Bidirectional(
                LSTM(64, return_sequences=True, kernel_regularizer=l2(0.001))
            )(inputs)
        else:
            lstm1 = LSTM(128, return_sequences=True, kernel_regularizer=l2(0.001))(
                inputs
            )

        lstm1 = BatchNormalization()(lstm1)
        lstm1 = Dropout(0.2)(lstm1)

        # === Attention Block: Multi-Head Temporal Attention ===
        attention_out = MultiHeadAttentionLayer(
            num_heads=self.num_attention_heads, key_dim=32, dropout_rate=0.1
        )(lstm1)

        # Residual connection - crucial for gradient flow
        if lstm1.shape[-1] == attention_out.shape[-1]:
            attention_out = Add()([lstm1, attention_out])

        attention_out = BatchNormalization()(attention_out)
        attention_out = Dropout(0.2)(attention_out)

        # === Encoder Block 2: Temporal Processing ===
        lstm2 = LSTM(64, return_sequences=True, kernel_regularizer=l2(0.001))(
            attention_out
        )
        lstm2 = BatchNormalization()(lstm2)
        lstm2 = Dropout(0.2)(lstm2)

        # === Second Attention Block ===
        attention_out2 = TemporalAttentionLayer(use_causal_mask=True)(lstm2)
        attention_out2 = Add()([lstm2, attention_out2])  # Residual
        attention_out2 = BatchNormalization()(attention_out2)

        # === Final LSTM: Sequence to Vector ===
        lstm3 = LSTM(32, return_sequences=False, kernel_regularizer=l2(0.001))(
            attention_out2
        )
        lstm3 = BatchNormalization()(lstm3)
        lstm3 = Dropout(0.3)(lstm3)

        # === Output Block ===
        # Explicitly build Dense layers with defined input shape
        dense1 = Dense(
            32, activation="relu", kernel_regularizer=l2(0.001), name="output_dense_1"
        )(lstm3)
        dense1 = Dropout(0.2)(dense1)
        dense2 = Dense(
            16, activation="relu", kernel_regularizer=l2(0.001), name="output_dense_2"
        )(dense1)
        outputs = Dense(1, name="prediction_output")(
            dense2
        )  # Output: percentage return

        model = Model(inputs=inputs, outputs=outputs)

        optimizer = Adam(learning_rate=learning_rate)
        model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])
        print(f"Attention model compiled with learning rate: {learning_rate}")

        return model

    def train(
        self,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.0002,
        patience: int = 15,
    ) -> Dict:
        """
        Train with early stopping, learning rate scheduling, and detailed logging

        Args:
            epochs: Maximum number of training epochs
            batch_size: Batch size for training
            learning_rate: Initial learning rate for Adam optimizer
            patience: Early stopping patience (epochs without improvement)
        """
        print(f"\n{'='*80}")
        print(f"Training OPTIMIZED Attention-LSTM for {self.symbol} ({self.interval})")
        print(f"{'='*80}")
        print(f"Hyperparameters:")
        print(f"  - Epochs: {epochs}")
        print(f"  - Batch Size: {batch_size}")
        print(f"  - Learning Rate: {learning_rate}")
        print(f"  - Early Stop Patience: {patience}")
        print(f"  - Attention Heads: {self.num_attention_heads}")
        print(f"  - Bidirectional: {self.use_bidirectional}")
        print(f"{'='*80}\n")

        # Fetch and prepare data
        data = self.fetch_intraday_data()
        X_train, y_train, X_test, y_test = self.prepare_training_data(data)

        # Build model with configurable learning rate
        self.model = self.build_model(
            (X_train.shape[1], X_train.shape[2]), learning_rate=learning_rate
        )

        # Print model summary
        self.model.summary()

        # Callbacks for better training
        training_logger = TrainingLogger(symbol=self.symbol)

        callbacks = [
            EarlyStopping(
                monitor="val_loss",
                patience=patience,
                restore_best_weights=True,
                verbose=1,
            ),
            ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=0.00001, verbose=1
            ),
            training_logger,
        ]

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
            callbacks=callbacks,
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


class LightweightAttentionPredictor(IntradayPredictor):
    """
    Simpler attention model that's easier to train
    Good for when you have limited data
    """

    def __init__(
        self,
        symbol: str,
        interval: str = "1d",  # Daily candles for better trend detection
        lookback_periods: int = 60,  # 60 days (~2 months) of daily data
        prediction_horizon: int = 1,
        use_csv: bool = True,  # Use CSV data instead of API
    ):
        super().__init__(symbol, interval, lookback_periods, prediction_horizon, use_csv)
        self.model_path = f"models/{symbol}_{interval}_lightweight_attention.keras"
        self.scaler_path = (
            f"models/{symbol}_{interval}_lightweight_attention_scaler.pkl"
        )

    def build_model(self, input_shape: Tuple) -> Model:
        """
        Lightweight attention model - simpler but effective
        """
        inputs = Input(shape=input_shape)

        # Single LSTM layer with dropout and recurrent dropout
        lstm = LSTM(128, return_sequences=True, dropout=0.2, recurrent_dropout=0.2)(
            inputs
        )
        lstm = Dropout(0.2)(lstm)

        # Simple temporal attention
        attention = TemporalAttentionLayer(use_causal_mask=True)(lstm)
        attention = Add()([lstm, attention])  # Residual

        # Final LSTM with dropout and recurrent dropout
        lstm2 = LSTM(64, dropout=0.2, recurrent_dropout=0.2)(attention)
        lstm2 = Dropout(0.2)(lstm2)

        # Output with L2 regularization
        dense = Dense(32, activation="relu", kernel_regularizer=l2(0.001))(lstm2)
        outputs = Dense(1)(dense)

        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])

        return model


def compare_all_models(
    symbol: str,
    interval: str = "1d",
    epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 0.0002,
    use_csv: bool = True,
) -> Dict:
    """
    Compare all three model architectures on the same data
    """
    import os
    from datetime import datetime

    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE MODEL COMPARISON: {symbol} ({interval} candles)")
    print(f"{'='*70}\n")

    results = {}

    # Create results directory if it doesn't exist
    results_dir = "training_results"
    os.makedirs(results_dir, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"{symbol}_{interval}_{timestamp}.txt")

    # Open file for writing results
    with open(results_file, "w") as f:
        f.write(f"{'='*70}\n")
        f.write(f"MODEL COMPARISON: {symbol} ({interval} candles)\n")
        f.write(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Learning Rate: {learning_rate}\n")
        f.write(f"{'='*70}\n\n")

        # 1.  Vanilla LSTM
        print("🔵 Training Vanilla LSTM...")
        f.write("🔵 Training Vanilla LSTM...\n")
        f.flush()

        vanilla = IntradayPredictor(symbol=symbol, interval=interval)
        results["vanilla"] = vanilla.train(
            epochs=epochs, batch_size=batch_size, learning_rate=learning_rate
        )

        f.write(f"✅ Vanilla LSTM Complete:\n")
        f.write(f"   Test Loss (MSE): {results['vanilla']['test_loss']:.6f}\n")
        f.write(f"   Test MAE: {results['vanilla']['test_mae']:.6f}\n")
        f.write(f"   Training Samples: {results['vanilla']['training_samples']}\n")
        f.write(f"   Test Samples: {results['vanilla']['test_samples']}\n")
        f.write(
            f"   Epochs Trained: {results['vanilla'].get('epochs_trained', 'N/A')}\n"
        )
        f.write(
            f"   Overfit Ratio: {results['vanilla'].get('final_overfit_ratio', 'N/A')}\n\n"
        )
        f.flush()

        print("\n" + "-" * 70 + "\n")

        # 2.  Lightweight Attention
        # print("🟡 Training Lightweight Attention-LSTM...")
        # f.write("🟡 Training Lightweight Attention-LSTM...\n")
        # f.flush()

        # lightweight = LightweightAttentionPredictor(symbol=symbol, interval=interval)
        # results["lightweight"] = lightweight.train(epochs=epochs, batch_size=batch_size)

        # f.write(f"✅ Lightweight Attention Complete:\n")
        # f.write(f"   Test Loss (MSE): {results['lightweight']['test_loss']:.6f}\n")
        # f.write(f"   Test MAE: {results['lightweight']['test_mae']:.6f}\n")
        # f.write(f"   Training Samples: {results['lightweight']['training_samples']}\n")
        # f.write(f"   Test Samples: {results['lightweight']['test_samples']}\n\n")
        # f.flush()

        # print("\n" + "-" * 70 + "\n")

        # 3. Optimized Attention (with early stopping, will run up to epochs)
        print("🟢 Training Optimized Multi-Head Attention-LSTM...")
        f.write("🟢 Training Optimized Multi-Head Attention-LSTM...\n")
        f.flush()

        optimized = OptimizedAttentionLSTMPredictor(symbol=symbol, interval=interval)
        results["optimized"] = optimized.train(
            epochs=epochs, batch_size=batch_size, learning_rate=learning_rate
        )

        f.write(f"✅ Optimized Attention Complete:\n")
        f.write(f"   Test Loss (MSE): {results['optimized']['test_loss']:.6f}\n")
        f.write(f"   Test MAE: {results['optimized']['test_mae']:.6f}\n")
        f.write(f"   Training Samples: {results['optimized']['training_samples']}\n")
        f.write(f"   Test Samples: {results['optimized']['test_samples']}\n")
        f.write(f"   Epochs Trained: {results['optimized']['epochs_trained']}\n")
        f.write(
            f"   Overfit Ratio: {results['optimized'].get('final_overfit_ratio', 'N/A')}\n\n"
        )
        f.flush()

        # Print comparison
        f.write(f"{'='*70}\n")
        f.write("FINAL COMPARISON RESULTS\n")
        f.write(f"{'='*70}\n\n")
        f.write(f"{'Model':<30} {'MSE Loss':>15} {'MAE':>15}\n")
        f.write("-" * 70 + "\n")

        for name, result in results.items():
            line = f"{name.upper():<30} {result['test_loss']:>15.6f} {result['test_mae']:>15.6f}\n"
            f.write(line)

        # Find winner
        best_model = min(results.items(), key=lambda x: x[1]["test_loss"])
        winner_line = f"\n✅ BEST MODEL: {best_model[0].upper()} (MSE: {best_model[1]['test_loss']:.6f})\n"
        f.write(winner_line)
        f.write(f"{'='*70}\n")

    # Print comparison to console
    print(f"\n{'='*70}")
    print("FINAL COMPARISON RESULTS")
    print(f"{'='*70}")
    print(f"\n{'Model':<30} {'MSE Loss':>15} {'MAE':>15}")
    print("-" * 70)

    for name, result in results.items():
        print(
            f"{name.upper():<30} {result['test_loss']:>15.6f} {result['test_mae']:>15.6f}"
        )

    # Find winner
    best_model = min(results.items(), key=lambda x: x[1]["test_loss"])
    print(
        f"\n✅ BEST MODEL: {best_model[0].upper()} (MSE: {best_model[1]['test_loss']:.6f})"
    )

    print(f"\n📝 Results saved to: {results_file}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train Attention-LSTM models for cryptocurrency prediction"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=["BTC-USD"],
        help="Cryptocurrency symbols to train (e.g., BTC-USD ETH-USD)",
    )
    parser.add_argument(
        "--interval", type=str, default="1d", help="Candle interval (1d recommended, 4h, 1h)"
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
        "--compare",
        action="store_true",
        help="Run comparison between vanilla and attention models",
    )
    parser.add_argument(
        "--all", action="store_true", help="Train all default cryptocurrencies"
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

    if args.compare:
        # Run comparison for each symbol
        for symbol in symbols:
            results = compare_all_models(
                symbol,
                interval=args.interval,
                epochs=args.epochs,
                batch_size=args.batch_size,
            )
            print("\n" + "=" * 70 + "\n")
    else:
        # Train only Optimized Attention model
        print("🚀 Training Optimized Attention-LSTM Models")
        print("=" * 80)

        for symbol in symbols:
            print(f"\n🔷 Training {symbol}...")
            predictor = OptimizedAttentionLSTMPredictor(
                symbol=symbol, interval=args.interval
            )
            result = predictor.train(
                epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                patience=args.patience,
            )
            print(
                f"✅ {symbol} complete: MSE={result['test_loss']:.6f}, MAE={result['test_mae']:.6f}"
            )

    print("\n✅ Training complete!")
    print(f"\nUsage examples:")
    print(
        f"  python attention_lstm_predictor.py --symbols BTC-USD ETH-USD --epochs 100 --learning-rate 0.0001"
    )
    print(f"  python attention_lstm_predictor.py --all --compare")
    print(
        f"  python attention_lstm_predictor.py --symbols SOL-USD --learning-rate 0.0005 --patience 20"
    )
