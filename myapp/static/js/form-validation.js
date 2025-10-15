/**
 * Comprehensive Form Validation Library
 * Provides real-time validation for all forms in the application
 */

class FormValidator {
    constructor() {
        this.validators = {
            required: this.validateRequired,
            email: this.validateEmail,
            phone: this.validatePhone,
            name: this.validateName,
            date: this.validateDate,
            futureDate: this.validateFutureDate,
            pastDate: this.validatePastDate,
            zipcode: this.validateZipcode,
            minLength: this.validateMinLength,
            maxLength: this.validateMaxLength,
            numeric: this.validateNumeric,
            alphanumeric: this.validateAlphanumeric
        };
        
        this.init();
    }
    
    init() {
        // Auto-initialize validation on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeFormValidation();
        });
    }
    
    initializeFormValidation() {
        // Find all forms with validation
        const forms = document.querySelectorAll('form[data-validate="true"], .needs-validation');
        
        forms.forEach(form => {
            this.setupFormValidation(form);
        });
        
        // Also setup validation for common form fields
        this.setupCommonValidations();
    }
    
    setupFormValidation(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Add real-time validation
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearErrors(input));
            
            // Special handling for specific field types
            if (input.type === 'email') {
                input.addEventListener('input', () => this.validateField(input, 'email'));
            }
            
            if (input.name === 'phone' || input.type === 'tel') {
                input.addEventListener('input', () => this.validateField(input, 'phone'));
            }
            
            if (input.name && (input.name.includes('name') || input.name.includes('Name'))) {
                input.addEventListener('input', () => this.validateField(input, 'name'));
            }
        });
        
        // Prevent form submission if validation fails
        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
                this.showFormErrors(form);
            }
        });
    }
    
    setupCommonValidations() {
        // Phone number fields
        const phoneFields = document.querySelectorAll('input[name="phone"], input[type="tel"], input[name*="phone"]');
        phoneFields.forEach(field => {
            field.addEventListener('input', () => this.validateField(field, 'phone'));
            field.addEventListener('blur', () => this.validateField(field, 'phone'));
        });
        
        // Email fields
        const emailFields = document.querySelectorAll('input[type="email"], input[name="email"]');
        emailFields.forEach(field => {
            field.addEventListener('input', () => this.validateField(field, 'email'));
            field.addEventListener('blur', () => this.validateField(field, 'email'));
        });
        
        // Name fields
        const nameFields = document.querySelectorAll('input[name*="name"], input[name*="Name"]');
        nameFields.forEach(field => {
            field.addEventListener('input', () => this.validateField(field, 'name'));
            field.addEventListener('blur', () => this.validateField(field, 'name'));
        });
        
        // Date fields
        const dateFields = document.querySelectorAll('input[type="date"]');
        dateFields.forEach(field => {
            if (field.name && field.name.includes('birth')) {
                field.addEventListener('change', () => this.validateField(field, 'pastDate'));
            } else if (field.name && field.name.includes('appointment')) {
                field.addEventListener('change', () => this.validateField(field, 'futureDate'));
            } else {
                field.addEventListener('change', () => this.validateField(field, 'date'));
            }
        });
        
        // Zipcode fields
        const zipcodeFields = document.querySelectorAll('input[name="zipcode"], input[name="zip"], input[name="postal_code"]');
        zipcodeFields.forEach(field => {
            field.addEventListener('input', () => this.validateField(field, 'zipcode'));
            field.addEventListener('blur', () => this.validateField(field, 'zipcode'));
        });
    }
    
    validateField(field, validationType = null) {
        const value = field.value.trim();
        const fieldName = field.name || field.id || 'field';
        let isValid = true;
        let errorMessage = '';
        
        // Check if field is required
        if (field.required && !value) {
            isValid = false;
            errorMessage = `${this.getFieldLabel(field)} is required.`;
        } else if (value) {
            // Apply specific validation based on type
            if (validationType) {
                const result = this.validators[validationType].call(this, value, field);
                isValid = result.isValid;
                errorMessage = result.message;
            } else {
                // Auto-detect validation type
                if (field.type === 'email') {
                    const result = this.validators.email.call(this, value, field);
                    isValid = result.isValid;
                    errorMessage = result.message;
                } else if (field.name === 'phone' || field.type === 'tel') {
                    const result = this.validators.phone.call(this, value, field);
                    isValid = result.isValid;
                    errorMessage = result.message;
                }
            }
        }
        
        // Update field appearance and show/hide error
        this.updateFieldValidation(field, isValid, errorMessage);
        
        return isValid;
    }
    
    validateForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        let isFormValid = true;
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isFormValid = false;
            }
        });
        
        return isFormValid;
    }
    
    // Validation methods
    validateRequired(value) {
        return {
            isValid: value.trim() !== '',
            message: 'This field is required.'
        };
    }
    
    validateEmail(value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isValid = emailRegex.test(value);
        
        return {
            isValid: isValid,
            message: isValid ? '' : 'Please enter a valid email address.'
        };
    }
    
    validatePhone(value) {
        // Remove all non-digit characters
        const cleanPhone = value.replace(/\D/g, '');
        
        // Check if it's exactly 10 digits
        if (cleanPhone.length !== 10) {
            return {
                isValid: false,
                message: 'Phone number must be exactly 10 digits.'
            };
        }
        
        // Check if it's all zeros
        if (cleanPhone === '0000000000') {
            return {
                isValid: false,
                message: 'Phone number cannot be all zeros.'
            };
        }
        
        // Check if it starts with 0 (invalid for Indian mobile numbers)
        if (cleanPhone.startsWith('0')) {
            return {
                isValid: false,
                message: 'Please enter a valid mobile number (should not start with 0).'
            };
        }
        
        return {
            isValid: true,
            message: ''
        };
    }
    
    validateName(value) {
        // Only letters, spaces, and common name characters
        const nameRegex = /^[a-zA-Z\s\.\-']+$/;
        const isValid = nameRegex.test(value) && value.length >= 2;
        
        return {
            isValid: isValid,
            message: isValid ? '' : 'Name should contain only letters and be at least 2 characters long.'
        };
    }
    
    validateDate(value) {
        const date = new Date(value);
        const isValid = !isNaN(date.getTime());
        
        return {
            isValid: isValid,
            message: isValid ? '' : 'Please enter a valid date.'
        };
    }
    
    validateFutureDate(value) {
        const date = new Date(value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (isNaN(date.getTime())) {
            return {
                isValid: false,
                message: 'Please enter a valid date.'
            };
        }
        
        const isValid = date >= today;
        
        return {
            isValid: isValid,
            message: isValid ? '' : 'Date must be today or in the future.'
        };
    }
    
    validatePastDate(value) {
        const date = new Date(value);
        const today = new Date();
        
        if (isNaN(date.getTime())) {
            return {
                isValid: false,
                message: 'Please enter a valid date.'
            };
        }
        
        const isValid = date < today;
        
        return {
            isValid: isValid,
            message: isValid ? '' : 'Date must be in the past.'
        };
    }
    
    validateZipcode(value) {
        // Indian pincode format (6 digits)
        const cleanZipcode = value.replace(/\D/g, '');
        
        // Check if it's exactly 6 digits
        if (cleanZipcode.length !== 6) {
            return {
                isValid: false,
                message: 'Zipcode must be exactly 6 digits.'
            };
        }
        
        // Check if it's all zeros
        if (cleanZipcode === '000000') {
            return {
                isValid: false,
                message: 'Zipcode cannot be all zeros.'
            };
        }
        
        // Check if it starts with 0 (invalid for Indian pincodes)
        if (cleanZipcode.startsWith('0')) {
            return {
                isValid: false,
                message: 'Indian pincode cannot start with 0.'
            };
        }
        
        return {
            isValid: true,
            message: ''
        };
    }
    
    validateMinLength(value, field) {
        const minLength = parseInt(field.getAttribute('data-min-length')) || 0;
        const isValid = value.length >= minLength;
        
        return {
            isValid: isValid,
            message: isValid ? '' : `Minimum length is ${minLength} characters.`
        };
    }
    
    validateMaxLength(value, field) {
        const maxLength = parseInt(field.getAttribute('data-max-length')) || Infinity;
        const isValid = value.length <= maxLength;
        
        return {
            isValid: isValid,
            message: isValid ? '' : `Maximum length is ${maxLength} characters.`
        };
    }
    
    validateNumeric(value) {
        const isValid = /^\d+$/.test(value);
        
        return {
            isValid: isValid,
            message: isValid ? '' : 'This field should contain only numbers.'
        };
    }
    
    validateAlphanumeric(value) {
        const isValid = /^[a-zA-Z0-9]+$/.test(value);
        
        return {
            isValid: isValid,
            message: isValid ? '' : 'This field should contain only letters and numbers.'
        };
    }
    
    // UI Helper methods
    updateFieldValidation(field, isValid, errorMessage) {
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid', 'valid', 'invalid');
        
        // Add appropriate class
        if (isValid) {
            field.classList.add('is-valid', 'valid');
        } else {
            field.classList.add('is-invalid', 'invalid');
            this.addShakeEffect(field);
        }
        
        // Handle error message
        this.updateErrorMessage(field, errorMessage);
    }
    
    updateErrorMessage(field, message) {
        // Find or create error message element
        let errorElement = field.parentNode.querySelector('.error-message, .invalid-feedback');
        
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message invalid-feedback';
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        errorElement.style.display = message ? 'block' : 'none';
    }
    
    clearErrors(field) {
        field.classList.remove('is-invalid', 'invalid');
        const errorElement = field.parentNode.querySelector('.error-message, .invalid-feedback');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }
    
    addShakeEffect(field) {
        field.classList.add('shake');
        setTimeout(() => {
            field.classList.remove('shake');
        }, 300);
    }
    
    getFieldLabel(field) {
        // Try to find label text
        const label = document.querySelector(`label[for="${field.id}"]`) || 
                     field.parentNode.querySelector('label') ||
                     field.closest('.form-group')?.querySelector('label');
        
        if (label) {
            return label.textContent.replace('*', '').trim();
        }
        
        // Fallback to field name or placeholder
        return field.getAttribute('placeholder') || 
               field.name.replace(/[_-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 
               'Field';
    }
    
    showFormErrors(form) {
        const firstInvalidField = form.querySelector('.is-invalid, .invalid');
        if (firstInvalidField) {
            firstInvalidField.focus();
            firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        // Show a general error message
        this.showNotification('Please correct the errors in the form before submitting.', 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease;
            max-width: 400px;
        `;
        
        // Set background color based on type
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Close button functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }
}

// CSS for validation styles
const validationCSS = `
    .is-valid, .valid {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 0.2rem rgba(16, 185, 129, 0.25) !important;
    }
    
    .is-invalid, .invalid {
        border-color: #ef4444 !important;
        box-shadow: 0 0 0 0.2rem rgba(239, 68, 68, 0.25) !important;
    }
    
    .error-message, .invalid-feedback {
        color: #ef4444;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        font-weight: 500;
    }
    
    .shake {
        animation: shake 0.3s;
    }
    
    @keyframes shake {
        0% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        50% { transform: translateX(5px); }
        75% { transform: translateX(-5px); }
        100% { transform: translateX(0); }
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        margin-left: 15px;
        padding: 0;
        line-height: 1;
    }
    
    .notification-close:hover {
        opacity: 0.8;
    }
`;

// Inject CSS
const style = document.createElement('style');
style.textContent = validationCSS;
document.head.appendChild(style);

// Initialize the validator
const formValidator = new FormValidator();

// Export for use in other scripts
window.FormValidator = FormValidator;
window.formValidator = formValidator;