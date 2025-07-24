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


