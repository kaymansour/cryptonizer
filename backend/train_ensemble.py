# backend/train_ensemble.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import yfinance as yf
import requests
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor
import tensorflow as tf
from tensorflow.keras import layers, models
from math import sqrt

from models.feature_utils import add_features, make_lstm_sequences

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "saved_models"
MODELS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------
# Helper: build BLSTM model
# ---------------------------------------------------------------------
def build_blstm(input_shape):
    model = models.Sequential(
        [
            layers.Bidirectional(layers.LSTM(64, return_sequences=False), input_shape=input_shape),
            layers.Dense(32, activation="relu"),
            layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    return model


# ---------------------------------------------------------------------
# Train ensemble for one symbol
# ---------------------------------------------------------------------
def train_for_symbol(symbol: str, interval: str = "4h", lookback: int = 60, test_size: float = 0.2) -> Dict[str, Any]:
    print(f"\n===== 🚀 Training ensemble for {symbol} ({interval}) =====")

    try:
        # 1️⃣ Download data
        data = yf.download(symbol, period="365d", interval=interval)
        data = data.dropna().reset_index(drop=True)

        if len(data) < lookback + 50:
            raise ValueError(f"Not enough data for {symbol} ({len(data)} rows).")

        # 2️⃣ Build BLSTM dataset
        X_seq, y_seq, feature_cols = make_lstm_sequences(
            data, lookback=lookback, feature_cols=["Close", "Volume"], target_col="Close"
        )

        seq_2d = X_seq.reshape(-1, X_seq.shape[-1])
        scaler_lstm = StandardScaler()
        seq_2d_scaled = scaler_lstm.fit_transform(seq_2d)
        X_seq_scaled = seq_2d_scaled.reshape(X_seq.shape)

        X_seq_train, X_seq_val, y_seq_train, y_seq_val = train_test_split(
            X_seq_scaled, y_seq, test_size=test_size, shuffle=False
        )

        # 3️⃣ Train BLSTM
        blstm = build_blstm(input_shape=(lookback, X_seq.shape[-1]))
        blstm.fit(
            X_seq_train,
            y_seq_train,
            epochs=10,
            batch_size=32,
            validation_data=(X_seq_val, y_seq_val),
            verbose=1,
        )

        y_pred_lstm_val = blstm.predict(X_seq_val).flatten()
        rmse_lstm = sqrt(mean_squared_error(y_seq_val, y_pred_lstm_val))
        print(f"{symbol} BLSTM RMSE: {rmse_lstm:.4f}")

        # 4️⃣ Train XGBoost
        df_feat = add_features(data[["Close", "Volume"]].copy())
        df_feat["target"] = df_feat["Close"].shift(-1)
        df_feat = df_feat.dropna().reset_index(drop=True)

        X_tab = df_feat.drop(columns=["target"]).values
        y_tab = df_feat["target"].values

        scaler_xgb = StandardScaler()
        X_tab_scaled = scaler_xgb.fit_transform(X_tab)

        X_tab_train, X_tab_val, y_tab_train, y_tab_val = train_test_split(
            X_tab_scaled, y_tab, test_size=test_size, shuffle=False
        )

        xgb = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
        )
        xgb.fit(X_tab_train, y_tab_train)

        y_pred_xgb_val = xgb.predict(X_tab_val)
        rmse_xgb = sqrt(mean_squared_error(y_tab_val, y_pred_xgb_val))
        print(f"{symbol} XGB RMSE: {rmse_xgb:.4f}")

        # 5️⃣ Combine ensemble weights
        inv_lstm = 1.0 / rmse_lstm
        inv_xgb = 1.0 / rmse_xgb
        w_lstm = inv_lstm / (inv_lstm + inv_xgb)
        w_xgb = inv_xgb / (inv_lstm + inv_xgb)

        print(f"{symbol} Ensemble Weights → BLSTM: {w_lstm:.3f}, XGB: {w_xgb:.3f}")

        # 6️⃣ Save models + metadata
        prefix = f"{symbol.replace('-', '')}_{interval.replace('/', '')}"

        blstm_path = MODELS_DIR / f"blstm_{prefix}.keras"
        blstm.save(blstm_path)

        joblib.dump(
            {"scaler": scaler_lstm, "lookback": lookback, "feature_cols": feature_cols},
            MODELS_DIR / f"blstm_meta_{prefix}.pkl",
        )

        joblib.dump(
            {"model": xgb, "scaler": scaler_xgb, "feature_names": list(df_feat.drop(columns=['target']).columns)},
            MODELS_DIR / f"xgb_{prefix}.pkl",
        )

        ensemble_meta = {
            "symbol": symbol,
            "interval": interval,
            "w_lstm": float(w_lstm),
            "w_xgb": float(w_xgb),
            "rmse_lstm": float(rmse_lstm),
            "rmse_xgb": float(rmse_xgb),
        }

        with open(MODELS_DIR / f"ensemble_{prefix}.json", "w") as f:
            json.dump(ensemble_meta, f, indent=2)

        print(f"✅ Saved all model files for {symbol}")
        return ensemble_meta

    except Exception as e:
        print(f"❌ Failed training {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


# ---------------------------------------------------------------------
# Main: train for top 50 coins dynamically
# ---------------------------------------------------------------------
def main():
    print("\n🌐 Fetching top 50 coins from CoinGecko...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 50, "page": 1, "sparkline": False}
    coins = requests.get(url, params=params, timeout=15).json()

    # Convert to Yahoo Finance symbols
    symbols = []
    for c in coins:
        symbol = f"{c['symbol'].upper()}-USD"
        symbols.append(symbol)

    print(f"📊 Found {len(symbols)} coins: {symbols}")

    interval = "4h"
    results = {}

    for sym in symbols:
        meta = train_for_symbol(sym, interval=interval)
        results[sym] = meta

    print("\n✅ All training complete. Saved models in", MODELS_DIR)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
