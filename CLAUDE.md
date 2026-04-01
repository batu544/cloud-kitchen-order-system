# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository

## Project Overview

Cloud Kitchen Order System - A Python-based REST API for managing a local cloud kitchen details present in @SPEC.md file with order management, payment tracking, catering services, and reporting capabilities. Designed for local deployment on Mac with staff access via Wi-Fi.

## Guidelines
- **keep the response clean and short. No need to display the code change details

## Development Environment

**Python Version**: 3.13
**Virtual Environment**: `.venv` (already created)

### Setup Commands
```bash
source .venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt  # Install dependencies (when created)
```

## High-Level Architecture

### Backend Stack
- **Language**: Python (Flask/FastAPI recommended per SPEC.md:230)
- **Database**: PostgreSQL with role `kitchen_user`
- **Authentication**: Session-based or JWT tokens for users/staff
- **Deployment**: Local Mac server, bind to 0.0.0.0 for Wi-Fi access

## Recommended Technology stack
- **Backend**: Python
- **Frontend**: Tailwind css


### Data Model Foundation
The system extends existing `kitch_*` tables:
- `kitch_category`, `kitch_item_catalg`, `kitch_customer`, `kitch_status`, `kitch_payment`

### Key New Tables (SPEC.md:38-113)
- **kitch_user**: Authentication and role management (customer/staff/admin)
- **kitch_order**: Order tracking with discount/tip/tax calculation
- **kitch_order_item**: Line items including catering tray support
- **kitch_order_status_history**: Audit trail for order lifecycle
- **kitch_payment**: Extended with order_id, tip_amount, payment_notes

## Critical Business Logic


### Reports (Admin Only)
- `GET /api/reports/sales` - Sales by period
- `GET /api/reports/top-items` - Best-selling items
- `GET /api/reports/top-customers` - Top spenders

## Reporting Queries (SPEC.md:179-209)

Key aggregations for admin dashboard:
- **Total sales by day**: Group by `date_trunc('day', order_date)`
- **Sales by item**: Join `kitch_order_item` + `kitch_order`, sum `line_total`
- **Top customers**: Join `kitch_order` + `kitch_customer`, sum `total_amount`

See SPEC.md lines 180-209 for complete SQL examples.

## Security Requirements (SPEC.md:235-239)

- Password hashing: bcrypt
- Role-based access: Validate user role for staff/admin endpoints
- Phone uniqueness: Enforce for registered customers
- Audit logging: Track all status and payment changes via `changed_by_user_id`

## User Flows

### Guest Checkout (SPEC.md:217-218)
1. Browse menu (no login)
2. Add to cart with quantities/special instructions
3. Provide name + phone at checkout
4. Receive `order_ref` for tracking

### Staff Phone Order (SPEC.md:219-220)
1. Staff searches by phone
2. System links to `kitch_customer` if exists
3. Staff adds items, applies discounts (percent or fixed)
4. Records manual payment with optional tip

### Order Tracking (SPEC.md:222)
Public tracking via `order_ref` shows status timeline from `kitch_order_status_history`.

## Testing Focus (SPEC.md:243-249)

- Unit tests for catering price calculations
- Discount computation (percent vs fixed)
- Phone lookup and customer linking
- Order total calculations with all modifiers
- Payment status transitions
- Report query accuracy with sample data
