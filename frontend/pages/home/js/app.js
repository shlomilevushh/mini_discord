// Main application entry point
console.log('=== APP.JS LOADED ===');

// Helper function to get cookie value
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

import { initState } from './state.js';
import { openAddFriendModal, closeAddFriendModal } from './modal.js';
import { acceptRequest, declineRequest } from './friendRequests.js';
import { updateStatus, startStatusRefresh } from './status.js';
import { openChat, sendMessage, initChatListeners, startCall, handleNewPrivateMessage } from './chat.js';
import { 
    switchTab, openCreateServerModal, closeCreateServerModal, handleCreateServer,
    openServer, closeServerView, joinChannel, sendChannelMessage,
    openCreateChannelModal, closeCreateChannelModal, handleCreateChannel,
    initChannelListeners, handleNewChannelMessage
} from './servers.js';
import {
    openInviteToServerModal, closeInviteToServerModal, inviteToServer,
    acceptServerInvite, declineServerInvite
} from './serverInvites.js';
import {
    handleCallOffer, handleCallAnswer, handleIceCandidate, handleCallEnd
} from './voiceCall.js';
import {
    handleChannelUsers, handleUserJoinedVoice, handleUserLeftVoice,
    handleChannelVoiceOffer, handleChannelVoiceAnswer, handleChannelIceCandidate
} from './channelVoice.js';

// Initialize the application
export function initApp(userId) {
    console.log('initApp called with userId:', userId);
    
    try {
        initState(userId);
        console.log('State initialized');
        
        initChatListeners();
        console.log('Chat listeners initialized');
        
        initChannelListeners();
        console.log('Channel listeners initialized');
        
        startStatusRefresh();
        console.log('Status refresh started');
        
        initWebSocket();
        console.log('WebSocket initialized');
        
        // Setup form listeners
        setupFormListeners();
        console.log('Form listeners setup complete');
        
        console.log('App initialization complete!');
    } catch (error) {
        console.error('Error during app initialization:', error);
    }
}

// Initialize WebSocket connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Get session token from window (set by server in template)
    const sessionToken = window.SESSION_TOKEN;
    console.log('Session token found:', sessionToken ? 'YES' : 'NO');
    
    if (!sessionToken) {
        console.error('No session token available! Cannot connect to WebSocket.');
        return;
    }
    
    const wsUrl = `${protocol}//${window.location.host}/ws?session=${sessionToken}`;
    
    console.log('Connecting to WebSocket with authentication...');
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected successfully');
    };
    
    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(initWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    // Store WebSocket globally for use in other modules
    window.ws = ws;
}

// Handle incoming WebSocket messages
function handleWebSocketMessage(message) {
    const { type } = message;
    
    switch (type) {
        // Voice call messages
        case 'voice-call-offer':
            if (handleCallOffer) handleCallOffer(message.from_user_id, message.from_username, message.offer);
            break;
        
        case 'voice-call-answer':
            if (handleCallAnswer) handleCallAnswer(message.from_user_id, message.answer);
            break;
        
        case 'ice-candidate':
            if (handleIceCandidate) handleIceCandidate(message.from_user_id, message.candidate);
            break;
        
        case 'call-end':
            if (handleCallEnd) handleCallEnd(message.from_user_id);
            break;
        
        // Channel voice messages
        case 'voice-channel-users':
            if (handleChannelUsers) handleChannelUsers(message.channel_id, message.user_ids);
            break;
        
        case 'user-joined-voice':
            if (handleUserJoinedVoice) handleUserJoinedVoice(message.user_id, message.username);
            break;
        
        case 'user-left-voice':
            if (handleUserLeftVoice) handleUserLeftVoice(message.user_id, message.username);
            break;
        
        case 'channel-voice-offer':
            if (handleChannelVoiceOffer) handleChannelVoiceOffer(message.from_user_id, message.channel_id, message.offer);
            break;
        
        case 'channel-voice-answer':
            if (handleChannelVoiceAnswer) handleChannelVoiceAnswer(message.from_user_id, message.channel_id, message.answer);
            break;
        
        case 'channel-ice-candidate':
            if (handleChannelIceCandidate) handleChannelIceCandidate(message.from_user_id, message.channel_id, message.candidate);
            break;
        
        // Real-time messaging
        case 'new-private-message':
            if (handleNewPrivateMessage) handleNewPrivateMessage(message.from_user_id, message.from_username, message.message, message.timestamp);
            break;
        
        case 'new-channel-message':
            if (handleNewChannelMessage) handleNewChannelMessage(message.channel_id, message.from_user_id, message.from_username, message.message, message.timestamp);
            break;
        
        // Friend requests
        case 'new-friend-request':
            console.log('New friend request from', message.from_username);
            showNotification(`Friend request from ${message.from_username}`);
            // Reload friend requests
            location.reload();
            break;
        
        case 'friend-request-accepted':
            console.log('Friend request accepted by', message.by_username);
            showNotification(`${message.by_username} accepted your friend request!`);
            // Reload friends list
            location.reload();
            break;
        
        // Server invites
        case 'new-server-invite':
            console.log('New server invite from', message.from_username, 'to', message.server_name);
            showNotification(`${message.from_username} invited you to ${message.server_name}`);
            // Reload server invites
            location.reload();
            break;
        
        // Status updates
        case 'friend-status-changed':
            console.log('Friend status changed:', message.username, message.status);
            updateFriendStatus(message.user_id, message.status);
            break;
        
        default:
            console.log('Unknown message type:', type);
    }
}

// Show notification
function showNotification(message) {
    // Simple alert for now - can be improved with toast notifications
    if (Notification.permission === 'granted') {
        new Notification('Mini Discord', { body: message });
    } else {
        console.log('Notification:', message);
    }
}

// Update friend status in the UI
function updateFriendStatus(userId, status) {
    const friendElement = document.querySelector(`[data-friend-id="${userId}"]`);
    if (friendElement) {
        const statusIndicator = friendElement.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.className = `status-indicator status-${status}`;
        }
    }
    
    // Update in chat header if chatting with this friend
    const chatFriendName = document.getElementById('chat-friend-name');
    const chatStatus = document.getElementById('chat-friend-status');
    if (chatFriendName && chatStatus) {
        const currentFriendElement = document.querySelector('.friend-item.active');
        if (currentFriendElement && parseInt(currentFriendElement.dataset.friendId) === userId) {
            chatStatus.className = `status-indicator status-${status}`;
        }
    }
}

// Setup form event listeners
function setupFormListeners() {
    // Create server form
    const createServerForm = document.getElementById('create-server-form');
    if (createServerForm) {
        createServerForm.addEventListener('submit', handleCreateServer);
    }
    
    // Create channel form
    const createChannelForm = document.getElementById('create-channel-form');
    if (createChannelForm) {
        createChannelForm.addEventListener('submit', handleCreateChannel);
    }
}

// Export functions to global scope for inline event handlers
window.openAddFriendModal = openAddFriendModal;
window.closeAddFriendModal = closeAddFriendModal;
window.acceptRequest = acceptRequest;
window.declineRequest = declineRequest;
window.updateStatus = updateStatus;
window.openChat = openChat;
window.sendMessage = sendMessage;
window.startCall = startCall;

// Server functions
window.switchTab = switchTab;
window.openCreateServerModal = openCreateServerModal;
window.closeCreateServerModal = closeCreateServerModal;
window.openServer = openServer;
window.closeServerView = closeServerView;
window.joinChannel = joinChannel;
window.sendChannelMessage = sendChannelMessage;
window.openCreateChannelModal = openCreateChannelModal;
window.closeCreateChannelModal = closeCreateChannelModal;

// Server invite functions
window.openInviteToServerModal = openInviteToServerModal;
window.closeInviteToServerModal = closeInviteToServerModal;
window.inviteToServer = inviteToServer;
window.acceptServerInvite = acceptServerInvite;
window.declineServerInvite = declineServerInvite;
