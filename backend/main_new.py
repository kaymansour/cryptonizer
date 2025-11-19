"""
Cryptocurrency API Backend
FastAPI server that provides cryptocurrency data from CoinGecko API with caching and ML predictions
"""

from core.config import create_app, print_startup_banner
from api.routes import coins, portfolio, backtest, debug


# Create the FastAPI application
app = create_app()

# Register route modules
app.include_router(coins.router)
app.include_router(portfolio.router)
app.include_router(backtest.router)
app.include_router(debug.router)


# Print startup information
print("Starting Cryptocurrency API Backend...")
print("Backend initialized and ready!")
print_startup_banner()
