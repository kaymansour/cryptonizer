# Critical Fixes for 99% Accuracy Bug

## Three Critical Issues Found and Fixed

### Issue #1: Using `<=` Instead of `==` for Next Candle (DATA LEAKAGE!)
**File**: `backend/ml_backtester.py` line 993

**What was wrong**:
```python
# WRONG - Gets all data up to and including next_timestamp
next_data = historical_data[symbol][
    historical_data[symbol].index <= next_timestamp  # ← BUG HERE
]
actual_next_price = float(next_data["Close"].iloc[-1])
```

**Why this causes 99% accuracy**:
- `<=` gets ALL candles from start to next_timestamp
- `iloc[-1]` gets the LAST candle in that range
- If there are multiple candles at next_timestamp or after, we're looking ahead!
- We're essentially comparing prediction to data the model shouldn't see

**Fixed to**:
```python
# CORRECT - Gets only the exact next candle
next_data = historical_data[symbol][
    historical_data[symbol].index == next_timestamp  # ✓ FIXED
]
actual_next_price = float(next_data["Close"].iloc[0])
```

---

### Issue #2: Mismatched Scaler File (CRITICAL!)
**File**: `backend/models/intraday_predictor.py`

**What was wrong**:
When you retrained the model:
- ✅ You replaced `BTC-USD_4h_optimized_attention.keras` (new model)
- ❌ You DIDN'T replace `BTC-USD_4h_optimized_attention_scaler.pkl` (old scaler)

**Why this causes wrong predictions**:

OLD SCALER (trained on absolute prices):
- Input range: $30,000 - $70,000
- Normalizes to: 0.0 - 1.0

NEW MODEL (trained on returns):
- Expects input range: -0.1 to +0.1 (percentage changes)
- Outputs: -0.05 to +0.05 (predicted return)

When you use OLD scaler with NEW model:
```python
# Model outputs: 0.02 (meaning +2% return)
# Old scaler tries to inverse transform as if it's a scaled price
# Result: Nonsense prediction!
```

**Fixed**:
```python
def save_model(self):
    # DELETE old scaler before saving new one
    if os.path.exists(self.scaler_path):
        os.remove(self.scaler_path)
        print(f"🗑️  Deleted old scaler")
    
    # Save new model and scaler together
    self.model.save(self.model_path)
    with open(self.scaler_path, "wb") as f:
        pickle.dump(self.scaler, f)
```

---

### Issue #3: Frontend Accuracy Calculation
**File**: `frontend/src/components/MLPredictionChart.tsx`

**What was wrong**:
```tsx
// WRONG - "Inverse error" always gives ~99%
const error = Math.abs(pred.actual_price - pred.predicted_price);
const percentError = (error / pred.actual_price) * 100;
return acc + (100 - percentError);
```

**Example showing why this is wrong**:
```
BTC actual: $50,000
BTC predicted: $50,100
Error: $100
Percent error: 100/50000 = 0.2%
Accuracy: 100 - 0.2 = 99.8% ← Looks great but meaningless!
```

The model could predict $50,050 when actual is $49,950 (wrong direction by $100) and still show 99.8% accuracy.

**Fixed to directional accuracy**:
```tsx
// CORRECT - Did we predict the right direction?
const prevActual = predictions[idx].actual_price;
const actualChange = pred.actual_price - prevActual;      // Actual: +$100
const predictedChange = pred.predicted_price - prevActual; // Predicted: -$50
const correctDirection = (actualChange * predictedChange) > 0; // false!
```

Now accuracy = % of times we predicted the correct direction (up vs down).

---

## How to Fix Your Current Situation

### Step 1: Delete ALL Old Scaler Files
```bash
cd backend
python3 cleanup_old_scalers.py
```

This will delete all `.pkl` files in the models directory.

### Step 2: Retrain All Models
```bash
cd backend
python3 models/hybrid_predictor.py
```

This will:
1. Train with returns (not absolute prices)
2. Create NEW scalers that match the new models
3. Save both together

### Step 3: Test One Symbol
```bash
cd backend
python3 -c "
from models.hybrid_predictor import HybridPredictor
import yfinance as yf

predictor = HybridPredictor('BTC-USD', interval='4h', auto_select=False)
data = yf.download('BTC-USD', period='2mo', interval='4h')
pred = predictor.predict_next(data)
print(f'Predicted change: {pred[\"predicted_change_percent\"]:.2f}%')
"
```

You should see small predictions like:
- `Predicted change: +1.2%` ✓
- `Predicted change: -0.8%` ✓

NOT:
- `Predicted change: +342.7%` ✗ (means old scaler still loaded)

### Step 4: Verify Backtesting
Run a backtest and check the accuracy:
- **Good**: 45-65% directional accuracy
- **Excellent**: 55-70% directional accuracy
- **Suspicious**: 90%+ accuracy (still a bug somewhere)

---

## Summary

| Issue | Impact | Status |
|-------|--------|--------|
| `<=` instead of `==` | Data leakage in backtest | ✅ FIXED |
| Mismatched scaler | Wrong predictions | ✅ FIXED |
| Frontend calculation | Misleading accuracy | ✅ FIXED |

All three issues worked together to create a perfect storm of 99% accuracy.

**The real accuracy should be 50-65%** for directional prediction, which is actually GOOD for crypto trading!
