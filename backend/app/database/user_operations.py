"""User-related database operations"""
from .connection import get_db_connection


def create_user(email: str, username: str, password: str, avatar: str) -> dict:
    """Create a new user"""
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
                "message": f"Account created successfully! Welcome, {username}!"
            }
    except Exception as e:
        error_msg = str(e).lower()
        if "unique" in error_msg:
            if "email" in error_msg:
                return {
                    "success": False,
                    "message": "Email already exists!"
                }
            elif "username" in error_msg:
                return {
                    "success": False,
                    "message": "Username already taken!"
                }
        return {
            "success": False,
            "message": f"Error creating account: {str(e)}"
        }


def verify_user(email: str, password: str) -> dict:
    """Verify user credentials and return user info"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, username, avatar, status FROM users WHERE email = ? AND password = ?",
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
                        "avatar": user['avatar'],
                        "status": user['status'] if user['status'] else 'online'
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
                "SELECT id, email, username, avatar, status FROM users WHERE id = ?",
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
                "SELECT id, username, avatar FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            if user:
                return dict(user)
            return None
    except Exception as e:
        print(f"Error getting user by username: {e}")
        return None


def update_user_status(user_id: int, status: str) -> dict:
    """Update user status (online/offline/invisible)"""
    try:
        valid_statuses = ['online', 'offline', 'invisible']
        if status not in valid_statuses:
            return {
                "success": False,
                "message": "Invalid status!"
            }
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status = ? WHERE id = ?",
                (status, user_id)
            )
            conn.commit()
            
            return {
                "success": True,
                "message": f"Status updated to {status}"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating status: {str(e)}"
        }
