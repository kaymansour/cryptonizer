"""
SQLite Database Connection Manager
Handles database connections and initialization
"""

import sqlite3
import os
from typing import Optional
from contextlib import contextmanager


# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "crypto_portfolio.db")


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database

    Returns:
        sqlite3.Connection: Database connection with row factory enabled
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


@contextmanager
def get_db_cursor():
    """
    Context manager for database operations
    Automatically commits and closes connection

    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def close_db_connection(conn: sqlite3.Connection):
    """
    Close a database connection

    Args:
        conn: SQLite connection to close
    """
    if conn:
        conn.close()


def init_database():
    """
    Initialize the database by creating all tables
    This will be called on application startup
    """
    # Import all model modules to register their table creation
    from database.models.users import create_users_table
    from database.models.portfolios import create_portfolios_table
    from database.models.investment_preferences import (
        create_investment_preferences_table,
    )
    from database.models.ml_backtest_results import create_ml_backtest_results_table

    # Create all tables in order (users first, then portfolios, then preferences, then ml backtest results)
    create_users_table()
    create_portfolios_table()
    create_investment_preferences_table()
    create_ml_backtest_results_table()

    print(f"Database initialized at: {DB_PATH}")
    print("✓ All tables created successfully")


def database_exists() -> bool:
    """
    Check if the database file exists

    Returns:
        bool: True if database file exists
    """
    return os.path.exists(DB_PATH)


if __name__ == "__main__":
    # Test database connection
    init_database()

    with get_db_cursor() as cursor:
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"SQLite version: {version}")
        print(f"Database location: {DB_PATH}")
