"""Message-related database operations"""
from .connection import get_db_connection


def save_message(sender_id: int, receiver_id: int, message: str) -> dict:
    """Save a private message"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)",
                (sender_id, receiver_id, message)
            )
            message_id = cursor.lastrowid
            
            # Get the timestamp
            cursor.execute(
                "SELECT created_at FROM messages WHERE id = ?",
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
            "message": f"Error sending message: {str(e)}"
        }


def get_chat_history(user1_id: int, user2_id: int, limit: int = 50) -> list:
    """Get chat history between two users"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, 
                       sender.username as sender_username, 
                       sender.avatar as sender_avatar,
                       receiver.username as receiver_username,
                       receiver.avatar as receiver_avatar
                FROM messages m
                JOIN users sender ON m.sender_id = sender.id
                JOIN users receiver ON m.receiver_id = receiver.id
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
