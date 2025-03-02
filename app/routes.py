import os
import io
import pandas as pd
from functools import wraps
from datetime import datetime
from flask import render_template, request, redirect, session, url_for, send_file, flash
from werkzeug.utils import secure_filename
from app import app, db
from app.models import Wholesaler, Product, Customer, PaymentMethod, Order, OrderItem, Admin, InvestmentRecord

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            flash("Successfully logged in as admin.", "success")
            return redirect(url_for('customers'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('admin_login'))

@app.route('/customers')
@login_required
def customers():
    q = request.args.get('q', '')
    if q:
        customers_list = Customer.query.filter(
            (Customer.first_name.ilike(f'%{q}%')) |
            (Customer.last_name.ilike(f'%{q}%')) |
            (Customer.email.ilike(f'%{q}%'))
        ).all()
    else:
        customers_list = Customer.query.all()
    return render_template('customers.html', customers=customers_list, query=q)

@app.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        new_customer = Customer(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            phone_number=request.form.get('phone_number'),
            country=request.form['country'],
            address=request.form['address'],
            city=request.form['city'],
            postal_code=request.form['postal_code']
        )
        db.session.add(new_customer)
        db.session.commit()
        flash("Customer added successfully!", "success")
        return redirect(url_for('customers'))
    return render_template('add_customer.html')

@app.route('/add_order', methods=['GET', 'POST'])
@login_required
def add_order():
    customers = Customer.query.all()
    if request.method == 'POST':
        if request.form.get('customer_option') == 'existing':
            customer_id = request.form.get('existing_customer_id')
            customer = Customer.query.get(customer_id)
            if not customer:
                flash("Selected customer does not exist.", "danger")
                return redirect(url_for('add_order'))
        else:
            email = request.form.get('customer_email')
            country = request.form.get('country')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone_number = request.form.get('phone_number')
            address = request.form.get('address')
            city = request.form.get('city')
            postal_code = request.form.get('postal_code', '')
            customer = Customer(
                email=email,
                country=country,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                address=address,
                city=city,
                postal_code=postal_code
            )
            db.session.add(customer)
            db.session.commit()
        try:
            order_total_price = float(request.form.get('order_total_price'))
        except (ValueError, TypeError):
            flash("Please enter a valid order total price.", "danger")
            return redirect(url_for('add_order'))
        if request.form.get('cash_on_delivery') == 'on':
            payment_method = PaymentMethod.cash_on_delivery.value
        else:
            payment_method = PaymentMethod.digital_wallet.value

        payment_status = request.form.get('payment_status')
        fulfillment_status = request.form.get('fulfillment_status')
        new_order = Order(
            order_total_price=order_total_price,
            customer_id=customer.id,
            payment_method=payment_method,
            payment_status=payment_status,
            fulfillment_status=fulfillment_status
        )
        db.session.add(new_order)
        db.session.commit()
        product_names = request.form.getlist('product_name')
        colors = request.form.getlist('color')
        quantities = request.form.getlist('quantity')
        prices = request.form.getlist('price')
        for i in range(len(product_names)):
            try:
                qty = int(quantities[i])
                price = float(prices[i])
            except (ValueError, TypeError):
                continue
            total = qty * price
            order_item = OrderItem(
                order_id=new_order.id,
                product_name=product_names[i],
                color=colors[i],
                quantity=qty,
                price=price,
                total=total
            )
            db.session.add(order_item)
        db.session.commit()
        flash("Order added successfully!", "success")
        return redirect(url_for('orders'))
    return render_template('add_order.html', customers=customers)

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        try:
            order.order_total_price = float(request.form.get('order_total_price'))
        except (ValueError, TypeError):
            flash("Invalid order total price.", "danger")
            return redirect(url_for('edit_order', order_id=order.id))
        order.payment_method = request.form.get('payment_method')
        order.payment_status = request.form.get('payment_status')
        order.fulfillment_status = request.form.get('fulfillment_status')
        for item in order.order_items:
            db.session.delete(item)
        product_names = request.form.getlist('product_name')
        colors = request.form.getlist('color')
        quantities = request.form.getlist('quantity')
        prices = request.form.getlist('price')
        for i in range(len(product_names)):
            try:
                qty = int(quantities[i])
                price = float(prices[i])
            except (ValueError, TypeError):
                continue
            total = qty * price
            order_item = OrderItem(
                order_id=order.id,
                product_name=product_names[i],
                color=colors[i],
                quantity=qty,
                price=price,
                total=total
            )
            db.session.add(order_item)
        db.session.commit()
        flash("Order updated successfully!", "success")
        return redirect(url_for('view_order', order_id=order.id))
    return render_template('edit_order.html', order=order)

@app.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash("Order deleted successfully!", "success")
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    orders_list = Order.query.order_by(Order.order_datetime.desc()).all()
    return render_template('orders.html', orders=orders_list)

@app.route('/order/<int:order_id>')
@login_required
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('view_order.html', order=order)

@app.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.payment_status = request.form.get('payment_status')
    order.fulfillment_status = request.form.get('fulfillment_status')
    db.session.commit()
    flash("Order statuses updated successfully!", "success")
    return redirect(url_for('orders'))

@app.route('/export_customers')
@login_required
def export_customers():
    customers_list = Customer.query.all()
    data = []
    for c in customers_list:
        data.append({
            'First Name': c.first_name,
            'Last Name': c.last_name,
            'Email': c.email,
            'Phone Number': c.phone_number,
            'Country': c.country,
            'Address': c.address,
            'City': c.city,
            'Postal Code': c.postal_code
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Customers')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="customers.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/customer/<int:customer_id>')
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('view_customer.html', customer=customer)

@app.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.first_name = request.form['first_name']
        customer.last_name = request.form['last_name']
        customer.email = request.form['email']
        customer.phone_number = request.form.get('phone_number')
        customer.country = request.form['country']
        customer.address = request.form['address']
        customer.city = request.form['city']
        customer.postal_code = request.form['postal_code']
        db.session.commit()
        flash("Customer updated successfully!", "success")
        return redirect(url_for('customers'))
    return render_template('edit_customer.html', customer=customer)

@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully!", "success")
    return redirect(url_for('customers'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    admin_id = session.get('admin_id')
    admin = Admin.query.get(admin_id)
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        admin_name = request.form.get('admin_name')
        admin_email = request.form.get('admin_email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if current_password != admin.password:
            flash("Current password is incorrect.", "danger")
        else:
            admin.name = admin_name
            admin.email = admin_email
            if new_password:
                if new_password == confirm_password:
                    admin.password = new_password
                    db.session.commit()
                    flash("Profile and password updated successfully! Please log in again.", "success")
                    session.pop('admin_logged_in', None)
                    session.pop('admin_id', None)
                    return redirect(url_for('admin_login'))
                else:
                    flash("New password and confirm password do not match.", "danger")
            else:
                db.session.commit()
                flash("Profile updated successfully!", "success")
    return render_template('settings.html', username=admin.username, admin_name=admin.name, admin_email=admin.email)

@app.route('/')
def index():
    wholesalers = Wholesaler.query.all()
    wholesalers_count = Wholesaler.query.count()
    customers_count = Customer.query.count()
    products_count = Product.query.count()
    return_policy_count = Wholesaler.query.filter_by(return_policy=True).count()
    return_policy_percentage = 0
    if wholesalers_count:
        return_policy_percentage = round((return_policy_count / wholesalers_count) * 100, 2)
    latest_wholesaler = Wholesaler.query.order_by(Wholesaler.id.desc()).first()
    latest_product = Product.query.order_by(Product.id.desc()).first()
    recent_customers = Customer.query.order_by(Customer.id.desc()).limit(5).all()
    return render_template('index.html', wholesalers=wholesalers, wholesalers_count=wholesalers_count, customers_count=customers_count, products_count=products_count, return_policy_percentage=return_policy_percentage, latest_wholesaler=latest_wholesaler, latest_product=latest_product, recent_customers=recent_customers)

@app.route('/add_wholesaler', methods=['GET', 'POST'])
def add_wholesaler():
    if request.method == 'POST':
        new_wholesaler = Wholesaler(
            shop_name=request.form['shop_name'],
            wholesaler_name=request.form['wholesaler_name'],
            phone_number=request.form.get('phone_number'),
            return_policy=True if request.form.get('return_policy') == 'on' else False
        )
        db.session.add(new_wholesaler)
        db.session.commit()
        flash("Wholesaler added successfully!", "success")
        return redirect(url_for('index'))
    return render_template('add_wholesaler.html')

@app.route('/edit_wholesaler/<int:wholesaler_id>', methods=['GET', 'POST'])
def edit_wholesaler(wholesaler_id):
    wholesaler = Wholesaler.query.get_or_404(wholesaler_id)
    if request.method == 'POST':
        wholesaler.shop_name = request.form['shop_name']
        wholesaler.wholesaler_name = request.form['wholesaler_name']
        wholesaler.phone_number = request.form.get('phone_number')
        wholesaler.return_policy = True if request.form.get('return_policy') == 'on' else False
        db.session.commit()
        flash("Wholesaler updated successfully!", "success")
        return redirect(url_for('index'))
    return render_template('edit_wholesaler.html', wholesaler=wholesaler)

@app.route('/delete_wholesaler/<int:wholesaler_id>', methods=['POST'])
def delete_wholesaler(wholesaler_id):
    wholesaler = Wholesaler.query.get_or_404(wholesaler_id)
    db.session.delete(wholesaler)
    db.session.commit()
    flash("Wholesaler deleted successfully!", "success")
    return redirect(url_for('index'))

@app.route('/add_product/<int:wholesaler_id>', methods=['GET', 'POST'])
def add_product(wholesaler_id):
    wholesaler = Wholesaler.query.get_or_404(wholesaler_id)
    if request.method == 'POST':
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
        new_product = Product(
            product_name=request.form['product_name'],
            price=float(request.form['price']),
            description=request.form.get('description'),
            image_filename=filename,
            wholesaler=wholesaler
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!", "success")
        return redirect(url_for('index'))
    return render_template('add_product.html', wholesaler=wholesaler)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.product_name = request.form['product_name']
        product.price = float(request.form['price'])
        product.description = request.form.get('description')
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            product.image_filename = filename
        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for('index'))
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!", "success")
    return redirect(url_for('index'))

@app.route('/compare')
def compare():
    sort_order = request.args.get('sort', 'low-high')
    product_names = db.session.query(Product.product_name).distinct().all()
    comparisons = []
    for (name,) in product_names:
        best_product = Product.query.filter_by(product_name=name).order_by(Product.price).first()
        comparisons.append({
            'product_name': name,
            'price': best_product.price,
            'wholesaler': best_product.wholesaler.wholesaler_name,
            'shop_name': best_product.wholesaler.shop_name,
            'phone_number': best_product.wholesaler.phone_number,
            'return_policy': best_product.wholesaler.return_policy
        })
    if sort_order == 'low-high':
        comparisons = sorted(comparisons, key=lambda x: x['price'])
    elif sort_order == 'high-low':
        comparisons = sorted(comparisons, key=lambda x: x['price'], reverse=True)
    return render_template('compare.html', comparisons=comparisons, sort_order=sort_order)

@app.route('/product_calculator', methods=['GET'])
def product_calculator():
    return render_template('product_price_calculator.html')

@app.route('/export')
def export():
    wholesalers = Wholesaler.query.all()
    data = []
    for wholesaler in wholesalers:
        for product in wholesaler.products:
            data.append({
                'Shop Name': wholesaler.shop_name,
                'Wholesaler Name': wholesaler.wholesaler_name,
                'Phone Number': wholesaler.phone_number,
                'Return Policy': wholesaler.return_policy,
                'Product Name': product.product_name,
                'Price': product.price,
                'Description': product.description,
                'Image Filename': product.image_filename
            })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="wholesaler_data.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/investment', methods=['GET', 'POST'])
@login_required
def investment():
    if request.method == 'POST':
        try:
            total_investment = float(request.form['total_investment'])
            profit_per_product = float(request.form['profit_per_product'])
            number_of_products = int(request.form['number_of_products'])
        except ValueError:
            flash("Please enter valid numeric values.", "danger")
            return redirect(url_for('investment'))
        total_profit = profit_per_product * number_of_products
        profit_margin = (total_profit / total_investment) * 100 if total_investment != 0 else 0
        record = InvestmentRecord(
            total_investment=total_investment,
            profit_per_product=profit_per_product,
            number_of_products=number_of_products,
            total_profit=total_profit,
            profit_margin=profit_margin
        )
        db.session.add(record)
        db.session.commit()
        flash("Investment record saved successfully!", "success")
        return redirect(url_for('investment'))
    records = InvestmentRecord.query.order_by(InvestmentRecord.timestamp.desc()).all()
    return render_template('investment.html', records=records)

@app.route('/delete_investment/<int:investment_id>', methods=['POST'])
@login_required
def delete_investment(investment_id):
    record = InvestmentRecord.query.get_or_404(investment_id)
    db.session.delete(record)
    db.session.commit()
    flash("Investment record deleted successfully!", "success")
    return redirect(url_for('investment'))
