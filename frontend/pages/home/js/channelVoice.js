/**
 * Channel Voice Module - Handles multi-user voice channels using WebRTC
 */

let peerConnections = {}; // userId -> RTCPeerConnection
let localStream = null;
let currentChannelId = null;
let isMuted = false;

// WebRTC configuration
const configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

/**
 * Join a voice channel
 */
export async function joinVoiceChannel(channelId) {
    if (currentChannelId) {
        await leaveVoiceChannel();
    }
    
    try {
        // Get user's microphone
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        
        currentChannelId = channelId;
        
        // Notify server
        window.ws.send(JSON.stringify({
            type: 'join-voice-channel',
            channel_id: channelId
        }));
        
        updateChannelVoiceUI(channelId, true);
        
    } catch (error) {
        console.error('Error joining voice channel:', error);
        alert('Could not access microphone. Please check permissions.');
    }
}

/**
 * Leave current voice channel
 */
export async function leaveVoiceChannel() {
    if (!currentChannelId) return;
    
    // Notify server
    window.ws.send(JSON.stringify({
        type: 'leave-voice-channel',
        channel_id: currentChannelId
    }));
    
    // Close all peer connections
    Object.values(peerConnections).forEach(pc => pc.close());
    peerConnections = {};
    
    // Stop local stream
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }
    
    updateChannelVoiceUI(currentChannelId, false);
    currentChannelId = null;
    isMuted = false;
}

/**
 * Handle existing users in channel (sent when joining)
 */
export async function handleChannelUsers(channelId, userIds) {
    if (channelId !== currentChannelId) return;
    
    // Create peer connections with all existing users
    for (const userId of userIds) {
        await createPeerConnectionAndOffer(userId, channelId);
    }
}

/**
 * Handle new user joining channel
 */
export async function handleUserJoinedVoice(userId, username) {
    if (!currentChannelId) return;
    
    console.log(`${username} joined voice channel`);
    // Wait for them to send us an offer (they will call createPeerConnectionAndOffer)
}

/**
 * Handle user leaving channel
 */
export function handleUserLeftVoice(userId, username) {
    if (!currentChannelId) return;
    
    console.log(`${username} left voice channel`);
    
    // Close peer connection with that user
    if (peerConnections[userId]) {
        peerConnections[userId].close();
        delete peerConnections[userId];
    }
}

/**
 * Create peer connection and send offer to a user
 */
async function createPeerConnectionAndOffer(userId, channelId) {
    if (peerConnections[userId]) return; // Already connected
    
    try {
        // Create peer connection
        const pc = new RTCPeerConnection(configuration);
        peerConnections[userId] = pc;
        
        // Add local stream
        if (localStream) {
            localStream.getTracks().forEach(track => {
                pc.addTrack(track, localStream);
            });
        }
        
        // Handle ICE candidates
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                window.ws.send(JSON.stringify({
                    type: 'channel-ice-candidate',
                    target_user_id: userId,
                    channel_id: channelId,
                    candidate: event.candidate
                }));
            }
        };
        
        // Handle remote stream
        pc.ontrack = (event) => {
            console.log(`Received remote track from user ${userId}:`, event);
            const remoteAudio = new Audio();
            remoteAudio.srcObject = event.streams[0];
            remoteAudio.autoplay = true;
            remoteAudio.volume = 1.0;
            remoteAudio.play().then(() => {
                console.log(`Remote audio playing from user ${userId}`);
            }).catch(err => {
                console.error(`Error playing remote audio from user ${userId}:`, err);
            });
            
            // Store audio element for this user
            remoteAudio.dataset.userId = userId;
        };
        
        // Handle connection state
        pc.onconnectionstatechange = () => {
            console.log(`Connection state with user ${userId}:`, pc.connectionState);
            if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
                if (peerConnections[userId]) {
                    peerConnections[userId].close();
                    delete peerConnections[userId];
                }
            }
        };
        
        // Create and send offer
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        
        window.ws.send(JSON.stringify({
            type: 'channel-voice-offer',
            target_user_id: userId,
            channel_id: channelId,
            offer: offer
        }));
        
    } catch (error) {
        console.error('Error creating peer connection:', error);
    }
}

/**
 * Handle incoming voice offer from channel user
 */
export async function handleChannelVoiceOffer(fromUserId, channelId, offer) {
    if (channelId !== currentChannelId) return;
    if (peerConnections[fromUserId]) return; // Already have connection
    
    try {
        // Create peer connection
        const pc = new RTCPeerConnection(configuration);
        peerConnections[fromUserId] = pc;
        
        // Add local stream
        if (localStream) {
            localStream.getTracks().forEach(track => {
                pc.addTrack(track, localStream);
            });
        }
        
        // Handle ICE candidates
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                window.ws.send(JSON.stringify({
                    type: 'channel-ice-candidate',
                    target_user_id: fromUserId,
                    channel_id: channelId,
                    candidate: event.candidate
                }));
            }
        };
        
        // Handle remote stream
        pc.ontrack = (event) => {
            console.log('Received remote track from user', fromUserId);
            const remoteAudio = new Audio();
            remoteAudio.srcObject = event.streams[0];
            remoteAudio.autoplay = true;
            remoteAudio.volume = 1.0;
            remoteAudio.play()
                .then(() => console.log('Channel remote audio playing successfully for user', fromUserId))
                .catch(err => console.error('Error playing channel remote audio:', err));
            
            // Store audio element for this user
            remoteAudio.dataset.userId = fromUserId;
        };
        
        // Handle connection state
        pc.onconnectionstatechange = () => {
            console.log(`Connection state with user ${fromUserId}:`, pc.connectionState);
            if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
                if (peerConnections[fromUserId]) {
                    peerConnections[fromUserId].close();
                    delete peerConnections[fromUserId];
                }
            }
        };
        
        // Set remote description and create answer
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        
        // Send answer
        window.ws.send(JSON.stringify({
            type: 'channel-voice-answer',
            target_user_id: fromUserId,
            channel_id: channelId,
            answer: answer
        }));
        
    } catch (error) {
        console.error('Error handling voice offer:', error);
    }
}

/**
 * Handle voice answer from channel user
 */
export async function handleChannelVoiceAnswer(fromUserId, channelId, answer) {
    if (channelId !== currentChannelId) return;
    
    const pc = peerConnections[fromUserId];
    if (!pc) {
        console.error('No peer connection for answer from user:', fromUserId);
        return;
    }
    
    try {
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (error) {
        console.error('Error handling voice answer:', error);
    }
}

/**
 * Handle ICE candidate from channel user
 */
export async function handleChannelIceCandidate(fromUserId, channelId, candidate) {
    if (channelId !== currentChannelId) return;
    
    const pc = peerConnections[fromUserId];
    if (!pc) {
        console.error('No peer connection for ICE candidate from user:', fromUserId);
        return;
    }
    
    try {
        await pc.addIceCandidate(new RTCIceCandidate(candidate));
    } catch (error) {
        console.error('Error adding ICE candidate:', error);
    }
}

/**
 * Toggle mute in channel
 */
export function toggleChannelMute() {
    if (!localStream) return;
    
    isMuted = !isMuted;
    localStream.getAudioTracks().forEach(track => {
        track.enabled = !isMuted;
    });
    
    updateMuteUI();
}

/**
 * Update channel voice UI
 */
function updateChannelVoiceUI(channelId, isJoined) {
    const channelElement = document.querySelector(`.channel-item[data-channel-id="${channelId}"]`);
    if (channelElement) {
        if (isJoined) {
            channelElement.classList.add('voice-active');
        } else {
            channelElement.classList.remove('voice-active');
        }
    }
    
    // Update voice controls in server modal
    const voiceControls = document.getElementById('voiceControls');
    if (voiceControls) {
        voiceControls.style.display = isJoined ? 'flex' : 'none';
    }
}

/**
 * Update mute UI
 */
function updateMuteUI() {
    const muteBtn = document.getElementById('channelMuteBtn');
    if (muteBtn) {
        if (isMuted) {
            muteBtn.classList.add('muted');
            muteBtn.textContent = '🔇 Unmute';
        } else {
            muteBtn.classList.remove('muted');
            muteBtn.textContent = '🎤 Mute';
        }
    }
}

/**
 * Get current channel ID
 */
export function getCurrentChannelId() {
    return currentChannelId;
}

/**
 * Check if in a voice channel
 */
export function isInVoiceChannel() {
    return currentChannelId !== null;
}

// Export for window access
window.channelVoice = {
    joinVoiceChannel,
    leaveVoiceChannel,
    toggleChannelMute,
    isInVoiceChannel,
    getCurrentChannelId
};
