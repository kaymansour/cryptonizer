"""
Cryptocurrency API Backend
FastAPI server that provides cryptocurrency data from CoinGecko API with caching and ML predictions
"""

from core.config import create_app, print_startup_banner
from api.routes import (
    coins,
    portfolio,
    backtest,
    debug,
    clerk_webhook,
    saved_portfolios,
)
from database.connection import init_database


# Create the FastAPI application
app = create_app()

# Initialize database on startup
init_database()

# Register route modules
app.include_router(coins.router)
app.include_router(portfolio.router)
app.include_router(backtest.router)
app.include_router(debug.router)
app.include_router(clerk_webhook.router)
app.include_router(saved_portfolios.router)


# Print startup information
print("Starting Cryptocurrency API Backend...")
print("Backend initialized and ready!")
print_startup_banner()
