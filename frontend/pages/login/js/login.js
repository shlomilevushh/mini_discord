// Login page functionality
const loginForm = document.getElementById('login-form');
const successMessage = document.getElementById('success-message');
const loginError = document.getElementById('login-error');

// Check for success message from registration
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('registered') === 'true') {
    successMessage.textContent = '✓ Registration successful! Please log in with your credentials.';
    successMessage.style.display = 'block';
}

// Check for unauthorized access error
if (urlParams.get('error') === 'unauthorized') {
    loginError.textContent = 'Please log in to access that page.';
    loginError.style.display = 'block';
}

function clearErrors() {
    document.getElementById('email-error').style.display = 'none';
    document.getElementById('password-error').style.display = 'none';
    loginError.style.display = 'none';
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Create form data
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);

    try {
        // Send POST request to server
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // If login successful, redirect to home immediately
        if (data.success) {
            window.location.href = '/home';
        } else {
            // Show error message
            loginError.textContent = data.message;
            loginError.style.display = 'block';
        }
    } catch (error) {
        loginError.textContent = 'Error connecting to server: ' + error.message;
        loginError.style.display = 'block';
    }
});
