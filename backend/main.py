"""
Cryptocurrency API Backend
FastAPI server that provides cryptocurrency data from CoinGecko API with caching and ML predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import time
import traceback


from portfolio_optimizer import optimize_crypto_portfolio, CryptoPortfolioOptimizer
from backtester import Backtester, backtest_portfolio
from strategy_comparator import StrategyComparator, compare_with_benchmarks
from ml_backtester import MLTradingBacktester


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


# Pydantic models for request validation
class PortfolioOptimizationRequest(BaseModel):
    symbols: List[str]
    total_value: float = 100000
    objective: str = "max_sharpe"
    period: str = "1y"


class EfficientFrontierRequest(BaseModel):
    symbols: List[str]
    period: str = "1y"
    num_portfolios: int = 50


class BacktestRequest(BaseModel):
    symbols: List[str]
    weights: Dict[str, float]
    initial_investment: float = 100000
    start_date: str
    end_date: str
    rebalance_frequency: str = "monthly"


class StrategyComparisonRequest(BaseModel):
    symbols: List[str]
    optimized_weights: Dict[str, float]
    initial_investment: float = 100000
    start_date: str
    end_date: str
    rebalance_frequency: str = "monthly"
    include_benchmarks: Optional[List[str]] = None


class MLBacktestRequest(BaseModel):
    symbols: List[str]
    weights: Dict[str, float]
    initial_investment: float = 100000
    start_date: str
    end_date: str
    interval: str = "4h"  # "1h" or "4h"
    signal_threshold: float = 0.5


# =============================================================================
# CACHING CONFIGURATION
# =============================================================================
# Cache configuration to reduce API calls to CoinGecko and improve performance
CACHE_TTL_COINS = 60  # Cache top 50 coins list for 1 minute
CACHE_TTL_COIN_DETAIL = 300  # Cache individual coin details for 5 minutes

# In-memory cache storage
coins_cache = {"data": [], "timestamp": 0}  # Stores the top coins list with timestamp
coin_detail_cache = (
    {}
)  # Dictionary cache for individual coin details: key=coin_id, value={"data": ..., "timestamp": ...}


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
    return {
        "message": "Hello from FastAPI",
        "status": "healthy",
        "timestamp": time.time(),
    }


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

    print(
        f"📦 Cache check - Has data: {bool(coins_cache['data'])}, Age: {cache_age:.1f}s, Valid: {is_cache_valid}"
    )

    if is_cache_valid:
        print(
            f"✅ Returning cached coins data ({len(coins_cache['data'])} coins, {cache_age:.1f}s old)"
        )
        return coins_cache["data"]

    try:
        print("🔄 Fetching fresh data from CoinGecko API...")

        # CoinGecko API endpoint for cryptocurrency markets data
        url = "https://api.coingecko.com/api/v3/coins/markets"

        # Make request to CoinGecko API with specific parameters
        params = {
            "vs_currency": "usd",  # Base currency for prices
            "order": "market_cap_desc",  # Sort by market cap (highest first)
            "per_page": 50,  # Limit to top 50 coins
            "page": 1,  # First page of results
            "sparkline": False,  # Exclude sparkline data for performance
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
            error_detail = (
                f"CoinGecko API error: {response.status_code} - {response.text}"
            )
            print(f"❌ {error_detail}")

            # Try to return cached data even if expired
            if coins_cache["data"]:
                print("🔄 Falling back to expired cache due to API error")
                return coins_cache["data"]

        # Parse JSON response from CoinGecko
        data = response.json()
        print(f"📦 Received data from CoinGecko:")
        print(f"   Type: {type(data)}")
        print(f"   Length: {len(data) if isinstance(data, list) else 'N/A'}")
        if isinstance(data, list) and len(data) > 0:
            print(f"   First item keys: {list(data[0].keys())}")

        # Validate response format - should be a list of coins
        if not isinstance(data, list):
            error_detail = (
                f"CoinGecko API did not return a list. Got: {type(data)} - {data}"
            )
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
                    "price_change_percentage_24h": coin.get(
                        "price_change_percentage_24h", 0
                    ),
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
                    print(
                        f"   ✅ Sample coin {i}: {coin_data['symbol']} - ${coin_data['current_price']}"
                    )

            except Exception as coin_error:
                print(
                    f"   ❌ Error processing coin {i} ({coin.get('id', 'unknown')}): {coin_error}"
                )
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

    except requests.exceptions.ConnectionError:
        error_detail = "Failed to connect to CoinGecko API - network issue"
        print(f"❌ {error_detail}")
        if coins_cache["data"]:
            print("🔄 Returning cached data due to connection error")
            return coins_cache["data"]

    except Exception as e:
        error_detail = f"Unexpected error in /coins endpoint: {str(e)}"
        print(f"❌ {error_detail}")
        print(f"🔍 Stack trace: {traceback.format_exc()}")

        if coins_cache["data"]:
            print("🔄 Returning cached data due to unexpected error")
            return coins_cache["data"]


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

    coin_id = coin_id.lower()  # Normalize coin_id to lowercase
    currency = currency.lower()  # Normalize currency to lowercase
    current_time = time.time()

    # Check cache
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
            raise HTTPException(
                status_code=404, detail=f"Cryptocurrency '{coin_id}' not found"
            )
        elif market_response.status_code != 200:
            error_msg = (
                f"CoinGecko API error for {coin_id}: {market_response.status_code}"
            )
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        # Parse the coin details from CoinGecko
        market_data = market_response.json()
        market_data_currency = market_data.get("market_data", {})
        print(f"💰 Extracting prices for currency: {currency}")

        current_price = market_data_currency.get("current_price", {}).get(currency, 0)
        market_cap = market_data_currency.get("market_cap", {}).get(currency, 0)
        total_volume = market_data_currency.get("total_volume", {}).get(currency, 0)
        price_change_24h = market_data_currency.get("price_change_24h", 0)
        price_change_percentage_24h = market_data_currency.get(
            "price_change_percentage_24h", 0
        )
        market_cap_rank = market_data.get("market_cap_rank", 0)

        # Historical price data
        history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        history_params = {"vs_currency": currency, "days": days}

        print(f"📊 Fetching historical data...")
        print(f"   URL: {history_url}")
        print(f"   Params: {history_params}")

        start_time = time.time()
        history_response = requests.get(history_url, params=history_params, timeout=10)
        history_time = time.time() - start_time

        print(
            f"   History response: {history_response.status_code}, Time: {history_time:.2f}s"
        )

        if history_response.status_code != 200:
            history_data = {"prices": []}
        else:
            history_data = history_response.json()

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
            "description": market_data.get("description", {}).get(
                "en", "No description available."
            ),
            "history": history_data.get("prices", []),
            "market_cap_rank": market_cap_rank,
        }

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
            print(
                f"🔄 Returning expired cached data for {coin_id} due to connection error"
            )
            return coin_detail_cache[coin_id]["data"]
        else:
            raise HTTPException(status_code=500, detail=error_detail)

    except HTTPException:
        raise

    except Exception as e:
        print(f"❌ Unexpected error fetching {coin_id}: {str(e)}")
        print(f"🔍 Stack trace: {traceback.format_exc()}")

        # Return cached data even if expired
        if coin_id in coin_detail_cache:
            print(
                f"🔄 Returning expired cached data for {coin_id} due to unexpected error"
            )
            return coin_detail_cache[coin_id]["data"]
        else:
            raise HTTPException(
                status_code=500, detail=f"Unexpected error fetching {coin_id}: {str(e)}"
            )


# =============================================================================
# 🧠 PREDICTION ENDPOINT (Integrated with model_predictor.py)
# =============================================================================
@app.get("/predict/{symbol}")
def predict_symbol(symbol: str, days: int = 7):
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
        print(
            f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
        )

        return result

    except ValueError as ve:
        error_msg = f"Prediction error for {symbol}: {str(ve)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=404, detail=str(ve))

    except Exception as e:
        print(f"❌ Prediction failed for {symbol}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# =============================================================================
# ML-DRIVEN BACKTESTING ENDPOINT
# =============================================================================
@app.post("/api/ml-backtest")
async def ml_backtest_endpoint(request: MLBacktestRequest):
    """
    Run ML-driven backtesting using LSTM predictions for trading signals
    Returns predicted vs actual prices for visualization
    """
    try:
        print(f"ML Backtesting portfolio with {len(request.symbols)} symbols")
        print(f"Period: {request.start_date} to {request.end_date}")
        print(f"Interval: {request.interval}")
        print(f"Signal threshold: {request.signal_threshold}")

        # Validate weights
        total_weight = sum(request.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Portfolio weights must sum to 1.0, got {total_weight:.4f}",
            )

        # Convert symbols to Yahoo Finance format if needed
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        # Create ML backtester
        backtester = MLTradingBacktester(
            symbols=yf_symbols,
            initial_capital=request.initial_investment,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval,
            signal_threshold=request.signal_threshold,
        )

        # Run backtest
        results = backtester.run_backtest()

        if not results.get("success"):
            raise HTTPException(
                status_code=500, detail="ML backtesting failed to complete successfully"
            )

        # Format portfolio history for frontend charting
        portfolio_history = results.get("portfolio_history", {})
        daily_values = [
            {
                "date": str(timestamp) if not isinstance(timestamp, str) else timestamp,
                "portfolio_value": value,
            }
            for timestamp, value in portfolio_history.items()
        ]

        # Get predictions log for comparison chart
        predictions_log = backtester.predictions_log

        # Group predictions by symbol for easier frontend processing
        predictions_by_symbol = {}
        for pred in predictions_log:
            symbol = pred["symbol"]
            if symbol not in predictions_by_symbol:
                predictions_by_symbol[symbol] = []

            # Convert timestamp to ISO format string
            timestamp = pred["timestamp"]
            if hasattr(timestamp, "isoformat"):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)

            predictions_by_symbol[symbol].append(
                {
                    "timestamp": timestamp_str,
                    "actual_price": pred.get(
                        "actual_next_price", pred.get("current_price", 0)
                    ),  # Use actual next price
                    "predicted_price": pred.get("predicted_price", 0),
                    "predicted_change": pred.get("predicted_change", 0),
                    "confidence": pred.get("confidence", 0),
                }
            )

        print(f"ML Backtest completed successfully")
        print(f"Final value: ${results['summary']['final_value']:,.2f}")
        print(f"Total return: {results['summary']['total_return']:.2f}%")
        print(f"Total trades: {results['trading_stats']['total_trades']}")

        return {
            "success": True,
            "backtest_results": {
                "summary": results["summary"],
                "trading_stats": results["trading_stats"],
                "daily_values": daily_values,
                "predictions_by_symbol": predictions_by_symbol,
                "trade_history": results.get("trade_history", []),
                "config": results.get("config", {}),
            },
            "summary": {
                "initial_investment": request.initial_investment,
                "final_value": results["summary"]["final_value"],
                "total_return": results["summary"]["total_return"],
                "annualized_return": results["summary"]["annualized_return"],
                "sharpe_ratio": results["summary"]["sharpe_ratio"],
                "max_drawdown": results["summary"]["max_drawdown"],
                "period": f"{request.start_date} to {request.end_date}",
                "total_trades": results["trading_stats"]["total_trades"],
                "win_rate": results["trading_stats"]["win_rate"],
            },
        }

    except ValueError as ve:
        print(f"Validation error in ML backtest: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in ML backtest endpoint: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"ML backtesting failed: {str(e)}")


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
            "is_valid": coins_cache_age < CACHE_TTL_COINS,
        },
        "coin_detail_cache": {
            "size": coin_detail_cache_size,
            "keys": list(coin_detail_cache.keys())[:10],  # First 10 keys
        },
        "current_time": time.time(),
    }

    print(f"📊 Cache debug info:")
    print(f"   Coins cache: {cache_info['coins_cache']}")
    print(f"   Coin detail cache: {cache_info['coin_detail_cache']}")

    return cache_info


@app.post("/api/optimize-portfolio")
async def optimize_portfolio(request: PortfolioOptimizationRequest):
    """
    Optimize a cryptocurrency portfolio using Modern Portfolio Theory
    """
    try:
        # Convert symbols to Yahoo Finance format (add -USD suffix if not present)
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        # Perform portfolio optimization
        result = optimize_crypto_portfolio(
            symbols=yf_symbols,
            total_value=request.total_value,
            objective=request.objective,
            period=request.period,
        )

        # Format response for frontend
        return {
            "success": True,
            "portfolio": {
                "expected_return": result["optimization"]["expected_return"],
                "volatility": result["optimization"]["volatility"],
                "sharpe_ratio": result["optimization"]["sharpe_ratio"],
                "weights": dict(result["optimization"]["weights"]),
                "objective": result["optimization"]["objective"],
            },
            "allocation": {
                "total_value": result["allocation"]["total_value"],
                "allocation": result["allocation"]["allocation"],
                "leftover": result["allocation"]["leftover"],
                "latest_prices": result["allocation"]["latest_prices"],
            },
            "metrics": {
                "var_95": result["metrics"]["var_95"],
                "max_drawdown": result["metrics"]["max_drawdown"],
            },
            "symbols": result["symbols"],
            "period": request.period,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Portfolio optimization failed: {str(e)}"
        )


@app.post("/api/efficient-frontier")
async def get_efficient_frontier(request: EfficientFrontierRequest):
    """
    Calculate the efficient frontier for given cryptocurrencies
    """
    try:
        # Convert symbols to Yahoo Finance format
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith("-USD"):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())

        # Create optimizer and calculate efficient frontier
        optimizer = CryptoPortfolioOptimizer(yf_symbols, period=request.period)
        optimizer.fetch_price_data()
        optimizer.calculate_expected_returns()
        optimizer.calculate_risk_matrix()

        volatilities, returns = optimizer.calculate_efficient_frontier(
            request.num_portfolios
        )

        # Also get some reference portfolios
        max_sharpe = optimizer.optimize_portfolio("max_sharpe")
        min_vol = optimizer.optimize_portfolio("min_volatility")

        return {
            "success": True,
            "efficient_frontier": {"volatilities": volatilities, "returns": returns},
            "reference_portfolios": {
                "max_sharpe": {
                    "return": max_sharpe["expected_return"],
                    "volatility": max_sharpe["volatility"],
                    "sharpe_ratio": max_sharpe["sharpe_ratio"],
                },
                "min_volatility": {
                    "return": min_vol["expected_return"],
                    "volatility": min_vol["volatility"],
                    "sharpe_ratio": min_vol["sharpe_ratio"],
                },
            },
            "symbols": optimizer.symbols,
            "period": request.period,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Efficient frontier calculation failed: {str(e)}"
        )


@app.get("/api/portfolio/objectives")
async def get_optimization_objectives():
    """
    Get available portfolio optimization objectives
    """
    return {
        "objectives": [
            {
                "id": "max_sharpe",
                "name": "Maximum Sharpe Ratio",
                "description": "Maximize risk-adjusted returns",
            },
            {
                "id": "min_volatility",
                "name": "Minimum Volatility",
                "description": "Minimize portfolio risk",
            },
            {
                "id": "efficient_return",
                "name": "Efficient Return",
                "description": "Optimize for target return level",
            },
            {
                "id": "efficient_risk",
                "name": "Efficient Risk",
                "description": "Optimize for target risk level",
            },
        ]
    }


@app.post("/api/backtest-portfolio")
async def backtest_portfolio_endpoint(request: BacktestRequest):
    """
    Backtest a portfolio with given weights over a historical period
    """
    try:
        print(f"Backtesting portfolio with {len(request.symbols)} symbols")
        print(f"Period: {request.start_date} to {request.end_date}")
        print(f"Weights: {request.weights}")

        # Validate weights
        total_weight = sum(request.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Portfolio weights must sum to 1.0, got {total_weight:.4f}",
            )

        # Create backtester
        backtester = Backtester(
            symbols=request.symbols,
            weights=request.weights,
            initial_investment=request.initial_investment,
            start_date=request.start_date,
            end_date=request.end_date,
            rebalance_frequency=request.rebalance_frequency,
        )

        # Generate comprehensive report
        report = backtester.generate_report(include_detailed_data=True)

        print(f"Backtest completed successfully")
        print(f"Final value: ${report['summary']['final_value']:,.2f}")
        print(f"Total return: {report['summary']['total_return']:.2f}%")

        return {
            "success": True,
            "backtest_results": report,
            "summary": {
                "initial_investment": request.initial_investment,
                "final_value": report["summary"]["final_value"],
                "total_return": report["summary"]["total_return"],
                "annualized_return": report["summary"]["annualized_return"],
                "sharpe_ratio": report["summary"]["sharpe_ratio"],
                "max_drawdown": report["summary"]["max_drawdown"],
                "period": f"{request.start_date} to {request.end_date}",
            },
        }

    except ValueError as ve:
        print(f"Validation error in backtest: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in backtest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backtesting failed: {str(e)}")


@app.post("/api/compare-strategies")
async def compare_strategies_endpoint(request: StrategyComparisonRequest):
    """
    Compare optimized portfolio against benchmark strategies
    """
    try:
        print(f"Comparing strategies for {len(request.symbols)} symbols")
        print(f"Period: {request.start_date} to {request.end_date}")
        print(f"Optimized weights: {request.optimized_weights}")

        # Validate optimized weights
        total_weight = sum(request.optimized_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Optimized weights must sum to 1.0, got {total_weight:.4f}",
            )

        # Set default benchmarks if not provided
        if request.include_benchmarks is None:
            request.include_benchmarks = [
                "equal_weight",
                "btc_only",
                "eth_only",
                "btc_eth_60_40",
            ]

        # Create strategy comparator
        comparator = StrategyComparator(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_investment=request.initial_investment,
        )

        # Run comparison
        comparison_results = comparator.compare_strategies(
            optimized_weights=request.optimized_weights,
            rebalance_frequency=request.rebalance_frequency,
            include_benchmarks=request.include_benchmarks,
        )

        print(f"Strategy comparison completed successfully")
        print(f"Compared {len(comparison_results['comparison_summary'])} strategies")

        # Find best performing strategy
        best_strategy = max(
            comparison_results["comparison_summary"].items(),
            key=lambda x: x[1]["total_return"],
        )

        return {
            "success": True,
            "comparison_results": comparison_results,
            "summary": {
                "period": comparison_results["period"],
                "initial_investment": comparison_results["initial_investment"],
                "strategies_compared": len(comparison_results["comparison_summary"]),
                "best_strategy": {
                    "name": best_strategy[1]["strategy_name"],
                    "total_return": best_strategy[1]["total_return"],
                    "sharpe_ratio": best_strategy[1]["sharpe_ratio"],
                },
            },
        }

    except ValueError as ve:
        print(f"Validation error in strategy comparison: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in strategy comparison endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Strategy comparison failed: {str(e)}"
        )


@app.post("/api/quick-backtest")
async def quick_backtest_endpoint(
    symbols: List[str], weights: Dict[str, float], days_back: int = 365
):
    """
    Quick backtest for the last N days (convenience endpoint)
    """
    try:
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Use the backtest_portfolio convenience function
        result = backtest_portfolio(
            symbols=symbols,
            weights=weights,
            initial_investment=100000,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency="monthly",
        )

        return {"success": True, "backtest_results": result, "period_days": days_back}

    except Exception as e:
        print(f"Error in quick backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick backtest failed: {str(e)}")


@app.get("/debug/clear-cache")
def clear_cache():
    """Debug endpoint to clear all caches"""
    print("\n🗑️  /debug/clear-cache endpoint called - CLEARING ALL CACHES")

    coins_cache["data"] = []
    coins_cache["timestamp"] = 0
    coin_detail_cache.clear()

    print("✅ All caches cleared")

    return {"message": "All caches cleared", "timestamp": time.time()}


print("\n" + "=" * 50)
print("✅ BACKEND STARTUP COMPLETE")
print("=" * 50)
print("🌐 Available endpoints:")
print("   GET /api/status                - Health check")
print("   GET /coins                     - Top 50 cryptocurrencies")
print("   GET /crypto/{coin_id}          - Coin details")
print("   GET /predict/{symbol}          - ML predictions")
print("   POST /api/optimize-portfolio   - Portfolio optimization")
print("   POST /api/efficient-frontier   - Efficient frontier calculation")
print("   GET /api/portfolio/objectives  - Available optimization objectives")
print("   POST /api/backtest-portfolio   - Historical portfolio backtesting")
print("   POST /api/ml-backtest          - ML-driven trading backtest")
print("   POST /api/compare-strategies   - Strategy performance comparison")
print("   POST /api/quick-backtest       - Quick backtest (convenience)")
print("   GET /debug/cache               - Cache status")
print("   GET /debug/clear-cache         - Clear caches")
print("=" * 50)
