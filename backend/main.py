from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

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
