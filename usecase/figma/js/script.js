// Food Website JavaScript

// Form validation function
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get form values
            const firstName = document.getElementById('firstName').value.trim();
            const lastName = document.getElementById('lastName').value.trim();
            const email = document.getElementById('email').value.trim();
            const message = document.getElementById('message').value.trim();
            
            // Simple validation
            let isValid = true;
            let errorMessage = '';
            
            if (!firstName) {
                isValid = false;
                errorMessage += 'First name is required.\n';
            }
            
            if (!lastName) {
                isValid = false;
                errorMessage += 'Last name is required.\n';
            }
            
            if (!email) {
                isValid = false;
                errorMessage += 'Email is required.\n';
            } else if (!isValidEmail(email)) {
                isValid = false;
                errorMessage += 'Please enter a valid email address.\n';
            }
            
            if (!message) {
                isValid = false;
                errorMessage += 'Message is required.\n';
            }
            
            if (isValid) {
                // In a real application, this would send the form data to a server
                alert('Form submitted successfully! We\'ll be in touch soon.');
                contactForm.reset();
            } else {
                alert('Please correct the following errors:\n\n' + errorMessage);
            }
        });
    }
    
    // Function to validate email format
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return; // Skip if it's just '#'
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Mobile navigation toggle (for responsive design)
    const createMobileNav = () => {
        const navContent = document.querySelector('.nav-content');
        const mainNav = document.querySelector('.main-nav');
        
        if (navContent && mainNav && !document.querySelector('.mobile-toggle')) {
            const mobileToggle = document.createElement('button');
            mobileToggle.className = 'mobile-toggle';
            mobileToggle.innerHTML = '☰';
            mobileToggle.setAttribute('aria-label', 'Toggle navigation menu');
            
            navContent.insertBefore(mobileToggle, mainNav);
            
            mobileToggle.addEventListener('click', () => {
                mainNav.classList.toggle('active');
                mobileToggle.textContent = mainNav.classList.contains('active') ? '✕' : '☰';
            });
        }
    };
    
    // Only create mobile nav on smaller screens
    const handleResize = () => {
        if (window.innerWidth <= 768) {
            createMobileNav();
        } 
    };
    
    // Initial check
    handleResize();
    
    // Update on resize
    window.addEventListener('resize', handleResize);
});
