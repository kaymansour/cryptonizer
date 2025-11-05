from models.intraday_predictor import IntradayPredictor
from models.intraday_predictor_blstm import IntradayPredictor as BLSTMPredictor
import yfinance as yf

symbol = "BTC-USD"
interval = "4h"

print(f"🔍 Comparing LSTM vs BLSTM for {symbol} ({interval})")

# Download recent data
data = yf.download(symbol, period="30d", interval=interval, progress=False)

# Load models
lstm = IntradayPredictor(symbol, interval=interval)
lstm.load_model()
blstm = BLSTMPredictor(symbol, interval=interval)
blstm.load_model()

# Predict
lstm_pred = lstm.predict_next(data)
blstm_pred = blstm.predict_next(data)

print("\n📊 LSTM Prediction:", lstm_pred)
print("📊 BLSTM Prediction:", blstm_pred)

# Compare
lstm_change = lstm_pred["predicted_change_percent"]
blstm_change = blstm_pred["predicted_change_percent"]
print(f"\n📈 Difference in confidence: {round(blstm_change - lstm_change, 3)}%")
