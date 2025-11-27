"""
CoinGecko API service for fetching cryptocurrency data
"""
import requests
import time
import traceback
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from services.cache import coins_cache, coin_detail_cache


class CoinGeckoService:
    """Service for interacting with CoinGecko API"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    REQUEST_TIMEOUT = 10
    
    @staticmethod
    def get_top_coins() -> List[Dict[str, Any]]:
        """
        Fetches top 50 cryptocurrencies by market cap from CoinGecko API
        Returns: List of coin objects with basic information
        """
        print(f"\n🎯 Fetching top coins at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check cache first
        cached_data = coins_cache.get("top_coins")
        if cached_data:
            print(f"✅ Returning cached coins data ({len(cached_data)} coins)")
            return cached_data
        
        try:
            print("🔄 Fetching fresh data from CoinGecko API...")
            
            url = f"{CoinGeckoService.BASE_URL}/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 50,
                "page": 1,
                "sparkline": False,
            }
            
            print(f"📡 Making request to CoinGecko API...")
            start_time = time.time()
            response = requests.get(url, params=params, timeout=CoinGeckoService.REQUEST_TIMEOUT)
            request_time = time.time() - start_time
            
            print(f"📊 CoinGecko API Response: Status {response.status_code}, Time {request_time:.2f}s")
            
            if response.status_code != 200:
                error_detail = f"CoinGecko API error: {response.status_code} - {response.text}"
                print(f"❌ {error_detail}")
                
                # Try to return expired cache
                fallback = coins_cache.get("top_coins")
                if fallback:
                    print("🔄 Falling back to expired cache")
                    return fallback
                raise HTTPException(status_code=500, detail=error_detail)
            
            data = response.json()
            
            if not isinstance(data, list):
                raise HTTPException(
                    status_code=500, 
                    detail=f"CoinGecko API did not return a list. Got: {type(data)}"
                )
            
            if not data:
                raise HTTPException(status_code=500, detail="CoinGecko API returned empty list")
            
            # Transform data
            coins = []
            for coin in data:
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
                    
                    if coin_data["id"] and coin_data["symbol"]:
                        coins.append(coin_data)
                except Exception as e:
                    print(f"   ⚠️ Error processing coin: {e}")
                    continue
            
            if not coins:
                raise HTTPException(status_code=500, detail="No coins were successfully processed")
            
            # Cache the results
            coins_cache.set("top_coins", coins)
            print(f"💾 Cached {len(coins)} coins")
            
            return coins
            
        except requests.exceptions.Timeout:
            print(f"❌ CoinGecko API request timed out")
            fallback = coins_cache.get("top_coins")
            if fallback:
                return fallback
            raise HTTPException(status_code=500, detail="CoinGecko API timeout")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed to connect to CoinGecko API")
            fallback = coins_cache.get("top_coins")
            if fallback:
                return fallback
            raise HTTPException(status_code=500, detail="Network connection error")
            
        except HTTPException:
            raise
            
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            fallback = coins_cache.get("top_coins")
            if fallback:
                return fallback
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    @staticmethod
    def get_coin_details(coin_id: str, currency: str = "usd", days: int = 7) -> Dict[str, Any]:
        """
        Fetches detailed information and price history for a specific cryptocurrency
        
        Args:
            coin_id: Unique identifier for the cryptocurrency
            currency: Currency to display prices in
            days: Number of days of historical data to fetch
            
        Returns:
            Detailed coin information including price history
        """
        print(f"\n🎯 Fetching details for {coin_id}")
        
        coin_id = coin_id.lower()
        currency = currency.lower()
        
        # Check cache
        cache_key = f"{coin_id}_{currency}_{days}"
        cached_data = coin_detail_cache.get(cache_key)
        if cached_data:
            print(f"✅ Returning cached data for {coin_id}")
            return cached_data
        
        try:
            print(f"🔄 Fetching data for {coin_id} from CoinGecko...")
            
            # Get market data
            market_url = f"{CoinGeckoService.BASE_URL}/coins/{coin_id}"
            params = {"tickers": "false", "market_data": "true"}
            
            market_response = requests.get(market_url, params=params, timeout=CoinGeckoService.REQUEST_TIMEOUT)
            
            if market_response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Cryptocurrency '{coin_id}' not found")
            elif market_response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"CoinGecko API error: {market_response.status_code}"
                )
            
            market_data = market_response.json()
            market_info = market_data.get("market_data", {})
            
            # Get historical data
            history_url = f"{CoinGeckoService.BASE_URL}/coins/{coin_id}/market_chart"
            history_params = {"vs_currency": currency, "days": days}
            history_response = requests.get(
                history_url, 
                params=history_params, 
                timeout=CoinGeckoService.REQUEST_TIMEOUT
            )
            
            history_data = history_response.json() if history_response.status_code == 200 else {"prices": []}
            
            # Build result
            result = {
                "id": market_data.get("id"),
                "name": market_data.get("name"),
                "symbol": market_data.get("symbol", "").lower(),
                "current_price": market_info.get("current_price", {}).get(currency, 0),
                "market_cap": market_info.get("market_cap", {}).get(currency, 0),
                "total_volume": market_info.get("total_volume", {}).get(currency, 0),
                "price_change_24h": market_info.get("price_change_24h", 0),
                "price_change_percentage_24h": market_info.get("price_change_percentage_24h", 0),
                "last_updated": market_data.get("last_updated"),
                "image": market_data.get("image", {}).get("large", ""),
                "description": market_data.get("description", {}).get("en", "No description available."),
                "history": history_data.get("prices", []),
                "market_cap_rank": market_data.get("market_cap_rank", 0),
            }
            
            # Cache the result
            coin_detail_cache.set(cache_key, result)
            print(f"💾 Cached data for {coin_id}")
            
            return result
            
        except requests.exceptions.Timeout:
            print(f"❌ CoinGecko API timeout for {coin_id}")
            fallback = coin_detail_cache.get(cache_key)
            if fallback:
                return fallback
            raise HTTPException(status_code=500, detail=f"CoinGecko API timeout for {coin_id}")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Network connection error for {coin_id}")
            fallback = coin_detail_cache.get(cache_key)
            if fallback:
                return fallback
            raise HTTPException(status_code=500, detail="Network connection error")
            
        except HTTPException:
            raise
            
        except Exception as e:
            print(f"❌ Unexpected error fetching {coin_id}: {str(e)}")
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            fallback = coin_detail_cache.get(cache_key)
            if fallback:
                return fallback
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
