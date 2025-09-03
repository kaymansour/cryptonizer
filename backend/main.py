from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests

from models.crypto_predictor import predict_crypto as predict_future_prices
from portfolio_optimizer import optimize_crypto_portfolio, CryptoPortfolioOptimizer

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from models.crypto_predictor import predict_crypto as predict_future_prices
from portfolio_optimizer import optimize_crypto_portfolio, CryptoPortfolioOptimizer

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

@app.get("/api/status")
def read_root():
    return {"message": "Hello from FastAPI"}


@app.get("/crypto/{symbol}")
async def get_crypto_data(symbol: str):
    # Convert symbol to lowercase for API consistency
    symbol = symbol.lower()
    
    try:
        # Get coin ID from symbol
        search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        print(f"Searching for cryptocurrency: {symbol}")
        print(f"Search URL: {search_url}")
        search_response = requests.get(search_url)
        search_data = search_response.json()
        
        if not search_data['coins']:
            raise HTTPException(status_code=404, detail="Cryptocurrency not found")
        
        # Take the first result
        coin_id = search_data['coins'][0]['id']
        
        # Get detailed market data
        market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?tickers=false&market_data=true"
        market_response = requests.get(market_url)
        market_data = market_response.json()
        
        # Extract relevant data
        return {
            "name": market_data['name'],
            "symbol": market_data['symbol'],
            "current_price": market_data['market_data']['current_price']['usd'],
            "market_cap": market_data['market_data']['market_cap']['usd'],
            "total_volume": market_data['market_data']['total_volume']['usd'],
            "price_change_24h": market_data['market_data']['price_change_24h'],
            "price_change_percentage_24h": market_data['market_data']['price_change_percentage_24h'],
            "last_updated": market_data['last_updated'],
            "image": market_data['image']['large']
        }

    


        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/{symbol}")
def predict(symbol: str):
    try:
        result = predict_future_prices(symbol.upper())
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/coins")
def get_coins():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        response = requests.get(url, params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,  # show top 50 coins
            "page": 1,
            "sparkline": False
        })
        data = response.json()

        # Simplify response
        coins = [
            {
                "id": coin["id"],
                "symbol": coin["symbol"],
                "name": coin["name"],
                "image": coin["image"],
                "current_price": coin["current_price"],
                "market_cap": coin["market_cap"],
                "price_change_percentage_24h": coin["price_change_percentage_24h"],
            }
            for coin in data
        ]
        return coins

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize-portfolio")
async def optimize_portfolio(request: PortfolioOptimizationRequest):
    """
    Optimize a cryptocurrency portfolio using Modern Portfolio Theory
    """
    try:
        # Convert symbols to Yahoo Finance format (add -USD suffix if not present)
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith('-USD'):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())
        
        # Perform portfolio optimization
        result = optimize_crypto_portfolio(
            symbols=yf_symbols,
            total_value=request.total_value,
            objective=request.objective,
            period=request.period
        )
        
        # Format response for frontend
        return {
            "success": True,
            "portfolio": {
                "expected_return": result['optimization']['expected_return'],
                "volatility": result['optimization']['volatility'],
                "sharpe_ratio": result['optimization']['sharpe_ratio'],
                "weights": dict(result['optimization']['weights']),
                "objective": result['optimization']['objective']
            },
            "allocation": {
                "total_value": result['allocation']['total_value'],
                "allocation": result['allocation']['allocation'],
                "leftover": result['allocation']['leftover'],
                "latest_prices": result['allocation']['latest_prices']
            },
            "metrics": {
                "var_95": result['metrics']['var_95'],
                "max_drawdown": result['metrics']['max_drawdown']
            },
            "symbols": result['symbols'],
            "period": request.period
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio optimization failed: {str(e)}")


@app.post("/api/efficient-frontier")
async def get_efficient_frontier(request: EfficientFrontierRequest):
    """
    Calculate the efficient frontier for given cryptocurrencies
    """
    try:
        # Convert symbols to Yahoo Finance format
        yf_symbols = []
        for symbol in request.symbols:
            if not symbol.endswith('-USD'):
                yf_symbols.append(f"{symbol.upper()}-USD")
            else:
                yf_symbols.append(symbol.upper())
        
        # Create optimizer and calculate efficient frontier
        optimizer = CryptoPortfolioOptimizer(yf_symbols, period=request.period)
        optimizer.fetch_price_data()
        optimizer.calculate_expected_returns()
        optimizer.calculate_risk_matrix()
        
        volatilities, returns = optimizer.calculate_efficient_frontier(request.num_portfolios)
        
        # Also get some reference portfolios
        max_sharpe = optimizer.optimize_portfolio("max_sharpe")
        min_vol = optimizer.optimize_portfolio("min_volatility")
        
        return {
            "success": True,
            "efficient_frontier": {
                "volatilities": volatilities,
                "returns": returns
            },
            "reference_portfolios": {
                "max_sharpe": {
                    "return": max_sharpe['expected_return'],
                    "volatility": max_sharpe['volatility'],
                    "sharpe_ratio": max_sharpe['sharpe_ratio']
                },
                "min_volatility": {
                    "return": min_vol['expected_return'],
                    "volatility": min_vol['volatility'],
                    "sharpe_ratio": min_vol['sharpe_ratio']
                }
            },
            "symbols": optimizer.symbols,
            "period": request.period
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Efficient frontier calculation failed: {str(e)}")


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
                "description": "Maximize risk-adjusted returns"
            },
            {
                "id": "min_volatility",
                "name": "Minimum Volatility",
                "description": "Minimize portfolio risk"
            },
            {
                "id": "efficient_return",
                "name": "Efficient Return",
                "description": "Optimize for target return level"
            },
            {
                "id": "efficient_risk",
                "name": "Efficient Risk",
                "description": "Optimize for target risk level"
            }
        ]
    }
