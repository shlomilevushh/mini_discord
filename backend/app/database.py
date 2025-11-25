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
    
    # Create channels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            name TEXT NOT NULL,
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
                "SELECT id, email, username, avatar, status FROM users WHERE username = ?",
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

def update_user_status(user_id: int, status: str) -> dict:
    """Update user status (online, offline, invisible)"""
    try:
        valid_statuses = ['online', 'offline', 'invisible']
        if status not in valid_statuses:
            return {
                "success": False,
                "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
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

def get_friends_with_status(user_id: int) -> list:
    """Get all friends with their online status (respects invisible mode)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.avatar,
                    CASE 
                        WHEN u.status = 'invisible' THEN 'offline'
                        ELSE u.status
                    END as status
                FROM friendships f
                JOIN users u ON (
                    CASE 
                        WHEN f.user1_id = ? THEN u.id = f.user2_id
                        WHEN f.user2_id = ? THEN u.id = f.user1_id
                    END
                )
                WHERE f.user1_id = ? OR f.user2_id = ?
                ORDER BY 
                    CASE u.status 
                        WHEN 'online' THEN 1
                        WHEN 'invisible' THEN 2
                        WHEN 'offline' THEN 3
                    END,
                    u.username
            """, (user_id, user_id, user_id, user_id))
            
            friends = cursor.fetchall()
            return [dict(friend) for friend in friends]
    except Exception as e:
        print(f"Error getting friends with status: {e}")
        return []

def save_message(sender_id: int, receiver_id: int, message: str) -> dict:
    """Save a private message between two users"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)",
                (sender_id, receiver_id, message)
            )
            conn.commit()
            
            return {
                "success": True,
                "message_id": cursor.lastrowid
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error saving message: {str(e)}"
        }

def get_chat_history(user1_id: int, user2_id: int, limit: int = 50) -> list:
    """Get chat history between two users"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.sender_id, m.receiver_id, m.message, m.created_at,
                       u.username as sender_username, u.avatar as sender_avatar
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE (m.sender_id = ? AND m.receiver_id = ?) 
                   OR (m.sender_id = ? AND m.receiver_id = ?)
                ORDER BY m.created_at DESC
                LIMIT ?
            """, (user1_id, user2_id, user2_id, user1_id, limit))
            
            messages = cursor.fetchall()
            # Reverse to get chronological order (oldest first)
            return [dict(msg) for msg in reversed(messages)]
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []


# ============================================
# SERVER FUNCTIONS
# ============================================

def create_server(name: str, owner_id: int) -> dict:
    """Create a new server"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if server name already exists
            cursor.execute("SELECT id FROM servers WHERE name = ?", (name,))
            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Server name already exists!"
                }
            
            # Create server
            cursor.execute(
                "INSERT INTO servers (name, owner_id) VALUES (?, ?)",
                (name, owner_id)
            )
            server_id = cursor.lastrowid
            
            # Add owner as member
            cursor.execute(
                "INSERT INTO server_members (server_id, user_id) VALUES (?, ?)",
                (server_id, owner_id)
            )
            
            # Create default "general" channel
            cursor.execute(
                "INSERT INTO channels (server_id, name) VALUES (?, ?)",
                (server_id, "general")
            )
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"Server '{name}' created successfully!",
                "server_id": server_id
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating server: {str(e)}"
        }


def get_user_servers(user_id: int) -> list:
    """Get all servers a user is a member of"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, sm.joined_at,
                       (s.owner_id = ?) as is_owner
                FROM servers s
                JOIN server_members sm ON s.id = sm.server_id
                WHERE sm.user_id = ?
                ORDER BY sm.joined_at DESC
            """, (user_id, user_id))
            
            servers = cursor.fetchall()
            return [dict(server) for server in servers]
    except Exception as e:
        print(f"Error getting user servers: {e}")
        return []


def get_server_by_id(server_id: int) -> dict:
    """Get server details by ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM servers WHERE id = ?",
                (server_id,)
            )
            server = cursor.fetchone()
            if server:
                return dict(server)
            return None
    except Exception as e:
        print(f"Error getting server: {e}")
        return None


def send_server_invite(server_id: int, from_user_id: int, to_user_id: int) -> dict:
    """Send a server invitation"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if server exists and sender is the owner
            cursor.execute(
                "SELECT owner_id FROM servers WHERE id = ?",
                (server_id,)
            )
            server = cursor.fetchone()
            if not server:
                return {
                    "success": False,
                    "message": "Server not found!"
                }
            
            if server['owner_id'] != from_user_id:
                return {
                    "success": False,
                    "message": "Only server owner can invite users!"
                }
            
            # Check if user is already a member
            cursor.execute(
                "SELECT id FROM server_members WHERE server_id = ? AND user_id = ?",
                (server_id, to_user_id)
            )
            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "User is already a member of this server!"
                }
            
            # Check for pending invite
            cursor.execute(
                "SELECT id FROM server_invites WHERE server_id = ? AND to_user_id = ? AND status = 'pending'",
                (server_id, to_user_id)
            )
            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Invite already sent!"
                }
            
            # Send invite
            cursor.execute(
                "INSERT INTO server_invites (server_id, from_user_id, to_user_id) VALUES (?, ?, ?)",
                (server_id, from_user_id, to_user_id)
            )
            conn.commit()
            
            return {
                "success": True,
                "message": "Server invite sent!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending invite: {str(e)}"
        }


def get_pending_server_invites(user_id: int) -> list:
    """Get all pending server invites for a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT si.*, s.name as server_name, u.username as from_username, u.avatar as from_avatar
                FROM server_invites si
                JOIN servers s ON si.server_id = s.id
                JOIN users u ON si.from_user_id = u.id
                WHERE si.to_user_id = ? AND si.status = 'pending'
                ORDER BY si.created_at DESC
            """, (user_id,))
            
            invites = cursor.fetchall()
            return [dict(invite) for invite in invites]
    except Exception as e:
        print(f"Error getting server invites: {e}")
        return []


def accept_server_invite(invite_id: int, user_id: int) -> dict:
    """Accept a server invitation"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get invite details
            cursor.execute(
                "SELECT * FROM server_invites WHERE id = ? AND to_user_id = ? AND status = 'pending'",
                (invite_id, user_id)
            )
            invite = cursor.fetchone()
            
            if not invite:
                return {
                    "success": False,
                    "message": "Invite not found or already processed!"
                }
            
            # Add user to server
            cursor.execute(
                "INSERT INTO server_members (server_id, user_id) VALUES (?, ?)",
                (invite['server_id'], user_id)
            )
            
            # Update invite status
            cursor.execute(
                "UPDATE server_invites SET status = 'accepted' WHERE id = ?",
                (invite_id,)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Server invite accepted!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error accepting invite: {str(e)}"
        }


def decline_server_invite(invite_id: int, user_id: int) -> dict:
    """Decline a server invitation"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE server_invites SET status = 'declined' WHERE id = ? AND to_user_id = ? AND status = 'pending'",
                (invite_id, user_id)
            )
            
            if cursor.rowcount == 0:
                return {
                    "success": False,
                    "message": "Invite not found or already processed!"
                }
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Server invite declined!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error declining invite: {str(e)}"
        }


def create_channel(server_id: int, name: str, owner_id: int) -> dict:
    """Create a new channel in a server (owner only)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user is the server owner
            cursor.execute(
                "SELECT owner_id FROM servers WHERE id = ?",
                (server_id,)
            )
            server = cursor.fetchone()
            
            if not server:
                return {
                    "success": False,
                    "message": "Server not found!"
                }
            
            if server['owner_id'] != owner_id:
                return {
                    "success": False,
                    "message": "Only server owner can create channels!"
                }
            
            # Check if channel name already exists in this server
            cursor.execute(
                "SELECT id FROM channels WHERE server_id = ? AND name = ?",
                (server_id, name)
            )
            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Channel name already exists in this server!"
                }
            
            # Create channel
            cursor.execute(
                "INSERT INTO channels (server_id, name) VALUES (?, ?)",
                (server_id, name)
            )
            conn.commit()
            
            return {
                "success": True,
                "message": f"Channel '{name}' created!",
                "channel_id": cursor.lastrowid
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating channel: {str(e)}"
        }


def get_server_channels(server_id: int) -> list:
    """Get all channels in a server"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM channels WHERE server_id = ? ORDER BY created_at ASC",
                (server_id,)
            )
            
            channels = cursor.fetchall()
            return [dict(channel) for channel in channels]
    except Exception as e:
        print(f"Error getting channels: {e}")
        return []


def join_channel(channel_id: int, user_id: int) -> dict:
    """Join a channel (leaves current channel if in one)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get server_id for this channel
            cursor.execute(
                "SELECT server_id FROM channels WHERE id = ?",
                (channel_id,)
            )
            channel = cursor.fetchone()
            
            if not channel:
                return {
                    "success": False,
                    "message": "Channel not found!"
                }
            
            # Check if user is a member of this server
            cursor.execute(
                "SELECT id FROM server_members WHERE server_id = ? AND user_id = ?",
                (channel['server_id'], user_id)
            )
            if not cursor.fetchone():
                return {
                    "success": False,
                    "message": "You are not a member of this server!"
                }
            
            # Leave all channels in this server first
            cursor.execute("""
                DELETE FROM channel_members 
                WHERE user_id = ? AND channel_id IN (
                    SELECT id FROM channels WHERE server_id = ?
                )
            """, (user_id, channel['server_id']))
            
            # Join the new channel
            cursor.execute(
                "INSERT INTO channel_members (channel_id, user_id) VALUES (?, ?)",
                (channel_id, user_id)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Joined channel!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error joining channel: {str(e)}"
        }


def leave_channel(channel_id: int, user_id: int) -> dict:
    """Leave a channel"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM channel_members WHERE channel_id = ? AND user_id = ?",
                (channel_id, user_id)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Left channel!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error leaving channel: {str(e)}"
        }


def get_channel_members(channel_id: int) -> list:
    """Get all users currently in a channel"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.avatar, u.status, cm.joined_at
                FROM users u
                JOIN channel_members cm ON u.id = cm.user_id
                WHERE cm.channel_id = ?
                ORDER BY cm.joined_at ASC
            """, (channel_id,))
            
            members = cursor.fetchall()
            return [dict(member) for member in members]
    except Exception as e:
        print(f"Error getting channel members: {e}")
        return []


def save_channel_message(channel_id: int, sender_id: int, message: str) -> dict:
    """Save a message to a channel"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verify user is in the channel
            cursor.execute(
                "SELECT id FROM channel_members WHERE channel_id = ? AND user_id = ?",
                (channel_id, sender_id)
            )
            if not cursor.fetchone():
                return {
                    "success": False,
                    "message": "You must be in the channel to send messages!"
                }
            
            cursor.execute(
                "INSERT INTO channel_messages (channel_id, sender_id, message) VALUES (?, ?, ?)",
                (channel_id, sender_id, message)
            )
            conn.commit()
            
            return {
                "success": True,
                "message": "Message sent!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error saving message: {str(e)}"
        }


def get_channel_messages(channel_id: int, limit: int = 50) -> list:
    """Get recent messages from a channel"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cm.*, u.username, u.avatar
                FROM channel_messages cm
                JOIN users u ON cm.sender_id = u.id
                WHERE cm.channel_id = ?
                ORDER BY cm.created_at DESC
                LIMIT ?
            """, (channel_id, limit))
            
            messages = cursor.fetchall()
            # Reverse to get chronological order
            return [dict(msg) for msg in reversed(messages)]
    except Exception as e:
        print(f"Error getting channel messages: {e}")
        return []
