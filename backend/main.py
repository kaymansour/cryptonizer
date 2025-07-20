from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

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


@app.get("/api/crypto-prices")
async def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,solana",  # CoinGecko coin ids
        "vs_currencies": "usd"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()


