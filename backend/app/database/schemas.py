"""Database schemas and initialization"""
import sqlite3
from .connection import DB_PATH


def init_database():
    """Initialize the database and create tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Migration: Add channel_type column if it doesn't exist
    try:
        cursor.execute("SELECT channel_type FROM channels LIMIT 1")
    except sqlite3.OperationalError:
        # Column doesn't exist, add it
        print("Adding channel_type column to channels table...")
        cursor.execute("ALTER TABLE channels ADD COLUMN channel_type TEXT NOT NULL DEFAULT 'voice'")
        conn.commit()
        print("Migration completed!")
    
    # Create users table with new fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'offline',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create friend_requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id),
            UNIQUE(sender_id, receiver_id)
        )
    """)
    
    # Create friendships table (accepted friends)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users(id),
            FOREIGN KEY (user2_id) REFERENCES users(id),
            UNIQUE(user1_id, user2_id)
        )
    """)
    
    # Create messages table for private chats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    """)
    
    # Create servers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)
    
    # Create server_members table (all users in a server)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(server_id, user_id)
        )
    """)
    
    # Create server_invites table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
            FOREIGN KEY (from_user_id) REFERENCES users(id),
            FOREIGN KEY (to_user_id) REFERENCES users(id),
            UNIQUE(server_id, to_user_id)
        )
    """)
    
    # Create channels table (voice or text channels)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            channel_type TEXT NOT NULL DEFAULT 'voice',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
            UNIQUE(server_id, name)
        )
    """)
    
    # Create channel_members table (users currently in a channel)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(channel_id, user_id)
        )
    """)
    
    # Create channel_messages table (messages in channels)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")
