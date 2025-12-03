# Overfitting and Accuracy Issues - Root Cause Analysis & Fix

## Problem
Despite fixing data leakage, ML backtesting showed unrealistic 99% accuracy between predictions and actual prices.

## Root Causes Identified

### 1. **Predicting Absolute Prices Instead of Returns** (CRITICAL)
**Location**: `models/intraday_predictor.py` - `prepare_training_data()`

**The Problem**:
- The model was predicting **absolute price values** (e.g., $50,000 → $50,100)
- Cryptocurrency prices are highly **autocorrelated** - tomorrow's price is almost always very close to today's price
- The model learned a trivial pattern: `predicted_price ≈ current_price`
- This gives 99%+ accuracy but provides **zero trading value**

**Example**:
```
Current BTC price: $50,000
Actual next price: $50,100 (+0.2%)
Model prediction: $50,050 (+0.1%)

Absolute price error: Only $50 off → 99.9% accuracy! ✓
Trading signal: WRONG - predicted +0.1% but actual was +0.2% ✗
```

**The Fix**:
Changed the model to predict **percentage returns** instead:
```python
# OLD (Wrong - predicts absolute price)
y.append(features[i + self.prediction_horizon, 0])

# NEW (Correct - predicts percentage change)
current_price = features[i, 0]
future_price = features[i + self.prediction_horizon, 0]
percentage_change = (future_price - current_price) / current_price
y.append(percentage_change)
```

Now the model predicts: `0.002` (meaning +0.2% return) instead of `50100` (absolute price).

### 2. **Incorrect Prediction Logging in Backtester**
**Location**: `ml_backtester.py` - `run_backtest()`

**The Problem**:
```python
# Line 987 - WRONG!
actual_next_price = signal_data["current_price"]  # Default to current price
if i < len(timestamps) - 1:
    # Try to get actual next price
    ...
```

If the code failed to get the actual next candle's price, it defaulted to the **current price**. This created artificial 100% accuracy because we were comparing predictions against the current price (which the model already knows).

**The Fix**:
Only log predictions when we **actually have** the next candle's data:
```python
# Only log if we have valid future data
if i < len(timestamps) - 1:
    next_timestamp = timestamps[i + 1]
    next_data = historical_data[symbol][...]
    if not next_data.empty:
        actual_next_price = float(next_data["Close"].iloc[-1])
        # NOW log the prediction vs actual
        self.predictions_log.append(...)
```

## Changes Made

### File: `backend/models/intraday_predictor.py`

1. **`prepare_training_data()` method**:
   - Changed target from absolute prices to percentage returns
   - Updated documentation to reflect this change
   - Removed scaling of y values (returns don't need scaling)

2. **`predict_next()` method**:
   - Changed to interpret model output as percentage return
   - Convert return to price: `predicted_price = current_price * (1 + predicted_return)`
   - Updated calculation of predicted_change_percent

3. **`build_model()` method**:
   - Updated documentation to clarify output is percentage return

### File: `backend/models/attention_lstm_predictor.py`

1. **`build_model()` method**:
   - Updated output layer comment to indicate percentage return
   - No code changes needed (inherits data preparation from IntradayPredictor)

### File: `backend/ml_backtester.py`

1. **`run_backtest()` method**:
   - Fixed prediction logging to only record when next candle data exists
   - Removed fallback to current_price (which was causing false accuracy)

## Impact

### Before Fix:
- 99% accuracy (misleading)
- Model essentially learned: `tomorrow ≈ today`
- No actual predictive power
- Trading signals were random

### After Fix:
- Accuracy will be much lower (expected: 50-65%)
- **This is GOOD!** - It's now measuring actual directional prediction accuracy
- Model must learn real patterns, not autocorrelation
- Trading signals will be based on genuine predictions

## Next Steps

### 1. Clean Old Scaler Files (CRITICAL!)
```bash
cd backend
python3 cleanup_old_scalers.py
```

**Why this is critical**: The old scalers were trained to normalize absolute prices (e.g., 0-50000). The new models output returns (e.g., -0.05 to +0.05). Using mismatched scalers causes completely wrong predictions.

### 2. Retrain All Models (REQUIRED)
```bash
cd backend
python3 models/hybrid_predictor.py
```

All existing models were trained with the old approach and must be retrained.

### 2. Expected Training Metrics
- **MSE**: Will be higher (but more honest)
- **MAE**: ~0.01 to 0.03 (meaning 1-3% average error in return prediction)
- **Directional Accuracy**: 50-60% is good, 60%+ is excellent

### 3. Evaluation Metrics That Matter
Don't focus on absolute accuracy. Focus on:
- **Sharpe Ratio** in backtests (>1.0 is good)
- **Win Rate** (>55% is profitable)
- **Profit Factor** (ratio of winning to losing trades)
- **Max Drawdown** (risk management)

## Technical Details

### Why Predicting Returns is Better

1. **Stationarity**: Returns are more stationary than prices
2. **Comparability**: 2% return on BTC is comparable to 2% on ETH
3. **No Autocorrelation**: Returns don't have the trivial pattern prices have
4. **Trading Focus**: We care about % changes, not absolute values

### Model Output Interpretation

```python
model_output = 0.023  # Model predicts 2.3% return

# Convert to price
current_price = 50000
predicted_price = 50000 * (1 + 0.023) = 51150

# Trading signal
if model_output > 0.005:  # Predict >0.5% gain
    signal = "BUY"
```

## Validation

After retraining, verify fixes by checking:

1. **Training logs should show**: "Predicting returns (not absolute prices)"
2. **MAE should be small numbers**: ~0.01 to 0.03 (not thousands)
3. **Backtest accuracy**: Should be 50-65%, not 99%
4. **Predictions should vary**: Both positive and negative returns predicted

## References

- Original issue: Data leakage (fixed previously via train/test split)
- This issue: Autocorrelation bias (fixed via return prediction)
- Related: Time series forecasting best practices (stationary data)
