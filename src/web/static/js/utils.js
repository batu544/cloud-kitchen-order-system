/**
 * Utility functions
 */

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format phone number
function formatPhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    return phone;
}

// Validate phone number (10 digits)
function validatePhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length === 10;
}

// Validate email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white transform transition-all duration-300 ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Show loading spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'flex items-center justify-center p-8';
    spinner.innerHTML = `
        <svg class="animate-spin h-8 w-8 text-orange-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
    `;
    element.innerHTML = '';
    element.appendChild(spinner);
}

// Handle API errors
function handleAPIError(error) {
    console.error('API Error:', error);
    showToast(error.message || 'An error occurred', 'error');
}

// Get catering price
function getCateringPrice(basePrice, size) {
    const multipliers = { small: 4, medium: 6, large: 12 };
    return basePrice * multipliers[size] * 0.9;
}

// Update cart badge
function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        const count = cart.getItemCount();
        badge.textContent = count;
        badge.classList.toggle('hidden', count === 0);
    }
}

// Initialize cart badge listener
window.addEventListener('cartUpdated', () => {
    updateCartBadge();
});

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();
});
