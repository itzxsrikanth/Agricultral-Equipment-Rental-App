document.addEventListener("DOMContentLoaded", function () {
    // Navbar scroll interaction
    const navbar = document.querySelector(".navbar-custom");
    if (navbar) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 50) {
                navbar.classList.add("scrolled");
            } else {
                navbar.classList.remove("scrolled");
            }
        });
    }

    // Auto-dismiss Flash Messages
    const flashMessages = document.querySelectorAll(".alert-dismissible");
    flashMessages.forEach(function (message) {
        setTimeout(function () {
            // Check bootstrap alert close action or use standard fade out
            message.style.transition = "opacity 0.5s ease";
            message.style.opacity = "0";
            setTimeout(function () {
                message.remove();
            }, 500);
        }, 5000);
    });

    // Hover tooltip initialized if present
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined' && tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
