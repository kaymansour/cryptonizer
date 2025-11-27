"""
Example Model Template
Copy this file and rename it for your specific table

This is a template showing how to create a table in the database
"""

import sys
import os
# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.connection import get_db_cursor


def create_example_table():
    """
    Create the example table in the database
    
    Example schema:
    - id: Primary key
    - name: Text field
    - created_at: Timestamp
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS example (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes if needed
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_example_name 
            ON example(name)
        """)
    
    print("✓ Example table created")


def insert_example(name: str, value: float):
    """Insert a new record into example table"""
    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO example (name, value) VALUES (?, ?)",
            (name, value)
        )
        return cursor.lastrowid


def get_all_examples():
    """Get all records from example table"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM example")
        return cursor.fetchall()


if __name__ == "__main__":
    # Test the table creation
    create_example_table()
    
    # Test insert
    example_id = insert_example("test", 123.45)
    print(f"Inserted example with ID: {example_id}")
    
    # Test select
    results = get_all_examples()
    for row in results:
        print(dict(row))
