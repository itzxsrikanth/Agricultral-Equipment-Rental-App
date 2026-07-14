from flask_sqlalchemy import SQLAlchemy

# Initialize db instance
db = SQLAlchemy()

# Import models to register them
from models.user import User
from models.equipment import Equipment
from models.booking import Booking
from models.payment import Payment
