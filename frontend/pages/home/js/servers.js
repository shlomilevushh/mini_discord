// Server management module
import { getState } from './state.js';

let currentServerId = null;
let currentChannelId = null;
let isOwner = false;

// Switch between Friends and Servers tabs
export function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Create Server Modal
export function openCreateServerModal() {
    document.getElementById('createServerModal').style.display = 'block';
    document.getElementById('server-name').value = '';
    document.getElementById('create-server-error').style.display = 'none';
    document.getElementById('create-server-success').style.display = 'none';
}

export function closeCreateServerModal() {
    document.getElementById('createServerModal').style.display = 'none';
}

export async function handleCreateServer(e) {
    e.preventDefault();
    
    const name = document.getElementById('server-name').value;
    const errorDiv = document.getElementById('create-server-error');
    const successDiv = document.getElementById('create-server-success');
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        
        const response = await fetch('/create-server', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = data.message;
            successDiv.style.display = 'block';
            
            setTimeout(() => {
                closeCreateServerModal();
                window.location.reload(); // Reload to show new server
            }, 1000);
        } else {
            errorDiv.textContent = data.message;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Error creating server: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

// Open server view
export async function openServer(serverId, serverName, isServerOwner) {
    currentServerId = serverId;
    isOwner = isServerOwner;
    
    document.getElementById('server-view-name').textContent = serverName;
    document.getElementById('serverViewModal').style.display = 'block';
    
    // Show/hide create channel button based on ownership
    const createChannelBtn = document.getElementById('create-channel-btn');
    if (isOwner) {
        createChannelBtn.style.display = 'inline-block';
    } else {
        createChannelBtn.style.display = 'none';
    }
    
    // Load channels
    await loadChannels(serverId);
}

export function closeServerView() {
    document.getElementById('serverViewModal').style.display = 'none';
    currentServerId = null;
    currentChannelId = null;
}

// Load channels for a server
async function loadChannels(serverId) {
    try {
        const response = await fetch(`/server/${serverId}/channels`);
        const data = await response.json();
        
        const channelsList = document.getElementById('channels-list');
        channelsList.innerHTML = '';
        
        if (data.channels && data.channels.length > 0) {
            data.channels.forEach(channel => {
                const channelDiv = document.createElement('div');
                channelDiv.className = 'channel-item';
                channelDiv.dataset.channelId = channel.id;
                channelDiv.dataset.channelType = channel.channel_type || 'voice';
                
                // Different icon for voice vs text channels
                const icon = (channel.channel_type === 'text') ? '#' : '🔊';
                
                channelDiv.innerHTML = `
                    <span class="channel-icon">${icon}</span>
                    <span class="channel-name">${channel.name}</span>
                `;
                channelDiv.onclick = () => joinChannel(channel.id, channel.name, channel.channel_type || 'voice');
                channelsList.appendChild(channelDiv);
            });
            
            // Auto-join the first channel
            if (data.channels[0]) {
                joinChannel(data.channels[0].id, data.channels[0].name, data.channels[0].channel_type || 'voice');
            }
        }
    } catch (error) {
        console.error('Error loading channels:', error);
    }
}

// Join a channel
export async function joinChannel(channelId, channelName, channelType = 'voice') {
    currentChannelId = channelId;
    
    // Update UI
    const channelIcon = (channelType === 'text') ? '#' : '🔊';
    document.getElementById('current-channel-name').textContent = `${channelIcon} ${channelName}`;
    
    // Highlight active channel
    document.querySelectorAll('.channel-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.channelId == channelId) {
            item.classList.add('active');
        }
    });
    
    try {
        // Join channel on backend
        const formData = new FormData();
        formData.append('channel_id', channelId);
        
        await fetch('/join-channel', {
            method: 'POST',
            body: formData
        });
        
        if (channelType === 'voice') {
            // For voice channels, join voice call
            handleVoiceChannelJoin(channelId, channelName);
        } else {
            // For text channels, show chat UI
            handleTextChannelJoin(channelId, channelName);
        }
        
        // Load members
        await loadChannelMembers(channelId);
    } catch (error) {
        console.error('Error joining channel:', error);
    }
}

// Handle joining a voice channel
function handleVoiceChannelJoin(channelId, channelName) {
    // Hide text chat UI elements
    const messageInput = document.getElementById('channel-message-input');
    const sendBtn = document.getElementById('channel-send-btn');
    if (messageInput) messageInput.style.display = 'none';
    if (sendBtn) sendBtn.style.display = 'none';
    
    // Clear messages
    const messagesDiv = document.getElementById('channel-messages');
    messagesDiv.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #b9bbbe;">
            <div style="font-size: 48px; margin-bottom: 20px;">🎤</div>
            <h3 style="color: #fff; margin-bottom: 10px;">Voice Channel</h3>
            <p>Join the voice channel to talk with other members</p>
            <button onclick="window.channelVoice.joinVoiceChannel(${channelId})" 
                    style="margin-top: 20px; padding: 10px 20px; background: #5865F2; color: white; border: none; border-radius: 4px; cursor: pointer;">
                🎤 Join Voice
            </button>
            <div id="voiceControls" style="display: none; margin-top: 20px;">
                <button id="channelMuteBtn" onclick="window.channelVoice.toggleChannelMute()" 
                        style="margin: 5px; padding: 8px 16px; background: #4E5D94; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🎤 Mute
                </button>
                <button onclick="window.channelVoice.leaveVoiceChannel()" 
                        style="margin: 5px; padding: 8px 16px; background: #ED4245; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    📞 Leave Voice
                </button>
            </div>
        </div>
    `;
}

// Handle joining a text channel
async function handleTextChannelJoin(channelId, channelName) {
    // Show text chat UI elements
    const messageInput = document.getElementById('channel-message-input');
    const sendBtn = document.getElementById('channel-send-btn');
    if (messageInput) {
        messageInput.style.display = 'block';
        messageInput.placeholder = `Message #${channelName}`;
    }
    if (sendBtn) sendBtn.style.display = 'block';
    
    // Load messages
    await loadChannelMessages(channelId);
}

// Load channel messages
async function loadChannelMessages(channelId) {
    try {
        const response = await fetch(`/channel/${channelId}/messages`);
        const data = await response.json();
        
        const messagesDiv = document.getElementById('channel-messages');
        messagesDiv.innerHTML = '';
        
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                
                const avatar = getAvatarEmoji(msg.avatar);
                const timestamp = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                messageDiv.innerHTML = `
                    <div class="message-avatar">${avatar}</div>
                    <div class="message-content">
                        <div class="message-header">
                            <span class="message-username">${msg.username}</span>
                            <span class="message-timestamp">${timestamp}</span>
                        </div>
                        <div class="message-text">${msg.message}</div>
                    </div>
                `;
                messagesDiv.appendChild(messageDiv);
            });
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Load channel members
async function loadChannelMembers(channelId) {
    try {
        const response = await fetch(`/channel/${channelId}/members`);
        const data = await response.json();
        
        const membersList = document.getElementById('channel-members-list');
        membersList.innerHTML = '';
        
        if (data.members && data.members.length > 0) {
            data.members.forEach(member => {
                const memberDiv = document.createElement('div');
                memberDiv.className = 'member-item';
                
                const avatar = getAvatarEmoji(member.avatar);
                const statusClass = `status-${member.status}`;
                
                memberDiv.innerHTML = `
                    <div class="member-avatar-container">
                        <div class="member-avatar">${avatar}</div>
                        <div class="status-indicator ${statusClass}"></div>
                    </div>
                    <span class="member-name">${member.username}</span>
                `;
                membersList.appendChild(memberDiv);
            });
        }
    } catch (error) {
        console.error('Error loading members:', error);
    }
}

// Send channel message
export async function sendChannelMessage() {
    const input = document.getElementById('channel-message-input');
    const message = input.value.trim();
    
    if (!message || !currentChannelId) return;
    
    // Send via WebSocket for real-time delivery
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'channel-message',
            channel_id: currentChannelId,
            message: message
        }));
        
        // Clear input immediately
        input.value = '';
    } else {
        console.error('WebSocket not connected');
        alert('Connection lost. Please refresh the page.');
    }
}

// Handle incoming channel message via WebSocket
export function handleNewChannelMessage(channelId, fromUserId, fromUsername, message, timestamp) {
    // If this is for the current channel, reload messages
    if (currentChannelId === channelId) {
        loadChannelMessages(channelId);
    }
}

// Create Channel Modal
export function openCreateChannelModal() {
    if (!isOwner) {
        alert('Only server owner can create channels!');
        return;
    }
    
    document.getElementById('createChannelModal').style.display = 'block';
    document.getElementById('channel-name').value = '';
    document.getElementById('create-channel-error').style.display = 'none';
    document.getElementById('create-channel-success').style.display = 'none';
}

export function closeCreateChannelModal() {
    document.getElementById('createChannelModal').style.display = 'none';
}

export async function handleCreateChannel(e) {
    e.preventDefault();
    
    if (!currentServerId) return;
    
    const name = document.getElementById('channel-name').value;
    const errorDiv = document.getElementById('create-channel-error');
    const successDiv = document.getElementById('create-channel-success');
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    try {
        const formData = new FormData();
        formData.append('server_id', currentServerId);
        formData.append('name', name);
        
        const response = await fetch('/create-channel', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = data.message;
            successDiv.style.display = 'block';
            
            setTimeout(() => {
                closeCreateChannelModal();
                loadChannels(currentServerId);
            }, 1000);
        } else {
            errorDiv.textContent = data.message;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Error creating channel: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

// Helper function to get avatar emoji
function getAvatarEmoji(avatar) {
    const avatars = {
        'avatar1': '🦊',
        'avatar2': '🐼',
        'avatar3': '🦁',
        'avatar4': '🐸',
        'avatar5': '🦄',
        'avatar6': '🐲'
    };
    return avatars[avatar] || '😊';
}

// Setup channel message input enter key
export function initChannelListeners() {
    const input = document.getElementById('channel-message-input');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChannelMessage();
            }
        });
    }
}

export function getCurrentServerId() {
    return currentServerId;
}

export function getCurrentChannelId() {
    return currentChannelId;
}
