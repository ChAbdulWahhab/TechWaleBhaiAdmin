import enum
import random
import string
from datetime import datetime
from app import db

def generate_order_code():
    """Generate a random order code in the format '#NDZQX' (1 '#' + 5 alphanumeric uppercase characters)."""
    return "#" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

class Wholesaler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    wholesaler_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    return_policy = db.Column(db.Boolean, default=False)
    products = db.relationship('Product', backref='wholesaler', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(100), nullable=True)
    wholesaler_id = db.Column(db.Integer, db.ForeignKey('wholesaler.id'), nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone_number = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    # 'orders' relationship is available via the backref in Order model.

class PaymentMethod(enum.Enum):
    cash_on_delivery = "Cash on Delivery"
    digital_wallet = "Digital Wallet"
    bank_transfer = "Bank Transfer"
    credit_debit_card = "Credit/Debit Card"
    other = "Other"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(10), unique=True, nullable=False, default=generate_order_code)
    order_total_price = db.Column(db.Float, nullable=False)
    order_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    payment_method = db.Column(db.String(50), default="Cash on Delivery", nullable=False)
    payment_status = db.Column(db.String(50), default="Awaiting Payment")
    fulfillment_status = db.Column(db.String(50), default="Awaiting Processing")
    # Updated relationship: when a Customer is deleted, its orders are also deleted.
    customer = db.relationship('Customer', backref=db.backref('orders', cascade="all, delete-orphan"), lazy=True)
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class InvestmentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_investment = db.Column(db.Float, nullable=False)
    profit_per_product = db.Column(db.Float, nullable=False)
    number_of_products = db.Column(db.Integer, nullable=False)
    total_profit = db.Column(db.Float, nullable=False)
    profit_margin = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
