// Status management

// Update user status via WebSocket
export async function updateStatus() {
    const status = document.getElementById('status-selector').value;
    
    // Send via WebSocket for real-time updates to friends
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'status-update',
            status: status
        }));
        
        console.log('Status updated to:', status);
    } else {
        console.error('WebSocket not connected');
    }
}

// Refresh friends status
export async function refreshFriendsStatus() {
    try {
        const response = await fetch('/api/friends/status');
        const data = await response.json();
        
        if (data.success) {
            // Update status indicators in friend list
            data.friends.forEach(friend => {
                const friendItem = document.querySelector(`[data-friend-id="${friend.id}"]`);
                if (friendItem) {
                    const statusIndicator = friendItem.querySelector('.status-indicator');
                    statusIndicator.className = `status-indicator status-${friend.status}`;
                }
                
                // Update chat header if this is the current chat
                const currentChatFriendId = window.chatModule?.getCurrentChatFriendId();
                if (currentChatFriendId === friend.id) {
                    const chatStatus = document.getElementById('chat-friend-status');
                    if (chatStatus) {
                        chatStatus.className = `status-indicator status-${friend.status}`;
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error refreshing friends status:', error);
    }
}

// Start periodic status refresh (every 10 seconds)
export function startStatusRefresh() {
    setInterval(refreshFriendsStatus, 10000);
}
