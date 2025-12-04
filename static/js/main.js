// ===== AUTO-HIDE FLASH MESSAGES =====
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(function(message) {
        // Auto hide after 5 seconds
        setTimeout(function() {
            message.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
});

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ===== NAVBAR SCROLL EFFECT =====
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
    }
    
    lastScroll = currentScroll;
});

// ===== INTERSECTION OBSERVER FOR ANIMATIONS =====
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Animate elements on scroll
document.addEventListener('DOMContentLoaded', () => {
    const animateElements = document.querySelectorAll(
        '.feature-card-modern, .step-card, .testimonial-card, .stat-item, .faq-item'
    );
    
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// ===== FORM VALIDATION ENHANCEMENT =====
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', function(e) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = '#ef4444';
            } else {
                field.style.borderColor = '#e2e8f0';
            }
        });
        
        if (!isValid) {
            e.preventDefault();
        }
    });
});

// ===== PASSWORD STRENGTH INDICATOR =====
const passwordInputs = document.querySelectorAll('input[type="password"]');
passwordInputs.forEach(input => {
    if (input.name === 'password' || input.name === 'new_password') {
        const strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength';
        strengthIndicator.style.cssText = `
            height: 4px;
            margin-top: 8px;
            border-radius: 2px;
            background: #e2e8f0;
            transition: all 0.3s ease;
        `;
        
        input.parentNode.insertBefore(strengthIndicator, input.nextSibling);
        
        input.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            
            if (password.length >= 8) strength++;
            if (password.match(/[a-z]/)) strength++;
            if (password.match(/[A-Z]/)) strength++;
            if (password.match(/[0-9]/)) strength++;
            if (password.match(/[^a-zA-Z0-9]/)) strength++;
            
            const colors = ['#ef4444', '#f59e0b', '#fbbf24', '#10b981', '#059669'];
            const widths = ['20%', '40%', '60%', '80%', '100%'];
            
            if (password.length > 0) {
                strengthIndicator.style.background = colors[strength - 1] || colors[0];
                strengthIndicator.style.width = widths[strength - 1] || widths[0];
            } else {
                strengthIndicator.style.width = '0';
                strengthIndicator.style.background = '#e2e8f0';
            }
        });
    }
});

// ===== PARALLAX EFFECT FOR HERO =====
window.addEventListener('scroll', () => {
    const heroShapes = document.querySelectorAll('.shape');
    const scrolled = window.pageYOffset;
    
    heroShapes.forEach((shape, index) => {
        const speed = 0.5 + (index * 0.1);
        shape.style.transform = `translateY(${scrolled * speed}px)`;
    });
});

// ===== FAQ ACCORDION =====
const faqItems = document.querySelectorAll('.faq-item');
faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');
    const answer = item.querySelector('.faq-answer');
    
    if (question && answer) {
        answer.style.maxHeight = answer.scrollHeight + 'px';
        answer.style.overflow = 'hidden';
        answer.style.transition = 'max-height 0.3s ease';
        
        question.style.cursor = 'pointer';
        question.addEventListener('click', () => {
            const isOpen = item.classList.contains('open');
            
            // Close all other items
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('open');
                    const otherAnswer = otherItem.querySelector('.faq-answer');
                    if (otherAnswer) {
                        otherAnswer.style.maxHeight = otherAnswer.scrollHeight + 'px';
                    }
                }
            });
            
            // Toggle current item
            item.classList.toggle('open');
        });
    }
});

// ===== FLOATING CARDS ANIMATION =====
const floatingCards = document.querySelectorAll('.floating-card');
floatingCards.forEach((card, index) => {
    card.style.animation = `float-card 3s infinite ease-in-out ${index * 0.5}s`;
});

// ===== LOADING STATE FOR BUTTONS =====
const submitButtons = document.querySelectorAll('button[type="submit"], input[type="submit"]');
submitButtons.forEach(button => {
    button.addEventListener('click', function(e) {
        const form = this.closest('form');
        if (form && form.checkValidity()) {
            this.disabled = true;
            const originalText = this.value || this.textContent;
            
            if (this.tagName === 'INPUT') {
                this.value = 'Загрузка...';
            } else {
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
            }
            
            // Re-enable after 3 seconds (fallback)
            setTimeout(() => {
                this.disabled = false;
                if (this.tagName === 'INPUT') {
                    this.value = originalText;
                } else {
                    this.textContent = originalText;
                }
            }, 3000);
        }
    });
});

// ===== STATS COUNTER ANIMATION =====
const statNumbers = document.querySelectorAll('.stat-number');
const countUpOptions = {
    duration: 2000,
    useEasing: true
};

const countUp = (element, target) => {
    const start = 0;
    const duration = 2000;
    const startTime = performance.now();
    
    const updateCount = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        
        const current = Math.floor(easeOutQuart * target);
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateCount);
        } else {
            element.textContent = target.toLocaleString();
        }
    };
    
    requestAnimationFrame(updateCount);
};

// Observe stat numbers
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            entry.target.classList.add('counted');
            const text = entry.target.textContent.trim();
            const number = parseInt(text.replace(/[^0-9]/g, ''));
            
            if (!isNaN(number)) {
                countUp(entry.target, number);
            }
        }
    });
}, { threshold: 0.5 });

statNumbers.forEach(stat => {
    statsObserver.observe(stat);
});

// ===== TOOLTIPS =====
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        const tooltipText = tooltip.getAttribute('data-tooltip');
        const position = tooltip.getAttribute('data-tooltip-position') || 'top';
        
        // Create tooltip element
        const tooltipEl = document.createElement('span');
        tooltipEl.className = `tooltip-text tooltip-${position}`;
        tooltipEl.textContent = tooltipText;
        
        // Wrap the element in a tooltip container
        const wrapper = document.createElement('span');
        wrapper.className = 'tooltip';
        
        // Insert wrapper before the element
        tooltip.parentNode.insertBefore(wrapper, tooltip);
        // Move the element into the wrapper
        wrapper.appendChild(tooltip);
        // Add tooltip text
        wrapper.appendChild(tooltipEl);
    });
}

// ===== ENHANCED FORM VALIDATION =====
function initEnhancedValidation() {
    // Live validation for all form inputs
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            // Clear error when user starts typing
            const errorContainer = this.parentNode.querySelector('.form-errors');
            if (errorContainer) {
                errorContainer.innerHTML = '';
            }
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const errorContainer = field.parentNode.querySelector('.form-errors') || 
                         createErrorContainer(field.parentNode);
    
    // Clear previous errors
    errorContainer.innerHTML = '';
    
    // Field-specific validation
    if (field.hasAttribute('required') && !value) {
        showError(errorContainer, 'Это поле обязательно для заполнения');
        return false;
    }
    
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showError(errorContainer, 'Введите корректный email адрес');
            return false;
        }
    }
    
    if (field.name === 'password' && value) {
        if (value.length < 8) {
            showError(errorContainer, 'Пароль должен содержать минимум 8 символов');
            return false;
        }
        if (!/[A-Z]/.test(value)) {
            showError(errorContainer, 'Пароль должен содержать хотя бы одну заглавную букву');
            return false;
        }
        if (!/[a-z]/.test(value)) {
            showError(errorContainer, 'Пароль должен содержать хотя бы одну строчную букву');
            return false;
        }
        if (!/\d/.test(value)) {
            showError(errorContainer, 'Пароль должен содержать хотя бы одну цифру');
            return false;
        }
    }
    
    return true;
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Add icon based on type
    const icon = document.createElement('i');
    icon.className = `fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}`;
    
    // Add message
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    
    // Add elements to toast
    toast.appendChild(icon);
    toast.appendChild(messageSpan);
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Remove toast after animation completes
    setTimeout(() => {
        toast.remove();
        // Remove container if empty
        if (toastContainer.children.length === 0) {
            toastContainer.remove();
        }
    }, 3000);
}

// Initialize tooltips and enhanced validation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    initEnhancedValidation();
    
    // Add loading spinners to form submit buttons
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton) {
                submitButton.classList.add('btn-loading');
                
                // Create spinner if it doesn't exist
                if (!submitButton.querySelector('.loading-spinner')) {
                    const spinner = document.createElement('span');
                    spinner.className = 'loading-spinner';
                    submitButton.insertBefore(spinner, submitButton.firstChild);
                }
                
                // Reset button after 3 seconds (in case form doesn't redirect)
                setTimeout(() => {
                    submitButton.classList.remove('btn-loading');
                }, 3000);
            }
        });
    });
});

console.log('Flask Auth App - Enhanced UI Loaded ✨');
