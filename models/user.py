from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='farmer')  # admin, farmer (renter), owner (lender)
    profile_image = db.Column(db.String(100), nullable=True, default='default.jpg')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    # If the user is an owner, they may list multiple equipments
    equipments = db.relationship('Equipment', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)
        
    def __repr__(self):
        return f"<User {self.name} - {self.role}>"
