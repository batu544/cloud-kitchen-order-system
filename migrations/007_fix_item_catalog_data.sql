-- Migration 007: Fix Item Catalog Data Quality Issues
-- Purpose: Clean up kitch_item_catalg data for production import
--
-- Fixes applied:
--   1. Remove embedded newline from item name (kic_id=18)
--   2. Correct wrong category for kheer desserts (kic_id=64, 66) → Desserts (cat 3)
--   3. Fix spelling: "Vermesil" → "Vermicelli" (kic_id=66)
--   4. Standardize "Biriyani" → "Biryani" spelling across all items
--   5. Deactivate overlapping seed/demo items superseded by real menu entries
--   6. Standardize name casing (Title Case) and fix formatting inconsistencies

-- ============================================================================
-- 1. Fix embedded newline in item name
-- ============================================================================
UPDATE kitch_item_catalg
SET kic_name   = 'Chilli Paneer',
    updated_at = CURRENT_TIMESTAMP
WHERE kic_id = 18;

-- ============================================================================
-- 2 & 3. Fix category and spelling for kheer desserts
-- ============================================================================
UPDATE kitch_item_catalg
SET category_id = 3,                  -- Desserts (was Main Course)
    kic_name    = 'Rice Kheer',
    updated_at  = CURRENT_TIMESTAMP
WHERE kic_id = 64;

UPDATE kitch_item_catalg
SET category_id = 3,                  -- Desserts (was Main Course)
    kic_name    = 'Vermicelli Kheer', -- fixed spelling (was "Vermesil kheer")
    updated_at  = CURRENT_TIMESTAMP
WHERE kic_id = 66;

-- ============================================================================
-- 4. Standardize Biryani spelling (Biriyani → Biryani)
-- ============================================================================
UPDATE kitch_item_catalg
SET kic_name   = 'Chicken Biryani',
    updated_at = CURRENT_TIMESTAMP
WHERE kic_id = 39;

UPDATE kitch_item_catalg
SET kic_name   = 'Mutton Biryani',
    updated_at = CURRENT_TIMESTAMP
WHERE kic_id = 41;

UPDATE kitch_item_catalg
SET kic_name   = 'Shrimp Biryani',
    updated_at = CURRENT_TIMESTAMP
WHERE kic_id = 43;

UPDATE kitch_item_catalg
SET kic_name   = 'Egg Biryani',
    updated_at = CURRENT_TIMESTAMP
WHERE kic_id = 59;

UPDATE kitch_item_catalg
SET kic_name   = 'Veg Biryani',
    updated_at = CURRENT_TIMESTAMP
WHERE kic_id = 71;

-- ============================================================================
-- 5. Deactivate overlapping seed/demo items
--    kic_id=2 "Paneer Butter Masala"  → superseded by kic_id=25 "Butter Paneer"
--    kic_id=3 "Biryani" (generic)     → superseded by specific biryani items
--    kic_id=4 "Samosa"               → superseded by kic_id=20 "Samosa (3)"
-- ============================================================================
UPDATE kitch_item_catalg
SET is_active  = FALSE,
    updated_at = CURRENT_TIMESTAMP
WHERE kic_id IN (2, 3, 4);

-- ============================================================================
-- 6. Standardize name casing and formatting
--    Rule: Title Case; spaces inside parentheses e.g. "(3)" not "(3)"
--          "+" gets spaces around it e.g. "Idli + Sambar"
-- ============================================================================

-- Fix lowercase / mixed-case names
UPDATE kitch_item_catalg SET kic_name = 'Mutton Curry',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 19;
UPDATE kitch_item_catalg SET kic_name = 'Samosa (3)',            updated_at = CURRENT_TIMESTAMP WHERE kic_id = 20;
UPDATE kitch_item_catalg SET kic_name = 'Jelebi (1lb)',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 21;
UPDATE kitch_item_catalg SET kic_name = 'Soya Chilli',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 22;
UPDATE kitch_item_catalg SET kic_name = 'Chicken Curry',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 23;
UPDATE kitch_item_catalg SET kic_name = 'Veg Puff (2)',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 24;
UPDATE kitch_item_catalg SET kic_name = 'Butter Paneer',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 25;
UPDATE kitch_item_catalg SET kic_name = 'Chilli Chicken',        updated_at = CURRENT_TIMESTAMP WHERE kic_id = 26;
UPDATE kitch_item_catalg SET kic_name = 'Egg Puff (2)',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 27;
UPDATE kitch_item_catalg SET kic_name = 'Kajukatli (3)',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 28;
UPDATE kitch_item_catalg SET kic_name = 'Chana Dal Fry',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 29;
UPDATE kitch_item_catalg SET kic_name = 'Chicken Lollipop (5)', updated_at = CURRENT_TIMESTAMP WHERE kic_id = 30;
UPDATE kitch_item_catalg SET kic_name = 'Veg Cutlet (3)',        updated_at = CURRENT_TIMESTAMP WHERE kic_id = 31;
UPDATE kitch_item_catalg SET kic_name = 'Toor Dal Fry',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 32;
UPDATE kitch_item_catalg SET kic_name = 'Rasmalai (4)',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 34;
UPDATE kitch_item_catalg SET kic_name = 'Aloo Gobi Mattar',      updated_at = CURRENT_TIMESTAMP WHERE kic_id = 35;
UPDATE kitch_item_catalg SET kic_name = 'Dragon Chicken',        updated_at = CURRENT_TIMESTAMP WHERE kic_id = 36;
UPDATE kitch_item_catalg SET kic_name = 'Rasabali (4)',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 37;
UPDATE kitch_item_catalg SET kic_name = 'Navaratna Korma',       updated_at = CURRENT_TIMESTAMP WHERE kic_id = 38;
UPDATE kitch_item_catalg SET kic_name = 'Dahi Vada',             updated_at = CURRENT_TIMESTAMP WHERE kic_id = 40;
UPDATE kitch_item_catalg SET kic_name = 'Aloo Dam',              updated_at = CURRENT_TIMESTAMP WHERE kic_id = 42;
UPDATE kitch_item_catalg SET kic_name = 'Coconut Sweet (6)',     updated_at = CURRENT_TIMESTAMP WHERE kic_id = 44;
UPDATE kitch_item_catalg SET kic_name = 'Rajma Curry',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 45;
UPDATE kitch_item_catalg SET kic_name = 'Shrimp Popcorn',        updated_at = CURRENT_TIMESTAMP WHERE kic_id = 46;
UPDATE kitch_item_catalg SET kic_name = 'Besan Ladoo (6)',       updated_at = CURRENT_TIMESTAMP WHERE kic_id = 47;
UPDATE kitch_item_catalg SET kic_name = 'Chola Curry',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 48;
UPDATE kitch_item_catalg SET kic_name = 'Chilli Shrimp',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 49;
UPDATE kitch_item_catalg SET kic_name = 'Rasagulla (10)',        updated_at = CURRENT_TIMESTAMP WHERE kic_id = 50;
UPDATE kitch_item_catalg SET kic_name = 'Aloo Parbal Korma',     updated_at = CURRENT_TIMESTAMP WHERE kic_id = 51;
UPDATE kitch_item_catalg SET kic_name = 'Shrimp Curry',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 52;
UPDATE kitch_item_catalg SET kic_name = 'Bundi Ladoo (1lb)',     updated_at = CURRENT_TIMESTAMP WHERE kic_id = 53;
UPDATE kitch_item_catalg SET kic_name = 'Kofta Curry',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 54;
UPDATE kitch_item_catalg SET kic_name = 'Egg Labadar',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 55;
UPDATE kitch_item_catalg SET kic_name = 'Idli + Sambar',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 56;
UPDATE kitch_item_catalg SET kic_name = 'Egg Curry',             updated_at = CURRENT_TIMESTAMP WHERE kic_id = 57;
UPDATE kitch_item_catalg SET kic_name = 'Vada + Sambar',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 58;
UPDATE kitch_item_catalg SET kic_name = 'Chicken Egg Roll',      updated_at = CURRENT_TIMESTAMP WHERE kic_id = 61;
UPDATE kitch_item_catalg SET kic_name = 'Paratha (3)',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 62;
UPDATE kitch_item_catalg SET kic_name = 'White Pasta',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 68;
UPDATE kitch_item_catalg SET kic_name = 'Fish Curry',            updated_at = CURRENT_TIMESTAMP WHERE kic_id = 69;
UPDATE kitch_item_catalg SET kic_name = 'Red Pasta',             updated_at = CURRENT_TIMESTAMP WHERE kic_id = 70;
UPDATE kitch_item_catalg SET kic_name = 'Paneer Mattar Pulao',   updated_at = CURRENT_TIMESTAMP WHERE kic_id = 72;
UPDATE kitch_item_catalg SET kic_name = 'Samosa Chaat',          updated_at = CURRENT_TIMESTAMP WHERE kic_id = 73;
UPDATE kitch_item_catalg SET kic_name = 'Crispy Gobi Fry',       updated_at = CURRENT_TIMESTAMP WHERE kic_id = 74;
UPDATE kitch_item_catalg SET kic_name = 'Gobi 65',               updated_at = CURRENT_TIMESTAMP WHERE kic_id = 75;
UPDATE kitch_item_catalg SET kic_name = 'Dal Makhani',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 76;
UPDATE kitch_item_catalg SET kic_name = 'Bhindi Masala',         updated_at = CURRENT_TIMESTAMP WHERE kic_id = 77;
UPDATE kitch_item_catalg SET kic_name = 'Brinjal Masala',        updated_at = CURRENT_TIMESTAMP WHERE kic_id = 78;
UPDATE kitch_item_catalg SET kic_name = 'Veg Noodles',           updated_at = CURRENT_TIMESTAMP WHERE kic_id = 81;
UPDATE kitch_item_catalg SET kic_name = 'Jeera Rice',            updated_at = CURRENT_TIMESTAMP WHERE kic_id = 85;
