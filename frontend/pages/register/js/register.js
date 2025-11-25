// Register page functionality
const registerForm = document.getElementById('register-form');
const avatarOptions = document.querySelectorAll('.avatar-option');

// Handle avatar selection styling
avatarOptions.forEach(option => {
    option.addEventListener('click', function() {
        avatarOptions.forEach(opt => opt.classList.remove('selected'));
        this.classList.add('selected');
        // Clear avatar error when selected
        document.getElementById('avatar-error').style.display = 'none';
    });
});

function clearErrors() {
    document.getElementById('email-error').style.display = 'none';
    document.getElementById('username-error').style.display = 'none';
    document.getElementById('password-error').style.display = 'none';
    document.getElementById('avatar-error').style.display = 'none';
}

function showError(fieldId, message) {
    const errorElement = document.getElementById(fieldId + '-error');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const avatar = document.querySelector('input[name="avatar"]:checked');

    // Validate avatar selection
    if (!avatar) {
        showError('avatar', 'Please select an avatar!');
        return;
    }

    // Create form data
    const formData = new FormData();
    formData.append('email', email);
    formData.append('username', username);
    formData.append('password', password);
    formData.append('avatar', avatar.value);

    try {
        // Send POST request to server
        const response = await fetch('/register', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Redirect to login page with success parameter
            window.location.href = '/?registered=true';
        } else {
            // Determine which field has the error and show it
            const message = data.message.toLowerCase();
            if (message.includes('email')) {
                showError('email', data.message);
            } else if (message.includes('username')) {
                showError('username', data.message);
            } else if (message.includes('password')) {
                showError('password', data.message);
            } else {
                showError('email', data.message);
            }
        }
    } catch (error) {
        showError('email', 'Error connecting to server: ' + error.message);
    }
});
