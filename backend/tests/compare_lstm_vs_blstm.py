from models.intraday_predictor import IntradayPredictor
from models.intraday_predictor_blstm import IntradayPredictor as BLSTMPredictor
import yfinance as yf
import math
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta


def bars_per_day_for_interval(interval: str) -> int:
    if interval == "1h":
        return 24
    if interval == "4h":
        return 6
    # Fallback: assume hourly granularity
    return 24


def main():
    symbol = "BTC-USD"
    interval = "4h"

    print(f"Comparing LSTM vs BLSTM for {symbol} ({interval})")

    # Instantiate models (to read lookback requirements and load models/scalers)
    lstm = IntradayPredictor(symbol, interval=interval)
    blstm = BLSTMPredictor(symbol, interval=interval)

    lstm.load_model()
    blstm.load_model()

    # Compute required history length to satisfy feature windows and lookback
    max_feature_window = 50  # MA_50 is the longest rolling window used
    lookback_needed = max(lstm.lookback_periods, blstm.lookback_periods)
    min_raw_bars = lookback_needed + max_feature_window
    bpd = bars_per_day_for_interval(interval)
    days_needed = math.ceil(min_raw_bars / bpd) + 5  # safety margin
    period_str = f"{days_needed}d"

    # Download recent data with sufficient history; expand window if needed
    max_days = 720  # yfinance limit for 4h/1h
    while True:
        data = yf.download(symbol, period=period_str, interval=interval, progress=False)
        # Validate after feature engineering for both models
        lstm_processed = len(lstm._add_features(data.copy()))
        blstm_processed = len(blstm._add_features(data.copy()))
        if (
            lstm_processed >= lstm.lookback_periods
            and blstm_processed >= blstm.lookback_periods
        ) or days_needed >= max_days:
            break
        # Expand window and retry
        days_needed = min(days_needed + 14, max_days)
        period_str = f"{days_needed}d"

    # Predict with independent copies to avoid in-place mutations
    blstm_pred = blstm.predict_next(data.copy())
    lstm_pred = lstm.predict_next(data.copy())

    # Pretty-print summary table
    def fmt_price(x: float) -> str:
        return f"${x:,.2f}"

    def fmt_pct(x: float) -> str:
        return f"{x:+.3f}%"

    current_price = lstm_pred.get("current_price")  # same for both
    lstm_change = float(lstm_pred["predicted_change_percent"])
    blstm_change = float(blstm_pred["predicted_change_percent"])
    diff_pp = blstm_change - lstm_change
    agreement = "YES" if lstm_pred["signal"] == blstm_pred["signal"] else "NO"

    header = f"Results Summary ({symbol}, {interval})"
    line = "=" * max(len(header), 60)
    print("\n" + line)
    print(header)
    print(line)
    print(
        f"Data window: period={period_str}, raw_bars={len(data)}, "
        f"lstm_processed={lstm_processed}, blstm_processed={blstm_processed}"
    )
    print(f"Current price: {fmt_price(current_price)} | Horizon: next candle")

    # Table header
    print("\nModel        Predicted Price     Change %     Signal")
    print("-" * 60)
    print(
        f"LSTM         {fmt_price(lstm_pred['predicted_price']):>15}  "
        f"{fmt_pct(lstm_change):>9}   {lstm_pred['signal']}"
    )
    print(
        f"BLSTM        {fmt_price(blstm_pred['predicted_price']):>15}  "
        f"{fmt_pct(blstm_change):>9}   {blstm_pred['signal']}"
    )

    print("-" * 60)
    direction = "more bullish" if diff_pp > 0 else ("more bearish" if diff_pp < 0 else "no difference")
    print(f"Confidence gap (BLSTM - LSTM): {fmt_pct(diff_pp)} ({direction})")
    print(f"Signal agreement: {agreement}")

    # ------------------------------------------------------------
    # Persist predictions to CSV and compute actuals/errors
    # ------------------------------------------------------------
    csv_path = Path(__file__).with_name("predictions_log.csv")

    # Determine the prediction timestamp (next candle time)
    last_idx = data.index[-1]
    # Normalize to UTC-aware Timestamp
    if getattr(last_idx, "tzinfo", None) is None or last_idx.tz is None:
        last_idx = pd.to_datetime(last_idx).tz_localize("UTC")
    else:
        last_idx = last_idx.tz_convert("UTC")

    hours = 4 if interval.endswith("4h") else 1
    next_bar_time = last_idx + pd.Timedelta(hours=hours)
    next_bar_time_utc = next_bar_time.tz_convert("UTC")

    # Create both UTC and Bahrain timestamps
    bahrain_time = next_bar_time_utc.tz_convert("Asia/Bahrain")
    bahrain_str = bahrain_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    ts_str = next_bar_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Prediction target (Bahrain time): {bahrain_str}")

    # Prepare row to append
    new_row = {
        "timestamp": ts_str,                # UTC time of the next candle
        "timestamp_bahrain": bahrain_str,   # Local Bahrain time
        "symbol": symbol,
        "interval": interval,
        "current_price": float(current_price) if current_price is not None else np.nan,
        "lstm_predicted_price": float(lstm_pred.get("predicted_price", np.nan)),
        "blstm_predicted_price": float(blstm_pred.get("predicted_price", np.nan)),
        "actual_price": np.nan,
        "lstm_error_pct": np.nan,
        "blstm_error_pct": np.nan,
    }

    cols = [
        "timestamp",
        "timestamp_bahrain",
        "symbol",
        "interval",
        "current_price",
        "lstm_predicted_price",
        "blstm_predicted_price",
        "actual_price",
        "lstm_error_pct",
        "blstm_error_pct",
    ]

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        # Ensure required columns exist
        for c in cols:
            if c not in df.columns:
                df[c] = np.nan
        df = df[cols]
    else:
        df = pd.DataFrame(columns=cols)

    # Append the new prediction row (allows duplicates if run multiple times)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Try to backfill actual prices for any rows missing them
    # Convert timestamp strings to UTC-aware Timestamps for matching
    ts_series = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["_ts"] = ts_series

    # Fetch sufficient history to cover missing actuals (up to 730d window for 4h/1h)
    missing_mask = df["actual_price"].isna() & df["_ts"].notna()
    actual_now = np.nan
    if missing_mask.any():
        try:
            hist = yf.download(symbol, period="730d", interval=interval, progress=False)
            if not hist.empty:
                if getattr(hist.index, "tzinfo", None) is None or hist.index.tz is None:
                    hist.index = hist.index.tz_localize("UTC")
                else:
                    hist.index = hist.index.tz_convert("UTC")

                close_series = hist["Close"].copy()
                # Map available actuals
                available_mask = missing_mask & df["_ts"].isin(close_series.index)
                if available_mask.any():
                    df.loc[available_mask, "actual_price"] = df.loc[available_mask, "_ts"].map(close_series)

                # Also check whether the just-predicted timestamp has an actual already
                if next_bar_time_utc in close_series.index:
                    actual_now = float(close_series.loc[next_bar_time_utc])
        except Exception as e:
            print(f"Warning: could not fetch history for actuals: {e}")

    # Compute error percentages where actual is available
    with np.errstate(divide="ignore", invalid="ignore"):
        has_actual = df["actual_price"].notna()
        df.loc[has_actual, "lstm_error_pct"] = (
            (df.loc[has_actual, "lstm_predicted_price"] - df.loc[has_actual, "actual_price"]).abs()
            / df.loc[has_actual, "actual_price"]
            * 100.0
        )
        df.loc[has_actual, "blstm_error_pct"] = (
            (df.loc[has_actual, "blstm_predicted_price"] - df.loc[has_actual, "actual_price"]).abs()
            / df.loc[has_actual, "actual_price"]
            * 100.0
        )

    # Drop helper column and persist the log (rewrite to keep file tidy)
    df = df.drop(columns=["_ts"]) 
    df.to_csv(csv_path, index=False)

    # Print summary for the current prediction vs actual (if available)
    if not np.isnan(actual_now):
        lstm_err = abs(new_row["lstm_predicted_price"] - actual_now) / actual_now * 100.0
        blstm_err = abs(new_row["blstm_predicted_price"] - actual_now) / actual_now * 100.0
        print("\nActual price:", fmt_price(actual_now))
        print(f"LSTM error: {lstm_err:.2f}%")
        print(f"BLSTM error: {blstm_err:.2f}%")
    else:
        print(
            f"\nActual price not available yet for {ts_str} (waiting for candle close)."
        )

    # Running averages across all logged predictions (where actual exists)
    has_actual_any = df["actual_price"].notna()
    if has_actual_any.any():
        lstm_mape = df.loc[has_actual_any, "lstm_error_pct"].astype(float).mean()
        blstm_mape = df.loc[has_actual_any, "blstm_error_pct"].astype(float).mean()
        lstm_mae = (df.loc[has_actual_any, "lstm_predicted_price"] - df.loc[has_actual_any, "actual_price"]).abs().mean()
        blstm_mae = (df.loc[has_actual_any, "blstm_predicted_price"] - df.loc[has_actual_any, "actual_price"]).abs().mean()
        count = int(has_actual_any.sum())
        print("\nRunning metrics (", count, "completed predictions):", sep="")
        print(f"- LSTM  MAPE: {lstm_mape:.2f}% | MAE: {fmt_price(lstm_mae)}")
        print(f"- BLSTM MAPE: {blstm_mape:.2f}% | MAE: {fmt_price(blstm_mae)}")


if __name__ == "__main__":
    main()
