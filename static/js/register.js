document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const usernameFeedback = document.getElementById('username-feedback');
    const emailFeedback = document.getElementById('email-feedback');
    const submitBtn = document.querySelector('button[type="submit"]');
    
    // Debounce function to limit API calls
    const debounce = (func, delay) => {
        let timeoutId;
        return function(...args) {
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };
    
    // Check if username exists
    const checkUsername = debounce(async (username) => {
        if (username.length < 3) {
            usernameFeedback.textContent = 'Username must be at least 3 characters';
            usernameFeedback.className = 'invalid-feedback d-block';
            usernameInput.classList.add('is-invalid');
            return;
        }
        
        try {
            const response = await fetch(`/api/check-username?username=${encodeURIComponent(username)}`);
            const data = await response.json();
            
            if (data.exists) {
                usernameFeedback.textContent = 'Username is already taken';
                usernameFeedback.className = 'invalid-feedback d-block';
                usernameInput.classList.add('is-invalid');
            } else {
                usernameFeedback.textContent = 'Username is available';
                usernameFeedback.className = 'valid-feedback d-block';
                usernameInput.classList.remove('is-invalid');
                usernameInput.classList.add('is-valid');
            }
        } catch (error) {
            console.error('Error checking username:', error);
        }
    }, 500);
    
    // Check if email exists
    const checkEmail = debounce(async (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            emailFeedback.textContent = 'Please enter a valid email address';
            emailFeedback.className = 'invalid-feedback d-block';
            emailInput.classList.add('is-invalid');
            return;
        }
        
        try {
            const response = await fetch(`/api/check-email?email=${encodeURIComponent(email)}`);
            const data = await response.json();
            
            if (data.exists) {
                emailFeedback.textContent = 'Email is already registered';
                emailFeedback.className = 'invalid-feedback d-block';
                emailInput.classList.add('is-invalid');
            } else {
                emailFeedback.textContent = 'Email is available';
                emailFeedback.className = 'valid-feedback d-block';
                emailInput.classList.remove('is-invalid');
                emailInput.classList.add('is-valid');
            }
        } catch (error) {
            console.error('Error checking email:', error);
        }
    }, 500);
    
    // Event listeners
    if (usernameInput) {
        usernameInput.addEventListener('input', (e) => {
            const username = e.target.value.trim();
            if (username.length > 0) {
                checkUsername(username);
            } else {
                usernameFeedback.textContent = '';
                usernameInput.classList.remove('is-invalid', 'is-valid');
            }
        });
    }
    
    if (emailInput) {
        emailInput.addEventListener('input', (e) => {
            const email = e.target.value.trim();
            if (email.length > 0) {
                checkEmail(email);
            } else {
                emailFeedback.textContent = '';
                emailInput.classList.remove('is-invalid', 'is-valid');
            }
        });
    }
    
    // Form submission validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            const invalidInputs = form.querySelectorAll('.is-invalid');
            if (invalidInputs.length > 0) {
                e.preventDefault();
                invalidInputs[0].focus();
            }
        });
    }
});
