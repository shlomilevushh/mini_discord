# Database Module Structure

The database module has been refactored from a single 1013-line file into a modular structure for better organization and maintainability.

## Directory Structure

```
backend/app/database/
├── __init__.py              # Module exports (all functions)
├── connection.py            # Database connection management
├── schemas.py               # Database table schemas
├── user_operations.py       # User-related operations
├── friend_operations.py     # Friend request and friendship operations
├── message_operations.py    # Private message operations
├── server_operations.py     # Server management operations
└── channel_operations.py    # Channel operations
```

## File Descriptions

### connection.py (20 lines)
- **Purpose**: Centralized database connection management
- **Contents**:
  - `DB_PATH`: Constant for database file location
  - `get_db_connection()`: Context manager for database connections

### schemas.py (158 lines)
- **Purpose**: Database table definitions
- **Contents**:
  - `init_database()`: Creates all 9 tables if they don't exist
  - Tables: users, friend_requests, friendships, messages, servers, server_members, server_invites, channels, channel_members, channel_messages

### user_operations.py (137 lines)
- **Purpose**: User account management
- **Functions**:
  - `create_user()`: Register a new user
  - `verify_user()`: Login authentication
  - `get_user_by_id()`: Fetch user by ID
  - `get_user_by_username()`: Fetch user by username
  - `update_user_status()`: Update user's online/offline status

### friend_operations.py (213 lines)
- **Purpose**: Friend request and friendship management
- **Functions**:
  - `send_friend_request()`: Send friend request to another user
  - `get_pending_friend_requests()`: Get all incoming friend requests
  - `accept_friend_request()`: Accept a friend request
  - `decline_friend_request()`: Decline a friend request
  - `get_friends()`: Get all friends of a user
  - `get_friends_with_status()`: Get friends with their online status

### message_operations.py (50 lines)
- **Purpose**: Direct messaging between users
- **Functions**:
  - `save_message()`: Save a direct message
  - `get_chat_history()`: Get message history between two users

### server_operations.py (248 lines)
- **Purpose**: Server creation and management
- **Functions**:
  - `create_server()`: Create a new server (unique name per user)
  - `get_user_servers()`: Get all servers a user is a member of
  - `get_server_by_id()`: Get server details by ID
  - `send_server_invite()`: Invite a friend to a server
  - `get_pending_server_invites()`: Get all pending server invites
  - `accept_server_invite()`: Accept a server invite
  - `decline_server_invite()`: Decline a server invite

### channel_operations.py (241 lines)
- **Purpose**: Channel management within servers
- **Functions**:
  - `create_channel()`: Create a new channel in a server (owner only)
  - `get_server_channels()`: Get all channels in a server
  - `join_channel()`: Join a specific channel (leaves current channel)
  - `leave_channel()`: Leave a channel
  - `get_channel_members()`: Get all users currently in a channel
  - `save_channel_message()`: Send a message to a channel
  - `get_channel_messages()`: Get message history from a channel

### __init__.py (95 lines)
- **Purpose**: Module interface - exports all functions
- **Contents**: Imports and re-exports all functions from the operation modules

## Usage in main.py

The import statement in `main.py` remains unchanged:

```python
from .database import (
    init_database, create_user, verify_user, get_user_by_id, get_user_by_username,
    send_friend_request, get_pending_friend_requests, 
    accept_friend_request, decline_friend_request, get_friends, get_friends_with_status,
    update_user_status, save_message, get_chat_history,
    create_server, get_user_servers, get_server_by_id, send_server_invite,
    get_pending_server_invites, accept_server_invite, decline_server_invite,
    create_channel, get_server_channels, join_channel, leave_channel,
    get_channel_members, save_channel_message, get_channel_messages
)
```

Python automatically uses the `__init__.py` file when importing from a package directory.

## Benefits

1. **Better Organization**: Related functions are grouped together by domain
2. **Easier Navigation**: Smaller files are easier to read and maintain
3. **Separation of Concerns**: Schema definitions separate from operations
4. **Scalability**: Easy to add new operation modules as features grow
5. **Maintainability**: Changes to one domain don't affect others

## Migration Notes

- Old `database.py` (1013 lines) has been deleted
- All functions have been preserved and tested
- No changes required to `main.py` imports
- Server starts successfully with the new structure
