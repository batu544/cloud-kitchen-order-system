"""Web UI routes for serving HTML pages."""
from flask import Blueprint, render_template

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
    """Staff order placement page."""
    return render_template('staff.html')


@web_bp.route('/login')
def login():
    """Login page."""
    return render_template('login.html')


@web_bp.route('/register')
def register():
    """Registration page."""
    return render_template('register.html')
