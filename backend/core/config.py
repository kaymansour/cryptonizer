"""
Core application configuration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Cryptocurrency API Backend",
        description="FastAPI server that provides cryptocurrency data from CoinGecko API with caching and ML predictions",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Frontend development server URL
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )
    
    return app


def print_startup_banner():
    """Print startup information"""
    print("\n" + "=" * 50)
    print("✅ BACKEND STARTUP COMPLETE")
    print("=" * 50)
    print("🌐 Available endpoints:")
    print("   GET /api/status                - Health check")
    print("   GET /coins                     - Top 50 cryptocurrencies")
    print("   GET /crypto/{coin_id}          - Coin details")
    print("   POST /api/optimize-portfolio   - Portfolio optimization")
    print("   POST /api/optimize-portfolio-lstm - LSTM-enhanced optimization")
    print("   POST /api/efficient-frontier   - Efficient frontier calculation")
    print("   GET /api/portfolio/objectives  - Available optimization objectives")
    print("   POST /api/backtest-portfolio   - Historical portfolio backtesting")
    print("   POST /api/ml-backtest          - ML-driven trading backtest")
    print("   POST /api/compare-strategies   - Strategy performance comparison")
    print("   POST /api/quick-backtest       - Quick backtest (convenience)")
    print("   GET /debug/cache               - Cache status")
    print("   GET /debug/clear-cache         - Clear caches")
    print("=" * 50)
