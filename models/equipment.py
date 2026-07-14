from datetime import datetime, timezone
from models import db

class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Tractors, Harvesters, Seeding, Irrigation, Tools, etc.
    price_per_day = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(100), nullable=True, default='default_equipment.jpg')
    availability = db.Column(db.Boolean, default=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to Owner (who is a user with role 'owner' or 'admin')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='equipment', lazy=True)
    
    def __repr__(self):
        return f"<Equipment {self.name} - ${self.price_per_day}/day>"
