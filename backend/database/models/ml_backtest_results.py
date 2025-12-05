"""
ML Backtest Results Table Model
Stores ML trading backtest results and configurations
"""

import os
import sys
import json

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database.connection import get_db_cursor
from typing import Optional, Dict, List
from datetime import datetime


def create_ml_backtest_results_table():
    """
    Create the ml_backtest_results table to store ML trading backtest results

    Schema:
    - id: Auto-incrementing primary key
    - clerk_id: Foreign key to users table
    - portfolio_id: Optional foreign key to portfolios table (can be standalone)
    - name: User-defined name for this backtest result
    - symbols: JSON array of cryptocurrency symbols
    - weights: JSON object of symbol->weight mappings
    - initial_investment: Starting capital

    -- Backtest Results --
    - final_value: Final portfolio value after backtest
    - total_return: Total return percentage
    - annualized_return: Annualized return percentage
    - volatility: Portfolio volatility
    - sharpe_ratio: Sharpe ratio
    - max_drawdown: Maximum drawdown percentage
    - total_trades: Number of trades executed
    - buy_trades: Number of buy trades
    - sell_trades: Number of sell trades
    - win_rate: Win rate percentage
    - total_realized_pnl: Total realized profit/loss

    -- Per-Symbol Results --
    - symbol_results: JSON object with per-symbol performance data

    -- ML Configuration --
    - interval: Trading interval (1d, 4h, 1h)
    - signal_threshold: ML signal threshold
    - max_position_size: Maximum position size
    - min_confidence: Minimum confidence threshold
    - rsi_oversold: RSI oversold level
    - rsi_overbought: RSI overbought level
    - stop_loss_pct: Stop loss percentage
    - trailing_stop_pct: Trailing stop percentage
    - trade_cooldown_periods: Cooldown periods between trades
    - required_confirmations: Required signal confirmations

    -- Time Period --
    - start_date: Backtest start date
    - end_date: Backtest end date
    - backtest_period: Period label (1m, 3m, 6m, 1y, 2y)

    - created_at: Result creation timestamp
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ml_backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clerk_id TEXT NOT NULL,
                portfolio_id INTEGER,
                name TEXT NOT NULL,
                symbols TEXT NOT NULL,
                weights TEXT NOT NULL,
                initial_investment REAL NOT NULL,
                
                -- Backtest Results --
                final_value REAL,
                total_return REAL,
                annualized_return REAL,
                volatility REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                total_trades INTEGER,
                buy_trades INTEGER,
                sell_trades INTEGER,
                win_rate REAL,
                total_realized_pnl REAL,
                avg_win REAL,
                avg_loss REAL,
                take_profit_trades INTEGER,
                stop_loss_trades INTEGER,
                trailing_stop_trades INTEGER,
                
                -- Per-Symbol Results --
                symbol_results TEXT,
                
                -- Trade History (JSON array) --
                trade_history TEXT,
                
                -- ML Configuration --
                interval TEXT DEFAULT '1d',
                signal_threshold REAL DEFAULT 1.5,
                max_position_size REAL DEFAULT 0.6,
                min_confidence REAL DEFAULT 0.35,
                rsi_oversold REAL DEFAULT 25,
                rsi_overbought REAL DEFAULT 60,
                stop_loss_pct REAL DEFAULT 0.03,
                trailing_stop_pct REAL DEFAULT 0.05,
                trade_cooldown_periods INTEGER DEFAULT 6,
                required_confirmations INTEGER DEFAULT 2,
                use_trend_filter INTEGER DEFAULT 1,
                use_rsi_filter INTEGER DEFAULT 1,
                use_volume_filter INTEGER DEFAULT 1,
                
                -- Time Period --
                start_date TEXT,
                end_date TEXT,
                backtest_period TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (clerk_id) REFERENCES users(clerk_id) ON DELETE CASCADE,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE SET NULL
            )
            """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ml_backtest_results_clerk_id 
            ON ml_backtest_results(clerk_id)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ml_backtest_results_portfolio_id 
            ON ml_backtest_results(portfolio_id)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ml_backtest_results_created_at 
            ON ml_backtest_results(created_at DESC)
            """
        )

    print("✓ ML Backtest Results table created")


def insert_ml_backtest_result(
    clerk_id: str,
    name: str,
    symbols: List[str],
    weights: Dict[str, float],
    initial_investment: float,
    # Backtest Results
    final_value: Optional[float] = None,
    total_return: Optional[float] = None,
    annualized_return: Optional[float] = None,
    volatility: Optional[float] = None,
    sharpe_ratio: Optional[float] = None,
    max_drawdown: Optional[float] = None,
    total_trades: Optional[int] = None,
    buy_trades: Optional[int] = None,
    sell_trades: Optional[int] = None,
    win_rate: Optional[float] = None,
    total_realized_pnl: Optional[float] = None,
    avg_win: Optional[float] = None,
    avg_loss: Optional[float] = None,
    take_profit_trades: Optional[int] = None,
    stop_loss_trades: Optional[int] = None,
    trailing_stop_trades: Optional[int] = None,
    # Per-Symbol Results
    symbol_results: Optional[Dict] = None,
    # Trade History
    trade_history: Optional[List[Dict]] = None,
    # ML Configuration
    interval: str = "1d",
    signal_threshold: float = 1.5,
    max_position_size: float = 0.6,
    min_confidence: float = 0.35,
    rsi_oversold: float = 25,
    rsi_overbought: float = 60,
    stop_loss_pct: float = 0.03,
    trailing_stop_pct: float = 0.05,
    trade_cooldown_periods: int = 6,
    required_confirmations: int = 2,
    use_trend_filter: bool = True,
    use_rsi_filter: bool = True,
    use_volume_filter: bool = True,
    # Time Period
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    backtest_period: Optional[str] = None,
    # Optional portfolio link
    portfolio_id: Optional[int] = None,
) -> int:
    """
    Insert a new ML backtest result

    Args:
        clerk_id: Clerk user ID
        name: User-defined name for this backtest
        symbols: List of cryptocurrency symbols
        weights: Dictionary of symbol->weight mappings
        initial_investment: Starting capital
        ... (backtest results and config)

    Returns:
        ID of the inserted backtest result
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ml_backtest_results (
                clerk_id, portfolio_id, name, symbols, weights, initial_investment,
                final_value, total_return, annualized_return, volatility, sharpe_ratio,
                max_drawdown, total_trades, buy_trades, sell_trades, win_rate,
                total_realized_pnl, avg_win, avg_loss, take_profit_trades,
                stop_loss_trades, trailing_stop_trades,
                symbol_results, trade_history,
                interval, signal_threshold, max_position_size, min_confidence,
                rsi_oversold, rsi_overbought, stop_loss_pct, trailing_stop_pct,
                trade_cooldown_periods, required_confirmations,
                use_trend_filter, use_rsi_filter, use_volume_filter,
                start_date, end_date, backtest_period
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clerk_id,
                portfolio_id,
                name,
                json.dumps(symbols),
                json.dumps(weights),
                initial_investment,
                final_value,
                total_return,
                annualized_return,
                volatility,
                sharpe_ratio,
                max_drawdown,
                total_trades,
                buy_trades,
                sell_trades,
                win_rate,
                total_realized_pnl,
                avg_win,
                avg_loss,
                take_profit_trades,
                stop_loss_trades,
                trailing_stop_trades,
                json.dumps(symbol_results) if symbol_results else None,
                json.dumps(trade_history) if trade_history else None,
                interval,
                signal_threshold,
                max_position_size,
                min_confidence,
                rsi_oversold,
                rsi_overbought,
                stop_loss_pct,
                trailing_stop_pct,
                trade_cooldown_periods,
                required_confirmations,
                1 if use_trend_filter else 0,
                1 if use_rsi_filter else 0,
                1 if use_volume_filter else 0,
                start_date,
                end_date,
                backtest_period,
            ),
        )
        return cursor.lastrowid


def get_ml_backtest_result_by_id(result_id: int) -> Optional[Dict]:
    """
    Get an ML backtest result by ID

    Args:
        result_id: Backtest result ID

    Returns:
        Dictionary with backtest result data or None if not found
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM ml_backtest_results WHERE id = ?",
            (result_id,),
        )
        row = cursor.fetchone()

        if row:
            result = dict(row)
            # Parse JSON fields
            result["symbols"] = json.loads(result["symbols"])
            result["weights"] = json.loads(result["weights"])
            if result["symbol_results"]:
                result["symbol_results"] = json.loads(result["symbol_results"])
            if result["trade_history"]:
                result["trade_history"] = json.loads(result["trade_history"])
            # Convert boolean flags
            result["use_trend_filter"] = bool(result["use_trend_filter"])
            result["use_rsi_filter"] = bool(result["use_rsi_filter"])
            result["use_volume_filter"] = bool(result["use_volume_filter"])
            return result

        return None


def get_ml_backtest_results_by_user(
    clerk_id: str, limit: int = 50, offset: int = 0
) -> List[Dict]:
    """
    Get all ML backtest results for a user

    Args:
        clerk_id: Clerk user ID
        limit: Maximum number of results to return
        offset: Offset for pagination

    Returns:
        List of backtest result dictionaries
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM ml_backtest_results 
            WHERE clerk_id = ? 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (clerk_id, limit, offset),
        )
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            result["symbols"] = json.loads(result["symbols"])
            result["weights"] = json.loads(result["weights"])
            if result["symbol_results"]:
                result["symbol_results"] = json.loads(result["symbol_results"])
            # Don't include full trade history in list view for performance
            result["trade_history"] = None
            # Convert boolean flags
            result["use_trend_filter"] = bool(result["use_trend_filter"])
            result["use_rsi_filter"] = bool(result["use_rsi_filter"])
            result["use_volume_filter"] = bool(result["use_volume_filter"])
            results.append(result)

        return results


def get_ml_backtest_results_by_portfolio(portfolio_id: int) -> List[Dict]:
    """
    Get all ML backtest results linked to a specific portfolio

    Args:
        portfolio_id: Portfolio ID

    Returns:
        List of backtest result dictionaries
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM ml_backtest_results 
            WHERE portfolio_id = ? 
            ORDER BY created_at DESC
            """,
            (portfolio_id,),
        )
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(row)
            result["symbols"] = json.loads(result["symbols"])
            result["weights"] = json.loads(result["weights"])
            if result["symbol_results"]:
                result["symbol_results"] = json.loads(result["symbol_results"])
            result["trade_history"] = None  # Exclude for list view
            result["use_trend_filter"] = bool(result["use_trend_filter"])
            result["use_rsi_filter"] = bool(result["use_rsi_filter"])
            result["use_volume_filter"] = bool(result["use_volume_filter"])
            results.append(result)

        return results


def update_ml_backtest_result_name(result_id: int, name: str) -> bool:
    """
    Update the name of an ML backtest result

    Args:
        result_id: Backtest result ID
        name: New name

    Returns:
        True if updated successfully
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "UPDATE ml_backtest_results SET name = ? WHERE id = ?",
            (name, result_id),
        )
        return cursor.rowcount > 0


def delete_ml_backtest_result(result_id: int) -> bool:
    """
    Delete an ML backtest result

    Args:
        result_id: Backtest result ID

    Returns:
        True if deleted successfully
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM ml_backtest_results WHERE id = ?",
            (result_id,),
        )
        return cursor.rowcount > 0


def count_user_ml_backtest_results(clerk_id: str) -> int:
    """
    Count the number of ML backtest results for a user

    Args:
        clerk_id: Clerk user ID

    Returns:
        Number of backtest results
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM ml_backtest_results WHERE clerk_id = ?",
            (clerk_id,),
        )
        return cursor.fetchone()[0]


if __name__ == "__main__":
    # Test table creation
    create_ml_backtest_results_table()
