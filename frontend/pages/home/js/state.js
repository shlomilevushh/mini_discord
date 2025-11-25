// Global state management
export const state = {
    currentChatFriendId: null,
    currentUserId: null,
    currentFriendId: null,
    avatarMap: {
        'avatar1': '🦊',
        'avatar2': '🐼',
        'avatar3': '🦁',
        'avatar4': '🐸',
        'avatar5': '🦄',
        'avatar6': '🐲'
    }
};

// Get the full state
export function getState() {
    return state;
}

// Initialize current user ID
export function initState(userId) {
    state.currentUserId = userId;
}

// Get current chat friend ID
export function getCurrentChatFriendId() {
    return state.currentChatFriendId;
}

// Set current chat friend ID
export function setCurrentChatFriendId(friendId) {
    state.currentChatFriendId = friendId;
    state.currentFriendId = friendId; // Also set for server invites
}

// Get avatar emoji by avatar ID
export function getAvatarEmoji(avatarId) {
    return state.avatarMap[avatarId] || '😊';
}

// Escape HTML to prevent XSS
export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
