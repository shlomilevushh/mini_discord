"""Server-related database operations"""
from .connection import get_db_connection


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
            invite_id = cursor.lastrowid
            conn.commit()
            
            return {
                "success": True,
                "message": "Server invite sent!",
                "invite_id": invite_id
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
