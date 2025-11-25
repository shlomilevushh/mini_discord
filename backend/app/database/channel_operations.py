"""Channel-related database operations"""
from .connection import get_db_connection


def create_channel(server_id: int, name: str, owner_id: int, channel_type: str = "voice") -> dict:
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
            
            # Validate channel type
            if channel_type not in ["voice", "text"]:
                channel_type = "voice"
            
            # Create channel
            cursor.execute(
                "INSERT INTO channels (server_id, name, channel_type) VALUES (?, ?, ?)",
                (server_id, name, channel_type)
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
            message_id = cursor.lastrowid
            
            # Get the timestamp
            cursor.execute(
                "SELECT created_at FROM channel_messages WHERE id = ?",
                (message_id,)
            )
            timestamp = cursor.fetchone()['created_at']
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Message sent!",
                "timestamp": timestamp
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
