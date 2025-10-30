"""
Non-LSTM price prediction with feature engineering and tree/linear models.

Key changes for better accuracy and robustness:
- Forecast next-day log returns (stationary) instead of raw prices.
- Feature engineering: return lags, moving-average gaps, volatility, RSI.
- Models: Linear Regression (scaled), RandomForest, XGBoost, plus RF+XGB ensemble.
- Time-aware split, reproducibility, and robust multi-step inference.
- Cached results and plot-as-base64 preserved to match API outputs.
"""

# type: ignore
import io
import base64
import time
import datetime
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBRegressor  # type: ignore
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False

import yfinance as yf

# ----------------------------------------------------------------------------
# Cache and randomness
# ----------------------------------------------------------------------------
cache: Dict[str, Dict[str, Any]] = {}
CACHE_DURATION = 60 * 60 * 24  # 24 hours
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)


# ----------------------------------------------------------------------------
# Data fetching
# ----------------------------------------------------------------------------
def fetch_data(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch OHLCV from Yahoo! Finance and return a DataFrame with a 'Close' column.
    Returns an empty DataFrame on failure.
    """
    try:
        df = yf.download(symbol, period=period, progress=False)
        if df.empty:
            print(f"No data found for {symbol}")
            return pd.DataFrame()

        # Handle MultiIndex columns (can happen for some tickers)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join([c for c in col if c]) for col in df.columns]

        # Find a close-like column
        close_col = None
        for col in df.columns:
            if "Close" in str(col):
                close_col = col
                break
        if close_col is None:
            print(f"No Close column found for {symbol} in columns: {list(df.columns)}")
            return pd.DataFrame()

        out = df[[close_col]].copy()
        out.columns = ["Close"]
        out.dropna(inplace=True)
        return out
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()


# ----------------------------------------------------------------------------
# Feature engineering
# ----------------------------------------------------------------------------
def _compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1 / window, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / window, adjust=False).mean()
    rs = roll_up / (roll_down + 1e-12)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list[str]]:
    data = df.copy()
    data["log_close"] = np.log(data["Close"].astype(float))
    data["log_return"] = data["log_close"].diff()

    # Return lags
    for lag in range(1, 6):
        data[f"r_lag{lag}"] = data["log_return"].shift(lag)

    # Moving averages and price gaps
    for w in [5, 10, 20]:
        data[f"sma_{w}"] = data["Close"].rolling(w).mean()
        data[f"gap_sma_{w}"] = data["Close"] / (data[f"sma_{w}"] + 1e-12) - 1.0

    # Volatility features (rolling std of returns)
    for w in [5, 10, 20]:
        data[f"vol_{w}"] = data["log_return"].rolling(w).std()

    # RSI (normalized around 0)
    data["rsi_14"] = _compute_rsi(data["Close"], 14)
    data["rsi_14_norm"] = (data["rsi_14"] - 50.0) / 50.0

    # Target: next-day log return
    data["target"] = data["log_return"].shift(-1)

    feature_cols = [
        "r_lag1",
        "r_lag2",
        "r_lag3",
        "r_lag4",
        "r_lag5",
        "gap_sma_5",
        "gap_sma_10",
        "gap_sma_20",
        "vol_5",
        "vol_10",
        "vol_20",
        "rsi_14_norm",
    ]

    data = data.dropna(subset=feature_cols + ["target"]).copy()
    X = data[feature_cols]
    y = data["target"]
    return X, y, feature_cols


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


# ----------------------------------------------------------------------------
# Training
# ----------------------------------------------------------------------------
def train_models(symbol: str):
    """Train models on engineered features to predict next-day log returns.
    Returns (df, model_bundle, best_name, best_rmse).
    """
    print(f"Training models for {symbol} (non-LSTM)")
    df = fetch_data(symbol)
    if df.empty:
        raise ValueError(f"Could not fetch data for {symbol}.")
    if len(df) < 60:
        raise ValueError(f"Not enough data for {symbol}. Need >=60 rows, got {len(df)}.")

    X, y, feature_cols = _build_features(df)
    if len(X) < 50:
        raise ValueError(
            f"Not enough samples after feature engineering for {symbol}. Got {len(X)}."
        )

    # Time-aware split (no shuffle)
    test_size = 0.2 if len(X) >= 100 else max(0.15, min(0.2, 20 / len(X)))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False
    )
    print(f"Train/Test sizes: {len(X_train)}/{len(X_test)}")

    # Scaler for linear model
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results: list[tuple[Dict[str, Any], Tuple[str, Any]]] = []

    # Linear Regression (baseline on scaled features)
    try:
        lr = LinearRegression()
        lr.fit(X_train_scaled, y_train)
        pred_lr = lr.predict(X_test_scaled)
        rmse_lr = _rmse(y_test.values, pred_lr)
        print(f"Linear Regression RMSE (returns): {rmse_lr:.6f}")
        results.append(({"model": "Linear Regression", "rmse": rmse_lr}, ("lr", lr)))
    except Exception as e:
        print(f"Linear Regression failed: {e}")

    # Random Forest
    try:
        rf = RandomForestRegressor(
            n_estimators=300,
            random_state=RANDOM_STATE,
            max_depth=None,
            min_samples_leaf=1,
            n_jobs=-1,
        )
        rf.fit(X_train, y_train)
        pred_rf = rf.predict(X_test)
        rmse_rf = _rmse(y_test.values, pred_rf)
        print(f"Random Forest RMSE (returns): {rmse_rf:.6f}")
        results.append(({"model": "Random Forest", "rmse": rmse_rf}, ("rf", rf)))
    except Exception as e:
        print(f"Random Forest failed: {e}")

    # XGBoost
    if XGB_AVAILABLE:
        try:
            xgb = XGBRegressor(
                n_estimators=400,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_lambda=1.0,
                random_state=RANDOM_STATE,
                n_jobs=-1,
                objective="reg:squarederror",
            )
            xgb.fit(
                X_train,
                y_train,
                eval_set=[(X_test, y_test)],
                eval_metric="rmse",
                verbose=False,
                early_stopping_rounds=25,
            )
            pred_xgb = xgb.predict(X_test)
            rmse_xgb = _rmse(y_test.values, pred_xgb)
            print(f"XGBoost RMSE (returns): {rmse_xgb:.6f}")
            results.append(({"model": "XGBoost", "rmse": rmse_xgb}, ("xgb", xgb)))
        except Exception as e:
            print(f"XGBoost failed: {e}")
    else:
        print("XGBoost not available; skipping.")

    # Simple ensemble of RF and XGB if both trained
    try:
        rf_model = next((m for (res, (nm, m)) in results if nm == "rf"), None)
        xgb_model = next((m for (res, (nm, m)) in results if nm == "xgb"), None)
        if rf_model is not None and xgb_model is not None:
            pred_ens = (rf_model.predict(X_test) + xgb_model.predict(X_test)) / 2.0
            rmse_ens = _rmse(y_test.values, pred_ens)
            print(f"Ensemble (RF+XGB) RMSE (returns): {rmse_ens:.6f}")
            results.append(
                (
                    {"model": "Ensemble(RF+XGB)", "rmse": rmse_ens},
                    ("ensemble", ("rf_xgb", rf_model, xgb_model)),
                )
            )
    except Exception as e:
        print(f"Ensemble failed: {e}")

    if not results:
        raise ValueError("No models were successfully trained")

    best_result, best_payload = min(results, key=lambda x: x[0]["rmse"])  # type: ignore
    best_name = best_result["model"]
    best_rmse = float(best_result["rmse"])
    print(f"Best: {best_name} (RMSE: {best_rmse:.6f} returns)")

    model_bundle = {
        "kind": best_payload[0],
        "model": best_payload[1],
        "features": feature_cols,
        "scaler": scaler,
    }
    return df, model_bundle, best_name, best_rmse


# ----------------------------------------------------------------------------
# Inference
# ----------------------------------------------------------------------------
def predict_future(symbol: str, days_ahead: int = 7) -> Dict[str, Any]:
    """Predict future prices for the given symbol for N days ahead.
    Keeps the previous response schema (model, rmse, last_price, plot_base64, future_predictions).
    """
    now = time.time()
    if symbol in cache and now - cache[symbol]["timestamp"] < CACHE_DURATION:
        return cache[symbol]["data"]

    try:
        df, bundle, best_name, best_rmse = train_models(symbol)
        last_price = float(df["Close"].iloc[-1])

        # Iterative multi-step forecasts using log-return predictions
        work_df = df.copy()
        future_prices: list[float] = []

        def _predict_next_log_return(bndl: Dict[str, Any], hist_df: pd.DataFrame) -> float:
            X_all, _, _ = _build_features(hist_df)
            if X_all.empty:
                return 0.0
            last_X = X_all.iloc[[-1]]
            kind = bndl["kind"]
            model = bndl["model"]
            if kind == "lr":
                X_last_scaled = bndl["scaler"].transform(last_X)
                return float(model.predict(X_last_scaled)[0])
            if kind == "rf":
                return float(model.predict(last_X)[0])
            if kind == "xgb":
                return float(model.predict(last_X)[0])
            if kind == "ensemble":
                rf_model = bndl["model"][1]
                xgb_model = bndl["model"][2]
                return float((rf_model.predict(last_X) + xgb_model.predict(last_X)) / 2.0)
            return 0.0

        for _ in range(days_ahead):
            try:
                pred_log_ret = _predict_next_log_return(bundle, work_df)
                next_price = float(work_df["Close"].iloc[-1] * np.exp(pred_log_ret))
            except Exception:
                next_price = float(work_df["Close"].iloc[-1])

            future_prices.append(next_price)
            next_idx = work_df.index[-1] + pd.Timedelta(days=1)
            work_df.loc[next_idx, "Close"] = next_price

        # Future date labels (as dates, for frontend rendering)
        future_dates = [datetime.date.today() + datetime.timedelta(days=i + 1) for i in range(days_ahead)]
        pred_df = pd.DataFrame({
            "Date": future_dates,
            "Predicted_Price": [round(float(p), 2) for p in future_prices],
        })

        # Plot: last 30 historical vs future
        plt.figure(figsize=(10, 6))
        historical_points = min(30, len(df))
        historical_dates = df.index[-historical_points:]
        historical_prices = df["Close"].tail(historical_points)

        plt.plot(historical_dates, historical_prices, label="Historical Prices", linewidth=2, color="#10b981")
        plt.plot(pred_df["Date"], pred_df["Predicted_Price"], label=f"Predicted ({best_name})", linestyle="--", marker="o", linewidth=2, color="#3b82f6")
        plt.title(f"{symbol} Price Prediction\nBest Model: {best_name} (RMSE: {best_rmse:.6f} returns)", fontsize=14)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Price (USD)", fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close()
        buf.seek(0)
        plot_base64 = base64.b64encode(buf.read()).decode("utf-8")

        data = {
            "symbol": symbol,
            "model": best_name,
            "rmse": round(float(best_rmse), 6),
            "last_price": round(float(last_price), 2),
            "plot_base64": plot_base64,
            "future_predictions": pred_df.to_dict(orient="records"),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        cache[symbol] = {"timestamp": now, "data": data}
        return data

    except Exception as e:
        # Fallback response
        return {
            "symbol": symbol,
            "model": "Fallback",
            "rmse": 0.0,
            "last_price": 0.0,
            "plot_base64": "",
            "future_predictions": [],
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
        }


def test_prediction() -> bool:
    """Quick local test using BTC-USD."""
    try:
        result = predict_future("BTC-USD", days_ahead=7)
        return "error" not in result
    except Exception:
        return False


if __name__ == "__main__":
    ok = test_prediction()
    print("Prediction test:", "OK" if ok else "FAILED")

