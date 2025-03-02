from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__, template_folder='../templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wholesalers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import models, routes

with app.app_context():
    db.create_all()
    from app.models import Admin
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', name='Admin', email='admin@example.com', password='admin123')
        db.session.add(admin)
        db.session.commit()
