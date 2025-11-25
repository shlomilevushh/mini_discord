/**
 * Voice Call Module - Handles 1-on-1 voice calls using WebRTC
 */

let peerConnection = null;
let localStream = null;
let currentCallUserId = null;
let isMuted = false;

// WebRTC configuration (using public STUN servers)
const configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

/**
 * Initialize voice call - start calling a friend
 */
export async function startVoiceCall(targetUserId, targetUsername) {
    if (currentCallUserId) {
        alert('You are already in a call!');
        return;
    }
    
    try {
        // Get user's microphone
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        
        // Create peer connection
        peerConnection = new RTCPeerConnection(configuration);
        
        // Add local stream to peer connection
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                window.ws.send(JSON.stringify({
                    type: 'ice-candidate',
                    target_user_id: targetUserId,
                    candidate: event.candidate
                }));
            }
        };
        
        // Handle remote stream
        peerConnection.ontrack = (event) => {
            console.log('Received remote track:', event);
            const remoteAudio = new Audio();
            remoteAudio.srcObject = event.streams[0];
            remoteAudio.autoplay = true;
            remoteAudio.volume = 1.0;
            remoteAudio.play().then(() => {
                console.log('Remote audio playing successfully');
            }).catch(err => {
                console.error('Error playing remote audio:', err);
            });
        };
        
        // Create and send offer
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        
        window.ws.send(JSON.stringify({
            type: 'voice-call-offer',
            target_user_id: targetUserId,
            offer: offer
        }));
        
        currentCallUserId = targetUserId;
        showCallUI(targetUsername, true);
        
    } catch (error) {
        console.error('Error starting call:', error);
        alert('Could not access microphone. Please check permissions.');
        endVoiceCall();
    }
}

/**
 * Handle incoming call offer
 */
export async function handleCallOffer(fromUserId, fromUsername, offer) {
    if (currentCallUserId) {
        // Already in a call, reject
        window.ws.send(JSON.stringify({
            type: 'call-end',
            target_user_id: fromUserId
        }));
        return;
    }
    
    // Ask user if they want to accept the call
    const accept = confirm(`${fromUsername} is calling you. Accept?`);
    
    if (!accept) {
        window.ws.send(JSON.stringify({
            type: 'call-end',
            target_user_id: fromUserId
        }));
        return;
    }
    
    try {
        // Get user's microphone
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        
        // Create peer connection
        peerConnection = new RTCPeerConnection(configuration);
        
        // Add local stream
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                window.ws.send(JSON.stringify({
                    type: 'ice-candidate',
                    target_user_id: fromUserId,
                    candidate: event.candidate
                }));
            }
        };
        
        // Handle remote stream
        peerConnection.ontrack = (event) => {
            console.log('Received remote track (answerer):', event);
            const remoteAudio = new Audio();
            remoteAudio.srcObject = event.streams[0];
            remoteAudio.autoplay = true;
            remoteAudio.volume = 1.0;
            remoteAudio.play().then(() => {
                console.log('Remote audio playing successfully (answerer)');
            }).catch(err => {
                console.error('Error playing remote audio (answerer):', err);
            });
        };
        
        // Set remote description and create answer
        await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        
        // Send answer
        window.ws.send(JSON.stringify({
            type: 'voice-call-answer',
            target_user_id: fromUserId,
            answer: answer
        }));
        
        currentCallUserId = fromUserId;
        showCallUI(fromUsername, false);
        
    } catch (error) {
        console.error('Error answering call:', error);
        alert('Could not access microphone. Please check permissions.');
        endVoiceCall();
    }
}

/**
 * Handle call answer
 */
export async function handleCallAnswer(fromUserId, answer) {
    if (!peerConnection) {
        console.error('No peer connection for answer');
        return;
    }
    
    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (error) {
        console.error('Error handling answer:', error);
    }
}

/**
 * Handle ICE candidate
 */
export async function handleIceCandidate(fromUserId, candidate) {
    if (!peerConnection) {
        console.error('No peer connection for ICE candidate');
        return;
    }
    
    try {
        await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
    } catch (error) {
        console.error('Error adding ICE candidate:', error);
    }
}

/**
 * End current voice call
 */
export function endVoiceCall() {
    // Notify other user
    if (currentCallUserId) {
        window.ws.send(JSON.stringify({
            type: 'call-end',
            target_user_id: currentCallUserId
        }));
    }
    
    // Close peer connection
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    
    // Stop local stream
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }
    
    currentCallUserId = null;
    isMuted = false;
    hideCallUI();
}

/**
 * Handle remote call end
 */
export function handleCallEnd(fromUserId) {
    if (fromUserId === currentCallUserId) {
        endVoiceCall();
    }
}

/**
 * Toggle mute/unmute
 */
export function toggleMute() {
    if (!localStream) return;
    
    isMuted = !isMuted;
    localStream.getAudioTracks().forEach(track => {
        track.enabled = !isMuted;
    });
    
    updateMuteButton();
}

/**
 * Show call UI
 */
function showCallUI(username, isCaller) {
    const callUI = document.getElementById('callUI');
    if (!callUI) {
        // Create call UI if it doesn't exist
        const ui = document.createElement('div');
        ui.id = 'callUI';
        ui.className = 'call-ui';
        ui.innerHTML = `
            <div class="call-info">
                <div class="call-avatar">🎤</div>
                <div class="call-username" id="callUsername"></div>
                <div class="call-status" id="callStatus">Connected</div>
            </div>
            <div class="call-controls">
                <button class="call-btn mute-btn" id="muteBtn" onclick="window.voiceCall.toggleMute()">
                    <span class="mute-icon">🎤</span>
                </button>
                <button class="call-btn end-call-btn" onclick="window.voiceCall.endVoiceCall()">
                    📞 End Call
                </button>
            </div>
        `;
        document.body.appendChild(ui);
    }
    
    document.getElementById('callUsername').textContent = username;
    document.getElementById('callStatus').textContent = isCaller ? 'Calling...' : 'Connected';
    document.getElementById('callUI').style.display = 'block';
}

/**
 * Hide call UI
 */
function hideCallUI() {
    const callUI = document.getElementById('callUI');
    if (callUI) {
        callUI.style.display = 'none';
    }
}

/**
 * Update mute button
 */
function updateMuteButton() {
    const muteBtn = document.getElementById('muteBtn');
    const muteIcon = document.querySelector('.mute-icon');
    if (muteBtn && muteIcon) {
        if (isMuted) {
            muteBtn.classList.add('muted');
            muteIcon.textContent = '🔇';
        } else {
            muteBtn.classList.remove('muted');
            muteIcon.textContent = '🎤';
        }
    }
}

/**
 * Check if currently in a call
 */
export function isInCall() {
    return currentCallUserId !== null;
}

// Export for window access
window.voiceCall = {
    startVoiceCall,
    endVoiceCall,
    toggleMute,
    isInCall
};
