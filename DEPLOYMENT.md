# Cloud Kitchen Order System - Deployment Guide

## Quick Start

### 1. Create .env File

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kitchen_db
DB_USER=kitchen_user
DB_PASSWORD=your_secure_password
```

### 2. Create PostgreSQL Database

```bash
# Create database
createdb kitchen_db

# Create user with password
psql -d postgres -c "CREATE USER kitchen_user WITH PASSWORD 'your_secure_password';"

# Grant permissions
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE kitchen_db TO kitchen_user;"
psql -d kitchen_db -c "GRANT ALL ON SCHEMA public TO kitchen_user;"
```

### 3. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Migrations

```bash
python -m src.database.migrate
```

This will create all necessary tables.

### 6. Load Sample Data (Optional but Recommended)

```bash
python -m src.database.seed
```

This creates sample users:
- **Admin**: admin@kitchen.com / password123
- **Staff**: staff@kitchen.com / password123
- **Customer**: john@example.com / password123

### 7. Start the Server

```bash
python run.py
```

The server will start on `http://0.0.0.0:5000`

### 8. Find Your Mac IP Address

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Access from other devices on your network: `http://<your-mac-ip>:5000`

## Testing the API

### Health Check

```bash
curl http://localhost:5000/health
```

### Register a User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "password123",
    "phone": "1234567890",
    "cust_name": "Test User"
  }'
```

### Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@kitchen.com",
    "password": "password123"
  }'
```

Save the token from the response.

### Get Menu

```bash
curl http://localhost:5000/api/menu
```

### Create Order (Example)

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer": {
      "phone": "1234567890",
      "name": "John Doe"
    },
    "items": [
      {
        "kic_id": 1,
        "quantity": 2
      }
    ],
    "tip_amount": 5.00
  }'
```

## API Endpoints Summary

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user (requires auth)

### Menu
- `GET /api/menu` - Get full menu
- `GET /api/menu/items/:id` - Get specific item
- `POST /api/menu/items` - Create item (admin only)
- `PUT /api/menu/items/:id` - Update item (admin only)

### Orders
- `POST /api/orders` - Create order
- `POST /api/orders/phone-lookup` - Find customer by phone (staff only)
- `GET /api/orders/:id` - Get order details
- `GET /api/orders/track/:ref` - Track order by reference (public)
- `PUT /api/orders/:id/status` - Update order status (staff only)
- `GET /api/orders/my-orders` - Get user's orders (requires auth)
- `GET /api/orders/recent` - Get recent orders (staff only)

### Payments
- `POST /api/payments/orders/:id/payments` - Record payment (staff only)
- `GET /api/payments/orders/:id/payments` - Get payment history

### Reports
- `GET /api/reports/sales` - Sales report (admin only)
- `GET /api/reports/top-items` - Top selling items (admin only)
- `GET /api/reports/top-customers` - Top customers (admin only)

## Database Migration Management

### Check Migration Status

```bash
python -m src.database.migrate
```

### Create New Migration

1. Create a new SQL file in `migrations/` directory
2. Name it with next number: `006_description.sql`
3. Run migrations: `python -m src.database.migrate`

## Troubleshooting

### Database Connection Error

- Check PostgreSQL is running: `brew services list | grep postgresql`
- Verify credentials in `.env`
- Test connection: `psql -U kitchen_user -d kitchen_db`

### Port Already in Use

Change the PORT in `.env` file:
```env
PORT=5001
```

### Import Errors

Ensure virtual environment is activated:
```bash
source .venv/bin/activate
```

## Production Considerations

1. **Change Secrets**: Update `SECRET_KEY` and `JWT_SECRET_KEY` in `.env`
2. **Use HTTPS**: Configure SSL/TLS for production
3. **Database Backups**: Set up regular PostgreSQL backups
4. **Logging**: Configure production-level logging
5. **Environment**: Set `FLASK_ENV=production` and `FLASK_DEBUG=False`
6. **Reverse Proxy**: Use Nginx or similar for production deployment

## Next Steps

The backend API is now fully functional. You can:

1. Test all API endpoints using curl or Postman
2. Build a web frontend (planned with Tailwind CSS)
3. Build a mobile app that consumes the API
4. Add additional features as needed

## Support

For issues, refer to:
- SPEC.md - Full specifications
- GEMINI.md - Development guidance
- README.md - Project overview
