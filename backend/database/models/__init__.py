"""
Database Models Package
Define your database tables here

File structure:
- Each file represents a logical grouping of related tables
- Example files you can create:
  - users.py: User accounts and authentication
  - portfolios.py: Portfolio data and allocations
  - predictions.py: ML prediction results
  - backtests.py: Backtest results and history
  - transactions.py: Trading transactions
"""

# Import your model modules here as you create them
from .users import create_users_table

__all__ = ["create_users_table"]
