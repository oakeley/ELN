// auth.js - Handles authentication functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle tab switching between login, register, and reset
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const resetTab = document.getElementById('reset-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const resetForm = document.getElementById('reset-form');

    if (loginTab && registerTab && resetTab) {
        loginTab.addEventListener('click', function(e) {
            e.preventDefault();
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            resetTab.classList.remove('active');
            loginForm.classList.remove('d-none');
            registerForm.classList.add('d-none');
            resetForm.classList.add('d-none');
        });

        registerTab.addEventListener('click', function(e) {
            e.preventDefault();
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            resetTab.classList.remove('active');
            registerForm.classList.remove('d-none');
            loginForm.classList.add('d-none');
            resetForm.classList.add('d-none');
        });

        resetTab.addEventListener('click', function(e) {
            e.preventDefault();
            resetTab.classList.add('active');
            loginTab.classList.remove('active');
            registerTab.classList.remove('active');
            resetForm.classList.remove('d-none');
            loginForm.classList.add('d-none');
            registerForm.classList.add('d-none');
        });
    }

    // Handle forgot password link
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    if (forgotPasswordLink && resetTab) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            resetTab.click();
        });
    }

    // Handle login form submission
    const loginFormElement = document.getElementById('login-form');
    if (loginFormElement) {
        loginFormElement.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/projects';
                } else {
                    const loginError = document.getElementById('login-error');
                    loginError.textContent = data.message || 'Login failed. Please check your credentials.';
                    loginError.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const loginError = document.getElementById('login-error');
                loginError.textContent = 'An error occurred during login. Please try again.';
                loginError.classList.remove('d-none');
            });
        });
    }

    // Handle register form submission
    const registerFormElement = document.getElementById('register-form');
    if (registerFormElement) {
        registerFormElement.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const confirmPassword = document.getElementById('register-confirm-password').value;
            
            // Basic validation
            if (password !== confirmPassword) {
                const registerError = document.getElementById('register-error');
                registerError.textContent = 'Passwords do not match';
                registerError.classList.remove('d-none');
                return;
            }
            
            fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/projects';
                } else {
                    const registerError = document.getElementById('register-error');
                    registerError.textContent = data.message || 'Registration failed. Please try again.';
                    registerError.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const registerError = document.getElementById('register-error');
                registerError.textContent = 'An error occurred during registration. Please try again.';
                registerError.classList.remove('d-none');
            });
        });
    }

    // Handle reset password form submission
    const resetFormElement = document.getElementById('reset-form');
    if (resetFormElement) {
        resetFormElement.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('reset-username').value;
            const newPassword = document.getElementById('reset-new-password').value;
            const confirmPassword = document.getElementById('reset-confirm-password').value;
            
            // Basic validation
            if (newPassword !== confirmPassword) {
                const resetError = document.getElementById('reset-error');
                resetError.textContent = 'Passwords do not match';
                resetError.classList.remove('d-none');
                return;
            }
            
            fetch('/api/auth/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    new_password: newPassword
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Password has been reset. Please login with your new password.');
                    // Switch to login tab
                    if (loginTab) {
                        loginTab.click();
                    }
                } else {
                    const resetError = document.getElementById('reset-error');
                    resetError.textContent = data.message || 'Password reset failed. Please try again.';
                    resetError.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const resetError = document.getElementById('reset-error');
                resetError.textContent = 'An error occurred during password reset. Please try again.';
                resetError.classList.remove('d-none');
            });
        });
    }
});
