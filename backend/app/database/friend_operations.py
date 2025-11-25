"""Friend-related database operations"""
from .connection import get_db_connection


def send_friend_request(sender_id: int, receiver_username: str) -> dict:
    """Send a friend request to another user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get receiver by username
            cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (receiver_username,)
            )
            receiver = cursor.fetchone()
            
            if not receiver:
                return {
                    "success": False,
                    "message": "User not found!"
                }
            
            receiver_id = receiver['id']
            
            # Can't send request to yourself
            if sender_id == receiver_id:
                return {
                    "success": False,
                    "message": "You can't add yourself as a friend!"
                }
            
            # Check if already friends
            cursor.execute(
                "SELECT id FROM friendships WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
                (sender_id, receiver_id, receiver_id, sender_id)
            )
            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "You are already friends!"
                }
            
            # Check for pending request
            cursor.execute(
                "SELECT id FROM friend_requests WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'",
                (sender_id, receiver_id)
            )
            if cursor.fetchone():
                return {
                    "success": False,
                    "message": "Friend request already sent!"
                }
            
            # Send request
            cursor.execute(
                "INSERT INTO friend_requests (sender_id, receiver_id) VALUES (?, ?)",
                (sender_id, receiver_id)
            )
            request_id = cursor.lastrowid
            conn.commit()
            
            return {
                "success": True,
                "message": f"Friend request sent to {receiver_username}!",
                "receiver_id": receiver_id,
                "request_id": request_id
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
                SELECT fr.id, u.username, u.avatar 
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
            
            # Get request details
            cursor.execute(
                "SELECT sender_id, receiver_id FROM friend_requests WHERE id = ? AND receiver_id = ? AND status = 'pending'",
                (request_id, user_id)
            )
            request = cursor.fetchone()
            
            if not request:
                return {
                    "success": False,
                    "message": "Friend request not found or already processed!"
                }
            
            sender_id = request['sender_id']
            receiver_id = request['receiver_id']
            
            # Create friendship
            cursor.execute(
                "INSERT INTO friendships (user1_id, user2_id) VALUES (?, ?)",
                (sender_id, receiver_id)
            )
            
            # Update request status
            cursor.execute(
                "UPDATE friend_requests SET status = 'accepted' WHERE id = ?",
                (request_id,)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Friend request accepted!",
                "requester_id": sender_id
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error accepting friend request: {str(e)}"
        }


def decline_friend_request(request_id: int, user_id: int) -> dict:
    """Decline a friend request"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE friend_requests SET status = 'declined' WHERE id = ? AND receiver_id = ? AND status = 'pending'",
                (request_id, user_id)
            )
            
            if cursor.rowcount == 0:
                return {
                    "success": False,
                    "message": "Friend request not found or already processed!"
                }
            
            conn.commit()
            
            return {
                "success": True,
                "message": "Friend request declined!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error declining friend request: {str(e)}"
        }


def get_friends(user_id: int) -> list:
    """Get all friends of a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.avatar
                FROM users u
                WHERE u.id IN (
                    SELECT user2_id FROM friendships WHERE user1_id = ?
                    UNION
                    SELECT user1_id FROM friendships WHERE user2_id = ?
                )
                ORDER BY u.username ASC
            """, (user_id, user_id))
            
            friends = cursor.fetchall()
            return [dict(friend) for friend in friends]
    except Exception as e:
        print(f"Error getting friends: {e}")
        return []


def get_friends_with_status(user_id: int) -> list:
    """Get all friends with their current status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.avatar, u.status
                FROM users u
                WHERE u.id IN (
                    SELECT user2_id FROM friendships WHERE user1_id = ?
                    UNION
                    SELECT user1_id FROM friendships WHERE user2_id = ?
                )
                ORDER BY u.username ASC
            """, (user_id, user_id))
            
            friends = cursor.fetchall()
            return [dict(friend) for friend in friends]
    except Exception as e:
        print(f"Error getting friends with status: {e}")
        return []
