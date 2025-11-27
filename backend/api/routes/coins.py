"""
Core cryptocurrency data routes (coins list and details)
"""
from fastapi import APIRouter, HTTPException
from services.coingecko import CoinGeckoService
import sys
import os
import yfinance as yf

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
from hybrid_predictor import HybridPredictor

router = APIRouter()


@router.get("/coins")
def get_coins():
    """
    Fetches top 50 cryptocurrencies by market cap from CoinGecko API
    Returns: List of coin objects with basic information
    """
    return CoinGeckoService.get_top_coins()


@router.get("/crypto/{coin_id}")
def get_crypto_data(coin_id: str, currency: str = "usd", days: int = 7):
    """
    Fetches detailed information and price history for a specific cryptocurrency
    
    Args:
        coin_id: Unique identifier for the cryptocurrency (e.g., "bitcoin")
        currency: Currency to display prices in ("usd" or "bhd")
        days: Number of days of historical data to fetch (default: 7)
        
    Returns:
        Detailed coin information including price history and market data
    """
    return CoinGeckoService.get_coin_details(coin_id, currency, days)


@router.get("/predict/{symbol}")
async def predict_price(symbol: str, interval: str = "4h"):
    """
    Predict next candle price using optimal model for this cryptocurrency
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC' or 'BTC-USD')
        interval: Candle interval (default: '4h')
        
    Returns:
        Prediction with model information and signal
    """
    try:
        # Convert to Yahoo Finance format if needed
        if not symbol.endswith("-USD"):
            symbol = f"{symbol.upper()}-USD"
        else:
            symbol = symbol.upper()
        
        # Use hybrid predictor (automatically selects best model)
        predictor = HybridPredictor(
            symbol=symbol,
            interval=interval,
            auto_select=False,  # Use pre-configured optimal models
        )
        
        print(f"🔮 Predicting for {symbol}")
        print(f"   Selected model: {predictor.selected_model}")
        
        # Load pre-trained model
        predictor.load_model()
        
        # Fetch recent data for prediction
        recent_data = yf.download(
            predictor.symbol,
            period="7d",
            interval=interval,
            progress=False
        )
        
        if recent_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {symbol}"
            )
        
        # Make prediction
        prediction = predictor.predict_next(recent_data)
        
        return {
            "success": True,
            "symbol": predictor.symbol,
            "model_used": prediction['model_used'],
            "current_price": prediction['current_price'],
            "predicted_price": prediction['predicted_price'],
            "predicted_change_percent": prediction['predicted_change_percent'],
            "signal": prediction['signal'],
            "interval": interval,
        }
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found for {symbol}. Please train the model first."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
