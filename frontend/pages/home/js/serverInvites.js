// Server invites management module
import { getState } from './state.js';

let currentFriendId = null;

// Open invite to server modal
export function openInviteToServerModal() {
    const friendId = getState().currentFriendId;
    if (!friendId) return;
    
    currentFriendId = friendId;
    
    // Clear messages
    document.getElementById('invite-server-error').style.display = 'none';
    document.getElementById('invite-server-success').style.display = 'none';
    
    document.getElementById('inviteToServerModal').style.display = 'block';
    loadOwnedServers();
}

export function closeInviteToServerModal() {
    document.getElementById('inviteToServerModal').style.display = 'none';
    currentFriendId = null;
    // Clear messages
    document.getElementById('invite-server-error').style.display = 'none';
    document.getElementById('invite-server-success').style.display = 'none';
}

// Load servers owned by current user
async function loadOwnedServers() {
    try {
        const response = await fetch('/my-servers');
        const data = await response.json();
        
        const container = document.getElementById('owned-servers-container');
        container.innerHTML = '';
        
        if (data.servers && data.servers.length > 0) {
            const ownedServers = data.servers.filter(server => server.is_owner);
            
            if (ownedServers.length > 0) {
                ownedServers.forEach(server => {
                    const serverDiv = document.createElement('div');
                    serverDiv.className = 'server-invite-item';
                    serverDiv.innerHTML = `
                        <div class="server-invite-info">
                            <span class="server-icon">🏠</span>
                            <span class="server-name">${server.name}</span>
                        </div>
                        <button class="invite-btn" onclick="inviteToServer(${server.id})">Invite</button>
                    `;
                    container.appendChild(serverDiv);
                });
            } else {
                container.innerHTML = '<div class="no-items">You don\'t own any servers yet!</div>';
            }
        } else {
            container.innerHTML = '<div class="no-items">You don\'t own any servers yet!</div>';
        }
    } catch (error) {
        console.error('Error loading owned servers:', error);
        const container = document.getElementById('owned-servers-container');
        container.innerHTML = '<div class="no-items">Error loading servers</div>';
    }
}

// Invite friend to server
export async function inviteToServer(serverId) {
    if (!currentFriendId) return;
    
    const errorDiv = document.getElementById('invite-server-error');
    const successDiv = document.getElementById('invite-server-success');
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    try {
        const formData = new FormData();
        formData.append('server_id', serverId);
        formData.append('user_id', currentFriendId);
        
        const response = await fetch('/invite-to-server', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = data.message;
            successDiv.style.display = 'block';
            
            setTimeout(() => {
                closeInviteToServerModal();
            }, 1500);
        } else {
            errorDiv.textContent = data.message;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Error inviting to server:', error);
        errorDiv.textContent = 'Error sending invite';
        errorDiv.style.display = 'block';
    }
}

// Accept server invite
export async function acceptServerInvite(inviteId) {
    try {
        const formData = new FormData();
        formData.append('invite_id', inviteId);
        
        const response = await fetch('/accept-server-invite', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove invite from UI
            const inviteElement = document.querySelector(`[data-invite-id="${inviteId}"]`);
            if (inviteElement) {
                inviteElement.remove();
            }
            
            // Update count
            const count = document.getElementById('server-invites-count');
            count.textContent = parseInt(count.textContent) - 1;
            
            // Reload page to show new server
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error accepting invite:', error);
        alert('Error accepting invite');
    }
}

// Decline server invite
export async function declineServerInvite(inviteId) {
    try {
        const formData = new FormData();
        formData.append('invite_id', inviteId);
        
        const response = await fetch('/decline-server-invite', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove invite from UI
            const inviteElement = document.querySelector(`[data-invite-id="${inviteId}"]`);
            if (inviteElement) {
                inviteElement.remove();
            }
            
            // Update count
            const count = document.getElementById('server-invites-count');
            count.textContent = parseInt(count.textContent) - 1;
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error declining invite:', error);
        alert('Error declining invite');
    }
}
