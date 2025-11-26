"""
Users Table Model
Stores user information synced from Clerk authentication
"""

import sys
import os
# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.connection import get_db_cursor
from typing import Optional, Dict
from datetime import datetime


def create_users_table():
    """
    Create the users table to store Clerk user data
    
    Schema:
    - clerk_id: Unique Clerk user ID (primary key)
    - email: User email address
    - username: User's display name
    - first_name: User's first name
    - last_name: User's last name
    - profile_image_url: URL to user's profile image
    - email_verified: Whether email is verified
    - created_at: Account creation timestamp
    - updated_at: Last update timestamp
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                clerk_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                profile_image_url TEXT,
                email_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_clerk_id 
            ON users(clerk_id)
        """)
    
    print("✓ Users table created")


def insert_user(
    clerk_id: str,
    email: str,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    profile_image_url: Optional[str] = None,
    email_verified: bool = False
) -> str:
    """
    Insert a new user from Clerk webhook
    
    Args:
        clerk_id: Clerk user ID
        email: User email
        username: Display name
        first_name: First name
        last_name: Last name
        profile_image_url: Profile image URL
        email_verified: Email verification status
    
    Returns:
        clerk_id of inserted user
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO users (
                clerk_id, email, username, first_name, last_name, 
                profile_image_url, email_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            clerk_id,
            email,
            username,
            first_name,
            last_name,
            profile_image_url,
            1 if email_verified else 0
        ))
    
    return clerk_id


def update_user(
    clerk_id: str,
    email: Optional[str] = None,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    profile_image_url: Optional[str] = None,
    email_verified: Optional[bool] = None
) -> bool:
    """
    Update user information from Clerk webhook
    
    Args:
        clerk_id: Clerk user ID
        **kwargs: Fields to update
    
    Returns:
        True if user was updated
    """
    updates = []
    values = []
    
    if email is not None:
        updates.append("email = ?")
        values.append(email)
    if username is not None:
        updates.append("username = ?")
        values.append(username)
    if first_name is not None:
        updates.append("first_name = ?")
        values.append(first_name)
    if last_name is not None:
        updates.append("last_name = ?")
        values.append(last_name)
    if profile_image_url is not None:
        updates.append("profile_image_url = ?")
        values.append(profile_image_url)
    if email_verified is not None:
        updates.append("email_verified = ?")
        values.append(1 if email_verified else 0)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(clerk_id)
    
    with get_db_cursor() as cursor:
        cursor.execute(f"""
            UPDATE users 
            SET {', '.join(updates)}
            WHERE clerk_id = ?
        """, values)
    
    return True


def delete_user(clerk_id: str) -> bool:
    """
    Delete a user from Clerk webhook
    
    Args:
        clerk_id: Clerk user ID
    
    Returns:
        True if user was deleted
    """
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE clerk_id = ?", (clerk_id,))
        return cursor.rowcount > 0


def get_user_by_clerk_id(clerk_id: str) -> Optional[Dict]:
    """
    Get user by Clerk ID
    
    Args:
        clerk_id: Clerk user ID
    
    Returns:
        User dict or None if not found
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE clerk_id = ?", (clerk_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Get user by email
    
    Args:
        email: User email
    
    Returns:
        User dict or None if not found
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def user_exists(clerk_id: str) -> bool:
    """
    Check if user exists
    
    Args:
        clerk_id: Clerk user ID
    
    Returns:
        True if user exists
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM users WHERE clerk_id = ? LIMIT 1", (clerk_id,))
        return cursor.fetchone() is not None


def get_all_users() -> list:
    """
    Get all users
    
    Returns:
        List of user dicts
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # Test the table creation
    create_users_table()
    
    # Test user operations
    test_clerk_id = "user_test123"
    test_email = "test@example.com"
    
    # Insert test user
    insert_user(
        clerk_id=test_clerk_id,
        email=test_email,
        username="testuser",
        first_name="Test",
        last_name="User",
        email_verified=True
    )
    print(f"✓ Inserted test user: {test_clerk_id}")
    
    # Get user
    user = get_user_by_clerk_id(test_clerk_id)
    print(f"✓ Retrieved user: {user}")
    
    # Update user
    update_user(test_clerk_id, username="updateduser")
    user = get_user_by_clerk_id(test_clerk_id)
    print(f"✓ Updated user: {user['username']}")
    
    # Delete test user
    delete_user(test_clerk_id)
    print(f"✓ Deleted test user")
