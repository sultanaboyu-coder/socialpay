// ============================================
// SOCIAL PAY - COMPLETE JAVASCRIPT
// Mobile-First Web Application
// ============================================

// ==================== CONFIGURATION ====================

const API_URL = window.location.origin + '/api';

// ==================== TOKEN MANAGEMENT ====================

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('user_id');
}

// ==================== API REQUEST HELPER ====================

async function apiRequest(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json',
    };

    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method,
        headers,
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, config);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Request failed');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ==================== ALERT SYSTEM ====================

function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fade-in`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// ==================== LOADING INDICATOR ====================

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

// ==================== AUTHENTICATION ====================

function checkAuth() {
    const token = getToken();
    const publicPages = ['/', '/login', '/register'];
    const currentPage = window.location.pathname;

    if (!token && !publicPages.includes(currentPage)) {
        window.location.href = '/login';
        return false;
    }

    if (token && (currentPage === '/login' || currentPage === '/register')) {
        window.location.href = '/dashboard';
        return false;
    }

    return true;
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        removeToken();
        window.location.href = '/login';
    }
}

// ==================== FORMATTING HELPERS ====================

function formatCurrency(amount, currency = '₦') {
    const num = parseFloat(amount);
    if (isNaN(num)) return `${currency}0.00`;
    return `${currency}${num.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')}`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatDateOnly(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatTimeAgo(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
    
    return formatDateOnly(dateString);
}

// ==================== MOBILE MENU ====================

function toggleMobileMenu() {
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
        navLinks.classList.toggle('active');
    }
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(event) {
    const navbar = document.querySelector('.navbar');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    if (navLinks && navLinks.classList.contains('active')) {
        if (!navbar.contains(event.target)) {
            navLinks.classList.remove('active');
        }
    }
});

// ==================== CLIPBOARD ====================

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard! 📋', 'success');
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        showAlert('Copied to clipboard! 📋', 'success');
    } catch (err) {
        showAlert('Failed to copy', 'danger');
    }
    
    document.body.removeChild(textarea);
}

// ==================== VALIDATION ====================

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9]{10,15}$/;
    return re.test(phone.replace(/[\s\-\(\)]/g, ''));
}

function validatePIN(pin) {
    return /^\d{4}$/.test(pin);
}

// ==================== FILE HANDLING ====================

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function validateImageFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/webp'];
    const maxSize = 5 * 1024 * 1024; // 5MB

    if (!validTypes.includes(file.type)) {
        throw new Error('Please upload a valid image file (JPG, PNG, GIF, WEBP)');
    }

    if (file.size > maxSize) {
        throw new Error('Image size must be less than 5MB');
    }

    return true;
}

// ==================== DEBOUNCE ====================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== LOCAL STORAGE HELPERS ====================

function setLocalData(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Error saving to localStorage:', error);
    }
}

function getLocalData(key) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return null;
    }
}

// ==================== ERROR HANDLING ====================

function handleError(error, customMessage = null) {
    console.error('Error:', error);
    
    let message = customMessage || error.message || 'An error occurred';
    
    // Handle specific error types
    if (error.message && error.message.includes('401')) {
        message = 'Session expired. Please login again.';
        removeToken();
        setTimeout(() => {
            window.location.href = '/login';
        }, 2000);
    }
    
    showAlert(message, 'danger');
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    checkAuth();

    // Setup mobile menu
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }

    // Setup logout button
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }

    // Close mobile menu on window resize
    window.addEventListener('resize', debounce(() => {
        if (window.innerWidth > 768) {
            const navLinks = document.querySelector('.nav-links');
            if (navLinks) {
                navLinks.classList.remove('active');
            }
        }
    }, 250));

    console.log('Social Pay App Initialized ✅');
});

// ==================== EXPORT FOR GLOBAL USE ====================

window.socialPay = {
    // API
    apiRequest,
    
    // Auth
    getToken,
    setToken,
    removeToken,
    checkAuth,
    logout,
    
    // UI
    showAlert,
    showLoading,
    hideLoading,
    toggleMobileMenu,
    
    // Formatting
    formatCurrency,
    formatDate,
    formatDateOnly,
    formatTimeAgo,
    
    // Utilities
    copyToClipboard,
    validateEmail,
    validatePhone,
    validatePIN,
    readFileAsBase64,
    validateImageFile,
    debounce,
    handleError,
    
    // Storage
    setLocalData,
    getLocalData
};

// ==================== SERVICE WORKER (Optional) ====================

// Uncomment to enable offline support
/*
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('ServiceWorker registered:', registration);
            })
            .catch(error => {
                console.log('ServiceWorker registration failed:', error);
            });
    });
}
*/

// ==================== END OF JAVASCRIPT ====================
