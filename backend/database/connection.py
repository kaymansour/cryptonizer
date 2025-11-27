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
    conn = sqlite3.connect(
        DB_PATH, 
        timeout=30.0,
        isolation_level=None,  # Autocommit mode for better concurrency
        check_same_thread=False  # Allow sharing connections across threads
    )
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Enable WAL mode for better concurrency (allows multiple readers with one writer)
    conn.execute("PRAGMA journal_mode=WAL")
    # Optimize for performance
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    conn.execute("PRAGMA temp_store=MEMORY")
    
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
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        yield cursor
        # Explicit commit (even though we're in autocommit mode)
        if conn:
            conn.commit()
    except Exception as e:
        # Rollback on error
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise e
    finally:
        # Always close cursor and connection, even if errors occur
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


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
    from database.models import create_users_table
    
    # Create all tables
    create_users_table()
    
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
