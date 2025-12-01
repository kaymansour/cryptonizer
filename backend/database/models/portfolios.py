"""
Portfolios Table Model
Stores optimized portfolio configurations created by users
"""

import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database.connection import get_db_cursor
from typing import Optional, Dict, List
from datetime import datetime
import json


def create_portfolios_table():
    """
    Create the portfolios table to store user-saved portfolio optimizations

    Schema:
    - id: Auto-incrementing primary key
    - clerk_id: Foreign key to users table
    - name: User-defined portfolio name
    - symbols: JSON array of cryptocurrency symbols
    - weights: JSON object of symbol->weight mappings
    - total_value: Total portfolio value in USD
    - expected_return: Expected annual return (decimal)
    - volatility: Portfolio volatility/risk (decimal)
    - sharpe_ratio: Sharpe ratio
    - objective: Optimization objective used (max_sharpe, min_volatility, etc.)
    - period: Historical data period used (1y, 2y, etc.)
    - allocation: JSON object of discrete allocation results
    - created_at: Portfolio creation timestamp
    - updated_at: Last update timestamp
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clerk_id TEXT NOT NULL,
                name TEXT NOT NULL,
                symbols TEXT NOT NULL,
                weights TEXT NOT NULL,
                total_value REAL NOT NULL,
                expected_return REAL,
                volatility REAL,
                sharpe_ratio REAL,
                objective TEXT,
                period TEXT,
                allocation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clerk_id) REFERENCES users(clerk_id) ON DELETE CASCADE
            )
        """
        )

        # Create indexes for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_portfolios_clerk_id 
            ON portfolios(clerk_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_portfolios_created_at 
            ON portfolios(created_at DESC)
        """
        )

    print("✓ Portfolios table created")


def insert_portfolio(
    clerk_id: str,
    name: str,
    symbols: List[str],
    weights: Dict[str, float],
    total_value: float,
    expected_return: Optional[float] = None,
    volatility: Optional[float] = None,
    sharpe_ratio: Optional[float] = None,
    objective: Optional[str] = None,
    period: Optional[str] = None,
    allocation: Optional[Dict] = None,
) -> int:
    """
    Insert a new portfolio

    Args:
        clerk_id: User's Clerk ID
        name: Portfolio name
        symbols: List of cryptocurrency symbols
        weights: Dictionary of symbol->weight mappings
        total_value: Total portfolio value
        expected_return: Expected annual return
        volatility: Portfolio volatility
        sharpe_ratio: Sharpe ratio
        objective: Optimization objective
        period: Historical period
        allocation: Discrete allocation details

    Returns:
        Portfolio ID of inserted portfolio
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO portfolios (
                clerk_id, name, symbols, weights, total_value,
                expected_return, volatility, sharpe_ratio, objective, period, allocation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                clerk_id,
                name,
                json.dumps(symbols),
                json.dumps(weights),
                total_value,
                expected_return,
                volatility,
                sharpe_ratio,
                objective,
                period,
                json.dumps(allocation) if allocation else None,
            ),
        )

        portfolio_id = cursor.lastrowid

    print(f"✓ Portfolio '{name}' created with ID: {portfolio_id}")
    return portfolio_id


def get_portfolio_by_id(portfolio_id: int) -> Optional[Dict]:
    """
    Get a portfolio by ID

    Args:
        portfolio_id: Portfolio ID

    Returns:
        Portfolio dict or None if not found
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM portfolios WHERE id = ?
        """,
            (portfolio_id,),
        )

        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "clerk_id": row["clerk_id"],
                "name": row["name"],
                "symbols": json.loads(row["symbols"]),
                "weights": json.loads(row["weights"]),
                "total_value": row["total_value"],
                "expected_return": row["expected_return"],
                "volatility": row["volatility"],
                "sharpe_ratio": row["sharpe_ratio"],
                "objective": row["objective"],
                "period": row["period"],
                "allocation": (
                    json.loads(row["allocation"]) if row["allocation"] else None
                ),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        return None


def get_portfolios_by_user(
    clerk_id: str, limit: int = 50, offset: int = 0
) -> List[Dict]:
    """
    Get all portfolios for a user

    Args:
        clerk_id: User's Clerk ID
        limit: Maximum number of portfolios to return
        offset: Offset for pagination

    Returns:
        List of portfolio dicts
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM portfolios 
            WHERE clerk_id = ? 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """,
            (clerk_id, limit, offset),
        )

        rows = cursor.fetchall()
        portfolios = []
        for row in rows:
            portfolios.append(
                {
                    "id": row["id"],
                    "clerk_id": row["clerk_id"],
                    "name": row["name"],
                    "symbols": json.loads(row["symbols"]),
                    "weights": json.loads(row["weights"]),
                    "total_value": row["total_value"],
                    "expected_return": row["expected_return"],
                    "volatility": row["volatility"],
                    "sharpe_ratio": row["sharpe_ratio"],
                    "objective": row["objective"],
                    "period": row["period"],
                    "allocation": (
                        json.loads(row["allocation"]) if row["allocation"] else None
                    ),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )

        return portfolios


def update_portfolio(
    portfolio_id: int,
    name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None,
    total_value: Optional[float] = None,
    expected_return: Optional[float] = None,
    volatility: Optional[float] = None,
    sharpe_ratio: Optional[float] = None,
    objective: Optional[str] = None,
    period: Optional[str] = None,
    allocation: Optional[Dict] = None,
) -> bool:
    """
    Update a portfolio

    Args:
        portfolio_id: Portfolio ID
        **kwargs: Fields to update

    Returns:
        True if portfolio was updated
    """
    updates = []
    values = []

    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if symbols is not None:
        updates.append("symbols = ?")
        values.append(json.dumps(symbols))
    if weights is not None:
        updates.append("weights = ?")
        values.append(json.dumps(weights))
    if total_value is not None:
        updates.append("total_value = ?")
        values.append(total_value)
    if expected_return is not None:
        updates.append("expected_return = ?")
        values.append(expected_return)
    if volatility is not None:
        updates.append("volatility = ?")
        values.append(volatility)
    if sharpe_ratio is not None:
        updates.append("sharpe_ratio = ?")
        values.append(sharpe_ratio)
    if objective is not None:
        updates.append("objective = ?")
        values.append(objective)
    if period is not None:
        updates.append("period = ?")
        values.append(period)
    if allocation is not None:
        updates.append("allocation = ?")
        values.append(json.dumps(allocation))

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(portfolio_id)

    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE portfolios 
            SET {', '.join(updates)}
            WHERE id = ?
        """,
            tuple(values),
        )

    return True


def delete_portfolio(portfolio_id: int) -> bool:
    """
    Delete a portfolio

    Args:
        portfolio_id: Portfolio ID

    Returns:
        True if portfolio was deleted
    """
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
        return cursor.rowcount > 0


def count_user_portfolios(clerk_id: str) -> int:
    """
    Count total portfolios for a user

    Args:
        clerk_id: User's Clerk ID

    Returns:
        Number of portfolios
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) as count FROM portfolios WHERE clerk_id = ?
        """,
            (clerk_id,),
        )

        row = cursor.fetchone()
        return row["count"] if row else 0


if __name__ == "__main__":
    # Test the table creation
    create_portfolios_table()

    # Test portfolio operations
    test_clerk_id = "user_test123"

    # Insert test portfolio
    portfolio_id = insert_portfolio(
        clerk_id=test_clerk_id,
        name="My Crypto Portfolio",
        symbols=["BTC", "ETH", "SOL"],
        weights={"BTC": 0.5, "ETH": 0.3, "SOL": 0.2},
        total_value=100000.0,
        expected_return=0.25,
        volatility=0.35,
        sharpe_ratio=1.5,
        objective="max_sharpe",
        period="1y",
    )
    print(f"✓ Created test portfolio with ID: {portfolio_id}")

    # Get portfolio
    portfolio = get_portfolio_by_id(portfolio_id)
    print(f"✓ Retrieved portfolio: {portfolio['name']}")

    # Get user portfolios
    portfolios = get_portfolios_by_user(test_clerk_id)
    print(f"✓ User has {len(portfolios)} portfolio(s)")

    # Update portfolio
    update_portfolio(portfolio_id, name="Updated Portfolio Name")
    portfolio = get_portfolio_by_id(portfolio_id)
    print(f"✓ Updated portfolio name: {portfolio['name']}")

    # Delete test portfolio
    delete_portfolio(portfolio_id)
    print(f"✓ Deleted test portfolio")
