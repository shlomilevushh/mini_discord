// Chat functionality
import { getCurrentChatFriendId, setCurrentChatFriendId, getAvatarEmoji, escapeHtml } from './state.js';

let currentChatFriendName = '';

// Open chat with a friend
export async function openChat(friendId, friendName, friendAvatar, friendStatus) {
    setCurrentChatFriendId(friendId);
    currentChatFriendName = friendName;
    
    // Update UI
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('chat-window').classList.add('active');
    
    // Update chat header
    document.getElementById('chat-friend-name').textContent = friendName;
    document.getElementById('chat-friend-avatar').textContent = getAvatarEmoji(friendAvatar);
    
    const chatStatus = document.getElementById('chat-friend-status');
    chatStatus.className = `status-indicator status-${friendStatus}`;
    
    // Show invite to server button and call button
    const inviteBtn = document.getElementById('invite-to-server-btn');
    if (inviteBtn) {
        inviteBtn.style.display = 'inline-block';
    }
    
    const callBtn = document.getElementById('voice-call-btn');
    if (callBtn) {
        callBtn.style.display = 'inline-block';
    }
    
    // Highlight active friend
    document.querySelectorAll('.friend-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeFriend = document.querySelector(`[data-friend-id="${friendId}"]`);
    if (activeFriend) {
        activeFriend.classList.add('active');
    }
    
    // Load chat history
    await loadChatHistory(friendId);
}

// Start voice call with current chat friend
export function startCall() {
    const friendId = getCurrentChatFriendId();
    if (!friendId) {
        alert('Please select a friend to call');
        return;
    }
    
    // Check if already in a call
    if (window.voiceCall && window.voiceCall.isInCall()) {
        alert('You are already in a call!');
        return;
    }
    
    // Start the call
    if (window.voiceCall) {
        window.voiceCall.startVoiceCall(friendId, currentChatFriendName);
    }
}

// Load chat history
export async function loadChatHistory(friendId) {
    try {
        const response = await fetch(`/api/messages/${friendId}`);
        const data = await response.json();
        
        if (data.success) {
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '';
            
            data.messages.forEach(msg => {
                addMessageToChat(msg);
            });
            
            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Add message to chat
function addMessageToChat(msg) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${getAvatarEmoji(msg.sender_avatar)}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">${escapeHtml(msg.sender_username)}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${escapeHtml(msg.message)}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
}

// Send message via WebSocket
export async function sendMessage() {
    const friendId = getCurrentChatFriendId();
    if (!friendId) return;
    
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Send via WebSocket for real-time delivery
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'private-message',
            receiver_id: friendId,
            message: message
        }));
        
        // Clear input immediately
        input.value = '';
        
        // Message will be added to chat when we receive confirmation or reload
        await loadChatHistory(friendId);
    } else {
        console.error('WebSocket not connected');
        alert('Connection lost. Please refresh the page.');
    }
}

// Handle incoming private message via WebSocket
export function handleNewPrivateMessage(fromUserId, fromUsername, message, timestamp) {
    const currentFriendId = getCurrentChatFriendId();
    
    // If this is from the current chat friend, add to chat
    if (currentFriendId === fromUserId) {
        // Reload chat history to show new message
        loadChatHistory(fromUserId);
    } else {
        // TODO: Show notification badge for unread messages
        console.log('New message from', fromUsername);
    }
}

// Initialize chat event listeners
export function initChatListeners() {
    // Enter key to send message
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}
