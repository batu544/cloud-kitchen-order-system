-- Migration 005: Additional performance indexes

-- Additional customer indexes
CREATE INDEX IF NOT EXISTS idx_kitch_customer_phone ON kitch_customer(cust_phone_number);
CREATE INDEX IF NOT EXISTS idx_kitch_customer_email ON kitch_customer(cust_email);
CREATE INDEX IF NOT EXISTS idx_kitch_customer_created ON kitch_customer(created_at);

-- Additional menu item indexes
CREATE INDEX IF NOT EXISTS idx_kitch_item_catalg_category ON kitch_item_catalg(category_id);
CREATE INDEX IF NOT EXISTS idx_kitch_item_catalg_active ON kitch_item_catalg(is_active);
CREATE INDEX IF NOT EXISTS idx_kitch_item_catalg_catering ON kitch_item_catalg(is_catering);
CREATE INDEX IF NOT EXISTS idx_kitch_item_catalg_price ON kitch_item_catalg(kic_price);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_kitch_order_cust_date ON kitch_order(cust_id, order_date DESC);
CREATE INDEX IF NOT EXISTS idx_kitch_order_status_date ON kitch_order(current_status_id, order_date DESC);
CREATE INDEX IF NOT EXISTS idx_kitch_order_payment_date ON kitch_order(payment_status, order_date DESC);
