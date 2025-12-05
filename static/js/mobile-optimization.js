// ===== MOBILE EXPERIENCE IMPROVEMENTS =====
(function() {
    'use strict';
    
    // Detect mobile device
    const isMobile = () => {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    };
    
    // Add mobile class to body
    if (isMobile()) {
        document.documentElement.classList.add('is-mobile');
    }
    
    // Detect device orientation
    function handleOrientationChange() {
        const isPortrait = window.matchMedia('(orientation: portrait)').matches;
        
        if (isPortrait) {
            document.documentElement.classList.add('portrait-mode');
            document.documentElement.classList.remove('landscape-mode');
        } else {
            document.documentElement.classList.add('landscape-mode');
            document.documentElement.classList.remove('portrait-mode');
        }
    }
    
    // Listen for orientation changes
    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('load', handleOrientationChange);
    
    // Improve touch interactions
    document.addEventListener('DOMContentLoaded', () => {
        // Add touch feedback to buttons
        const buttons = document.querySelectorAll('button, a[class*="btn"], .clickable');
        
        buttons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.style.opacity = '0.8';
                this.style.transform = 'scale(0.98)';
            });
            
            button.addEventListener('touchend', function() {
                this.style.opacity = '1';
                this.style.transform = 'scale(1)';
            });
        });
    });
    
    // Prevent zoom on double-tap
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(event) {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
    
    // Improve form handling on mobile
    document.addEventListener('DOMContentLoaded', () => {
        const inputs = document.querySelectorAll('input, textarea');
        
        inputs.forEach(input => {
            // Auto-focus on label click (mobile friendly)
            if (input.id) {
                const label = document.querySelector(`label[for="${input.id}"]`);
                if (label) {
                    label.addEventListener('click', (e) => {
                        e.preventDefault();
                        input.focus();
                    });
                }
            }
            
            // Add padding for notches (safe area)
            if ('constants' in window && 'safeAreaInsets' in navigator) {
                const insets = navigator.safeAreaInsets;
                if (insets.bottom > 0 || insets.left > 0 || insets.right > 0) {
                    input.style.paddingBottom = `max(${input.style.paddingBottom}, ${insets.bottom}px)`;
                }
            }
        });
    });
    
    // Haptic feedback for important interactions
    function triggerHaptic(type = 'light') {
        if (navigator.vibrate) {
            const duration = {
                'light': 10,
                'medium': 20,
                'heavy': 50
            };
            navigator.vibrate(duration[type] || 20);
        }
    }
    
    // Expose haptic feedback
    window.triggerHaptic = triggerHaptic;
    
    // Add haptic to important buttons
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('form button[type="submit"]').forEach(button => {
            button.addEventListener('click', () => triggerHaptic('medium'));
        });
    });
    
    // Mobile-friendly viewport handling
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport && isMobile()) {
        viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=5, user-scalable=yes');
    }
    
    // Prevent 300ms tap delay on mobile
    document.addEventListener('touchstart', function() {}, true);
    
    // Handle soft keyboard appearance
    let windowHeight = window.innerHeight;
    
    window.addEventListener('resize', () => {
        const newHeight = window.innerHeight;
        
        if (newHeight < windowHeight * 0.75) {
            // Keyboard is open
            document.body.classList.add('keyboard-open');
            document.documentElement.style.position = 'fixed';
        } else {
            // Keyboard is closed
            document.body.classList.remove('keyboard-open');
            document.documentElement.style.position = 'relative';
        }
        
        windowHeight = newHeight;
    });
    
    // Smooth scrolling behavior
    if ('scrollBehavior' in document.documentElement.style === false) {
        // Polyfill for smooth scroll
        window.smoothScroll = function(target) {
            const start = window.scrollY;
            const end = target.offsetTop;
            const distance = end - start;
            const duration = 1000;
            let start_time = null;
            
            const ease = (t, b, c, d) => {
                t /= d / 2;
                if (t < 1) return c / 2 * t * t + b;
                t--;
                return -c / 2 * (t * (t - 2) - 1) + b;
            };
            
            const animation = currentTime => {
                if (start_time === null) start_time = currentTime;
                const elapsed = currentTime - start_time;
                window.scrollTo(0, ease(elapsed, start, distance, duration));
                if (elapsed < duration) requestAnimationFrame(animation);
            };
            
            requestAnimationFrame(animation);
        };
    }
})();

console.log('Mobile Experience Module Loaded 📱');
