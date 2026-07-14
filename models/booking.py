from datetime import datetime, timezone
from models import db

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Approved, Rejected, Paid, Completed, Cancelled
    booking_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    payments = db.relationship('Payment', backref='booking', lazy=True)
    
    def __repr__(self):
        return f"<Booking {self.id}: User {self.user_id} - Equip {self.equipment_id}>"
