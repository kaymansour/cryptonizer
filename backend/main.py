"""
Cryptocurrency API Backend
FastAPI server that provides cryptocurrency data from CoinGecko API with caching and ML predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
from models.crypto_predictor import predict_crypto as predict_future_prices

# Initialize FastAPI application
app = FastAPI()

# Configure CORS (Cross-Origin Resource Sharing) to allow frontend requests
# This enables the React frontend running on localhost:3000 to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend development server URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================
# Cache configuration to reduce API calls to CoinGecko and improve performance
CACHE_TTL_COINS = 60           # Cache top 50 coins list for 1 minute
CACHE_TTL_COIN_DETAIL = 300    # Cache individual coin details for 5 minutes

# In-memory cache storage
coins_cache = {"data": [], "timestamp": 0}  # Stores the top coins list with timestamp
coin_detail_cache = {}          # Dictionary cache for individual coin details: key=coin_id, value={"data": ..., "timestamp": ...}


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================
@app.get("/api/status")
def read_root():
    """Health check endpoint to verify the API is running"""
    return {"message": "Hello from FastAPI"}


# =============================================================================
# TOP CRYPTOCURRENCIES ENDPOINT
# =============================================================================
@app.get("/coins")
def get_coins():
    """
    Fetches top 50 cryptocurrencies by market cap from CoinGecko API
    Returns: List of coin objects with basic information
    """
    current_time = time.time()
    
    # Check if cached data exists and is still valid (within TTL)
    if coins_cache["data"] and (current_time - coins_cache["timestamp"] < CACHE_TTL_COINS):
        return coins_cache["data"]  # Return cached data to avoid API call

    try:
        # CoinGecko API endpoint for cryptocurrency markets data
        url = "https://api.coingecko.com/api/v3/coins/markets"
        
        # Make request to CoinGecko API with specific parameters
        response = requests.get(url, params={
            "vs_currency": "usd",           # Base currency for prices
            "order": "market_cap_desc",     # Sort by market cap (highest first)
            "per_page": 50,                 # Limit to top 50 coins
            "page": 1,                      # First page of results
            "sparkline": False              # Exclude sparkline data for performance
        })

        # Check if CoinGecko API returned successful response
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"CoinGecko API error: {response.status_code}")

        # Parse JSON response from CoinGecko
        data = response.json()

        # Validate response format - should be a list of coins
        if not isinstance(data, list):
            raise HTTPException(status_code=500, detail="CoinGecko API did not return a list")

        # Transform CoinGecko data to our application's format
        coins = [
            {
                "id": coin.get("id", ""),                           # Unique coin identifier (e.g., "bitcoin")
                "symbol": coin.get("symbol", "").lower(),           # Coin symbol (e.g., "btc")
                "name": coin.get("name", ""),                       # Full coin name (e.g., "Bitcoin")
                "image": coin.get("image", ""),                     # URL to coin logo/image
                "current_price": coin.get("current_price", 0),      # Current price in USD
                "market_cap": coin.get("market_cap", 0),           # Total market capitalization
                "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),  # 24h price change percentage
                "market_cap_rank": coin.get("market_cap_rank", 0), # Global market cap ranking (1 = highest)
            }
            for coin in data  # Process each coin in the response
        ]
        
        # Update cache with new data and current timestamp
        coins_cache["data"] = coins
        coins_cache["timestamp"] = current_time
        
        return coins

    except Exception as e:
        # Handle any unexpected errors during the API call
        raise HTTPException(status_code=500, detail=f"Error fetching coins: {str(e)}")


# =============================================================================
# INDIVIDUAL COIN DETAILS ENDPOINT
# =============================================================================
@app.get("/crypto/{coin_id}")
def get_crypto_data(coin_id: str, currency: str = "usd", days: int = 7):
    """
    Fetches detailed information and price history for a specific cryptocurrency
    Args:
        coin_id: Unique identifier for the cryptocurrency (e.g., "bitcoin")
        currency: Currency to display prices in ("usd" or "bhd")
        days: Number of days of historical data to fetch (default: 7)
    
    Returns: Detailed coin information including price history and market data
    """
    coin_id = coin_id.lower()      # Normalize coin_id to lowercase
    currency = currency.lower()    # Normalize currency to lowercase
    current_time = time.time()

    # Check if this coin's data is already cached and still valid
    if coin_id in coin_detail_cache:
        cached = coin_detail_cache[coin_id]
        if current_time - cached["timestamp"] < CACHE_TTL_COIN_DETAIL:
            return cached["data"]  # Return cached data to avoid API call

    try:
        # CoinGecko API endpoint for specific coin details
        market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?tickers=false&market_data=true"
        market_response = requests.get(market_url)
        
        # Handle case where coin is not found
        if market_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Cryptocurrency not found")
            
        # Parse the coin details from CoinGecko
        market_data = market_response.json()

        # Extract market data in the requested currency
        market_data_currency = market_data.get("market_data", {})
        current_price = market_data_currency.get("current_price", {}).get(currency, 0)
        market_cap = market_data_currency.get("market_cap", {}).get(currency, 0)
        total_volume = market_data_currency.get("total_volume", {}).get(currency, 0)
        price_change_24h = market_data_currency.get("price_change_24h", 0)
        price_change_percentage_24h = market_data_currency.get("price_change_percentage_24h", 0)
        market_cap_rank = market_data.get("market_cap_rank", 0)  # Global ranking

        # Fetch historical price data for charting
        history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        history_response = requests.get(history_url, params={
            "vs_currency": currency,  # Historical prices in requested currency
            "days": days              # Number of days of historical data
        })
        history_data = history_response.json()

        # Structure the response data
        result = {
            "id": market_data.get("id"),                                  # Coin ID
            "name": market_data.get("name"),                              # Coin name
            "symbol": market_data.get("symbol", "").lower(),              # Coin symbol
            "current_price": current_price,                               # Current price
            "market_cap": market_cap,                                     # Market capitalization
            "total_volume": total_volume,                                 # 24h trading volume
            "price_change_24h": price_change_24h,                         # Absolute 24h price change
            "price_change_percentage_24h": price_change_percentage_24h,   # Percentage 24h price change
            "last_updated": market_data.get("last_updated"),              # Last data update timestamp
            "image": market_data.get("image", {}).get("large", ""),       # Large coin image URL
            "description": market_data.get("description", {}).get("en", "No description available."),  # English description
            "history": history_data.get("prices", []),                    # Price history data for charts
            "market_cap_rank": market_cap_rank,                           # Global market cap rank
        }

        # Update cache with this coin's data and current timestamp
        coin_detail_cache[coin_id] = {"data": result, "timestamp": current_time}

        return result

    except Exception as e:
        # Handle any unexpected errors during the API call
        raise HTTPException(status_code=500, detail=f"Error fetching coin: {str(e)}")


# =============================================================================
# MACHINE LEARNING PREDICTION ENDPOINT
# =============================================================================
@app.get("/predict/{symbol}")
def predict(symbol: str):
    """
    Uses machine learning model to predict future cryptocurrency prices
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC" for Bitcoin)
    
    Returns: Prediction results from the ML model
    """
    try:
        # Call the ML prediction function with uppercase symbol
        result = predict_future_prices(symbol.upper())
        return result
    except ValueError as ve:
        # Handle case where cryptocurrency is not supported by the model
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # Handle any unexpected errors in the prediction model
        raise HTTPException(status_code=500, detail=str(e))