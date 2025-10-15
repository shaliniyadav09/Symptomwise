// Main JavaScript File

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize form enhancements
    initializeFormEnhancements();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize auto-hide messages
    initializeAutoHideMessages();
    
    console.log('HealthCare Pro app initialized');
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize scroll animations
function initializeAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in-up');
            }
        });
    }, observerOptions);
    
    // Observe elements with animation classes
    document.querySelectorAll('.card, .feature-card, .service-card, .doctor-card').forEach(el => {
        observer.observe(el);
    });
}

// Enhance form functionality
function initializeFormEnhancements() {
    // Add floating labels effect
    const formControls = document.querySelectorAll('.form-control');
    formControls.forEach(control => {
        control.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        control.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Check if already has value
        if (control.value) {
            control.parentElement.classList.add('focused');
        }
    });
    
    // Add form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Show validation feedback
                showFormValidationErrors(form);
            }
            form.classList.add('was-validated');
        });
    });
}

// Show form validation errors
function showFormValidationErrors(form) {
    const invalidFields = form.querySelectorAll(':invalid');
    if (invalidFields.length > 0) {
        invalidFields[0].focus();
        showMessage('Please fill in all required fields correctly.', 'warning');
    }
}

// Initialize smooth scrolling for anchor links
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Auto-hide messages after 5 seconds
function initializeAutoHideMessages() {
    const messages = document.querySelectorAll('.alert');
    messages.forEach(message => {
        setTimeout(() => {
            if (message.parentElement) {
                message.classList.remove('show');
                setTimeout(() => {
                    if (message.parentElement) {
                        message.remove();
                    }
                }, 150);
            }
        }, 5000);
    });
}

// Utility function to show messages
function showMessage(text, type = 'info') {
    const messagesContainer = document.querySelector('.messages-container') || createMessagesContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${text}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    messagesContainer.appendChild(alertDiv);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.classList.remove('show');
            setTimeout(() => {
                if (alertDiv.parentElement) {
                    alertDiv.remove();
                }
            }, 150);
        }
    }, 5000);
}

// Create messages container if it doesn't exist
function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

// Loading state management
function showLoading(element) {
    const originalContent = element.innerHTML;
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    element.disabled = true;
    
    return function hideLoading() {
        element.innerHTML = originalContent;
        element.disabled = false;
    };
}

// AJAX form submission helper
function submitFormAjax(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    const hideLoading = showLoading(form.querySelector('button[type="submit"]'));
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            if (successCallback) successCallback(data);
            showMessage(data.message || 'Operation completed successfully!', 'success');
        } else {
            if (errorCallback) errorCallback(data);
            showMessage(data.message || 'An error occurred.', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        if (errorCallback) errorCallback(error);
        showMessage('An unexpected error occurred.', 'danger');
    });
}

// Export functions for global use
window.HealthCarePro = {
    showMessage,
    showLoading,
    submitFormAjax
};