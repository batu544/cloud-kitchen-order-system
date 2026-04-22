/**
 * Staff Dashboard JavaScript
 * Handles order listing, filtering, pagination, and bulk operations
 */

let selectedOrders = new Set();
let currentPage = 1;
let currentDate = null;
let currentStatusFilter = null;
let totalPages = 1;
let currentTab = 'orders';

// Initialize dashboard
async function initDashboard() {
    // Check authentication
    const user = api.getCurrentUser();
    if (!user) {
        showToast('Please log in to access staff dashboard', 'warning');
        window.location.href = '/login?redirect=/staff/dashboard';
        return;
    }

    if (user.role !== 'staff' && user.role !== 'admin') {
        showToast('Access denied. Staff only.', 'error');
        window.location.href = '/';
        return;
    }

    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date-filter').value = today;
    currentDate = today;

    // Load statuses for filters
    await loadStatuses();

    // Load initial orders
    await loadOrders(1);

    // Set up event listeners
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    // Date filter change
    document.getElementById('date-filter').addEventListener('change', (e) => {
        currentDate = e.target.value;
        if (currentTab === 'items') {
            loadItemSummary();
        } else {
            loadOrders(1);
        }
    });

    // Status filter change
    document.getElementById('status-filter').addEventListener('change', (e) => {
        currentStatusFilter = e.target.value ? parseInt(e.target.value) : null;
        loadOrders(1);
    });

    // Select all checkbox
    document.getElementById('select-all').addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.order-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = e.target.checked;
            const orderId = parseInt(checkbox.value);
            if (e.target.checked) {
                selectedOrders.add(orderId);
            } else {
                selectedOrders.delete(orderId);
            }
        });
        updateBulkActionsBar();
    });
}

// Load statuses for dropdowns
async function loadStatuses() {
    try {
        const response = await api.getAllStatuses();
        const statuses = response.data;

        // Populate filter dropdown
        const statusFilter = document.getElementById('status-filter');
        statusFilter.innerHTML = '<option value="">All Statuses</option>';
        statuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status.status_id;
            option.textContent = status.status_name;
            statusFilter.appendChild(option);
        });

        // Populate bulk action dropdown
        const bulkStatusSelect = document.getElementById('bulk-status-select');
        bulkStatusSelect.innerHTML = '<option value="">Select new status...</option>';
        statuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status.status_id;
            option.textContent = status.status_name;
            bulkStatusSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load statuses:', error);
    }
}

// Load orders with pagination
async function loadOrders(page = 1) {
    currentPage = page;

    // Show loading state
    document.getElementById('loading-state').classList.remove('hidden');
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('pagination').classList.add('hidden');

    try {
        const response = await api.getDailyOrders(currentDate, page, 10, currentStatusFilter);
        const data = response.data;

        // Hide loading
        document.getElementById('loading-state').classList.add('hidden');

        if (data.orders && data.orders.length > 0) {
            renderOrdersTable(data.orders);
            renderPagination(data.pagination);
            document.getElementById('pagination').classList.remove('hidden');
        } else {
            document.getElementById('orders-table-body').innerHTML = '';
            document.getElementById('empty-state').classList.remove('hidden');
        }

        // Clear selection when changing page
        selectedOrders.clear();
        updateBulkActionsBar();

    } catch (error) {
        document.getElementById('loading-state').classList.add('hidden');
        handleAPIError(error);
    }
}

// Render orders table
function renderOrdersTable(orders) {
    const tbody = document.getElementById('orders-table-body');

    tbody.innerHTML = orders.map(order => {
        const statusClass = getStatusClass(order.current_status_name);
        const paymentClass = getPaymentClass(order.payment_status);

        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <input type="checkbox" value="${order.order_id}" class="order-checkbox rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <a href="/staff/orders/${order.order_id}" class="text-orange-600 hover:text-orange-700 font-medium">
                        #${order.order_id}
                    </a>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${escapeHtml(order.cust_name || 'Guest')}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${formatPhone(order.order_phone)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${order.item_count || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">${formatCurrency(order.total_amount)}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${statusClass}">
                        ${escapeHtml(order.current_status_name)}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${paymentClass}">
                        ${escapeHtml(order.payment_status)}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    ${getNextStatusButton(order)}
                </td>
            </tr>
        `;
    }).join('');

    // Attach checkbox listeners
    document.querySelectorAll('.order-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });
}

// Handle individual checkbox change
function handleCheckboxChange(event) {
    const orderId = parseInt(event.target.value);
    if (event.target.checked) {
        selectedOrders.add(orderId);
    } else {
        selectedOrders.delete(orderId);
        document.getElementById('select-all').checked = false;
    }
    updateBulkActionsBar();
}

// Update bulk actions bar visibility and count
function updateBulkActionsBar() {
    const bar = document.getElementById('bulk-actions-bar');
    const count = document.getElementById('selection-count');

    if (selectedOrders.size > 0) {
        bar.classList.remove('hidden');
        count.textContent = `${selectedOrders.size} order${selectedOrders.size > 1 ? 's' : ''} selected`;
    } else {
        bar.classList.add('hidden');
    }
}

// Clear selection
function clearSelection() {
    selectedOrders.clear();
    document.querySelectorAll('.order-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    document.getElementById('select-all').checked = false;
    updateBulkActionsBar();
}

// Bulk update status
async function bulkUpdateStatus() {
    const statusId = parseInt(document.getElementById('bulk-status-select').value);
    const note = document.getElementById('bulk-note').value.trim();

    if (!statusId) {
        showToast('Please select a status', 'warning');
        return;
    }

    if (selectedOrders.size === 0) {
        showToast('No orders selected', 'warning');
        return;
    }

    if (!confirm(`Update status for ${selectedOrders.size} order(s)?`)) {
        return;
    }

    try {
        const response = await api.bulkUpdateStatus(Array.from(selectedOrders), statusId, note);
        const results = response.data;

        if (results.success_count > 0) {
            showToast(`Successfully updated ${results.success_count} order(s)`, 'success');
        }

        if (results.failed_ids && results.failed_ids.length > 0) {
            showToast(`Failed to update ${results.failed_ids.length} order(s)`, 'error');
        }

        // Reload orders and clear selection
        clearSelection();
        document.getElementById('bulk-note').value = '';
        await loadOrders(currentPage);

    } catch (error) {
        handleAPIError(error);
    }
}

// Render pagination
function renderPagination(pagination) {
    totalPages = pagination.total_pages;
    currentPage = pagination.page;

    // Update showing text
    const from = (pagination.page - 1) * pagination.per_page + 1;
    const to = Math.min(pagination.page * pagination.per_page, pagination.total);
    document.getElementById('showing-from').textContent = from;
    document.getElementById('showing-to').textContent = to;
    document.getElementById('total-records').textContent = pagination.total;

    // Update prev/next buttons
    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === totalPages;

    // Render page numbers
    const pageNumbers = document.getElementById('page-numbers');
    pageNumbers.innerHTML = '';

    // Show max 5 page numbers
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    startPage = Math.max(1, endPage - 4);

    for (let i = startPage; i <= endPage; i++) {
        const button = document.createElement('button');
        button.textContent = i;
        button.onclick = () => loadOrders(i);
        button.className = `px-4 py-2 border rounded-lg text-sm font-medium ${
            i === currentPage
                ? 'bg-orange-600 text-white border-orange-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
        }`;
        pageNumbers.appendChild(button);
    }
}

// Navigation functions
function goToPreviousPage() {
    if (currentPage > 1) {
        loadOrders(currentPage - 1);
    }
}

function goToNextPage() {
    if (currentPage < totalPages) {
        loadOrders(currentPage + 1);
    }
}

// Helper: Get status badge class
function getStatusClass(status) {
    const statusMap = {
        'Pending': 'bg-yellow-100 text-yellow-800',
        'Confirmed': 'bg-blue-100 text-blue-800',
        'Preparing': 'bg-purple-100 text-purple-800',
        'Ready': 'bg-indigo-100 text-indigo-800',
        'Completed': 'bg-green-100 text-green-800',
        'Cancelled': 'bg-red-100 text-red-800'
    };
    return statusMap[status] || 'bg-gray-100 text-gray-800';
}

// Helper: Get payment status badge class
function getPaymentClass(paymentStatus) {
    const paymentMap = {
        'pending': 'bg-yellow-100 text-yellow-800',
        'partially_paid': 'bg-orange-100 text-orange-800',
        'paid': 'bg-green-100 text-green-800',
        'refunded': 'bg-red-100 text-red-800',
        'cancelled': 'bg-gray-100 text-gray-800'
    };
    return paymentMap[paymentStatus] || 'bg-gray-100 text-gray-800';
}

// Next status progression map (matches DB: 1=Pending,2=Confirmed,3=Preparing,4=Ready,5=Completed,6=Cancelled)
// Status 4 (Ready) triggers payment modal instead of direct status advance.
// Completed and Cancelled show no next action — use order detail page.
const NEXT_STATUS = {
    1: { id: 2, label: 'Confirm' },
    2: { id: 3, label: 'Prepare' },
    3: { id: 4, label: 'Mark Ready' }
};

// Helper: Get next status button HTML
function getNextStatusButton(order) {
    // Ready (4) → open payment modal
    if (order.current_status_id === 4) {
        return `<button onclick="openPaymentModal(${order.order_id}, ${order.total_amount})"
            class="px-3 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition font-medium">
            Ready for Payment
        </button>`;
    }
    const next = NEXT_STATUS[order.current_status_id];
    if (!next) return '<span class="text-gray-400 text-xs">—</span>';
    return `<button onclick="advanceStatus(${order.order_id}, ${next.id})"
        class="px-3 py-1 bg-orange-600 text-white text-xs rounded-lg hover:bg-orange-700 transition font-medium">
        ${next.label}
    </button>`;
}

// Advance order to next status with one click
async function advanceStatus(orderId, nextStatusId) {
    try {
        await api.request(`/orders/${orderId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status_id: nextStatusId })
        });
        showToast('Status updated', 'success');
        await loadOrders(currentPage);
    } catch (error) {
        handleAPIError(error);
    }
}

// ── Payment Modal ────────────────────────────────────────────────────────────

let _paymentOrderId = null;

function openPaymentModal(orderId, orderTotal) {
    _paymentOrderId = orderId;

    document.getElementById('pay-modal-order-id').textContent = `#${orderId}`;
    document.getElementById('pay-modal-order-total').textContent = formatCurrency(orderTotal);
    document.getElementById('pay-amount').value = parseFloat(orderTotal).toFixed(2);
    document.getElementById('pay-method').value = '';
    document.getElementById('pay-status').value = 'paid';
    document.getElementById('pay-tip').value = '0';
    document.getElementById('pay-notes').value = '';
    document.getElementById('pay-error').classList.add('hidden');
    document.getElementById('pay-submit-btn').disabled = false;
    document.getElementById('pay-submit-btn').textContent = 'Confirm Payment';

    document.getElementById('payment-modal').classList.remove('hidden');
}

function closePaymentModal() {
    document.getElementById('payment-modal').classList.add('hidden');
    _paymentOrderId = null;
}

async function submitPayment(event) {
    event.preventDefault();
    if (!_paymentOrderId) return;

    const amount = parseFloat(document.getElementById('pay-amount').value);
    const method = document.getElementById('pay-method').value;
    const status = document.getElementById('pay-status').value;
    const tip = parseFloat(document.getElementById('pay-tip').value) || 0;
    const notes = document.getElementById('pay-notes').value.trim();

    const errorEl = document.getElementById('pay-error');
    errorEl.classList.add('hidden');

    if (!method) {
        errorEl.textContent = 'Please select a payment method.';
        errorEl.classList.remove('hidden');
        return;
    }

    const submitBtn = document.getElementById('pay-submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';

    try {
        // 1. Record the payment
        await api.recordPayment(_paymentOrderId, {
            amount,
            payment_method: method,
            payment_status: status,
            tip_amount: tip,
            payment_notes: notes || null
        });

        // 2. Advance order status to Completed (5)
        await api.request(`/orders/${_paymentOrderId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status_id: 5, note: 'Payment accepted' })
        });

        showToast('Payment recorded — order completed!', 'success');
        closePaymentModal();
        await loadOrders(currentPage);
    } catch (error) {
        errorEl.textContent = error.message || 'Failed to record payment. Please try again.';
        errorEl.classList.remove('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Confirm Payment';
    }
}

// ── Tab switching ────────────────────────────────────────────────────────────

function switchTab(tab) {
    currentTab = tab;

    document.getElementById('panel-orders').classList.toggle('hidden', tab !== 'orders');
    document.getElementById('panel-items').classList.toggle('hidden', tab !== 'items');

    ['orders', 'items'].forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        btn.classList.toggle('border-orange-500', t === tab);
        btn.classList.toggle('text-orange-600', t === tab);
        btn.classList.toggle('border-transparent', t !== tab);
        btn.classList.toggle('text-gray-500', t !== tab);
        btn.classList.toggle('hover:text-gray-700', t !== tab);
    });

    if (tab === 'items') loadItemSummary();
}

// ── Item Count Tab ────────────────────────────────────────────────────────────

async function loadItemSummary() {
    document.getElementById('items-loading').classList.remove('hidden');
    document.getElementById('items-table-wrapper').classList.add('hidden');

    try {
        const resp = await api.request(`/orders/daily-items?date=${currentDate}`);
        const data = resp.data;
        document.getElementById('items-total-qty').textContent = data.summary.total_quantity;
        document.getElementById('items-unique').textContent = data.summary.unique_items;
        renderItemsTable(data.items);
    } catch (e) {
        handleAPIError(e);
    } finally {
        document.getElementById('items-loading').classList.add('hidden');
    }
}

function renderItemsTable(items) {
    const tbody = document.getElementById('items-tbody');
    const empty = document.getElementById('items-empty');
    const wrapper = document.getElementById('items-table-wrapper');

    wrapper.classList.remove('hidden');

    if (!items.length) {
        tbody.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    tbody.innerHTML = items.map(item => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap font-medium text-gray-900">${escapeHtml(item.name)}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="text-xl font-bold text-orange-600">${item.total_quantity}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${item.order_count} order${item.order_count !== 1 ? 's' : ''}
            </td>
        </tr>
    `).join('');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDashboard);
