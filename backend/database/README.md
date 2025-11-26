# Database Directory

SQLite database setup for the cryptocurrency portfolio application.

## File Structure

```
database/
├── __init__.py                 # Package initialization
├── connection.py              # Database connection manager
├── crypto_portfolio.db        # SQLite database file (auto-created)
├── models/                    # Table definitions
│   ├── __init__.py
│   ├── example_template.py   # Template for creating new tables
│   └── [your_tables].py      # Add your table files here
└── migrations/               # Schema migration scripts
    ├── __init__.py
    └── [YYYYMMDD_description].py
```

## Quick Start

### 1. Test the Database Setup

```bash
cd /home/weed/senior/backend
python3 -c "from database.connection import init_database; init_database()"
```

### 2. Create Your First Table

Copy `models/example_template.py` and modify it:

```bash
cp database/models/example_template.py database/models/users.py
# Edit users.py to define your users table
```

### 3. Example Table Definition

```python
# database/models/users.py
from database.connection import get_db_cursor

def create_users_table():
    with get_db_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
```

### 4. Use in Your Application

```python
from database.connection import get_db_cursor
from database.models.users import create_users_table

# Initialize table
create_users_table()

# Query data
with get_db_cursor() as cursor:
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
```

## Suggested Tables for Crypto Portfolio App

Based on your application, consider creating these tables:

### `models/users.py`
- User accounts and authentication

### `models/portfolios.py`
- Portfolio configurations
- Asset allocations
- Optimization settings

### `models/predictions.py`
- LSTM prediction results
- Prediction history
- Model performance metrics

### `models/backtests.py`
- Backtest results
- Performance metrics
- Historical comparisons

### `models/transactions.py`
- Simulated/real trades
- Trade history
- Position tracking

### `models/watchlists.py`
- User cryptocurrency watchlists
- Favorite coins

## Database Location

The database file will be created at:
`/home/weed/senior/backend/database/crypto_portfolio.db`

## Features

- ✅ Auto-commit on successful operations
- ✅ Auto-rollback on errors
- ✅ Row factory for dictionary-like access
- ✅ Context manager for safe operations
- ✅ Thread-safe connections

## Notes

- The database file is **not** in `.gitignore` by default - add it if needed
- Use migrations for schema changes in production
- The `get_db_cursor()` context manager handles commit/rollback automatically
