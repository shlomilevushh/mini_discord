# Voice Chat Features - Mini Discord

This document describes the voice chat implementation for Mini Discord, including 1-on-1 voice calls and multi-user voice channels.

## Features Overview

### 1. **One-on-One Voice Calls**
- Click the 📞 button in a friend's chat to start a voice call
- Real-time peer-to-peer audio communication using WebRTC
- Call controls: Mute/Unmute and End Call
- Visual call UI with connection status
- Automatic microphone permission handling

### 2. **Voice Channels in Servers**
- All channels are voice channels by default (can be text channels too)
- Join voice channels by clicking on them
- Multi-user voice communication (supports multiple participants)
- Individual peer connections for each user in the channel
- Voice controls: Join Voice, Mute, and Leave Voice buttons
- Visual indicators for active voice channels

## Technical Implementation

### Backend Components

#### 1. **Database Schema** (`schemas.py`)
- **channels table**: Added `channel_type` field (varchar: 'voice' or 'text')
  - Default: 'voice'
  - Allows mixed text/voice channels in the future

#### 2. **WebSocket Signaling** (`main.py`)
- **ConnectionManager class**: Manages active WebSocket connections
  - `active_connections`: Maps user_id → WebSocket
  - `channel_connections`: Maps channel_id → set of user_ids
  - Methods for broadcasting to users/channels

- **WebSocket message types**:
  - **1-on-1 calls**:
    - `voice-call-offer`: Initiate call with WebRTC offer
    - `voice-call-answer`: Respond to call with WebRTC answer
    - `ice-candidate`: Exchange ICE candidates for connection
    - `call-end`: Terminate the call
  
  - **Channel voice**:
    - `join-voice-channel`: User joins voice channel
    - `leave-voice-channel`: User leaves voice channel
    - `channel-voice-offer`: WebRTC offer for channel peer
    - `channel-voice-answer`: WebRTC answer for channel peer
    - `channel-ice-candidate`: ICE candidate for channel peer
    - `user-joined-voice`: Notify others of new joiner
    - `user-left-voice`: Notify others of user leaving
    - `voice-channel-users`: Send list of existing users

### Frontend Components

#### 1. **voiceCall.js** - 1-on-1 Voice Calls
**Functions:**
- `startVoiceCall(targetUserId, targetUsername)`: Initiate call
- `handleCallOffer(fromUserId, fromUsername, offer)`: Receive incoming call
- `handleCallAnswer(fromUserId, answer)`: Process call answer
- `handleIceCandidate(fromUserId, candidate)`: Handle ICE candidates
- `endVoiceCall()`: Terminate current call
- `toggleMute()`: Mute/unmute microphone

**Features:**
- WebRTC peer connection with STUN servers
- Automatic microphone access request
- Call UI with avatar and status
- Mute button with visual feedback
- End call button
- Handles busy state (already in call)

#### 2. **channelVoice.js** - Multi-User Voice Channels
**Functions:**
- `joinVoiceChannel(channelId)`: Join voice channel
- `leaveVoiceChannel()`: Leave current voice channel
- `handleChannelUsers(channelId, userIds)`: Connect to existing users
- `handleUserJoinedVoice(userId, username)`: New user notification
- `handleUserLeftVoice(userId, username)`: User left notification
- `handleChannelVoiceOffer/Answer/IceCandidate`: WebRTC signaling
- `toggleChannelMute()`: Mute in channel

**Features:**
- Multiple simultaneous peer connections (one per user)
- Mesh networking (each user connects to all others)
- Automatic peer connection management
- Voice controls within channel UI
- Visual indicators for active voice channel

#### 3. **app.js** - Main Application
- WebSocket connection initialization
- Message routing to appropriate handlers
- Auto-reconnect on disconnect
- Global exports for voice functions

#### 4. **chat.js** - Chat Interface
- `startCall()`: Wrapper for starting 1-on-1 calls
- Shows call button when chatting with friend
- Validates call state before starting

#### 5. **servers.js** - Server/Channel Interface
- Updated `joinChannel()` to handle voice vs text channels
- `handleVoiceChannelJoin()`: Shows voice UI with join button
- `handleTextChannelJoin()`: Shows text chat UI
- Channel rendering with voice/text icons (🔊 vs #)
- Voice controls in channel view

### CSS Styling

#### **voice.css**
**Styles for:**
- `.call-ui`: Floating call interface (top-right)
- `.call-controls`: Mute and end call buttons
- `.voice-indicator`: Animated speaking indicator
- `.channel-item.voice-active`: Active voice channel highlighting
- `.member-item.in-voice`: Member voice indicators
- Voice control buttons with hover effects
- Responsive design for mobile devices

## WebRTC Architecture

### 1-on-1 Calls (Peer-to-Peer)
```
User A                    Server (WebSocket)              User B
  |                              |                          |
  |--- voice-call-offer -------->|-------- forward -------->|
  |                              |                          |
  |<------ forward --------------|<-- voice-call-answer ----|
  |                              |                          |
  |<---- ice-candidate -------->|<---- ice-candidate ----->|
  |                              |                          |
  |<========= Direct RTC Audio Stream ===================>|
```

### Channel Voice (Mesh Network)
```
User A connects to User B and User C:

User A                    Server                    User B
  |                         |                         |
  |--- join-voice -------->|                         |
  |<-- channel-users -------|                         |
  |                         |                         |
  |--- offer (to B) ------>|------- forward -------->|
  |<----- forward ---------|<------ answer ----------|
  |<========== Direct RTC Audio ==================>|

(Same process repeated for User A ↔ User C connection)
```

## Usage Guide

### For Users

**Starting a 1-on-1 Call:**
1. Open a chat with a friend
2. Click the 📞 button in the chat header
3. Allow microphone access when prompted
4. Wait for friend to accept
5. Use mute button to toggle microphone
6. Click "End Call" to hang up

**Joining Voice Channels:**
1. Open a server
2. Click on a voice channel (🔊 icon)
3. Click "🎤 Join Voice" button
4. Allow microphone access
5. You'll be connected to all users in the channel
6. Use "🎤 Mute" to toggle microphone
7. Click "📞 Leave Voice" to exit

### For Developers

**Adding Text Channels:**
When creating a channel, set `channel_type='text'`:
```python
create_channel(server_id, "general-chat", owner_id, channel_type="text")
```

**Extending Voice Features:**
- Add video support: Change `getUserMedia({ audio: true, video: true })`
- Add screen sharing: Use `getDisplayMedia()` instead
- Add recording: Implement `MediaRecorder` API
- Add voice activity detection: Analyze audio levels

## Browser Compatibility

**Requirements:**
- WebRTC support (Chrome 23+, Firefox 22+, Safari 11+, Edge 79+)
- WebSocket support (all modern browsers)
- Microphone access permission

**HTTPS Note:**
- WebRTC requires HTTPS in production
- `getUserMedia()` only works on localhost (HTTP) or HTTPS domains
- For production deployment, obtain SSL certificate

## Configuration

**STUN Servers** (in voiceCall.js and channelVoice.js):
```javascript
const configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};
```

**For Better Performance:**
- Add TURN servers for NAT traversal:
```javascript
{
    urls: 'turn:your-turn-server.com',
    username: 'user',
    credential: 'pass'
}
```

## Troubleshooting

**Call Not Connecting:**
1. Check microphone permissions in browser
2. Verify both users are online (WebSocket connected)
3. Check browser console for errors
4. Try refreshing the page

**No Audio:**
1. Unmute both users
2. Check system audio settings
3. Verify microphone is not used by another app
4. Check browser audio permissions

**Channel Voice Issues:**
1. Leave and rejoin the channel
2. Check if other users can hear each other
3. Verify WebSocket connection
4. Check browser console for peer connection errors

## Future Enhancements

- [ ] Video calling support
- [ ] Screen sharing
- [ ] Voice activity indicators (visual feedback when speaking)
- [ ] Push-to-talk mode
- [ ] Voice channel recording
- [ ] Better audio quality controls
- [ ] Echo cancellation settings
- [ ] Background noise suppression
- [ ] Server-side audio mixing (for scalability)
- [ ] SFU (Selective Forwarding Unit) for large channels

## Performance Considerations

- **Mesh networking** (current): Works well for 2-8 users
- **For 8+ users**: Consider implementing SFU architecture
- **Bandwidth**: Each peer connection uses ~50-100 Kbps
- **CPU**: Audio encoding/decoding is minimal
- **Memory**: ~5-10MB per peer connection

## Security Notes

- WebRTC connections are encrypted (DTLS-SRTP)
- Signaling goes through authenticated WebSocket
- No audio data stored on server
- Peer-to-peer means no server-side recording

## Credits

- WebRTC: Real-Time Communication for the Web
- STUN Servers: Google's public STUN servers
- Icons: Unicode emoji characters
