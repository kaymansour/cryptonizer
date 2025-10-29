# type: ignore
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io, base64, datetime, time
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

# TensorFlow imports with comprehensive error handling
LSTM_AVAILABLE = False
Sequential = None
LSTM = None
Dense = None
TimeseriesGenerator = None

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
    LSTM_AVAILABLE = True
    print("✅ TensorFlow/Keras imports successful")
except ImportError as e:
    print(f"⚠️ TensorFlow not available: {e}")
    print("⚠️ LSTM model will be skipped. Using traditional ML models only.")

import yfinance as yf

# ------------------------------
# 🔹 In-memory cache (coin → result)
# ------------------------------
cache = {}
CACHE_DURATION = 60 * 60 * 24  # 24 hours

def fetch_data(symbol: str, period: str = "6mo"):
    """Fetch stock/crypto data from Yahoo Finance"""
    try:
        print(f"📊 Fetching data for {symbol} with period {period}")
        df = yf.download(symbol, period=period, progress=False)
        
        if df.empty:
            print(f"❌ No data found for {symbol}")
            return pd.DataFrame()
            
        print(f"✅ Data fetched: {len(df)} rows, columns: {list(df.columns)}")
        
        # Handle multi-index columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            print("🔧 Multi-index columns detected, flattening...")
            # Flatten the multi-index columns
            df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns]
            print(f"🔧 Flattened columns: {list(df.columns)}")
        
        # Extract Close price column (handle different column naming)
        close_col = None
        for col in df.columns:
            if 'Close' in str(col):
                close_col = col
                break
        
        if close_col is None:
            print(f"❌ No Close column found in: {list(df.columns)}")
            return pd.DataFrame()
            
        print(f"🔧 Using column for Close prices: {close_col}")
        df = df[[close_col]].copy()
        df.columns = ['Close']  # Rename to standard 'Close'
        
        df.dropna(inplace=True)
        
        if df.empty:
            print(f"❌ No data after processing for {symbol}")
            return pd.DataFrame()
            
        print(f"✅ Final data shape: {df.shape}, first few prices: {df['Close'].head(3).values.tolist()}")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return pd.DataFrame()

def evaluate_model(model_name, y_true, y_pred):
    """Evaluate model performance using RMSE"""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {"model": model_name, "rmse": rmse}

def train_models(symbol: str):
    """Train multiple models and select the best one"""
    print(f"🧠 Starting model training for {symbol}")
    
    df = fetch_data(symbol)
    if df.empty:
        raise ValueError(f"Could not fetch data for {symbol}. Symbol might be invalid.")
    
    if len(df) < 20:
        raise ValueError(f"Not enough data for {symbol}. Only {len(df)} data points available.")
    
    print(f"📈 Data prepared: {len(df)} rows, price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
    
    # Prepare data for traditional models
    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    X = df[['Close']].values
    y = df['Target'].values
    
    if len(X) < 10:
        raise ValueError(f"Not enough data after processing for {symbol}. Only {len(X)} samples.")
    
    # Use smaller test size for small datasets
    test_size = min(0.2, 0.1 if len(X) < 50 else 0.2)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)

    print(f"📊 Train/test split: {len(X_train)} train, {len(X_test)} test")
    
    results = []

    # --- Model 1: Linear Regression ---
    try:
        print("🔹 Training Linear Regression...")
        lr = LinearRegression().fit(X_train, y_train)
        pred_lr = lr.predict(X_test)
        lr_rmse = evaluate_model("Linear Regression", y_test, pred_lr)['rmse']
        print(f"✅ Linear Regression RMSE: {lr_rmse:.4f}")
        results.append((evaluate_model("Linear Regression", y_test, pred_lr), lr))
    except Exception as e:
        print(f"❌ Linear Regression failed: {e}")

    # --- Model 2: Random Forest ---
    try:
        print("🔹 Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
        rf.fit(X_train, y_train)
        pred_rf = rf.predict(X_test)
        rf_rmse = evaluate_model("Random Forest", y_test, pred_rf)['rmse']
        print(f"✅ Random Forest RMSE: {rf_rmse:.4f}")
        results.append((evaluate_model("Random Forest", y_test, pred_rf), rf))
    except Exception as e:
        print(f"❌ Random Forest failed: {e}")

    # --- Model 3: XGBoost ---
    try:
        print("🔹 Training XGBoost...")
        xgb = XGBRegressor(n_estimators=50, learning_rate=0.1, random_state=42, max_depth=6)
        xgb.fit(X_train, y_train)
        pred_xgb = xgb.predict(X_test)
        xgb_rmse = evaluate_model("XGBoost", y_test, pred_xgb)['rmse']
        print(f"✅ XGBoost RMSE: {xgb_rmse:.4f}")
        results.append((evaluate_model("XGBoost", y_test, pred_xgb), xgb))
    except Exception as e:
        print(f"❌ XGBoost failed: {e}")

    # Skip LSTM for now to simplify
    print("🔹 Skipping LSTM for faster predictions...")

    if not results:
        raise ValueError("No models were successfully trained")

    # Choose best model
    best_model, best_rmse, best_name = None, float('inf'), ''
    for result, model in results:
        if result['rmse'] < best_rmse:
            best_rmse = result['rmse']
            best_model = model
            best_name = result['model']

    print(f"✅ Best model selected: {best_name} (RMSE: {best_rmse:.4f})")
    return df, best_model, best_name, best_rmse

def predict_future(symbol: str, days_ahead: int = 7):
    """Generate predictions for future prices"""
    # Check cache first
    now = time.time()
    if symbol in cache and now - cache[symbol]['timestamp'] < CACHE_DURATION:
        print(f"✅ Cache hit for {symbol}")
        return cache[symbol]['data']

    print(f"🧠 Training new models for {symbol}...")
    
    try:
        df, best_model, best_name, best_rmse = train_models(symbol)
        last_price = df['Close'].values[-1]
        print(f"💰 Last price for {symbol}: ${last_price:.2f}")

        # Generate future predictions
        future_prices = []
        current_price = last_price
        
        print(f"🔮 Generating {days_ahead} day predictions...")
        for i in range(days_ahead):
            try:
                if hasattr(best_model, 'predict'):
                    # For scikit-learn models
                    next_price = best_model.predict([[current_price]])[0]
                    print(f"   Day {i+1}: ${current_price:.2f} → ${next_price:.2f}")
                else:
                    # Fallback
                    next_price = current_price * (1 + np.random.normal(0, 0.01))
            except Exception as e:
                print(f"   ⚠️ Prediction error for day {i+1}: {e}")
                next_price = current_price
                
            future_prices.append(float(next_price))
            current_price = next_price

        # Create future dates
        future_dates = [datetime.date.today() + datetime.timedelta(days=i+1) for i in range(days_ahead)]
        pred_df = pd.DataFrame({
            "Date": future_dates, 
            "Predicted_Price": [round(float(price), 2) for price in future_prices]
        })

        print(f"📅 Prediction dates: {[str(d) for d in future_dates]}")

        # Create plot
        plt.figure(figsize=(10, 6))
        
        # Historical data (last 30 days or all if less)
        historical_points = min(30, len(df))
        historical_dates = df.index[-historical_points:]
        historical_prices = df['Close'].tail(historical_points)
        
        plt.plot(historical_dates, historical_prices, label='Historical Prices', linewidth=2, color='#10b981')
        
        # Future predictions
        plt.plot(pred_df['Date'], pred_df['Predicted_Price'], 
                 label=f'Predicted ({best_name})', 
                 linestyle='--', marker='o', linewidth=2, color='#3b82f6')
        
        plt.title(f'{symbol} Price Prediction\nBest Model: {best_name} (RMSE: {best_rmse:.4f})', fontsize=14)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Price (USD)", fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Convert plot to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        plot_base64 = base64.b64encode(buf.read()).decode('utf-8')

        # Prepare response data
        data = {
            "symbol": symbol,
            "model": best_name,
            "rmse": round(float(best_rmse), 4),
            "last_price": round(float(last_price), 2),
            "plot_base64": plot_base64,
            "future_predictions": pred_df.to_dict(orient='records'),
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Store in cache
        cache[symbol] = {
            "timestamp": now,
            "data": data
        }

        print(f"✅ Prediction completed and cached for {symbol}")
        return data
        
    except Exception as e:
        print(f"❌ Prediction failed for {symbol}: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        # Return a fallback response instead of crashing
        fallback_data = {
            "symbol": symbol,
            "model": "Fallback",
            "rmse": 0.0,
            "last_price": 0.0,
            "plot_base64": "",
            "future_predictions": [],
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }
        return fallback_data

# Test function with better error handling
def test_prediction():
    """Test the prediction function with Bitcoin"""
    try:
        print("🚀 Testing prediction with BTC-USD...")
        result = predict_future("BTC-USD", days_ahead=7)
        
        if "error" in result:
            print(f"❌ Test failed with error: {result['error']}")
            return False
            
        print(f"✅ Test successful!")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Best Model: {result['model']}")
        print(f"   RMSE: {result['rmse']}")
        print(f"   Last Price: ${result['last_price']}")
        print(f"   Predictions: {len(result['future_predictions'])} days")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Starting model predictor test...")
    test_prediction()