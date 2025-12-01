"""
Investment Preferences Table Model
Stores user's investment strategy preferences for each portfolio
"""

import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database.connection import get_db_cursor
from typing import Optional, Dict, List
from datetime import datetime
import json


def create_investment_preferences_table():
    """
    Create the investment_preferences table to store ML config and strategy preferences

    Schema:
    - id: Auto-incrementing primary key
    - portfolio_id: Foreign key to portfolios table
    - trading_frequency: passive/moderate/active
    - loss_tolerance: low/medium/high
    - profit_taking: quick/balanced/patient
    - investment_horizon: short/medium/long
    - signal_threshold: ML signal threshold (default 2.0)
    - max_position_size: Maximum position size (default 0.6)
    - rsi_oversold: RSI oversold level (default 25)
    - rsi_overbought: RSI overbought level (default 60)
    - stop_loss_pct: Stop loss percentage (default 0.03)
    - trailing_stop_pct: Trailing stop percentage (default 0.05)
    - trade_cooldown_periods: Cooldown periods between trades (default 6)
    - take_profit_levels: JSON array of take profit levels
    - interval: Trading interval (1h/4h)
    - use_trend_filter: Whether to use trend filtering
    - use_rsi_filter: Whether to use RSI filtering
    - use_volume_filter: Whether to use volume filtering
    - created_at: Preferences creation timestamp
    - updated_at: Last update timestamp
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS investment_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                trading_frequency TEXT,
                loss_tolerance TEXT,
                profit_taking TEXT,
                investment_horizon TEXT,
                signal_threshold REAL DEFAULT 2.0,
                max_position_size REAL DEFAULT 0.6,
                rsi_oversold REAL DEFAULT 25,
                rsi_overbought REAL DEFAULT 60,
                stop_loss_pct REAL DEFAULT 0.03,
                trailing_stop_pct REAL DEFAULT 0.05,
                trade_cooldown_periods INTEGER DEFAULT 6,
                take_profit_levels TEXT,
                interval TEXT DEFAULT '4h',
                use_trend_filter INTEGER DEFAULT 1,
                use_rsi_filter INTEGER DEFAULT 1,
                use_volume_filter INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """
        )

        # Create indexes for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_investment_preferences_portfolio_id 
            ON investment_preferences(portfolio_id)
        """
        )

    print("✓ Investment preferences table created")


def insert_investment_preferences(
    portfolio_id: int,
    trading_frequency: Optional[str] = None,
    loss_tolerance: Optional[str] = None,
    profit_taking: Optional[str] = None,
    investment_horizon: Optional[str] = None,
    signal_threshold: float = 2.0,
    max_position_size: float = 0.6,
    rsi_oversold: float = 25,
    rsi_overbought: float = 60,
    stop_loss_pct: float = 0.03,
    trailing_stop_pct: float = 0.05,
    trade_cooldown_periods: int = 6,
    take_profit_levels: Optional[List[float]] = None,
    interval: str = "4h",
    use_trend_filter: bool = True,
    use_rsi_filter: bool = True,
    use_volume_filter: bool = True,
) -> int:
    """
    Insert investment preferences for a portfolio

    Args:
        portfolio_id: Portfolio ID
        trading_frequency: passive/moderate/active
        loss_tolerance: low/medium/high
        profit_taking: quick/balanced/patient
        investment_horizon: short/medium/long
        signal_threshold: ML signal threshold
        max_position_size: Maximum position size
        rsi_oversold: RSI oversold level
        rsi_overbought: RSI overbought level
        stop_loss_pct: Stop loss percentage
        trailing_stop_pct: Trailing stop percentage
        trade_cooldown_periods: Cooldown periods
        take_profit_levels: List of take profit levels
        interval: Trading interval
        use_trend_filter: Use trend filtering
        use_rsi_filter: Use RSI filtering
        use_volume_filter: Use volume filtering

    Returns:
        Preference ID
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO investment_preferences (
                portfolio_id, trading_frequency, loss_tolerance, profit_taking,
                investment_horizon, signal_threshold, max_position_size,
                rsi_oversold, rsi_overbought, stop_loss_pct, trailing_stop_pct,
                trade_cooldown_periods, take_profit_levels, interval,
                use_trend_filter, use_rsi_filter, use_volume_filter
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                portfolio_id,
                trading_frequency,
                loss_tolerance,
                profit_taking,
                investment_horizon,
                signal_threshold,
                max_position_size,
                rsi_oversold,
                rsi_overbought,
                stop_loss_pct,
                trailing_stop_pct,
                trade_cooldown_periods,
                (
                    json.dumps(take_profit_levels)
                    if take_profit_levels
                    else json.dumps([0.03, 0.05, 0.08])
                ),
                interval,
                1 if use_trend_filter else 0,
                1 if use_rsi_filter else 0,
                1 if use_volume_filter else 0,
            ),
        )

        preference_id = cursor.lastrowid

    print(f"✓ Investment preferences created with ID: {preference_id}")
    return preference_id


def get_preferences_by_portfolio_id(portfolio_id: int) -> Optional[Dict]:
    """
    Get investment preferences for a portfolio

    Args:
        portfolio_id: Portfolio ID

    Returns:
        Preferences dict or None if not found
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM investment_preferences WHERE portfolio_id = ?
        """,
            (portfolio_id,),
        )

        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "portfolio_id": row["portfolio_id"],
                "trading_frequency": row["trading_frequency"],
                "loss_tolerance": row["loss_tolerance"],
                "profit_taking": row["profit_taking"],
                "investment_horizon": row["investment_horizon"],
                "signal_threshold": row["signal_threshold"],
                "max_position_size": row["max_position_size"],
                "rsi_oversold": row["rsi_oversold"],
                "rsi_overbought": row["rsi_overbought"],
                "stop_loss_pct": row["stop_loss_pct"],
                "trailing_stop_pct": row["trailing_stop_pct"],
                "trade_cooldown_periods": row["trade_cooldown_periods"],
                "take_profit_levels": (
                    json.loads(row["take_profit_levels"])
                    if row["take_profit_levels"]
                    else [0.03, 0.05, 0.08]
                ),
                "interval": row["interval"],
                "use_trend_filter": bool(row["use_trend_filter"]),
                "use_rsi_filter": bool(row["use_rsi_filter"]),
                "use_volume_filter": bool(row["use_volume_filter"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        return None


def update_investment_preferences(
    portfolio_id: int,
    trading_frequency: Optional[str] = None,
    loss_tolerance: Optional[str] = None,
    profit_taking: Optional[str] = None,
    investment_horizon: Optional[str] = None,
    signal_threshold: Optional[float] = None,
    max_position_size: Optional[float] = None,
    rsi_oversold: Optional[float] = None,
    rsi_overbought: Optional[float] = None,
    stop_loss_pct: Optional[float] = None,
    trailing_stop_pct: Optional[float] = None,
    trade_cooldown_periods: Optional[int] = None,
    take_profit_levels: Optional[List[float]] = None,
    interval: Optional[str] = None,
    use_trend_filter: Optional[bool] = None,
    use_rsi_filter: Optional[bool] = None,
    use_volume_filter: Optional[bool] = None,
) -> bool:
    """
    Update investment preferences for a portfolio

    Args:
        portfolio_id: Portfolio ID
        **kwargs: Fields to update

    Returns:
        True if preferences were updated
    """
    updates = []
    values = []

    if trading_frequency is not None:
        updates.append("trading_frequency = ?")
        values.append(trading_frequency)
    if loss_tolerance is not None:
        updates.append("loss_tolerance = ?")
        values.append(loss_tolerance)
    if profit_taking is not None:
        updates.append("profit_taking = ?")
        values.append(profit_taking)
    if investment_horizon is not None:
        updates.append("investment_horizon = ?")
        values.append(investment_horizon)
    if signal_threshold is not None:
        updates.append("signal_threshold = ?")
        values.append(signal_threshold)
    if max_position_size is not None:
        updates.append("max_position_size = ?")
        values.append(max_position_size)
    if rsi_oversold is not None:
        updates.append("rsi_oversold = ?")
        values.append(rsi_oversold)
    if rsi_overbought is not None:
        updates.append("rsi_overbought = ?")
        values.append(rsi_overbought)
    if stop_loss_pct is not None:
        updates.append("stop_loss_pct = ?")
        values.append(stop_loss_pct)
    if trailing_stop_pct is not None:
        updates.append("trailing_stop_pct = ?")
        values.append(trailing_stop_pct)
    if trade_cooldown_periods is not None:
        updates.append("trade_cooldown_periods = ?")
        values.append(trade_cooldown_periods)
    if take_profit_levels is not None:
        updates.append("take_profit_levels = ?")
        values.append(json.dumps(take_profit_levels))
    if interval is not None:
        updates.append("interval = ?")
        values.append(interval)
    if use_trend_filter is not None:
        updates.append("use_trend_filter = ?")
        values.append(1 if use_trend_filter else 0)
    if use_rsi_filter is not None:
        updates.append("use_rsi_filter = ?")
        values.append(1 if use_rsi_filter else 0)
    if use_volume_filter is not None:
        updates.append("use_volume_filter = ?")
        values.append(1 if use_volume_filter else 0)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(portfolio_id)

    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE investment_preferences 
            SET {', '.join(updates)}
            WHERE portfolio_id = ?
        """,
            tuple(values),
        )

    return True


def delete_preferences(portfolio_id: int) -> bool:
    """
    Delete investment preferences for a portfolio

    Args:
        portfolio_id: Portfolio ID

    Returns:
        True if preferences were deleted
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM investment_preferences WHERE portfolio_id = ?", (portfolio_id,)
        )
        return cursor.rowcount > 0


if __name__ == "__main__":
    # Test the table creation
    create_investment_preferences_table()

    # Test preferences operations (requires a portfolio to exist)
    test_portfolio_id = 1

    # Insert test preferences
    pref_id = insert_investment_preferences(
        portfolio_id=test_portfolio_id,
        trading_frequency="moderate",
        loss_tolerance="medium",
        profit_taking="balanced",
        investment_horizon="medium",
        signal_threshold=2.0,
        max_position_size=0.6,
        take_profit_levels=[0.05, 0.10, 0.15],
    )
    print(f"✓ Created test preferences with ID: {pref_id}")

    # Get preferences
    prefs = get_preferences_by_portfolio_id(test_portfolio_id)
    print(f"✓ Retrieved preferences: {prefs['trading_frequency']}")

    # Update preferences
    update_investment_preferences(test_portfolio_id, trading_frequency="active")
    prefs = get_preferences_by_portfolio_id(test_portfolio_id)
    print(f"✓ Updated trading frequency: {prefs['trading_frequency']}")

    # Delete test preferences
    delete_preferences(test_portfolio_id)
    print(f"✓ Deleted test preferences")
