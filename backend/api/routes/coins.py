"""
Core cryptocurrency data routes (coins list and details)
"""
from fastapi import APIRouter
from services.coingecko import CoinGeckoService

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
