// ===== IMAGE OPTIMIZATION & LAZY LOADING =====
(function() {
    'use strict';
    
    // Lazy load images with IntersectionObserver
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // Load from data-src to src
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    
                    // Load from data-srcset to srcset
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                        img.removeAttribute('data-srcset');
                    }
                    
                    // Add loaded class for animation
                    img.classList.add('loaded');
                    
                    // Stop observing after loading
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        // Observe all lazy-load images
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        });
    } else {
        // Fallback for older browsers
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('img[data-src]').forEach(img => {
                img.src = img.dataset.src;
                if (img.dataset.srcset) img.srcset = img.dataset.srcset;
            });
        });
    }
    
    // Picture element support for responsive images
    function supportsPictureElement() {
        return 'HTMLPictureElement' in window;
    }
    
    // Responsive image loading based on screen size
    function loadResponsiveImages() {
        const dpr = window.devicePixelRatio || 1;
        const vw = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
        
        document.querySelectorAll('[data-responsive]').forEach(img => {
            const responsive = JSON.parse(img.dataset.responsive);
            
            // Select appropriate image based on viewport width
            let selectedSrc = responsive.default;
            
            if (vw >= 1200 && responsive.lg) selectedSrc = responsive.lg;
            else if (vw >= 992 && responsive.md) selectedSrc = responsive.md;
            else if (vw >= 768 && responsive.sm) selectedSrc = responsive.sm;
            
            // Apply device pixel ratio
            if (dpr > 1 && responsive.high_dpi) {
                selectedSrc = responsive.high_dpi;
            }
            
            if (img.dataset.src !== selectedSrc) {
                img.dataset.src = selectedSrc;
                
                // Trigger lazy load
                const loadEvent = new Event('load', { bubbles: true });
                if (observer) observer.observe(img);
            }
        });
    }
    
    // Load responsive images on resize
    window.addEventListener('resize', debounce(loadResponsiveImages, 250));
    
    // Initial load
    document.addEventListener('DOMContentLoaded', loadResponsiveImages);
})();

// ===== IMAGE PLACEHOLDER BLUR EFFECT =====
(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', () => {
        // Add blur animation to images
        document.querySelectorAll('img').forEach(img => {
            if (!img.classList.contains('no-placeholder')) {
                // Set initial placeholder
                if (img.hasAttribute('data-placeholder')) {
                    img.style.backgroundImage = `url(${img.dataset.placeholder})`;
                    img.style.backgroundSize = 'cover';
                }
                
                // Smooth transition when loaded
                img.addEventListener('load', function() {
                    this.style.animation = 'fadeIn 0.5s ease';
                });
                
                img.addEventListener('error', function() {
                    // Show error placeholder
                    this.style.backgroundColor = '#e2e8f0';
                });
            }
        });
    });
})();

// ===== SVG ICON OPTIMIZATION =====
(function() {
    'use strict';
    
    // Cache SVG icons for better performance
    const svgCache = {};
    
    function loadSVG(url, targetElement) {
        if (svgCache[url]) {
            targetElement.innerHTML = svgCache[url];
            return Promise.resolve();
        }
        
        return fetch(url)
            .then(response => response.text())
            .then(svgContent => {
                // Remove any script tags for security
                const sanitized = svgContent.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
                svgCache[url] = sanitized;
                targetElement.innerHTML = sanitized;
            })
            .catch(error => {
                console.error('Failed to load SVG:', error);
            });
    }
    
    // Auto-load SVGs with data-svg attribute
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-svg]').forEach(el => {
            loadSVG(el.dataset.svg, el);
        });
    });
    
    // Expose SVG loader to global scope
    window.loadSVG = loadSVG;
})();

console.log('Image Optimization Module Loaded ✨');
