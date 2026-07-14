import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db
from models.user import User
from models.equipment import Equipment
from routes.auth import auth_bp
from routes.equipment import equipment_bp
from routes.booking import booking_bp
from routes.admin import admin_bp
from routes.profile import profile_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the instance directory exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize SQLAlchemy database
    db.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)

    # Register home page route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        seed_data()

    return app

def seed_data():
    # Only seed if database is empty
    if User.query.first() is not None:
        print("Database already contains data, skipping seed.")
        return

    print("Seeding database with sample agricultural users and equipment...")

    # 1. Create Sample Users
    owner = User(
        name="Harpreet Singh",
        email="owner@agrirent.com",
        phone="+91 9876543210",
        role="owner",
        profile_image="default.jpg"
    )
    owner.set_password("password")
    db.session.add(owner)

    farmer = User(
        name="Rajesh Kumar",
        email="farmer@agrirent.com",
        phone="+91 9876543211",
        role="farmer",
        profile_image="default.jpg"
    )
    farmer.set_password("password")
    db.session.add(farmer)

    admin = User(
        name="AgriRent System Admin",
        email="admin@agrirent.com",
        phone="+91 9876543212",
        role="admin",
        profile_image="default.jpg"
    )
    admin.set_password("password")
    db.session.add(admin)
    
    db.session.commit()  # commit users first to generate IDs
    
    # 2. Create Sample Equipments
    eq1 = Equipment(
        name="John Deere 5050D Tractor",
        category="Tractors",
        price_per_day=50.0,
        description="A heavy-duty 50 HP tractor suitable for deep tillage, plowing, and heavy haulage operations. Extremely reliable with high fuel efficiency.",
        image="tractor_cat.jpg",
        availability=True,
        location="Punjab",
        owner_id=owner.id
    )
    
    eq2 = Equipment(
        name="Mahindra Arjun 555 DI Tractor",
        category="Tractors",
        price_per_day=45.0,
        description="Versatile 50 HP multi-application tractor with advanced hydraulics. Ideal for cultivation, puddling, rotavation, and harvesting support.",
        image="tractor_cat.jpg",
        availability=True,
        location="Haryana",
        owner_id=owner.id
    )
    
    eq3 = Equipment(
        name="Case IH Combine Harvester",
        category="Harvesters",
        price_per_day=120.0,
        description="Premium combine harvester for wheat and rice. High grain tank capacity, comfortable cabin, and advanced sensor monitoring for minimum crop loss.",
        image="harvester_cat.jpg",
        availability=True,
        location="Punjab",
        owner_id=owner.id
    )
    
    eq4 = Equipment(
        name="Netafim Drip Irrigation Setup",
        category="Irrigation",
        price_per_day=25.0,
        description="Smart water saving drip irrigation kits, including pressure regulators, filtration units, and flexible piping systems tailored for large row crops.",
        image="irrigation_cat.jpg",
        availability=True,
        location="Maharashtra",
        owner_id=owner.id
    )
    
    eq5 = Equipment(
        name="Lemken Hydraulic Reversible Plow",
        category="Tools",
        price_per_day=15.0,
        description="Professional soil cultivation tool that offers deep plowing, excellent soil inversion, and weeds clearance. Fits standard high HP tractors.",
        image="tools_cat.jpg",
        availability=True,
        location="Karnataka",
        owner_id=owner.id
    )

    db.session.add_all([eq1, eq2, eq3, eq4, eq5])
    db.session.commit()
    print("Database seeding completed successfully.")

app = create_app()

if __name__ == '__main__':
    # Run the application locally
    app.run(debug=True)
