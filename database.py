"""
Database module for managing users, messages, and subscriptions.
Uses SQLite for local persistence.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database handler for the bot."""
    
    def __init__(self, db_path: str = "bot_data.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Messages table (chat history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Payments table (for tracking Robokassa payments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_id TEXT UNIQUE,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database tables initialized.")
    
    def create_user(self, user_id: int, name: str) -> None:
        """Create a new user if not exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
                (user_id, name)
            )
            conn.commit()
            logger.info(f"User {user_id} created or already exists.")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
        finally:
            conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def save_message(self, user_id: int, role: str, content: str) -> None:
        """Save a message to the conversation history."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )
            conn.commit()
            logger.info(f"Message saved for user {user_id}.")
        except Exception as e:
            logger.error(f"Error saving message: {e}")
        finally:
            conn.close()
    
    def get_user_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get conversation history for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT role, content, timestamp FROM messages 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            # Reverse to get chronological order
            return [dict(row) for row in reversed(rows)]
        finally:
            conn.close()
    
    def clear_user_history(self, user_id: int) -> None:
        """Clear all messages for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"History cleared for user {user_id}.")
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
        finally:
            conn.close()
    
    def create_subscription(self, user_id: int, days: int = 30) -> None:
        """Create or update a subscription for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            expires_at = datetime.now() + timedelta(days=days)
            
            cursor.execute(
                """INSERT INTO subscriptions (user_id, expires_at, status) 
                   VALUES (?, ?, 'active')
                   ON CONFLICT(user_id) DO UPDATE SET 
                   expires_at = ?, status = 'active'""",
                (user_id, expires_at, expires_at)
            )
            conn.commit()
            logger.info(f"Subscription created for user {user_id}, expires at {expires_at}.")
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
        finally:
            conn.close()
    
    def is_user_subscribed(self, user_id: int) -> bool:
        """Check if user has active subscription."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT * FROM subscriptions 
                   WHERE user_id = ? AND status = 'active' AND expires_at > datetime('now')""",
                (user_id,)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def get_subscription(self, user_id: int) -> Optional[Dict]:
        """Get subscription details for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def save_payment(self, user_id: int, transaction_id: str, amount: float) -> None:
        """Save payment record."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO payments (user_id, transaction_id, amount, status) 
                   VALUES (?, ?, ?, 'pending')""",
                (user_id, transaction_id, amount)
            )
            conn.commit()
            logger.info(f"Payment saved for user {user_id}, transaction {transaction_id}.")
        except Exception as e:
            logger.error(f"Error saving payment: {e}")
        finally:
            conn.close()
    
    def complete_payment(self, transaction_id: str, days: int = 30) -> bool:
        """Mark payment as completed and activate subscription."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get user_id from payment
            cursor.execute(
                "SELECT user_id FROM payments WHERE transaction_id = ?",
                (transaction_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"Payment not found: {transaction_id}")
                return False
            
            user_id = row[0]
            
            # Update payment status
            cursor.execute(
                """UPDATE payments SET status = 'completed', completed_at = datetime('now') 
                   WHERE transaction_id = ?""",
                (transaction_id,)
            )
            
            # Create or update subscription
            expires_at = datetime.now() + timedelta(days=days)
            cursor.execute(
                """INSERT INTO subscriptions (user_id, expires_at, status) 
                   VALUES (?, ?, 'active')
                   ON CONFLICT(user_id) DO UPDATE SET 
                   expires_at = ?, status = 'active'""",
                (user_id, expires_at, expires_at)
            )
            
            conn.commit()
            logger.info(f"Payment completed for user {user_id}.")
            return True
        except Exception as e:
            logger.error(f"Error completing payment: {e}")
            return False
        finally:
            conn.close()
    
    def get_payment(self, transaction_id: str) -> Optional[Dict]:
        """Get payment details."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM payments WHERE transaction_id = ?",
                (transaction_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
