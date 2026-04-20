# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Guidelines
- Keep responses clean and short — no need to display code change details
- Use parameterized SQL only — never f-strings or string interpolation in queries
- All API responses must use `success_response()` / `error_response()` from `src/utils/responses.py`
- Never commit `.env` — it contains DB credentials and JWT secret

---

## Project Overview

**Cloud Kitchen Order System** — Flask REST API + PostgreSQL + Tailwind CSS web UI.
Local Mac deployment; staff access via Wi-Fi. No external payment gateway.

Full spec: `SPEC.md`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, Flask 3.0.2 |
| Database | PostgreSQL, role `kitchen_user` |
| Auth | PyJWT 2.8.0, bcrypt 4.1.2 |
| Rate limiting | Flask-Limiter 3.5.0 |
| CORS | Flask-CORS 4.0.0 |
| Frontend | Tailwind CSS (CDN), vanilla JS |

---

## Development Commands

```bash
source .venv/bin/activate           # Activate virtual environment
pip install -r requirements.txt     # Install dependencies
python run.py                       # Start server (0.0.0.0:5000)

python -m src.database.migrate      # Run SQL migrations
python -m src.database.seed         # Load demo data (admin/staff/customer users + menu)

pytest tests/                       # All tests
pytest tests/unit/ -q               # Unit tests only (fast)
pytest tests/e2e/                   # End-to-end tests
```

---

## Architecture

Layered: **API Blueprints → Services → Repositories → PostgreSQL**

```
src/
├── __init__.py              # Flask app factory (CORS, rate limiter, security headers, blueprints)
├── api/                     # 6 blueprints (~40 endpoints)
│   ├── auth.py              # /api/auth — register, login, me, change-password
│   ├── menu.py              # /api/menu — get items, popular, create/update (admin)
│   ├── orders.py            # /api/orders — create, track, status, item edits
│   ├── payments.py          # /api/payments — record manual payments
│   ├── reports.py           # /api/reports — sales, top-items, top-customers (admin)
│   ├── admin.py             # /api/admin — user management (admin)
│   └── web_routes.py        # Serves 15 HTML templates
├── services/                # Business logic (call these from API, not repositories directly)
│   ├── auth_service.py
│   ├── order_service.py     # Order creation, status, item management
│   ├── pricing_service.py   # Catering calculations, discounts, totals
│   ├── payment_service.py
│   ├── menu_service.py
│   ├── report_service.py
│   └── customer_service.py
├── repositories/            # Data access (SQL queries, no business logic here)
│   ├── base.py              # BaseRepository with CRUD helpers
│   ├── order_repository.py
│   ├── customer_repository.py
│   ├── menu_repository.py
│   ├── payment_repository.py
│   ├── user_repository.py
│   ├── report_repository.py
│   └── audit_repository.py
├── models/                  # Dataclass models (Order, OrderItem, Payment, User, MenuItem)
├── middleware/
│   ├── auth_middleware.py   # Decorators: require_auth, require_role, optional_auth
│   └── error_handler.py
├── utils/
│   ├── responses.py         # success_response(), error_response()
│   ├── validators.py        # validate_phone (10 digits), validate_email, validate_order_items
│   └── security.py          # hash_password, verify_password, generate_token, verify_token
└── database/
    ├── connection.py        # ThreadedConnectionPool (min=2, max=10)
    ├── migrate.py           # Migration runner with version tracking
    └── seed.py              # Demo data loader
```

---

## Database Migrations

Files live in `migrations/` and are numbered sequentially:

| File | Contents |
|---|---|
| 001 | Base tables: `kitch_category`, `kitch_customer`, `kitch_item_catalg`, `kitch_status`, `kitch_payment` |
| 002 | `kitch_user` (auth, roles: customer/staff/admin) |
| 003 | `kitch_order`, `kitch_order_item`, `kitch_order_status_history` |
| 004 | Extend `kitch_payment` with order_id, tip_amount, payment_notes |
| 005 | Performance indexes |
| 006 | `kitch_order_edit_history` (JSONB audit), payment overrides, "Delivered" status |

**Rules:** Never edit existing migration files. New changes = new file (007_, 008_, ...).

---

## Authentication

- JWT Bearer tokens (24h expiry, configurable via `JWT_EXPIRATION_HOURS`)
- Decorators in `src/middleware/auth_middleware.py`:
  - `@require_auth` — blocks unauthenticated requests
  - `@require_role('staff', 'admin')` — enforces role restriction
  - `@optional_auth` — works with or without token

---

## Critical Business Logic

### Catering Pricing (`src/services/pricing_service.py`)
```python
small  = plate_price * 4  * 0.9
medium = plate_price * 6  * 0.9
large  = plate_price * 12 * 0.9
```

### Discount Calculation
- `discount_type = 'percent'`: `discount_amount` is 0–100 (percentage of subtotal)
- `discount_type = 'fixed'`: `discount_amount` subtracted directly (capped at subtotal)
- Staff only — customers cannot apply discounts

### Order Total
```
subtotal = sum(line_total for all items)
discount = apply_discount(subtotal, type, value)
total    = (subtotal - discount) + tip_amount   # tax is always 0
```
All calculations are server-side. Never trust client-sent totals.

### Phone Linking
- Phone must be exactly 10 digits (validated in `src/utils/validators.py`)
- On order creation: if phone matches `kitch_customer.cust_phone_number`, link `cust_id` to order

---

## Testing

```
tests/
├── unit/
│   ├── test_pricing_service.py   # Catering, discounts, totals (48 tests)
│   ├── test_order_service.py
│   ├── test_auth_service.py
│   ├── test_menu_service.py
│   ├── test_payment_service.py
│   └── test_validators.py
├── integration/                  # Real PostgreSQL tests
└── e2e/
    ├── conftest.py               # Fixtures, test DB setup
    └── test_app.py               # Full user flows
```

Always run `pytest tests/unit/` before committing pricing or validation changes.

---

## Frontend

15 Tailwind CSS templates in `src/web/templates/`. JS files in `src/web/static/js/`:

| File | Purpose |
|---|---|
| `api.js` | REST client wrapper with Bearer token injection |
| `cart.js` | Cart state in localStorage (supports catering sizes) |
| `utils.js` | `showToast()`, `formatCurrency()`, `validatePhone()` |
| `staff-dashboard.js` | Daily order list, status updates, pagination |
| `staff-order-detail.js` | Order editing, item management |

Primary color: `orange-600`. Background: `gray-*`.

---

## Security

- `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, CSP headers on all responses
- Rate limits: register 5/min, login 10/min
- Input validation at API boundary; business rules enforced in services
- Audit trail: `kitch_order_status_history` and `kitch_order_edit_history` (JSONB)
