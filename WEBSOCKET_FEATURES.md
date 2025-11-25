# WebSocket Real-Time Features

## Overview
The application now uses WebSocket for ALL real-time updates, including messages, calls, status updates, and notifications.

## Implementation Details

### Backend WebSocket Handler (`backend/app/main.py`)

The WebSocket endpoint (`/ws`) handles the following message types:

#### 1. **Voice Call Signaling** (Already Implemented)
- `voice-call-offer` - Initiate 1-on-1 call
- `voice-call-answer` - Answer 1-on-1 call
- `ice-candidate` - WebRTC ICE candidates
- `call-end` - End 1-on-1 call

#### 2. **Voice Channel Signaling** (Already Implemented)
- `join-voice-channel` - Join a voice channel
- `leave-voice-channel` - Leave a voice channel
- `channel-voice-offer` - WebRTC offer for channel voice
- `channel-voice-answer` - WebRTC answer for channel voice
- `channel-ice-candidate` - ICE candidates for channel voice

#### 3. **Private Messages** (NEW)
- **Send**: Client sends `private-message` with `receiver_id` and `message`
- **Receive**: Server broadcasts `new-private-message` to receiver with:
  - `from_user_id`: Sender's ID
  - `from_username`: Sender's username
  - `message`: Message content
  - `timestamp`: When message was sent

#### 4. **Channel Messages** (NEW)
- **Send**: Client sends `channel-message` with `channel_id` and `message`
- **Receive**: Server broadcasts `new-channel-message` to all channel members with:
  - `channel_id`: Channel ID
  - `from_user_id`: Sender's ID
  - `from_username`: Sender's username
  - `message`: Message content
  - `timestamp`: When message was sent

#### 5. **Status Updates** (NEW)
- **Send**: Client sends `status-update` with `status` (online/offline/invisible)
- **Receive**: Server broadcasts `friend-status-changed` to all friends with:
  - `user_id`: User whose status changed
  - `username`: User's username
  - `status`: New status

#### 6. **Friend Requests** (NEW)
- **Notification**: Server sends `new-friend-request` when someone sends you a request:
  - `from_user_id`: Requester's ID
  - `from_username`: Requester's username
  - `request_id`: Request ID

- **Accept Notification**: Server sends `friend-request-accepted` to requester when accepted:
  - `by_user_id`: User who accepted
  - `by_username`: Username of accepter

#### 7. **Server Invites** (NEW)
- **Notification**: Server sends `new-server-invite` when invited to a server:
  - `from_user_id`: Inviter's ID
  - `from_username`: Inviter's username
  - `server_id`: Server ID
  - `server_name`: Server name
  - `invite_id`: Invite ID

## Frontend Implementation

### Connection Management (`frontend/pages/home/js/app.js`)
- WebSocket connects on page load with session authentication
- Automatic reconnection after 3 seconds if disconnected
- All messages routed through `handleWebSocketMessage()`

### Private Messages (`frontend/pages/home/js/chat.js`)
- `sendMessage()` - Sends via WebSocket instead of HTTP
- `handleNewPrivateMessage()` - Receives real-time messages
- Auto-refreshes chat when message from current friend arrives

### Channel Messages (`frontend/pages/home/js/servers.js`)
- `sendChannelMessage()` - Sends via WebSocket instead of HTTP
- `handleNewChannelMessage()` - Receives real-time channel messages
- Auto-refreshes channel chat when message arrives

### Status Updates (`frontend/pages/home/js/status.js`)
- `updateStatus()` - Sends status via WebSocket
- Status updates are pushed to all friends in real-time
- UI updates automatically when friend status changes

### Notifications (`frontend/pages/home/js/app.js`)
- Friend requests trigger page reload to show new requests
- Server invites trigger page reload to show new invites
- Browser notifications supported (with permission)

## Database Updates

All database operations now return additional fields for WebSocket notifications:

1. **`save_message()`** - Returns `timestamp`
2. **`save_channel_message()`** - Returns `timestamp`
3. **`send_friend_request()`** - Returns `receiver_id` and `request_id`
4. **`accept_friend_request()`** - Returns `requester_id`
5. **`send_server_invite()`** - Returns `invite_id`

## Benefits

### ✅ Real-Time Communication
- Messages appear instantly without page refresh
- Status changes update immediately
- Notifications arrive in real-time

### ✅ Better User Experience
- No polling needed - WebSocket push notifications
- Reduced server load (no constant HTTP requests)
- Smoother, more responsive interface

### ✅ Scalability
- Single persistent connection per user
- Efficient message broadcasting
- ConnectionManager tracks all active users

## Testing Instructions

1. **Private Messages**:
   - Open two browser windows (different accounts)
   - Send messages between them
   - Messages should appear instantly without refresh

2. **Channel Messages**:
   - Join same channel with multiple users
   - Send messages - all users see them instantly

3. **Status Updates**:
   - Change your status (online/offline/invisible)
   - Friends should see status change immediately

4. **Friend Requests**:
   - Send friend request to another user
   - Receiver sees notification and page reloads

5. **Voice Calls**:
   - Click call button to start 1-on-1 voice call
   - Both users can hear each other (audio fix applied)

6. **Voice Channels**:
   - Join voice channel
   - All users in channel can hear each other

## WebSocket Message Flow

```
Client → WebSocket → Server
         ↓
    ConnectionManager
         ↓
   Routes to Recipients
         ↓
    Broadcast/Send
         ↓
    Client Receives
         ↓
    Update UI
```

## Error Handling

- WebSocket disconnection triggers automatic reconnection
- Failed sends show alert to user
- Console logging for debugging
- Connection status checks before sending

## Security

- WebSocket authentication via session token (query param)
- Session validation on connection
- User ID verified for all operations
- Database checks for permissions (channel membership, friendships, etc.)

## Next Steps for Improvement

1. **Typing Indicators**: Show when someone is typing
2. **Read Receipts**: Mark messages as read
3. **Unread Badges**: Show count of unread messages
4. **Toast Notifications**: Better UI for notifications instead of alerts
5. **Message History**: Load older messages on scroll
6. **File Sharing**: Send images/files via WebSocket
7. **User Presence**: Show last seen time
8. **Message Editing**: Edit/delete sent messages
9. **Emoji Reactions**: React to messages
10. **Voice Activity Detection**: Show speaking indicator in voice channels
