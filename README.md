# Cloud Kitchen Order System

A Python/Flask-based order management system for cloud kitchens with support for registered users, guest checkout, staff phone orders, manual payment tracking, catering tray pricing, and comprehensive reporting.

## Features

- **User Management**: Registration, login with JWT authentication
- **Order Management**: Guest checkout, registered user orders, staff phone orders
- **Menu System**: Categories, items, catering options
- **Catering Pricing**: Automatic calculation for small/medium/large trays
- **Discounts**: Support for percentage and fixed amount discounts
- **Payment Tracking**: Manual payment recording with tips
- **Order Tracking**: Public tracking via order reference
- **Reporting**: Sales, top items, top customers
- **Local Network Access**: Accessible from all devices on Wi-Fi

## Technology Stack

- **Backend**: Flask 3.0.2
- **Database**: PostgreSQL
- **Authentication**: JWT tokens with bcrypt password hashing
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript

## Project Structure

```
Python_Projects/
├── config.py                    # Configuration management
├── run.py                       # Application entry point
├── migrations/                  # SQL database migrations
├── src/
│   ├── database/               # Database connection and migrations
│   ├── models/                 # Data models
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic
│   ├── api/                    # REST API endpoints
│   ├── middleware/             # Authentication, error handling
│   ├── utils/                  # Utilities (validators, security)
│   └── web/                    # Web UI (templates, static files)
└── tests/                      # Test suite
```

## Setup Instructions

### Prerequisites

- Python 3.13+
- PostgreSQL (already installed on your system)

### 1. Clone and Navigate

```bash
cd /Users/prasanta/Documents/Python_Projects
```

### 2. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kitchen_db
DB_USER=kitchen_user
DB_PASSWORD=your_password_here
```

### 5. Create Database

```bash
createdb kitchen_db
psql -d postgres -c "CREATE USER kitchen_user WITH PASSWORD 'your_password';"
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE kitchen_db TO kitchen_user;"
psql -d kitchen_db -c "GRANT ALL ON SCHEMA public TO kitchen_user;"
```

### 6. Run Migrations

```bash
python -m src.database.migrate
```

### 7. (Optional) Load Sample Data

```bash
python -m src.database.seed
```

This creates sample menu items, customers, and test users:
- **Admin**: admin@kitchen.com / password123
- **Staff**: staff@kitchen.com / password123
- **Customer**: john@example.com / password123

### 8. Start Server

```bash
python run.py
```

The server will start on `http://0.0.0.0:5000`

### 9. Find Your Mac IP for Wi-Fi Access

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Access the application from any device on your Wi-Fi network using:
- `http://<your-mac-ip>:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info (protected)

### Menu
- `GET /api/menu` - Get menu with categories and items
- `POST /api/menu/items` - Add menu item (admin only)
- `PUT /api/menu/items/:id` - Update menu item (admin only)

### Orders
- `POST /api/orders` - Create new order
- `POST /api/orders/phone-lookup` - Find customer by phone (staff only)
- `GET /api/orders/:id` - Get order details
- `GET /api/orders/track/:ref` - Track order by reference (public)
- `PUT /api/orders/:id/status` - Update order status (staff only)

### Payments
- `POST /api/orders/:id/payments` - Record payment (staff only)
- `GET /api/orders/:id/payments` - Get payment history

### Reports
- `GET /api/reports/sales` - Sales by period (admin only)
- `GET /api/reports/top-items` - Top selling items (admin only)
- `GET /api/reports/top-customers` - Top customers (admin only)

## Business Logic

### Catering Pricing Formula

Per SPEC.md lines 130-147:
- **Small**: `plate_price × 4 × 0.9`
- **Medium**: `plate_price × 6 × 0.9`
- **Large**: `plate_price × 12 × 0.9`

### Discount Calculation

Per SPEC.md lines 119-123:
- **Percent**: `discount_value` is percentage (0-100)
- **Fixed**: `discount_value` is currency amount to subtract

### Order Total Calculation

`subtotal → discount → tip → total_amount` (no tax)

### Phone-Based Customer Linking

When staff places an order (SPEC.md line 26):
1. Search customer by phone (exactly 10 digits)
2. If found, link `cust_id` to order
3. If not found, create guest order

## Development

### Running Tests

```bash
pytest
```

### Running Migrations

```bash
python -m src.database.migrate
```

### Checking Migration Status

```bash
python -m src.database.migrate
```

## Configuration

Key configuration options in `.env`:

- `DB_*`: Database connection settings
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `JWT_EXPIRATION_HOURS`: Token expiration (default: 24 hours)
- `HOST`: Server host (0.0.0.0 for Wi-Fi access)
- `PORT`: Server port (default: 5000)
- `TAX_RATE`: Sales tax rate (default: 0.00)

## Security

- Passwords hashed with bcrypt
- JWT token-based authentication
- Role-based authorization (customer, staff, admin)
- 10-digit phone validation
- Server-side calculation of all totals

## License

Proprietary

## Support

For issues and questions, refer to SPEC.md and GEMINI.md for detailed specifications and implementation guidance.
