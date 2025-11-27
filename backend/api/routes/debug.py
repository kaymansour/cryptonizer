"""
Debug and utility routes
"""
from fastapi import APIRouter
import time
from services.cache import coins_cache, coin_detail_cache

router = APIRouter()


@router.get("/api/status")
def health_check():
    """Health check endpoint to verify the API is running"""
    print("🏥 Health check endpoint called")
    return {
        "message": "Hello from FastAPI",
        "status": "healthy",
        "timestamp": time.time(),
    }


@router.get("/debug/cache")
def debug_cache():
    """Debug endpoint to check cache status"""
    print("\n🔍 /debug/cache endpoint called")
    
    coins_stats = coins_cache.get_stats()
    coin_detail_stats = coin_detail_cache.get_stats()
    
    cache_info = {
        "coins_cache": coins_stats,
        "coin_detail_cache": coin_detail_stats,
        "current_time": time.time(),
    }
    
    print(f"📊 Cache debug info:")
    print(f"   Coins cache: {coins_stats}")
    print(f"   Coin detail cache: {coin_detail_stats}")
    
    return cache_info


@router.get("/debug/clear-cache")
def clear_cache():
    """Debug endpoint to clear all caches"""
    print("\n🗑️  /debug/clear-cache endpoint called - CLEARING ALL CACHES")
    
    coins_cache.clear()
    coin_detail_cache.clear()
    
    print("✅ All caches cleared")
    
    return {"message": "All caches cleared", "timestamp": time.time()}
