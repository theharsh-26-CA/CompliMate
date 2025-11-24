// CompliancePro360 - Advanced JavaScript Features

// Dark Mode Toggle
function initDarkMode() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);

    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            // Update icon
            toggleBtn.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
        });

        // Set initial icon
        toggleBtn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Scroll Progress Indicator
function initScrollProgress() {
    const indicator = document.createElement('div');
    indicator.className = 'scroll-indicator';
    document.body.appendChild(indicator);

    window.addEventListener('scroll', () => {
        const winHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrolled = (window.scrollY / winHeight) * 100;
        indicator.style.width = scrolled + '%';
    });
}

// Intersection Observer for Scroll Animations
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// Toast Notifications
class Toast {
    static show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.5rem;">
                    ${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}
                </span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// Form Validation with Visual Feedback
function enhanceFormValidation() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], textarea[required]');

        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.validity.valid) {
                    input.style.borderColor = 'var(--success)';
                } else {
                    input.style.borderColor = 'var(--danger)';
                }
            });

            input.addEventListener('input', () => {
                if (input.validity.valid) {
                    input.style.borderColor = 'var(--border-color)';
                }
            });
        });
    });
}

// Smooth Scroll for Anchor Links
function initSmoothScroll() {
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
}

// Loading State for Buttons
function addLoadingState(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem; justify-content: center;">
                <div class="loading-spinner" style="width: 20px; height: 20px; border-width: 2px;"></div>
                <span>Loading...</span>
            </div>
        `;
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
    }
}

// Enhanced Submit Buttons
function enhanceSubmitButtons() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.classList.contains('no-loading')) {
                addLoadingState(submitBtn, true);
            }
        });
    });
}

// Copy to Clipboard with Feedback
function setupCopyButtons() {
    document.querySelectorAll('[data-copy]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const textToCopy = btn.dataset.copy || btn.previousElementSibling?.value;

            try {
                await navigator.clipboard.writeText(textToCopy);
                Toast.show('Copied to clipboard!', 'success', 2000);

                // Visual feedback
                const originalText = btn.innerHTML;
                btn.innerHTML = '✓ Copied';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            } catch (err) {
                Toast.show('Failed to copy', 'error');
            }
        });
    });
}

// Number Counter Animation
function animateNumbers() {
    const counters = document.querySelectorAll('.stat-value');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const finalValue = parseInt(target.textContent.replace(/,/g, ''));

                if (!isNaN(finalValue)) {
                    let current = 0;
                    const increment = finalValue / 50;
                    const duration = 1000;
                    const stepTime = duration / 50;

                    const timer = setInterval(() => {
                        current += increment;
                        if (current >= finalValue) {
                            target.textContent = finalValue.toLocaleString();
                            clearInterval(timer);
                        } else {
                            target.textContent = Math.floor(current).toLocaleString();
                        }
                    }, stepTime);
                }

                observer.unobserve(target);
            }
        });
    });

    counters.forEach(counter => observer.observe(counter));
}

// Modal System
class Modal {
    static show(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.3s;
        `;

        const modalContent = document.createElement('div');
        modalContent.className = 'card';
        modalContent.style.cssText = `
            max-width: 500px;
            width: 90%;
            animation: fadeInUp 0.3s;
        `;

        modalContent.innerHTML = `
            <h2 style="margin-bottom: 1rem;">${title}</h2>
            <div style="margin-bottom: 1.5rem;">${content}</div>
            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                ${buttons.map(btn => `
                    <button class="btn ${btn.class || 'btn-outline'}" onclick="${btn.action}">${btn.text}</button>
                `).join('')}
            </div>
        `;

        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                Modal.close();
            }
        });
    }

    static close() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.style.animation = 'fadeOut 0.3s';
            setTimeout(() => modal.remove(), 300);
        }
    }
}

// Parallax Effect for Hero Sections
function initParallax() {
    const parallaxElements = document.querySelectorAll('[data-parallax]');

    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;

        parallaxElements.forEach(el => {
            const speed = el.dataset.parallax || 0.5;
            el.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
}

// Initialize All Features
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initScrollProgress();
    initScrollAnimations();
    initSmoothScroll();
    enhanceFormValidation();
    enhanceSubmitButtons();
    setupCopyButtons();
    animateNumbers();
    initParallax();

    console.log('CompliancePro360 - Advanced UI Initialized ✓');
});

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100px); }
    }
`;
document.head.appendChild(style);

// Expose utilities globally
window.Toast = Toast;
window.Modal = Modal;
window.addLoadingState = addLoadingState;
