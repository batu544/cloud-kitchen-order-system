-- Migration 004: Extend payment tables with order linkage

ALTER TABLE kitch_payment
ADD COLUMN IF NOT EXISTS order_id INTEGER REFERENCES kitch_order(order_id) ON DELETE CASCADE;

ALTER TABLE kitch_payment
ADD COLUMN IF NOT EXISTS payment_notes TEXT;

ALTER TABLE kitch_payment
ADD COLUMN IF NOT EXISTS tip_amount NUMERIC(10,2) DEFAULT 0 CHECK (tip_amount >= 0);

ALTER TABLE kitch_payment
ADD COLUMN IF NOT EXISTS recorded_by_user_id INTEGER REFERENCES kitch_user(user_id) ON DELETE SET NULL;

ALTER TABLE kitch_payment
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create index for order lookups
CREATE INDEX IF NOT EXISTS idx_kitch_payment_order_id ON kitch_payment(order_id);
CREATE INDEX IF NOT EXISTS idx_kitch_payment_date ON kitch_payment(payment_date);
CREATE INDEX IF NOT EXISTS idx_kitch_payment_status ON kitch_payment(payment_status);
