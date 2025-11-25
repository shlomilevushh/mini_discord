"""Database module - modular structure for database operations"""

# Import database initialization
from .schemas import init_database

# Import user operations
from .user_operations import (
    create_user,
    verify_user,
    get_user_by_id,
    get_user_by_username,
    update_user_status
)

# Import friend operations
from .friend_operations import (
    send_friend_request,
    get_pending_friend_requests,
    accept_friend_request,
    decline_friend_request,
    get_friends,
    get_friends_with_status
)

# Import message operations
from .message_operations import (
    save_message,
    get_chat_history
)

# Import server operations
from .server_operations import (
    create_server,
    get_user_servers,
    get_server_by_id,
    send_server_invite,
    get_pending_server_invites,
    accept_server_invite,
    decline_server_invite
)

# Import channel operations
from .channel_operations import (
    create_channel,
    get_server_channels,
    join_channel,
    leave_channel,
    get_channel_members,
    save_channel_message,
    get_channel_messages
)

# Export all functions
__all__ = [
    # Database initialization
    'init_database',
    
    # User operations
    'create_user',
    'verify_user',
    'get_user_by_id',
    'get_user_by_username',
    'update_user_status',
    
    # Friend operations
    'send_friend_request',
    'get_pending_friend_requests',
    'accept_friend_request',
    'decline_friend_request',
    'get_friends',
    'get_friends_with_status',
    
    # Message operations
    'save_message',
    'get_chat_history',
    
    # Server operations
    'create_server',
    'get_user_servers',
    'get_server_by_id',
    'send_server_invite',
    'get_pending_server_invites',
    'accept_server_invite',
    'decline_server_invite',
    
    # Channel operations
    'create_channel',
    'get_server_channels',
    'join_channel',
    'leave_channel',
    'get_channel_members',
    'save_channel_message',
    'get_channel_messages'
]
