"""Database connection management"""
import sqlite3
import os
from contextlib import contextmanager

# Get the database path - store it in the backend folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "mini_discord.db")


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
    finally:
        conn.close()
