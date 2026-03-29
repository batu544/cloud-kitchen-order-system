/**
 * Shopping Cart Manager
 */

class ShoppingCart {
    constructor() {
        this.items = this.loadCart();
    }

    loadCart() {
        const cartStr = localStorage.getItem('cart');
        return cartStr ? JSON.parse(cartStr) : [];
    }

    saveCart() {
        localStorage.setItem('cart', JSON.stringify(this.items));
        this.dispatchCartUpdate();
    }

    addItem(item) {
        // Check if item already exists
        const existing = this.items.find(i =>
            i.kic_id === item.kic_id &&
            i.catering_size === item.catering_size
        );

        if (existing) {
            existing.quantity += item.quantity;
        } else {
            this.items.push({
                kic_id: item.kic_id,
                name: item.name,
                price: item.price,
                quantity: item.quantity,
                is_catering: item.is_catering || false,
                catering_size: item.catering_size || null,
                special_instructions: item.special_instructions || ''
            });
        }

        this.saveCart();
        return true;
    }

    updateQuantity(index, quantity) {
        if (quantity <= 0) {
            this.removeItem(index);
        } else {
            this.items[index].quantity = quantity;
            this.saveCart();
        }
    }

    updateInstructions(index, instructions) {
        this.items[index].special_instructions = instructions;
        this.saveCart();
    }

    removeItem(index) {
        this.items.splice(index, 1);
        this.saveCart();
    }

    clear() {
        this.items = [];
        this.saveCart();
    }

    getItems() {
        return this.items;
    }

    getItemCount() {
        return this.items.reduce((sum, item) => sum + item.quantity, 0);
    }

    calculateSubtotal() {
        return this.items.reduce((sum, item) => {
            // For catering items, price is already calculated with multiplier in menu.html
            // For regular items, price is the base price
            const itemPrice = item.price;
            return sum + (itemPrice * item.quantity);
        }, 0);
    }

    calculateTotal(discount = 0, tip = 0) {
        const subtotal = this.calculateSubtotal();
        const total = subtotal - discount + tip;
        return Math.max(0, total);
    }

    dispatchCartUpdate() {
        window.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: {
                itemCount: this.getItemCount(),
                subtotal: this.calculateSubtotal()
            }
        }));
    }

    prepareOrderData(customerInfo, discountInfo = null, tipAmount = 0) {
        return {
            customer: customerInfo,
            items: this.items.map(item => ({
                kic_id: item.kic_id,
                quantity: item.quantity,
                special_instructions: item.special_instructions,
                is_catering: item.is_catering,
                catering_size: item.catering_size
            })),
            discount: discountInfo,
            tip_amount: tipAmount
        };
    }
}

// Global cart instance
const cart = new ShoppingCart();
