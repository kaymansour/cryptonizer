"""
Cryptocurrency API Backend
FastAPI server that provides cryptocurrency data from CoinGecko API with caching and ML predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import traceback
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


print("🚀 Starting Cryptocurrency API Backend...")
print("📊 Cache configuration:")
print(f"   - Coins cache TTL: {CACHE_TTL_COINS}s")
print(f"   - Coin detail cache TTL: {CACHE_TTL_COIN_DETAIL}s")
print("🔧 Backend initialized and ready!")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================
@app.get("/api/status")
def read_root():
    """Health check endpoint to verify the API is running"""
    print("🏥 Health check endpoint called")
    return {"message": "Hello from FastAPI", "status": "healthy", "timestamp": time.time()}


# =============================================================================
# TOP CRYPTOCURRENCIES ENDPOINT
# =============================================================================
@app.get("/coins")
def get_coins():
    """
    Fetches top 50 cryptocurrencies by market cap from CoinGecko API
    Returns: List of coin objects with basic information
    """
    print(f"\n🎯 /coins endpoint called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    current_time = time.time()
    
    # Check if cached data exists and is still valid (within TTL)
    cache_age = current_time - coins_cache.get("timestamp", 0)
    is_cache_valid = coins_cache["data"] and (cache_age < CACHE_TTL_COINS)
    
    print(f"📦 Cache check - Has data: {bool(coins_cache['data'])}, Age: {cache_age:.1f}s, Valid: {is_cache_valid}")
    
    if is_cache_valid:
        print(f"✅ Returning cached coins data ({len(coins_cache['data'])} coins, {cache_age:.1f}s old)")
        return coins_cache["data"]

    try:
        print("🔄 Fetching fresh data from CoinGecko API...")
        
        # CoinGecko API endpoint for cryptocurrency markets data
        url = "https://api.coingecko.com/api/v3/coins/markets"
        
        # Make request to CoinGecko API with specific parameters
        params = {
            "vs_currency": "usd",           # Base currency for prices
            "order": "market_cap_desc",     # Sort by market cap (highest first)
            "per_page": 50,                 # Limit to top 50 coins
            "page": 1,                      # First page of results
            "sparkline": False              # Exclude sparkline data for performance
        }
        
        print(f"📡 Making request to CoinGecko API...")
        print(f"   URL: {url}")
        print(f"   Params: {params}")
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=10)
        request_time = time.time() - start_time
        
        print(f"📊 CoinGecko API Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {request_time:.2f}s")
        print(f"   Headers: {dict(response.headers)}")

        # Check if CoinGecko API returned successful response
        if response.status_code != 200:
            error_detail = f"CoinGecko API error: {response.status_code} - {response.text}"
            print(f"❌ {error_detail}")
            
            # Try to return cached data even if expired
            if coins_cache["data"]:
                print("🔄 Falling back to expired cache due to API error")
                return coins_cache["data"]
            else:
                print("🔄 Falling back to static fallback data")
                return FALLBACK_COINS

        # Parse JSON response from CoinGecko
        data = response.json()
        print(f"📦 Received data from CoinGecko:")
        print(f"   Type: {type(data)}")
        print(f"   Length: {len(data) if isinstance(data, list) else 'N/A'}")
        if isinstance(data, list) and len(data) > 0:
            print(f"   First item keys: {list(data[0].keys())}")

        # Validate response format - should be a list of coins
        if not isinstance(data, list):
            error_detail = f"CoinGecko API did not return a list. Got: {type(data)} - {data}"
            print(f"❌ {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)

        # Check if we got any data
        if not data:
            error_detail = "CoinGecko API returned empty list"
            print(f"❌ {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)

        # Transform CoinGecko data to our application's format
        coins = []
        successful_coins = 0
        failed_coins = 0
        
        print("🛠️ Processing coin data...")
        for i, coin in enumerate(data):
            try:
                coin_data = {
                    "id": coin.get("id", ""),
                    "symbol": coin.get("symbol", "").lower(),
                    "name": coin.get("name", ""),
                    "image": coin.get("image", ""),
                    "current_price": coin.get("current_price", 0),
                    "market_cap": coin.get("market_cap", 0),
                    "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),
                    "market_cap_rank": coin.get("market_cap_rank", 0),
                }
                
                # Validate required fields
                if not coin_data["id"] or not coin_data["symbol"]:
                    print(f"   ⚠️ Coin {i} missing required fields: {coin_data}")
                    failed_coins += 1
                    continue
                    
                coins.append(coin_data)
                successful_coins += 1
                
                # Log first few coins for verification
                if i < 3:
                    print(f"   ✅ Sample coin {i}: {coin_data['symbol']} - ${coin_data['current_price']}")
                    
            except Exception as coin_error:
                print(f"   ❌ Error processing coin {i} ({coin.get('id', 'unknown')}): {coin_error}")
                failed_coins += 1
                continue

        print(f"📊 Coin processing results:")
        print(f"   ✅ Successful: {successful_coins}")
        print(f"   ❌ Failed: {failed_coins}")
        print(f"   📝 Total: {len(coins)}")

        if not coins:
            print("❌ No coins were successfully processed")
            if coins_cache["data"]:
                print("🔄 Returning cached data as fallback")
                return coins_cache["data"]
            else:
                print("🔄 Returning static fallback data")
                return FALLBACK_COINS

        # Update cache with new data and current timestamp
        coins_cache["data"] = coins
        coins_cache["timestamp"] = current_time
        
        print(f"💾 Cache updated with {len(coins)} coins")
        print(f"✅ Successfully returning {len(coins)} coins")
        
        return coins

    except requests.exceptions.Timeout:
        error_detail = "CoinGecko API request timed out (10s)"
        print(f"❌ {error_detail}")
        if coins_cache["data"]:
            print("🔄 Returning cached data due to timeout")
            return coins_cache["data"]
        else:
            print("🔄 Returning static fallback data due to timeout")
            return FALLBACK_COINS
            
    except requests.exceptions.ConnectionError:
        error_detail = "Failed to connect to CoinGecko API - network issue"
        print(f"❌ {error_detail}")
        if coins_cache["data"]:
            print("🔄 Returning cached data due to connection error")
            return coins_cache["data"]
        else:
            print("🔄 Returning static fallback data due to connection error")
            return FALLBACK_COINS
            
    except Exception as e:
        error_detail = f"Unexpected error in /coins endpoint: {str(e)}"
        print(f"❌ {error_detail}")
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        
        if coins_cache["data"]:
            print("🔄 Returning cached data due to unexpected error")
            return coins_cache["data"]
        else:
            print("🔄 Returning static fallback data due to unexpected error")
            return FALLBACK_COINS


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
    print(f"\n🎯 /crypto/{coin_id} endpoint called")
    print(f"   Parameters: currency={currency}, days={days}")
    
    coin_id = coin_id.lower()      # Normalize coin_id to lowercase
    currency = currency.lower()    # Normalize currency to lowercase
    current_time = time.time()

    # Check if this coin's data is already cached and still valid
    cache_age = 0
    if coin_id in coin_detail_cache:
        cached = coin_detail_cache[coin_id]
        cache_age = current_time - cached["timestamp"]
        is_cache_valid = cache_age < CACHE_TTL_COIN_DETAIL
        
        print(f"📦 Cache check for {coin_id}:")
        print(f"   Found in cache: Yes")
        print(f"   Cache age: {cache_age:.1f}s")
        print(f"   Valid: {is_cache_valid}")
        
        if is_cache_valid:
            print(f"✅ Returning cached data for {coin_id}")
            return cached["data"]
        else:
            print(f"🔄 Cache expired for {coin_id}, fetching fresh data")
    else:
        print(f"📦 Cache check for {coin_id}: Not found in cache")

    try:
        print(f"🔄 Fetching data for {coin_id} from CoinGecko...")
        
        # CoinGecko API endpoint for specific coin details
        market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?tickers=false&market_data=true"
        print(f"📡 Market data URL: {market_url}")
        
        start_time = time.time()
        market_response = requests.get(market_url, timeout=10)
        market_time = time.time() - start_time
        
        print(f"📊 Market data response:")
        print(f"   Status: {market_response.status_code}")
        print(f"   Time: {market_time:.2f}s")
        
        # Handle case where coin is not found
        if market_response.status_code == 404:
            error_msg = f"Cryptocurrency '{coin_id}' not found"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)
        elif market_response.status_code != 200:
            error_msg = f"CoinGecko API error for {coin_id}: {market_response.status_code}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
        # Parse the coin details from CoinGecko
        market_data = market_response.json()
        print(f"✅ Successfully fetched market data for {coin_id}")
        print(f"   Coin name: {market_data.get('name', 'Unknown')}")
        print(f"   Symbol: {market_data.get('symbol', 'Unknown')}")

        # Extract market data in the requested currency
        market_data_currency = market_data.get("market_data", {})
        print(f"💰 Extracting prices for currency: {currency}")
        
        current_price = market_data_currency.get("current_price", {}).get(currency, 0)
        market_cap = market_data_currency.get("market_cap", {}).get(currency, 0)
        total_volume = market_data_currency.get("total_volume", {}).get(currency, 0)
        price_change_24h = market_data_currency.get("price_change_24h", 0)
        price_change_percentage_24h = market_data_currency.get("price_change_percentage_24h", 0)
        market_cap_rank = market_data.get("market_cap_rank", 0)

        print(f"📈 Market data extracted:")
        print(f"   Current price: ${current_price}")
        print(f"   Market cap: ${market_cap}")
        print(f"   24h change: {price_change_percentage_24h}%")
        print(f"   Rank: #{market_cap_rank}")

        # Fetch historical price data for charting
        history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        history_params = {
            "vs_currency": currency,
            "days": days
        }
        
        print(f"📊 Fetching historical data...")
        print(f"   URL: {history_url}")
        print(f"   Params: {history_params}")
        
        start_time = time.time()
        history_response = requests.get(history_url, params=history_params, timeout=10)
        history_time = time.time() - start_time
        
        print(f"   History response: {history_response.status_code}, Time: {history_time:.2f}s")
        
        if history_response.status_code != 200:
            print(f"⚠️ Historical data fetch failed: {history_response.status_code}")
            history_data = {"prices": []}
        else:
            history_data = history_response.json()
            print(f"   History data points: {len(history_data.get('prices', []))}")

        # Structure the response data
        result = {
            "id": market_data.get("id"),
            "name": market_data.get("name"),
            "symbol": market_data.get("symbol", "").lower(),
            "current_price": current_price,
            "market_cap": market_cap,
            "total_volume": total_volume,
            "price_change_24h": price_change_24h,
            "price_change_percentage_24h": price_change_percentage_24h,
            "last_updated": market_data.get("last_updated"),
            "image": market_data.get("image", {}).get("large", ""),
            "description": market_data.get("description", {}).get("en", "No description available."),
            "history": history_data.get("prices", []),
            "market_cap_rank": market_cap_rank,
        }

        # Update cache with this coin's data and current timestamp
        coin_detail_cache[coin_id] = {"data": result, "timestamp": current_time}
        
        print(f"💾 Cached data for {coin_id}")
        print(f"✅ Successfully returning data for {coin_id}")
        
        return result

    except requests.exceptions.Timeout:
        error_detail = f"CoinGecko API timeout for {coin_id}"
        print(f"❌ {error_detail}")
        
        # Return cached data even if expired
        if coin_id in coin_detail_cache:
            print(f"🔄 Returning expired cached data for {coin_id} due to timeout")
            return coin_detail_cache[coin_id]["data"]
        else:
            raise HTTPException(status_code=500, detail=error_detail)
            
    except requests.exceptions.ConnectionError:
        error_detail = f"Network connection error for {coin_id}"
        print(f"❌ {error_detail}")
        
        # Return cached data even if expired
        if coin_id in coin_detail_cache:
            print(f"🔄 Returning expired cached data for {coin_id} due to connection error")
            return coin_detail_cache[coin_id]["data"]
        else:
            raise HTTPException(status_code=500, detail=error_detail)
            
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
        
    except Exception as e:
        error_detail = f"Unexpected error fetching {coin_id}: {str(e)}"
        print(f"❌ {error_detail}")
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        
        # Return cached data even if expired
        if coin_id in coin_detail_cache:
            print(f"🔄 Returning expired cached data for {coin_id} due to unexpected error")
            return coin_detail_cache[coin_id]["data"]
        else:
            raise HTTPException(status_code=500, detail=error_detail)


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
    print(f"\n🎯 /predict/{symbol} endpoint called")
    print(f"   Symbol: {symbol}")
    
    try:
        print(f"🤖 Calling ML prediction model for {symbol.upper()}...")
        
        # Call the ML prediction function with uppercase symbol
        start_time = time.time()
        result = predict_future_prices(symbol.upper())
        prediction_time = time.time() - start_time
        
        print(f"✅ ML prediction completed:")
        print(f"   Time: {prediction_time:.2f}s")
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        return result
        
    except ValueError as ve:
        error_msg = f"Prediction error for {symbol}: {str(ve)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=404, detail=str(ve))
        
    except Exception as e:
        error_msg = f"ML model error for {symbol}: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ADDITIONAL DEBUGGING ENDPOINTS
# =============================================================================
@app.get("/debug/cache")
def debug_cache():
    """Debug endpoint to check cache status"""
    print("\n🔍 /debug/cache endpoint called")
    
    coins_cache_age = time.time() - coins_cache.get("timestamp", 0)
    coin_detail_cache_size = len(coin_detail_cache)
    
    cache_info = {
        "coins_cache": {
            "has_data": bool(coins_cache["data"]),
            "data_count": len(coins_cache["data"]) if coins_cache["data"] else 0,
            "age_seconds": coins_cache_age,
            "is_valid": coins_cache_age < CACHE_TTL_COINS
        },
        "coin_detail_cache": {
            "size": coin_detail_cache_size,
            "keys": list(coin_detail_cache.keys())[:10]  # First 10 keys
        },
        "current_time": time.time()
    }
    
    print(f"📊 Cache debug info:")
    print(f"   Coins cache: {cache_info['coins_cache']}")
    print(f"   Coin detail cache: {cache_info['coin_detail_cache']}")
    
    return cache_info


@app.get("/debug/clear-cache")
def clear_cache():
    """Debug endpoint to clear all caches"""
    print("\n🗑️  /debug/clear-cache endpoint called - CLEARING ALL CACHES")
    
    coins_cache["data"] = []
    coins_cache["timestamp"] = 0
    coin_detail_cache.clear()
    
    print("✅ All caches cleared")
    
    return {"message": "All caches cleared", "timestamp": time.time()}


print("\n" + "="*50)
print("✅ BACKEND STARTUP COMPLETE")
print("="*50)
print("🌐 Available endpoints:")
print("   GET /api/status          - Health check")
print("   GET /coins               - Top 50 cryptocurrencies") 
print("   GET /crypto/{coin_id}    - Coin details")
print("   GET /predict/{symbol}    - ML predictions")
print("   GET /debug/cache         - Cache status")
print("   GET /debug/clear-cache   - Clear caches")
print("="*50)