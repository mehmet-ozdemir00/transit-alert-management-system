import { CONTACT_API_URL } from "./config";

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('contact');
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Validate form
    if (!validateForm(data)) {
      return;
    }
    
    try {
      // Simulate form submission (replace with actual fetch to your backend)
      await submitForm(data);
      
      // Show success message
      showFeedback('Message sent successfully!', 'success');
      form.reset();
    } catch (error) {
      showFeedback('Failed to send message. Please try again.', 'error');
      console.error('Submission error:', error);
    }
  });
  
  // Form validation function
  const validateForm = (data) => {
    const { name, email, message } = data;
    
    // Clear previous error messages
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    
    let isValid = true;
    
    if (!name.trim()) {
      showError('name', 'Name is required');
      isValid = false;
    }
    
    if (!email.trim()) {
      showError('email', 'Email is required');
      isValid = false;
    } else if (!isValidEmail(email)) {
      showError('email', 'Please enter a valid email');
      isValid = false;
    }
    
    if (!message.trim()) {
      showError('message', 'Message is required');
      isValid = false;
    } else if (message.trim().length < 10) {
      showError('message', 'Message should be at least 10 characters');
      isValid = false;
    }
    
    return isValid;
  };
  
  // Helper function to show error messages
  const showError = (fieldId, message) => {
    const field = document.getElementById(fieldId);
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.style.color = '#ff3860';
    errorElement.style.fontSize = '0.8em';
    errorElement.style.marginTop = '0.25rem';
    errorElement.textContent = message;
    
    // Insert after the field
    field.insertAdjacentElement('afterend', errorElement);
    
    // Highlight the field
    field.style.borderColor = '#ff3860';
    
    // Remove error styling when user starts typing
    field.addEventListener('input', () => {
      field.style.borderColor = '';
      errorElement.remove();
    }, { once: true });
  };
  
  // Email validation helper
  const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };
  
  // Simulated form submission (replace with actual fetch)
  const submitForm = (data) => {
    return new Promise((resolve, reject) => {
      // Simulate network delay
      setTimeout(() => {
        console.log('Form data to be submitted:', data);
        // In a real app, you would use fetch() to send to your backend
        // return fetch('/api/contact', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(data)
        // });
        resolve();
      }, 1000);
    });
  };
  
  // Show feedback message
  const showFeedback = (message, type) => {
    // Remove any existing feedback
    const existingFeedback = document.querySelector('.form-feedback');
    if (existingFeedback) existingFeedback.remove();
    
    const feedbackElement = document.createElement('div');
    feedbackElement.className = `form-feedback ${type}`;
    feedbackElement.textContent = message;
    feedbackElement.style.padding = '1rem';
    feedbackElement.style.margin = '1rem 0';
    feedbackElement.style.borderRadius = '4px';
    feedbackElement.style.color = type === 'error' ? '#ff3860' : '#23d160';
    feedbackElement.style.backgroundColor = type === 'error' ? '#feecf0' : '#effaf3';
    
    // Insert before the form
    form.parentNode.insertBefore(feedbackElement, form);
    
    // Remove after 5 seconds
    setTimeout(() => {
      feedbackElement.remove();
    }, 5000);
  };
});