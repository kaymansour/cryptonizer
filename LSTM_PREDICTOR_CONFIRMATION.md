# LSTM Predictor Architecture - Confirmation

## Yes, Using the SAME `IntradayPredictor` Class

The `/api/predict-next-candles` endpoint uses **exactly the same** LSTM predictor as the ML Trading Backtest.

### Shared Components:

```python
# Location: backend/models/intraday_predictor.py
class IntradayPredictor:
    """
    LSTM-based price predictor for intraday trading (1h or 4h candles)
    """
```

### What Gets Reused:

1. **Same Model Architecture**:
   - 3-layer stacked LSTM (128 → 64 → 32 units)
   - Same training data and features
   - Same `.keras` model files loaded from disk

2. **Same Feature Engineering**:
   - MA_20, MA_50 (Moving Averages)
   - RSI (Relative Strength Index)
   - Price_Change, Volatility, Volume_Change
   - Identical `_add_features()` method

3. **Same `predict_next()` Method**:
   - Both endpoints call `predictor.predict_next(recent_data)`
   - Returns: `{current_price, predicted_price, predicted_change_percent, signal}`

### Key Differences in Usage:

| Feature | ML Trading Backtest | Predict Next Candles API |
|---------|-------------------|-------------------------|
| **Purpose** | Historical simulation | Future prediction |
| **Time Direction** | Looks backward | Looks forward |
| **Iterations** | Loops through historical data | Loops 7 steps into future |
| **Data Source** | Past market data | Recent + simulated future |
| **Output** | Trade history + performance | 7-step price predictions |

### Multi-Step Prediction Process:

```python
# From portfolio.py line ~230
for step in range(7):  # Predict 7 candles ahead
    pred = predictor.predict_next(current_data)  # Same method!
    
    # Store prediction
    candle_predictions.append(pred)
    
    # Simulate: Append predicted price as if it happened
    # Then re-run feature engineering for next prediction
    current_data = update_with_prediction(current_data, pred)
```

### Data Fetching Fix (Your Error):

**Problem**: Feature engineering drops ~60 rows (NaN from rolling windows)

**Solution**: 
```python
# OLD (caused "Got 0 periods" error)
recent_data = predictor.fetch_intraday_data(days_back=60)  # Not enough!

# NEW (fixed)
days_to_fetch = 365 if interval == "4h" else 730
recent_data = predictor.fetch_intraday_data(days_back=days_to_fetch)
# After feature engineering: Still have 168+ periods ✅
```

### Debug Logs Added:

```
🔮 Predicting for BTC-USD
   Loading model from: models/BTC-USD_4h_predictor.keras
   Model loaded successfully
   Fetching 365 days of data...
   Fetched 2190 candles
   After feature engineering: 2130 candles  ✅ (enough for 168 lookback)
   Predicting step 1/7
   Predicting step 2/7
   ...
   ✅ Completed predictions for BTC-USD
```

### Accuracy Note:

- **Step 1 prediction**: Most accurate (uses real data)
- **Step 2-3**: Good (1 simulated candle)
- **Step 4-7**: Less accurate (multiple simulated candles stacked)

This is why the UI says: *"Multi-step predictions become less accurate over time"*

## Summary:

✅ **Same predictor class**  
✅ **Same trained models**  
✅ **Same features & architecture**  
✅ **Different usage pattern** (historical vs future)  
✅ **Now fetches enough data** (365/730 days instead of 60)
