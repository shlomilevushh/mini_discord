import sqlite3
import os
from contextlib import contextmanager

# Get the database path - store it in the backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "mini_discord.db")

def init_database():
    """Initialize the database and create tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table with new fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT NOT NULL,
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
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
    finally:
        conn.close()

def create_user(email: str, username: str, password: str, avatar: str) -> dict:
    """
    Create a new user in the database
    Returns: dict with success status and message
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, username, password, avatar) VALUES (?, ?, ?, ?)",
                (email, username, password, avatar)
            )
            conn.commit()
            return {
                "success": True,
                "message": f"User '{username}' registered successfully!"
            }
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "email" in error_msg.lower():
            return {
                "success": False,
                "message": f"Email '{email}' is already registered!"
            }
        elif "username" in error_msg.lower():
            return {
                "success": False,
                "message": f"Username '{username}' is already taken!"
            }
        else:
            return {
                "success": False,
                "message": "Email or username already exists!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating user: {str(e)}"
        }

def verify_user(email: str, password: str) -> dict:
    """
    Verify user credentials using email and password
    Returns: dict with success status, message, and user data
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, username, avatar FROM users WHERE email = ? AND password = ?",
                (email, password)
            )
            user = cursor.fetchone()
            
            if user:
                return {
                    "success": True,
                    "message": f"Welcome back, {user['username']}!",
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "username": user['username'],
                        "avatar": user['avatar']
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Invalid email or password!"
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error verifying user: {str(e)}"
        }

def get_user_by_id(user_id: int) -> dict:
    """Get user by ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, username, avatar FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            if user:
                return dict(user)
            return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def get_user_by_username(username: str) -> dict:
    """Get user by username"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, username, avatar FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            if user:
                return dict(user)
            return None
    except Exception as e:
        print(f"Error getting user by username: {e}")
        return None

def send_friend_request(sender_id: int, receiver_username: str) -> dict:
    """Send a friend request to another user by username"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get receiver by username
            receiver = get_user_by_username(receiver_username)
            if not receiver:
                return {
                    "success": False,
                    "message": f"User '{receiver_username}' not found!"
                }
            
            receiver_id = receiver['id']
            
            # Can't send request to yourself
            if sender_id == receiver_id:
                return {
                    "success": False,
                    "message": "You can't send a friend request to yourself!"
                }
            
            # Check if already friends
            cursor.execute("""
                SELECT * FROM friendships 
                WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
            """, (sender_id, receiver_id, receiver_id, sender_id))
            
            if cursor.fetchone():
                return {
                    "success": False,
                    "message": f"You are already friends with {receiver_username}!"
                }
            
            # Check if pending request already exists
            cursor.execute("""
                SELECT * FROM friend_requests 
                WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
                AND status = 'pending'
            """, (sender_id, receiver_id, receiver_id, sender_id))
            
            existing_request = cursor.fetchone()
            if existing_request:
                return {
                    "success": False,
                    "message": "Friend request already exists!"
                }
            
            # Create friend request
            cursor.execute(
                "INSERT INTO friend_requests (sender_id, receiver_id, status) VALUES (?, ?, 'pending')",
                (sender_id, receiver_id)
            )
            conn.commit()
            
            return {
                "success": True,
                "message": f"Friend request sent to {receiver_username}!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending friend request: {str(e)}"
        }

def get_pending_friend_requests(user_id: int) -> list:
    """Get all pending friend requests for a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fr.id, fr.sender_id, u.username, u.avatar, fr.created_at
                FROM friend_requests fr
                JOIN users u ON fr.sender_id = u.id
                WHERE fr.receiver_id = ? AND fr.status = 'pending'
                ORDER BY fr.created_at DESC
            """, (user_id,))
            
            requests = cursor.fetchall()
            return [dict(req) for req in requests]
    except Exception as e:
        print(f"Error getting friend requests: {e}")
        return []

def accept_friend_request(request_id: int, user_id: int) -> dict:
    """Accept a friend request"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get the request
            cursor.execute(
                "SELECT * FROM friend_requests WHERE id = ? AND receiver_id = ? AND status = 'pending'",
                (request_id, user_id)
            )
            request = cursor.fetchone()
            
            if not request:
                return {
                    "success": False,
                    "message": "Friend request not found!"
                }
            
            sender_id = request['sender_id']
            receiver_id = request['receiver_id']
            
            # Create friendship (always store smaller ID first for consistency)
            user1_id = min(sender_id, receiver_id)
            user2_id = max(sender_id, receiver_id)
            
            cursor.execute(
                "INSERT INTO friendships (user1_id, user2_id) VALUES (?, ?)",
                (user1_id, user2_id)
            )
            
            # Update request status
            cursor.execute(
                "UPDATE friend_requests SET status = 'accepted' WHERE id = ?",
                (request_id,)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Friend request accepted!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error accepting friend request: {str(e)}"
        }

def decline_friend_request(request_id: int, user_id: int) -> dict:
    """Decline a friend request - deletes it completely from the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verify the request belongs to this user
            cursor.execute(
                "SELECT * FROM friend_requests WHERE id = ? AND receiver_id = ? AND status = 'pending'",
                (request_id, user_id)
            )
            request = cursor.fetchone()
            
            if not request:
                return {
                    "success": False,
                    "message": "Friend request not found!"
                }
            
            # Delete the friend request completely
            cursor.execute(
                "DELETE FROM friend_requests WHERE id = ?",
                (request_id,)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Friend request declined."
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error declining friend request: {str(e)}"
        }

def get_friends(user_id: int) -> list:
    """Get all friends for a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.avatar
                FROM friendships f
                JOIN users u ON (
                    CASE 
                        WHEN f.user1_id = ? THEN u.id = f.user2_id
                        WHEN f.user2_id = ? THEN u.id = f.user1_id
                    END
                )
                WHERE f.user1_id = ? OR f.user2_id = ?
                ORDER BY u.username
            """, (user_id, user_id, user_id, user_id))
            
            friends = cursor.fetchall()
            return [dict(friend) for friend in friends]
    except Exception as e:
        print(f"Error getting friends: {e}")
        return []

def get_all_users() -> list:
    """Get all users (for debugging)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, username, avatar, created_at FROM users")
            users = cursor.fetchall()
            return [dict(user) for user in users]
    except Exception as e:
        print(f"Error getting users: {e}")
        return []
