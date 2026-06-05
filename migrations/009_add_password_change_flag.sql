-- Migration 009: Add requires_password_change flag to kitch_user

ALTER TABLE kitch_user ADD COLUMN requires_password_change BOOLEAN DEFAULT FALSE;
