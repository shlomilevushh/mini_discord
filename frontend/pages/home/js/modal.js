// Friend modal management
const modal = document.getElementById('addFriendModal');
const addFriendForm = document.getElementById('add-friend-form');
const errorDiv = document.getElementById('add-friend-error');
const successDiv = document.getElementById('add-friend-success');

export function openAddFriendModal() {
    modal.classList.add('show');
    document.getElementById('friend-username').value = '';
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
}

export function closeAddFriendModal() {
    modal.classList.remove('show');
}

// Close modal when clicking outside
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeAddFriendModal();
    }
});

// Add friend form submission
addFriendForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';

    const username = document.getElementById('friend-username').value;
    const formData = new FormData();
    formData.append('username', username);

    try {
        const response = await fetch('/api/friends/request', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            successDiv.textContent = data.message;
            successDiv.style.display = 'block';
            setTimeout(() => {
                closeAddFriendModal();
                location.reload();
            }, 1500);
        } else {
            errorDiv.textContent = data.message;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Error sending request: ' + error.message;
        errorDiv.style.display = 'block';
    }
});
