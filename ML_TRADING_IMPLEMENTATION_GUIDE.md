# ML-Driven Trading Backtester - Implementation Guide

## 🎯 Your Request
Transform the backtester from simple monthly rebalancing to **ML-driven trading** that:
- Uses LSTM predictions to make buy/sell decisions
- Trades on **1h or 4h candles** (not daily)
- Makes active trading decisions (not just rebalancing)

## ✅ Is This Possible?
**YES**, but requires significant work. I've created the foundation, but here's what you need to understand:

---

## GPU Setup (Ubuntu 24.04)

Install CUDA Toolkit 12.3:
   ```bash
   wget https://developer.download.nvidia.com/compute/cuda/12.3.2/local_installers/cuda-repo-wsl-ubuntu-12-3-local_12.3.2-1_amd64.deb
   sudo dpkg -i cuda-repo-wsl-ubuntu-12-3-local_12.3.2-1_amd64.deb
   sudo cp /var/cuda-repo-wsl-ubuntu-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
   sudo apt-get update
   sudo apt-get -y install cuda-toolkit-12-3

## install libtinfo5 
wget http://ftp.debian.org/debian/pool/main/n/ncurses/libtinfo5_6.4-4_amd64.deb
sudo dpkg -i libtinfo5_6.4-4_amd64.deb

## verify
nvcc --version
nvidia-smi
```
## 🚨 Critical Limitations & Requirements

### 1. **Data Availability (MAJOR CONSTRAINT)**

#### Current Problem:
- Your existing models are trained on **DAILY** data (5 years)
- They predict next-day prices
- **Cannot** be used for hourly trading

#### What You Need:
```python
# For 1h candles:
yf.download("BTC-USD", interval="1h", period="730d")  # MAX 730 DAYS
                                                        # = 2 years only!

# For 4h candles:  
yf.download("BTC-USD", interval="4h", period="730d")  # MAX 730 DAYS
                                                        # = 2 years only!
```

**⚠️ YOU CAN ONLY BACKTEST 2 YEARS MAX with yfinance for hourly data**

#### Solutions:
1. **Use 4h candles** (recommended) - still 2 year limit but more data points
2. **Alternative data sources**:
   - Binance API (free, historical data available)
   - CoinGecko Pro API (paid)
   - Cryptocompare API (paid)
   - Download CSV files from exchanges manually

### 2. **Model Retraining (CRITICAL)**

Your current 20 `.h5` models are **USELESS** for hourly trading because:
- Trained on daily close prices
- 100-day lookback window (daily)
- Predict next day, not next hour

#### What You Must Do:
```bash
# Step 1: Train new models on intraday data
cd /home/weed/senior/backend
python models/intraday_predictor.py
```

This will create:
- `BTC-USD_4h_predictor.h5`
- `BTC-USD_4h_scaler.pkl`
- (Same for each crypto)

**Training time**: ~5-10 minutes per crypto for 2 years of 4h data

### 3. **Computational Requirements**

**Training Phase:**
- GPU recommended but not required
- CPU training: ~10 min per crypto
- GPU training: ~2 min per crypto
- Total for 20 cryptos: 3-4 hours (CPU) or 40 min (GPU)

**Backtesting Phase:**
- Predictions needed for every candle
- 4h candles over 2 years = ~4,380 predictions per crypto
- Runtime: 10-30 minutes depending on number of assets

### 4. **Realistic Trading Constraints**

The new `ml_backtester.py` includes:
- ✅ Transaction costs (0.1% default)
- ✅ Position size limits (max 30% per asset)
- ✅ Minimum trade size ($10)
- ✅ Signal confidence thresholds
- ❌ Slippage (you may want to add this)
- ❌ Market impact (for large orders)
- ❌ Bid-ask spread

---

## 📋 Implementation Roadmap

### Phase 1: Setup & Training (NEW MODELS REQUIRED)

#### Step 1: Install Additional Dependencies
```bash
cd /home/weed/senior/backend
source venv/bin/activate
pip install keras tensorflow scikit-learn
```

#### Step 2: Train Intraday Models
```bash
# Train models for specific cryptos (recommended start small)
python models/intraday_predictor.py
```

**Edit `intraday_predictor.py` line 302** to train your cryptos:
```python
symbols = ["BTC-USD", "ETH-USD", "ADA-USD", "SOL-USD"]  # Start with 4
```

#### Step 3: Verify Models Created
```bash
ls -lh models/*_4h_predictor.h5
ls -lh models/*_4h_scaler.pkl
```

### Phase 2: Test ML Backtester

#### Step 1: Run Simple Test
```bash
python ml_backtester.py
```

This tests BTC-USD and ETH-USD over last 1 month with 4h candles.

#### Step 2: Test API Integration
Create `test_ml_backtesting.py`:

```python
import requests
import json

# Test ML backtesting endpoint
response = requests.post('http://localhost:8000/api/ml-backtest', json={
    "symbols": ["BTC-USD", "ETH-USD"],
    "initial_capital": 100000,
    "start_date": "2024-08-01",
    "end_date": "2024-10-29",
    "interval": "4h",
    "signal_threshold": 0.5
})

result = response.json()
print(json.dumps(result, indent=2))
```

### Phase 3: Add API Endpoints

Add to `main.py`:

```python
from ml_backtester import MLTradingBacktester, ml_backtest_portfolio

@app.post("/api/ml-backtest")
async def ml_backtest(request: dict):
    """
    ML-driven trading backtest
    """
    try:
        result = ml_backtest_portfolio(
            symbols=request.get("symbols"),
            initial_capital=request.get("initial_capital", 100000),
            start_date=request.get("start_date"),
            end_date=request.get("end_date"),
            interval=request.get("interval", "4h"),
            signal_threshold=request.get("signal_threshold", 0.5)
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Phase 4: Frontend Integration

Update `BacktestDashboard.tsx` to add ML trading option:

```typescript
const [backtestMode, setBacktestMode] = useState<"rebalance" | "ml-trading">("rebalance");

// When ML trading selected:
if (backtestMode === "ml-trading") {
  const response = await fetch("http://localhost:8000/api/ml-backtest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbols: portfolioData.symbols,
      initial_capital: portfolioData.initial_investment,
      start_date: startDate,
      end_date: endDate,
      interval: "4h",
      signal_threshold: 0.5
    })
  });
}
```

---

## 🎮 How It Works

### Trading Logic Flow:

```
For each 4h candle:
  1. Get last 168 periods (1 week) of data
  2. Feed to LSTM model
  3. Get predicted next price
  4. Calculate predicted % change
  
  If predicted_change > +0.5%:
    → BUY signal
    → Calculate position size (max 30% of portfolio)
    → Execute buy (with 0.1% fee)
  
  Else if predicted_change < -0.5%:
    → SELL signal
    → Sell portion of holdings (based on confidence)
    → Execute sell (with 0.1% fee)
  
  Else:
    → HOLD (do nothing)
  
  4. Track portfolio value
  5. Log trade for analysis
```

### Signal Confidence:
- Confidence = |predicted_change| / 10
- Example: 3% predicted rise = 0.3 confidence → buy 30% of max position
- Prevents over-trading on weak signals

---

## 📊 Expected Performance Characteristics

### Compared to Rebalancing Strategy:

**ML Trading Advantages:**
- ✅ Can profit from short-term price movements
- ✅ Actively avoids predicted downturns
- ✅ More trades = more opportunities
- ✅ Can hold cash during bear markets

**ML Trading Disadvantages:**
- ❌ More transaction costs (100+ trades vs 12 rebalances)
- ❌ Model prediction errors compound
- ❌ Overfitting risk (great in backtest, poor in real trading)
- ❌ Requires constant model updates
- ❌ More complex to explain/justify

### Realistic Expectations:
- **Good scenario**: 5-10% outperformance vs rebalancing
- **Typical scenario**: Similar performance, higher volatility
- **Bad scenario**: Underperformance due to transaction costs

**Key insight**: More trades ≠ more profit in crypto

---

## ⚠️ Major Challenges & Solutions

### Challenge 1: Lookahead Bias
**Problem**: Using future data to make past predictions

**Solution**: 
- ✅ Implemented in `ml_backtester.py`
- Only use data `<= current_timestamp`
- Models trained on data before backtest period

### Challenge 2: Model Staleness
**Problem**: Models trained on 2023-2024 data might not work in 2025

**Solution**: 
- Retrain models monthly
- Use rolling window training
- Add walk-forward optimization

### Challenge 3: Overfitting
**Problem**: Model performs great in backtest, terrible in real trading

**Solution**:
- Use train/validation/test split
- Add dropout layers (✅ included)
- Test on out-of-sample data
- Compare against simple benchmarks

### Challenge 4: Execution Slippage
**Problem**: Real trades execute at worse prices than backtest

**Solution**:
- Add slippage parameter (1-2% of trade)
- Use limit orders instead of market orders
- Model market depth

---

## 🚀 Quick Start Commands

### 1. Train Models (REQUIRED FIRST)
```bash
cd /home/weed/senior/backend
source venv/bin/activate

# Install if needed
pip install keras tensorflow

# Train 4h models for your cryptos
python models/intraday_predictor.py
```

### 2. Test ML Backtester
```bash
# Simple test
python ml_backtester.py

# Should output:
# - Training/loading models
# - Fetching 4h data
# - Running predictions
# - Final performance metrics
```

### 3. Compare Strategies
```bash
# Test both approaches
python compare_rebalance_vs_ml.py
```

---

## 📈 Performance Metrics

### Both strategies track:
- Total return
- Annualized return  
- Sharpe ratio
- Max drawdown
- Volatility

### ML-specific metrics:
- **Number of trades** (should be 50-200 for 3 months)
- **Win rate** (% of profitable trades)
- **Average trade size**
- **Prediction accuracy** (% correct direction)

---

## 🎯 Recommendations

### For Best Results:

1. **Start with 4h candles** (not 1h)
   - Less noise than 1h
   - More data points than daily
   - Better balance

2. **Use 3-4 cryptos initially**
   - BTC, ETH, SOL, ADA
   - Easier to monitor
   - Faster training

3. **Conservative signal threshold**
   - Start with 1.0% (not 0.5%)
   - Reduces overtrading
   - Higher quality signals

4. **Compare against benchmarks**
   - Always compare to buy-and-hold
   - Compare to simple rebalancing
   - If ML doesn't beat these, don't use it

5. **Walk-forward testing**
   - Train on 2023, test on 2024 Q1
   - Retrain, test on 2024 Q2
   - Prevents overfitting

---

## 🔧 Next Steps (Priority Order)

### Immediate (Required):
1. ✅ Review generated files (`intraday_predictor.py`, `ml_backtester.py`)
2. 🔲 Train intraday models for your cryptos
3. 🔲 Test ML backtester standalone
4. 🔲 Compare ML vs rebalancing strategy

### Short-term (1-2 weeks):
1. 🔲 Add API endpoints to `main.py`
2. 🔲 Create frontend toggle for ML vs rebalancing
3. 🔲 Add trade history visualization
4. 🔲 Implement walk-forward testing

### Medium-term (1 month):
1. 🔲 Add slippage and market impact models
2. 🔲 Implement model auto-retraining
3. 🔲 Add alternative data sources (Binance API)
4. 🔲 Create model performance dashboard

### Long-term (2-3 months):
1. 🔲 Ensemble models (combine multiple predictions)
2. 🔲 Sentiment analysis integration
3. 🔲 Real-time trading execution
4. 🔲 Risk management alerts

---

## ❓ FAQ

**Q: Can I use my existing .h5 models?**
A: No, they're trained on daily data. You need new models for hourly trading.

**Q: How long does training take?**
A: 5-10 min per crypto (CPU), 1-2 min (GPU). Total: 2-3 hours for 20 cryptos.

**Q: Can I backtest more than 2 years?**
A: Not with yfinance hourly data. Use Binance API or other sources.

**Q: Will ML trading beat buy-and-hold?**
A: Maybe. Backtesting will tell you. Often it doesn't due to transaction costs.

**Q: Can I trade on 1-minute candles?**
A: Technically yes, but only 60 days of data available. Not recommended.

**Q: Do I need a GPU?**
A: No, but it's 5x faster. Google Colab offers free GPU if needed.

---

## 📞 Support

If you encounter issues:

1. **Model training fails**: Check TensorFlow installation
2. **Data fetching errors**: yfinance rate limiting, try different dates
3. **Prediction errors**: Model not found, retrain models
4. **Performance issues**: Reduce number of symbols or use longer intervals

---

## ✅ Summary

**What I've Created:**
1. ✅ `intraday_predictor.py` - Train LSTM models on 1h/4h data
2. ✅ `ml_backtester.py` - ML-driven trading backtester
3. ✅ This implementation guide

**What You Need to Do:**
1. 🔲 Train intraday models (2-3 hours)
2. 🔲 Test the ML backtester
3. 🔲 Compare against simple rebalancing
4. 🔲 Integrate into your frontend

**Bottom Line:**
This is possible and I've built the framework, but expect 1-2 weeks of work to fully implement and test. The ML approach is more sophisticated but not guaranteed to outperform simpler strategies.

**Key Decision**: Do you want to invest the time in ML trading, or would a simpler momentum/technical indicator strategy be sufficient? The rebalancing approach you have now is actually quite solid for long-term investing.
