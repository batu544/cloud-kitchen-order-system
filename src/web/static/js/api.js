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

    async getUserDetails() {
        return this.request('/auth/me');
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

    async trackOrder(orderId) {
        return this.request(`/orders/track/${orderId}`);
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

    // Staff Dashboard methods
    async getDailyOrders(date, page, perPage, status) {
        const params = new URLSearchParams({
            ...(date && {date}),
            ...(page && {page}),
            ...(perPage && {per_page: perPage}),
            ...(status && {status})
        });
        return this.request(`/orders/daily?${params}`);
    }

    async bulkUpdateStatus(orderIds, statusId, note) {
        return this.request('/orders/bulk-status', {
            method: 'PUT',
            body: JSON.stringify({
                order_ids: orderIds,
                status_id: statusId,
                note
            })
        });
    }

    // Order Item Management methods
    async updateOrderItem(orderId, itemId, updates) {
        return this.request(`/orders/${orderId}/items/${itemId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    async removeOrderItem(orderId, itemId, reason) {
        return this.request(`/orders/${orderId}/items/${itemId}`, {
            method: 'DELETE',
            body: JSON.stringify({ reason })
        });
    }

    async addOrderItem(orderId, itemData) {
        return this.request(`/orders/${orderId}/items`, {
            method: 'POST',
            body: JSON.stringify(itemData)
        });
    }

    async updateOrder(orderId, updates) {
        return this.request(`/orders/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    async updateOrderStatus(orderId, data) {
        return this.request(`/orders/${orderId}/status`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async getOrderHistory(orderId, entityType) {
        const params = new URLSearchParams({
            ...(entityType && {entity_type: entityType})
        });
        return this.request(`/orders/${orderId}/history?${params}`);
    }

    // Helper method to get all statuses
    async getAllStatuses() {
        // Fetch from menu endpoint which has status info, or create dedicated endpoint
        return this.request('/orders/recent?limit=1').then(response => {
            // This is a workaround - ideally create GET /api/statuses endpoint
            // For now, we'll define statuses client-side
            return {
                success: true,
                data: [
                    {status_id: 1, status_name: 'Pending'},
                    {status_id: 2, status_name: 'Confirmed'},
                    {status_id: 3, status_name: 'Preparing'},
                    {status_id: 4, status_name: 'Ready'},
                    {status_id: 5, status_name: 'Delivered'},
                    {status_id: 6, status_name: 'Completed'},
                    {status_id: 7, status_name: 'Cancelled'}
                ]
            };
        });
    }
}

// Global API client instance
const api = new APIClient();
