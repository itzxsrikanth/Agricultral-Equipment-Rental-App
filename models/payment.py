from datetime import datetime, timezone
from models import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    
    payment_method = db.Column(db.String(50), nullable=False)  # UPI, Credit Card, Cash, etc.
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Completed, Failed
    payment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    transaction_id = db.Column(db.String(100), unique=True, nullable=True)
    
    def __repr__(self):
        return f"<Payment {self.id}: Booking {self.booking_id} - {self.status}>"
