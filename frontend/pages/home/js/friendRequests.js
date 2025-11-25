// Friend request management

// Accept friend request
export async function acceptRequest(requestId) {
    try {
        const response = await fetch(`/api/friends/accept/${requestId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            location.reload();
        } else {
            console.error(data.message);
        }
    } catch (error) {
        console.error('Error accepting request:', error);
    }
}

// Decline friend request
export async function declineRequest(requestId) {
    try {
        const response = await fetch(`/api/friends/decline/${requestId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            location.reload();
        } else {
            console.error(data.message);
        }
    } catch (error) {
        console.error('Error declining request:', error);
    }
}
