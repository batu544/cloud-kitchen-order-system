/**
 * Staff Order Detail JavaScript
 * Handles order viewing, status updates, item management, and payment recording
 */

let currentOrder = null;
let menuItems = [];

// Initialize page
async function initOrderDetail() {
    // Check authentication
    const user = api.getCurrentUser();
    if (!user) {
        showToast('Please log in to access order details', 'warning');
        window.location.href = '/login?redirect=' + window.location.pathname;
        return;
    }

    if (user.role !== 'staff' && user.role !== 'admin') {
        showToast('Access denied. Staff only.', 'error');
        window.location.href = '/';
        return;
    }

    // Get order ID from URL
    const orderId = getOrderIdFromURL();
    if (!orderId) {
        showToast('Invalid order ID', 'error');
        window.location.href = '/staff/dashboard';
        return;
    }

    // Load order data
    await loadOrder(orderId);

    // Setup event listeners
    setupEventListeners();
}

// Get order ID from URL path
function getOrderIdFromURL() {
    const match = window.location.pathname.match(/\/staff\/orders\/(\d+)/);
    return match ? parseInt(match[1]) : null;
}

// Load order details
async function loadOrder(orderId) {
    showLoading(true);

    try {
        const response = await api.getOrder(orderId);
        currentOrder = response.data;

        // Render all order sections
        renderOrderHeader();
        renderOrderInfo();
        renderOrderItems();
        renderOrderSummary();
        renderStatusSection();
        renderPaymentSection();
        await loadEditHistory();

    } catch (error) {
        handleAPIError(error);
        setTimeout(() => {
            window.location.href = '/staff/dashboard';
        }, 2000);
    } finally {
        showLoading(false);
    }
}

// Render order header
function renderOrderHeader() {
    document.getElementById('order-id').textContent = currentOrder.order_id;

    const statusClass = getStatusClass(currentOrder.current_status_name);
    const subtitle = `${currentOrder.order_ref} · ${formatDateTime(currentOrder.order_date)}`;
    document.getElementById('order-subtitle').textContent = subtitle;
}

// Render order information
function renderOrderInfo() {
    document.getElementById('order-ref').textContent = currentOrder.order_ref;
    document.getElementById('order-date').textContent = formatDateTime(currentOrder.order_date);
    document.getElementById('customer-name').textContent = currentOrder.cust_name || 'Guest';
    document.getElementById('customer-phone').textContent = formatPhone(currentOrder.order_phone);
}

// Render order items
function renderOrderItems() {
    const container = document.getElementById('order-items');

    if (!currentOrder.items || currentOrder.items.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-sm">No items in this order.</p>';
        return;
    }

    container.innerHTML = currentOrder.items.map(item => {
        const isCatering = item.is_catering;
        const cateringText = isCatering ? ` (${item.catering_size} tray)` : '';

        return `
            <div class="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                <div class="flex-1">
                    <h4 class="font-medium text-gray-900">${item.name}${cateringText}</h4>
                    ${item.special_instructions ? `<p class="text-sm text-gray-600 mt-1">${item.special_instructions}</p>` : ''}
                    <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                        <span>Qty: ${item.quantity}</span>
                        <span>Unit: ${formatCurrency(item.unit_price)}</span>
                        <span class="font-semibold text-gray-900">Total: ${formatCurrency(item.line_total)}</span>
                    </div>
                </div>
                <div class="flex space-x-2 ml-4">
                    <button onclick="editOrderItem(${item.order_item_id})" class="text-blue-600 hover:text-blue-700 text-sm">
                        Edit
                    </button>
                    <button onclick="removeOrderItem(${item.order_item_id})" class="text-red-600 hover:text-red-700 text-sm">
                        Remove
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Render order summary
function renderOrderSummary() {
    const order = currentOrder;

    document.getElementById('summary-subtotal').textContent = formatCurrency(order.subtotal);
    document.getElementById('summary-tax').textContent = formatCurrency(order.tax_amount);
    document.getElementById('summary-total').textContent = formatCurrency(order.total_amount);

    // Show/hide discount row
    if (order.discount_amount > 0) {
        document.getElementById('discount-row').classList.remove('hidden');
        const discountDisplay = order.discount_type === 'percent'
            ? `-${order.discount_amount}%`
            : `-${formatCurrency(order.discount_amount)}`;
        document.getElementById('summary-discount').textContent = discountDisplay;
    } else {
        document.getElementById('discount-row').classList.add('hidden');
    }

    // Show/hide tip row
    if (order.tip_amount > 0) {
        document.getElementById('tip-row').classList.remove('hidden');
        document.getElementById('summary-tip').textContent = formatCurrency(order.tip_amount);
    } else {
        document.getElementById('tip-row').classList.add('hidden');
    }
}

// Render status section
function renderStatusSection() {
    const badge = document.getElementById('current-status-badge');
    const statusClass = getStatusClass(currentOrder.current_status_name);
    badge.className = `px-3 py-1 rounded-full text-sm font-semibold ${statusClass}`;
    badge.textContent = currentOrder.current_status_name;

    // Populate status dropdown (exclude current status)
    const select = document.getElementById('new-status');
    const statuses = [
        {id: 1, name: 'Pending'},
        {id: 2, name: 'Confirmed'},
        {id: 3, name: 'Preparing'},
        {id: 4, name: 'Ready'},
        {id: 5, name: 'Delivered'},
        {id: 6, name: 'Completed'},
        {id: 7, name: 'Cancelled'}
    ];

    select.innerHTML = '<option value="">Select new status...</option>';
    statuses
        .filter(s => s.id !== currentOrder.current_status_id)
        .forEach(status => {
            const option = document.createElement('option');
            option.value = status.id;
            option.textContent = status.name;
            select.appendChild(option);
        });
}

// Render payment section
function renderPaymentSection() {
    const badge = document.getElementById('payment-status-badge');
    const paymentClass = getPaymentClass(currentOrder.payment_status);
    badge.className = `px-3 py-1 rounded-full text-sm font-semibold ${paymentClass}`;
    badge.textContent = currentOrder.payment_status.replace('_', ' ');

    // Render payment history
    renderPaymentHistory();
}

// Render payment history
function renderPaymentHistory() {
    const container = document.getElementById('payment-history');

    if (!currentOrder.payments || currentOrder.payments.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-500">No payments recorded.</p>';
        return;
    }

    container.innerHTML = currentOrder.payments.map(payment => `
        <div class="text-sm border-t pt-2">
            <div class="flex justify-between">
                <span class="font-medium">${formatCurrency(payment.amount_paid)}</span>
                <span class="text-gray-600">${payment.payment_method}</span>
            </div>
            ${payment.tip_amount > 0 ? `<div class="text-gray-600">Tip: ${formatCurrency(payment.tip_amount)}</div>` : ''}
            <div class="text-gray-500 text-xs">${formatDateTime(payment.payment_date)}</div>
        </div>
    `).join('');
}

// Load edit history
async function loadEditHistory() {
    try {
        const response = await api.getOrderHistory(currentOrder.order_id);
        const history = response.data;

        const container = document.getElementById('edit-history');

        if (!history || history.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">No edit history available.</p>';
            return;
        }

        container.innerHTML = history.map(entry => {
            const icon = getHistoryIcon(entry.entity_type);

            return `
                <div class="flex items-start space-x-3 border-l-2 border-gray-300 pl-4 py-2">
                    <div class="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                        ${icon}
                    </div>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-gray-900">${entry.action_type}</p>
                        ${entry.change_description ? `<p class="text-sm text-gray-600 mt-1">${entry.change_description}</p>` : ''}
                        ${entry.note ? `<p class="text-sm text-gray-500 italic mt-1">"${entry.note}"</p>` : ''}
                        <p class="text-xs text-gray-500 mt-1">
                            ${formatDateTime(entry.changed_at)} by ${entry.changed_by_username || 'System'}
                        </p>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load edit history:', error);
    }
}

// Update order status
async function updateStatus() {
    const statusId = parseInt(document.getElementById('new-status').value);
    const note = document.getElementById('status-note').value.trim();

    if (!statusId) {
        showToast('Please select a new status', 'warning');
        return;
    }

    try {
        await api.updateOrderStatus(currentOrder.order_id, {
            status_id: statusId,
            note: note || undefined
        });

        showToast('Status updated successfully', 'success');

        // Reset form
        document.getElementById('new-status').value = '';
        document.getElementById('status-note').value = '';

        // Reload order
        await loadOrder(currentOrder.order_id);

    } catch (error) {
        handleAPIError(error);
    }
}

// Show add item modal
async function showAddItemModal() {
    const modal = document.getElementById('add-item-modal');
    modal.classList.remove('hidden');

    // Load menu items if not already loaded
    if (menuItems.length === 0) {
        try {
            const response = await api.getMenu();
            menuItems = response.data.items || [];
        } catch (error) {
            showToast('Failed to load menu items', 'error');
            closeAddItemModal();
            return;
        }
    }

    // Render menu items
    const container = document.getElementById('menu-items-list');
    container.innerHTML = menuItems.map(item => `
        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
            <div class="flex-1">
                <h5 class="font-medium text-gray-900">${item.kic_name}</h5>
                <p class="text-sm text-gray-600">${formatCurrency(item.kic_price)}</p>
            </div>
            <button onclick="addItemToOrder(${item.kic_id})" class="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700">
                Add
            </button>
        </div>
    `).join('');
}

// Close add item modal
function closeAddItemModal() {
    document.getElementById('add-item-modal').classList.add('hidden');
}

// Add item to order
async function addItemToOrder(itemId) {
    const quantity = prompt('Enter quantity:', '1');
    if (!quantity || parseInt(quantity) <= 0) {
        return;
    }

    const specialInstructions = prompt('Special instructions (optional):');

    try {
        await api.addOrderItem(currentOrder.order_id, {
            kic_id: itemId,
            quantity: parseInt(quantity),
            special_instructions: specialInstructions || undefined
        });

        showToast('Item added successfully', 'success');
        closeAddItemModal();
        await loadOrder(currentOrder.order_id);

    } catch (error) {
        handleAPIError(error);
    }
}

// Edit order item
async function editOrderItem(itemId) {
    const item = currentOrder.items.find(i => i.order_item_id === itemId);
    if (!item) return;

    const quantity = prompt('Enter new quantity:', item.quantity);
    if (!quantity || parseInt(quantity) <= 0) {
        return;
    }

    const specialInstructions = prompt('Special instructions:', item.special_instructions || '');

    try {
        await api.updateOrderItem(currentOrder.order_id, itemId, {
            quantity: parseInt(quantity),
            special_instructions: specialInstructions || undefined
        });

        showToast('Item updated successfully', 'success');
        await loadOrder(currentOrder.order_id);

    } catch (error) {
        handleAPIError(error);
    }
}

// Remove order item
async function removeOrderItem(itemId) {
    const reason = prompt('Reason for removal (required):');
    if (!reason || reason.trim() === '') {
        showToast('Reason is required to remove an item', 'warning');
        return;
    }

    if (!confirm('Are you sure you want to remove this item?')) {
        return;
    }

    try {
        await api.removeOrderItem(currentOrder.order_id, itemId, reason);
        showToast('Item removed successfully', 'success');
        await loadOrder(currentOrder.order_id);

    } catch (error) {
        handleAPIError(error);
    }
}

// Show payment modal
function showPaymentModal() {
    document.getElementById('payment-modal').classList.remove('hidden');

    // Pre-fill amount with remaining balance
    const totalPaid = currentOrder.payments?.reduce((sum, p) => sum + p.amount_paid, 0) || 0;
    const remaining = currentOrder.total_amount - totalPaid;
    document.getElementById('payment-amount').value = remaining.toFixed(2);
}

// Close payment modal
function closePaymentModal() {
    document.getElementById('payment-modal').classList.add('hidden');
    document.getElementById('payment-form').reset();
    document.getElementById('override-fields').classList.add('hidden');
}

// Setup event listeners
function setupEventListeners() {
    // Payment form submission
    document.getElementById('payment-form').addEventListener('submit', handlePaymentSubmit);

    // Override checkbox
    document.getElementById('use-override').addEventListener('change', (e) => {
        const fields = document.getElementById('override-fields');
        if (e.target.checked) {
            fields.classList.remove('hidden');
        } else {
            fields.classList.add('hidden');
        }
    });
}

// Handle payment form submission
async function handlePaymentSubmit(e) {
    e.preventDefault();

    const amount = parseFloat(document.getElementById('payment-amount').value);
    const method = document.getElementById('payment-method').value;
    const tip = parseFloat(document.getElementById('tip-amount').value) || 0;
    const useOverride = document.getElementById('use-override').checked;

    const paymentData = {
        amount: amount,
        payment_method: method,
        tip_amount: tip
    };

    if (useOverride) {
        const overrideAmount = parseFloat(document.getElementById('override-amount').value);
        const overrideReason = document.getElementById('override-reason').value.trim();

        if (!overrideAmount || overrideAmount <= 0) {
            showToast('Please enter a valid override amount', 'warning');
            return;
        }

        if (!overrideReason) {
            showToast('Please provide a reason for the override', 'warning');
            return;
        }

        paymentData.override_final_amount = overrideAmount;
        paymentData.payment_notes = overrideReason;
    }

    try {
        await api.recordPayment(currentOrder.order_id, paymentData);
        showToast('Payment recorded successfully', 'success');
        closePaymentModal();
        await loadOrder(currentOrder.order_id);

    } catch (error) {
        handleAPIError(error);
    }
}

// Helper: Get history icon
function getHistoryIcon(entityType) {
    const icons = {
        'order': '<svg class="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/></svg>',
        'order_item': '<svg class="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20"><path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/></svg>',
        'status': '<svg class="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/></svg>',
        'payment': '<svg class="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/><path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/></svg>'
    };
    return icons[entityType] || icons['order'];
}

// Helper: Get status badge class
function getStatusClass(status) {
    const statusMap = {
        'Pending': 'bg-yellow-100 text-yellow-800',
        'Confirmed': 'bg-blue-100 text-blue-800',
        'Preparing': 'bg-purple-100 text-purple-800',
        'Ready': 'bg-indigo-100 text-indigo-800',
        'Delivered': 'bg-green-100 text-green-800',
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

// Helper: Format date and time
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Helper: Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initOrderDetail);
