"""
Optimized Attention-LSTM Cryptocurrency Price Predictor
Enhanced LSTM with multi-head attention mechanism for improved temporal pattern recognition
"""

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
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras import backend as K
import tensorflow as tf

from intraday_predictor import IntradayPredictor


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

    def build(self, input_shape):
        # input_shape: (batch_size, time_steps, features)
        self.features = input_shape[-1]

        # Query, Key, Value projections for each head
        self.query_dense = Dense(self.num_heads * self.key_dim, use_bias=False)
        self.key_dense = Dense(self.num_heads * self.key_dim, use_bias=False)
        self.value_dense = Dense(self.num_heads * self.key_dim, use_bias=False)

        # Output projection
        self.output_dense = Dense(self.features)

        # Dropout for attention weights
        self.attention_dropout = Dropout(self.dropout_rate)

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


class TemporalAttentionLayer(Layer):
    """
    Temporal attention that preserves sequence information
    Produces attention-weighted features while keeping temporal dimension
    """

    def __init__(self, use_causal_mask: bool = True, **kwargs):
        super(TemporalAttentionLayer, self).__init__(**kwargs)
        self.use_causal_mask = use_causal_mask

    def build(self, input_shape):
        self.features = input_shape[-1]

        self.W_query = self.add_weight(
            name="query_weight",
            shape=(self.features, self.features),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.W_key = self.add_weight(
            name="key_weight",
            shape=(self.features, self.features),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.W_value = self.add_weight(
            name="value_weight",
            shape=(self.features, self.features),
            initializer="glorot_uniform",
            trainable=True,
        )

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
        interval: str = "1h",
        lookback_periods: int = 168,
        prediction_horizon: int = 1,
        num_attention_heads: int = 4,
        use_bidirectional: bool = True,
    ):
        super().__init__(symbol, interval, lookback_periods, prediction_horizon)

        self.num_attention_heads = num_attention_heads
        self.use_bidirectional = use_bidirectional

        # Override model paths
        self.model_path = f"models/{symbol}_{interval}_optimized_attention.keras"
        self.scaler_path = f"models/{symbol}_{interval}_optimized_attention_scaler.pkl"

    def build_model(self, input_shape: Tuple) -> Model:
        """
        Build Optimized Attention-LSTM model

        Architecture:
        - Bidirectional LSTM for rich temporal features
        - Multi-head attention with causal masking
        - Residual connections
        - Gradual dimension reduction
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
        dense1 = Dense(32, activation="relu", kernel_regularizer=l2(0.001))(lstm3)
        dense1 = Dropout(0.2)(dense1)
        dense2 = Dense(16, activation="relu", kernel_regularizer=l2(0.001))(dense1)
        outputs = Dense(1)(dense2)

        model = Model(inputs=inputs, outputs=outputs)

        # Use a lower learning rate for attention models
        from keras.optimizers import Adam

        optimizer = Adam(learning_rate=0.0005)

        model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])

        return model

    def train(self, epochs: int = 100, batch_size: int = 32) -> Dict:
        """
        Train with early stopping and learning rate scheduling
        """
        print(f"\n{'='*60}")
        print(f"Training OPTIMIZED Attention-LSTM for {self.symbol} ({self.interval})")
        print(f"{'='*60}")

        # Fetch and prepare data
        data = self.fetch_intraday_data()
        X_train, y_train, X_test, y_test = self.prepare_training_data(data)

        # Build model
        self.model = self.build_model((X_train.shape[1], X_train.shape[2]))

        # Print model summary
        self.model.summary()

        # Callbacks for better training
        callbacks = [
            EarlyStopping(
                monitor="val_loss", patience=15, restore_best_weights=True, verbose=1
            ),
            ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=0.00001, verbose=1
            ),
        ]

        # Train with more epochs but early stopping
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
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
            "epochs_trained": len(history.history["loss"]),
        }


class LightweightAttentionPredictor(IntradayPredictor):
    """
    Simpler attention model that's easier to train
    Good for when you have limited data
    """

    def __init__(
        self,
        symbol: str,
        interval: str = "1h",
        lookback_periods: int = 168,
        prediction_horizon: int = 1,
    ):
        super().__init__(symbol, interval, lookback_periods, prediction_horizon)
        self.model_path = f"models/{symbol}_{interval}_lightweight_attention.keras"
        self.scaler_path = (
            f"models/{symbol}_{interval}_lightweight_attention_scaler.pkl"
        )

    def build_model(self, input_shape: Tuple) -> Model:
        """
        Lightweight attention model - simpler but effective
        """
        inputs = Input(shape=input_shape)

        # Single LSTM layer with more units
        lstm = LSTM(128, return_sequences=True)(inputs)
        lstm = Dropout(0.2)(lstm)

        # Simple temporal attention
        attention = TemporalAttentionLayer(use_causal_mask=True)(lstm)
        attention = Add()([lstm, attention])  # Residual

        # Final LSTM to collapse sequence
        lstm2 = LSTM(64)(attention)
        lstm2 = Dropout(0.2)(lstm2)

        # Output
        dense = Dense(32, activation="relu")(lstm2)
        outputs = Dense(1)(dense)

        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])

        return model


def compare_all_models(
    symbol: str, interval: str = "4h", epochs: int = 100, batch_size: int = 32
) -> Dict:
    """
    Compare all three model architectures on the same data
    """
    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE MODEL COMPARISON: {symbol} ({interval} candles)")
    print(f"{'='*70}\n")

    results = {}

    # 1.  Vanilla LSTM
    print("🔵 Training Vanilla LSTM...")
    vanilla = IntradayPredictor(symbol=symbol, interval=interval)
    results["vanilla"] = vanilla.train(epochs=epochs, batch_size=batch_size)

    print("\n" + "-" * 70 + "\n")

    # 2.  Lightweight Attention
    print("🟡 Training Lightweight Attention-LSTM...")
    lightweight = LightweightAttentionPredictor(symbol=symbol, interval=interval)
    results["lightweight"] = lightweight.train(epochs=epochs, batch_size=batch_size)

    print("\n" + "-" * 70 + "\n")

    # 3. Optimized Attention (with early stopping, will run up to epochs)
    print("🟢 Training Optimized Multi-Head Attention-LSTM...")
    optimized = OptimizedAttentionLSTMPredictor(symbol=symbol, interval=interval)
    results["optimized"] = optimized.train(epochs=epochs, batch_size=batch_size)

    # Print comparison
    print(f"\n{'='*70}")
    print("FINAL COMPARISON RESULTS")
    print(f"{'='*70}")
    print(f"\n{'Model':<30} {'MSE Loss':>15} {'MAE':>15}")
    print("-" * 70)

    for name, result in results.items():
        print(
            f"{name. upper():<30} {result['test_loss']:>15. 6f} {result['test_mae']:>15.6f}"
        )

    # Find winner
    best_model = min(results.items(), key=lambda x: x[1]["test_loss"])
    print(
        f"\n✅ BEST MODEL: {best_model[0]. upper()} (MSE: {best_model[1]['test_loss']:. 6f})"
    )

    return results


if __name__ == "__main__":
    # Test on BTC and ETH
    for symbol in ["BTC-USD", "ETH-USD"]:
        results = compare_all_models(symbol, interval="4h", epochs=100, batch_size=32)
        print("\n" + "=" * 70 + "\n")
