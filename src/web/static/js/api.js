/**
 * API Client for Cloud Kitchen Order System
 */

const API_BASE_URL = window.location.origin + '/api';

class APIClient {
    constructor() {
        this.token = localStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth methods
    async login(username, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        this.token = data.data.token;
        localStorage.setItem('auth_token', this.token);
        localStorage.setItem('user', JSON.stringify(data.data));
        return data;
    }

    async register(userData) {
        const data = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        this.token = data.data.token;
        localStorage.setItem('auth_token', this.token);
        localStorage.setItem('user', JSON.stringify(data.data));
        return data;
    }

    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        window.location.href = '/';
    }

    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    isAuthenticated() {
        return !!this.token;
    }

    // Menu methods
    async getMenu(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/menu?${params}`);
    }

    async getMenuItem(itemId) {
        return this.request(`/menu/items/${itemId}`);
    }

    // Order methods
    async createOrder(orderData) {
        return this.request('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    async getOrder(orderId) {
        return this.request(`/orders/${orderId}`);
    }

    async trackOrder(orderRef) {
        return this.request(`/orders/track/${orderRef}`);
    }

    async phoneLookup(phone) {
        return this.request('/orders/phone-lookup', {
            method: 'POST',
            body: JSON.stringify({ phone })
        });
    }

    async getMyOrders() {
        return this.request('/orders/my-orders');
    }

    // Payment methods
    async recordPayment(orderId, paymentData) {
        return this.request(`/payments/orders/${orderId}/payments`, {
            method: 'POST',
            body: JSON.stringify(paymentData)
        });
    }
}

// Global API client instance
const api = new APIClient();
