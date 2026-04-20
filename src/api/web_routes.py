"""Web UI routes for serving HTML pages."""
from flask import Blueprint, render_template, redirect

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Landing page."""
    return render_template('index.html')


@web_bp.route('/menu')
def menu():
    """Menu page."""
    return render_template('menu.html')


@web_bp.route('/cart')
def cart():
    """Shopping cart page."""
    return render_template('cart.html')


@web_bp.route('/checkout')
def checkout():
    """Checkout page."""
    return render_template('checkout.html')


@web_bp.route('/track')
def track():
    """Order tracking page."""
    return render_template('track.html')


@web_bp.route('/staff')
def staff():
    """Redirect old staff route to new dashboard."""
    return redirect('/staff/dashboard')


@web_bp.route('/staff/dashboard')
def staff_dashboard():
    """Staff dashboard - main landing page for staff."""
    return render_template('staff_dashboard.html')


@web_bp.route('/staff/orders/new')
def staff_new_order():
    """Staff new order creation page."""
    return render_template('staff_new_order.html')


@web_bp.route('/staff/orders/<int:order_id>')
def staff_order_detail(order_id):
    """Staff order detail and edit page."""
    return render_template('staff_order_detail.html')


@web_bp.route('/staff/reports')
def admin_reports():
    """Admin reports page."""
    return render_template('admin_reports.html')


@web_bp.route('/my-orders')
def my_orders():
    """Customer order history page."""
    return render_template('my_orders.html')


@web_bp.route('/login')
def login():
    """Login page."""
    return render_template('login.html')


@web_bp.route('/register')
def register():
    """Registration page."""
    return render_template('register.html')


@web_bp.route('/admin/users')
def admin_users():
    """Admin user management page."""
    return render_template('admin_users.html')


@web_bp.route('/admin/menu')
def admin_menu():
    """Admin menu management page."""
    return render_template('admin_menu.html')
