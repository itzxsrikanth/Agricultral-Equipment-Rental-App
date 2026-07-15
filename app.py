import os
import gc
from datetime import datetime, date, timezone
from io import BytesIO
import streamlit as st

# Setup background Flask application to share database configuration
from flask import Flask
from config import Config
from models import db
from models.user import User
from models.equipment import Equipment
from models.booking import Booking
from models.payment import Payment

# Reportlab imports for invoice generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# Initialize DB connection via Flask application context
@st.cache_resource
def get_flask_db_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    with app.app_context():
        db.create_all()
        # Seed initial data if empty
        if User.query.first() is None:
            # Create Users
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
            
            db.session.commit()

            # Create Equipments
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
    return app

# Instantiate Flask app context wrapper
flask_app = get_flask_db_app()

# Helper function to generate PDF Invoice using reportlab
def generate_invoice_pdf(booking):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # Title Banner
    elements.append(Paragraph("<b>AgriRent</b> — Agricultural Equipment Rental", styles['Title']))
    elements.append(Paragraph("www.agrirent.com | support@agrirent.com", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Invoice #{booking.id:04d}</b>", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Meta Table
    meta = [
        ['Booking Date:', booking.booking_date.strftime('%d %B %Y')],
        ['Status:',       booking.status],
        ['Renter Name:',  booking.user.name],
        ['Renter Email:', booking.user.email],
    ]
    meta_table = Table(meta, colWidths=[150, 300])
    meta_table.setStyle(TableStyle([
        ('FONTNAME',  (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',  (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',  (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))

    # Rental Details Table
    elements.append(Paragraph("<b>Rental Details</b>", styles['Heading3']))
    elements.append(Spacer(1, 8))
    rental_data = [
        ['Equipment', 'Category', 'Location', 'Start Date', 'End Date', 'Days', 'Rate/Day', 'Total'],
        [
            booking.equipment.name,
            booking.equipment.category,
            booking.equipment.location,
            booking.start_date.strftime('%d %b %Y'),
            booking.end_date.strftime('%d %b %Y'),
            str(max((booking.end_date - booking.start_date).days, 1)),
            f'INR {booking.equipment.price_per_day:.2f}',
            f'INR {booking.total_price:.2f}',
        ],
    ]
    rental_table = Table(rental_data, colWidths=[110, 70, 60, 65, 65, 35, 55, 60])
    rental_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 9),
        ('BACKGROUND',   (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E8F5E9')]),
        ('ALIGN',        (5, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 8),
    ]))
    elements.append(rental_table)
    elements.append(Spacer(1, 20))

    # Grand Total
    total_data = [['', '', '', '', '', '', 'Grand Total:', f'INR {booking.total_price:.2f}']]
    total_table = Table(total_data, colWidths=[110, 70, 60, 65, 65, 35, 55, 60])
    total_table.setStyle(TableStyle([
        ('FONTNAME',   (6, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 11),
        ('TEXTCOLOR',  (7, 0), (7, 0), colors.HexColor('#2E7D32')),
        ('ALIGN',      (6, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Thank you for using AgriRent. Happy farming!", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# Main Application Setup
def main():
    st.set_page_config(page_title="AgriRent 🌾", page_icon="🌾", layout="wide")

    # Injects premium CSS matching original layout colors
    st.markdown("""
        <style>
            .stApp {
                background-color: #F8F9FA;
            }
            h1, h2, h3 {
                color: #2E7D32 !important;
                font-family: 'Outfit', sans-serif !important;
            }
            .sidebar .sidebar-content {
                background-color: #E8F5E9 !important;
            }
            .card {
                background-color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border-left: 5px solid #2E7D32;
                margin-bottom: 1rem;
            }
            .accent-card {
                background-color: #E8F5E9;
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #C8E6C9;
                margin-bottom: 1rem;
            }
            .stButton>button {
                background-color: #2E7D32 !important;
                color: white !important;
                font-weight: bold !important;
                border-radius: 8px !important;
                border: none !important;
                transition: all 0.3s ease !important;
            }
            .stButton>button:hover {
                background-color: #FF9800 !important;
                box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3) !important;
                transform: scale(1.02);
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize Session States
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'email' not in st.session_state:
        st.session_state.email = None
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
    if 'selected_eq_id' not in st.session_state:
        st.session_state.selected_eq_id = None

    # Handle Sidebar
    st.sidebar.markdown("<h2 style='text-align: center;'>🚜 AgriRent</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if st.session_state.user_id:
        st.sidebar.markdown(f"**Logged in as:**\n{st.session_state.name} ({st.session_state.role.capitalize()})")
        st.sidebar.markdown(f"📧 `{st.session_state.email}`")
        
        # Navigation Options
        pages = ["Home", "Browse Machinery"]
        if st.session_state.role in ['farmer', 'admin']:
            pages.append("My Bookings")
        if st.session_state.role in ['owner', 'admin']:
            pages.append("Owner Dashboard")
        if st.session_state.role == 'admin':
            pages.append("Admin Panel")
        pages.append("My Profile")
        
        selected_page = st.sidebar.radio("Navigation", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
        if selected_page != st.session_state.page:
            st.session_state.page = selected_page
            st.session_state.selected_eq_id = None
            st.rerun()

        st.sidebar.markdown("---")
        if st.sidebar.button("Logout", key="logout_btn"):
            st.session_state.user_id = None
            st.session_state.role = None
            st.session_state.name = None
            st.session_state.email = None
            st.session_state.page = "Home"
            st.session_state.selected_eq_id = None
            st.success("Logged out successfully!")
            st.rerun()
    else:
        st.sidebar.info("Please Log In or Register using the main tab interface to book or list equipment.")

    # Render Pages
    if not st.session_state.user_id:
        render_auth_page()
    else:
        if st.session_state.selected_eq_id:
            render_detail_page()
        elif st.session_state.page == "Home":
            render_home_page()
        elif st.session_state.page == "Browse Machinery":
            render_catalog_page()
        elif st.session_state.page == "My Bookings":
            render_history_page()
        elif st.session_state.page == "Owner Dashboard":
            render_owner_dashboard()
        elif st.session_state.page == "Admin Panel":
            render_admin_panel()
        elif st.session_state.page == "My Profile":
            render_profile_page()


# Auth Page (Login / Registration)
def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>🌾 Welcome to AgriRent 🌾</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>A Premium, Modern Agricultural Equipment Rental Platform</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔒 Sign In", "📝 Create Account"])
        
        with tab_login:
            st.subheader("Login to your Account")
            email = st.text_input("Email Address", key="login_email").strip()
            password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Sign In"):
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    user = User.query.filter_by(email=email).first()
                    if user and user.check_password(password):
                        st.session_state.user_id = user.id
                        st.session_state.role = user.role
                        st.session_state.name = user.name
                        st.session_state.email = user.email
                        st.session_state.page = "Home"
                        st.success(f"Welcome back, {user.name}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please try again.")
                        
        with tab_register:
            st.subheader("Create a New Account")
            reg_name = st.text_input("Full Name", key="reg_name").strip()
            reg_email = st.text_input("Email Address", key="reg_email").strip()
            reg_phone = st.text_input("Phone Number", key="reg_phone").strip()
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_role = st.selectbox("I want to register as a:", ["Farmer (Renter)", "Machinery Owner (Lender)"], key="reg_role")
            
            if st.button("Register Account"):
                if not reg_name or not reg_email or not reg_password:
                    st.error("Name, email, and password are required.")
                elif User.query.filter_by(email=reg_email).first() is not None:
                    st.error("This email is already registered. Please go to Sign In.")
                else:
                    role_key = "farmer" if "Farmer" in reg_role else "owner"
                    new_user = User(
                        name=reg_name,
                        email=reg_email,
                        phone=reg_phone,
                        role=role_key
                    )
                    new_user.set_password(reg_password)
                    db.session.add(new_user)
                    db.session.commit()
                    st.success("Account created successfully! Please proceed to the Sign In tab.")


# Home Page
def render_home_page():
    st.markdown("<h1>🌾 AgriRent Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.15rem; color: #555;'>The direct connection between equipment owners and farmers.</p>", unsafe_allow_html=True)
    
    # Showcase stats
    total_users = User.query.count()
    total_equip = Equipment.query.filter_by(availability=True).count()
    total_bookings = Booking.query.count()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
            <div class="card">
                <h3>👥 Total Members</h3>
                <h2 style="color: #2E7D32;">{total_users} Active</h2>
                <small>Farmers and equipment owners registered</small>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="card">
                <h3>🚜 Machinery Listed</h3>
                <h2 style="color: #2E7D32;">{total_equip} Available</h2>
                <small>High quality farm machineries ready to rent</small>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="card">
                <h3>📅 Bookings Placed</h3>
                <h2 style="color: #2E7D32;">{total_bookings} Total</h2>
                <small>Completed and pending rentals</small>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Showcase categories and description
    st.subheader("Our Premium Offerings")
    cats = ["Tractors", "Harvesters", "Irrigation", "Tools"]
    cat_cols = st.columns(4)
    
    for i, cat in enumerate(cats):
        with cat_cols[i]:
            img_file = f"static/images/{cat.lower()}_cat.jpg"
            if os.path.exists(img_file):
                st.image(img_file, use_column_width=True)
            st.markdown(f"<h4 style='text-align: center; color: #2E7D32;'>{cat}</h4>", unsafe_allow_html=True)
            
    st.markdown("---")
    
    st.subheader("How It Works")
    step_col1, step_col2, step_col3 = st.columns(3)
    with step_col1:
        st.markdown("""
            <div class="accent-card">
                <h5>1. Search & Filter</h5>
                <p>Browse through high-quality machinery listed in different states of India. Filter by category or location.</p>
            </div>
        """, unsafe_allow_html=True)
    with step_col2:
        st.markdown("""
            <div class="accent-card">
                <h5>2. Request Booking</h5>
                <p>Select your desired dates, calculate the pricing instantly, and submit a rental request to the owner.</p>
            </div>
        """, unsafe_allow_html=True)
    with step_col3:
        st.markdown("""
            <div class="accent-card">
                <h5>3. Rent & Earn</h5>
                <p>Once approved, secure your equipment, complete work, download invoices, and generate extra revenue.</p>
            </div>
        """, unsafe_allow_html=True)


# Catalog Page
def render_catalog_page():
    st.markdown("<h1>🚜 Browse Equipment Catalog</h1>", unsafe_allow_html=True)
    
    # Filter Controls
    col_search, col_cat, col_loc = st.columns([2, 1, 1])
    with col_search:
        search_q = st.text_input("🔍 Search Machinery by name or description...", value="").strip()
    with col_cat:
        category_options = ["All Categories", "Tractors", "Harvesters", "Irrigation", "Tools"]
        selected_cat = st.selectbox("📁 Category", category_options)
    with col_loc:
        location_options = ["All Regions", "Punjab", "Haryana", "Maharashtra", "Karnataka"]
        selected_loc = st.selectbox("📍 Region / State", location_options)

    # Build DB Query
    query = Equipment.query.filter_by(availability=True)
    if search_q:
        query = query.filter((Equipment.name.like(f"%{search_q}%")) | (Equipment.description.like(f"%{search_q}%")))
    if selected_cat != "All Categories":
        query = query.filter(Equipment.category == selected_cat)
    if selected_loc != "All Regions":
        query = query.filter(Equipment.location == selected_loc)
        
    equipments = query.all()
    
    if not equipments:
        st.warning("No equipment matches your search or filter selection.")
        return
        
    # Render Equipment Grid
    st.markdown(f"**Showing {len(equipments)} available equipments**")
    cols = st.columns(3)
    for idx, eq in enumerate(equipments):
        with cols[idx % 3]:
            # Load image
            img_path = f"static/images/{eq.image}"
            if not os.path.exists(img_path) or not eq.image:
                img_path = "static/images/default.jpg"
                
            st.image(img_path, use_column_width=True)
            
            st.markdown(f"### {eq.name}")
            st.markdown(f"📍 **{eq.location}** | 📁 **{eq.category}**")
            st.markdown(f"💵 **₹{eq.price_per_day:.2f} / day**")
            
            # Truncated description
            desc = eq.description if eq.description else ""
            if len(desc) > 100:
                desc = desc[:100] + "..."
            st.write(desc)
            
            if st.button("Details & Booking", key=f"details_btn_{eq.id}"):
                st.session_state.selected_eq_id = eq.id
                st.rerun()


# Detail View Page
def render_detail_page():
    eq_id = st.session_state.selected_eq_id
    eq = db.session.get(Equipment, eq_id)
    
    if not eq:
        st.error("Equipment not found.")
        if st.button("Back to Catalog"):
            st.session_state.selected_eq_id = None
            st.rerun()
        return

    st.markdown(f"<h1>🌾 {eq.name}</h1>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Catalog"):
        st.session_state.selected_eq_id = None
        st.rerun()

    c_left, c_right = st.columns([3, 2])
    with c_left:
        # Load image
        img_path = f"static/images/{eq.image}"
        if not os.path.exists(img_path) or not eq.image:
            img_path = "static/images/default.jpg"
        st.image(img_path, use_column_width=True)
        
        st.subheader("Description")
        st.write(eq.description if eq.description else "No description provided.")
        
        st.subheader("Specifications")
        st.markdown(f"""
        * **Category:** {eq.category}
        * **Listed Location:** {eq.location}
        * **Availability:** {"Available" if eq.availability else "Unavailable"}
        * **Listed By:** {eq.owner.name} (+91 {eq.owner.phone if eq.owner.phone else "N/A"})
        """)

    with c_right:
        st.markdown(f"""
            <div class="card">
                <h4>Booking Configuration</h4>
                <p style="font-size: 1.25rem; font-weight: bold; color: #2E7D32;">Price: ₹{eq.price_per_day:.2f} / Day</p>
            </div>
        """, unsafe_allow_html=True)

        start_date = st.date_input("Start Date", value=date.today())
        end_date = st.date_input("End Date", value=date.today() + date.resolution)
        
        # Calculate days and price
        delta = (end_date - start_date).days
        rental_days = max(delta, 1)
        total_price = rental_days * eq.price_per_day
        
        st.write(f"**Rental Duration:** {rental_days} day(s)")
        st.markdown(f"### Total Price: **₹{total_price:.2f}**")
        
        if st.button("Request Booking Now"):
            # Validations
            if eq.owner_id == st.session_state.user_id:
                st.error("You cannot rent your own machinery listings!")
            elif start_date < date.today():
                st.error("The start date cannot be set in the past.")
            elif end_date < start_date:
                st.error("The end date must be on or after the start date.")
            else:
                new_booking = Booking(
                    user_id=st.session_state.user_id,
                    equipment_id=eq.id,
                    start_date=start_date,
                    end_date=end_date,
                    total_price=total_price,
                    status='Pending'
                )
                db.session.add(new_booking)
                db.session.commit()
                st.success("Booking request submitted successfully! The owner will review it.")
                st.session_state.selected_eq_id = None
                st.session_state.page = "My Bookings"
                st.rerun()


# Booking History Page
def render_history_page():
    st.markdown("<h1>📅 My Rental History</h1>", unsafe_allow_html=True)
    
    # Query user bookings
    bookings = Booking.query.filter_by(user_id=st.session_state.user_id).order_by(Booking.booking_date.desc()).all()
    
    if not bookings:
        st.info("You have not requested any bookings yet. Browse the machinery catalog to place one!")
        return

    # Render bookings in cards
    for b in bookings:
        status_color = "#FFA500" if b.status == "Pending" else "#2E7D32" if b.status in ["Approved", "Paid"] else "#D32F2F"
        
        with st.container():
            st.markdown(f"""
                <div style="background-color: white; padding: 1.25rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 1rem; border-left: 5px solid {status_color};">
                    <span style="float: right; font-weight: bold; color: {status_color}; padding: 0.25rem 0.5rem; border-radius: 4px; border: 1px solid {status_color};">{b.status}</span>
                    <h4 style="margin: 0; color: #2E7D32;">{b.equipment.name}</h4>
                    <p style="margin: 5px 0 0 0; color: #555;">📍 {b.equipment.location} | 💵 <b>₹{b.total_price:.2f} total</b></p>
                    <p style="margin: 2px 0 0 0; font-size: 0.9rem; color: #666;">Duration: <b>{b.start_date.strftime('%d %b %Y')}</b> to <b>{b.end_date.strftime('%d %b %Y')}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col_act1, col_act2, _ = st.columns([1, 1, 4])
            with col_act1:
                if b.status == 'Pending':
                    if st.button("Cancel Request", key=f"cancel_b_{b.id}"):
                        b.status = 'Cancelled'
                        db.session.commit()
                        st.success("Booking request cancelled successfully.")
                        st.rerun()
            with col_act2:
                if b.status in ['Approved', 'Paid', 'Completed']:
                    pdf_bytes = generate_invoice_pdf(b)
                    st.download_button(
                        label="Download PDF Invoice",
                        data=pdf_bytes,
                        file_name=f"agrirent_invoice_{b.id:04d}.pdf",
                        mime="application/pdf",
                        key=f"dl_invoice_{b.id}"
                    )


# Owner Dashboard Page
def render_owner_dashboard():
    st.markdown("<h1>🌾 Owner Dashboard</h1>", unsafe_allow_html=True)
    
    # 1. Fetch owner data
    my_equipment = Equipment.query.filter_by(owner_id=st.session_state.user_id).order_by(Equipment.created_at.desc()).all()
    my_eq_ids = [eq.id for eq in my_equipment]
    
    incoming_bookings = Booking.query.filter(Booking.equipment_id.in_(my_eq_ids)).order_by(Booking.booking_date.desc()).all() if my_eq_ids else []
    earnings = sum([b.total_price for b in incoming_bookings if b.status in ['Approved', 'Paid', 'Completed']])

    # Owner Stats Header
    col_st1, col_st2, col_st3 = st.columns(3)
    with col_st1:
        st.metric("Listed Equipments", len(my_equipment))
    with col_st2:
        st.metric("Total Booking Requests", len(incoming_bookings))
    with col_st3:
        st.metric("Total Earnings", f"₹{earnings:.2f}")
        
    st.markdown("---")

    tab_listings, tab_add, tab_incoming = st.tabs(["🚜 My Machinery Listings", "➕ Add New Equipment", "📩 Incoming Booking Requests"])

    with tab_listings:
        if not my_equipment:
            st.info("You haven't listed any equipment yet.")
        else:
            for eq in my_equipment:
                with st.container():
                    st.markdown(f"""
                        <div class="card">
                            <h4>{eq.name}</h4>
                            <p><b>Category:</b> {eq.category} | <b>Location:</b> {eq.location} | <b>Price:</b> ₹{eq.price_per_day:.2f}/day</p>
                            <p><b>Status:</b> {"Active / Available" if eq.availability else "Disabled"}</p>
                        </div>
                    """, unsafe_allow_html=True)

    with tab_add:
        st.subheader("List New Equipment")
        eq_name = st.text_input("Equipment Name", key="add_eq_name").strip()
        eq_desc = st.text_area("Detailed Description", key="add_eq_desc").strip()
        eq_cat = st.selectbox("Category", ["Tractors", "Harvesters", "Seeding", "Irrigation", "Tools"], key="add_eq_cat")
        eq_loc = st.selectbox("Location / State", ["Punjab", "Haryana", "Maharashtra", "Karnataka", "Tamil Nadu", "Andhra Pradesh"], key="add_eq_loc")
        eq_price = st.number_input("Rental Price per Day (INR)", min_value=1.0, value=50.0, step=5.0, key="add_eq_price")
        
        # Image Uploader
        eq_image = st.file_uploader("Upload Product Image (optional)", type=["png", "jpg", "jpeg", "webp"])
        
        if st.button("List Machinery Now"):
            if not eq_name or not eq_desc:
                st.error("Name and description fields are required.")
            else:
                image_filename = "default.jpg"
                if eq_image:
                    image_filename = eq_image.name
                    # Secure local copy of file
                    os.makedirs(os.path.join("static", "images"), exist_ok=True)
                    upload_path = os.path.join("static", "images", image_filename)
                    with open(upload_path, "wb") as f:
                        f.write(eq_image.getvalue())
                        
                new_eq = Equipment(
                    name=eq_name,
                    description=eq_desc,
                    category=eq_cat,
                    location=eq_loc,
                    price_per_day=eq_price,
                    image=image_filename,
                    owner_id=st.session_state.user_id,
                    availability=True
                )
                db.session.add(new_eq)
                db.session.commit()
                st.success(f'Successfully listed "{eq_name}"!')
                st.rerun()

    with tab_incoming:
        pending_incoming = [b for b in incoming_bookings if b.status == 'Pending']
        
        if not pending_incoming:
            st.info("No pending rental requests for your machinery.")
        else:
            for b in pending_incoming:
                with st.container():
                    st.markdown(f"""
                        <div style="background-color: white; padding: 1.25rem; border-radius: 10px; margin-bottom: 1rem; border-left: 5px solid #FF9800;">
                            <h4>Request for {b.equipment.name}</h4>
                            <p>👤 <b>Renter:</b> {b.user.name} | 📞 <b>Phone:</b> {b.user.phone if b.user.phone else 'N/A'}</p>
                            <p>📅 <b>Duration:</b> {b.start_date.strftime('%d %b %Y')} to {b.end_date.strftime('%d %b %Y')} ({max((b.end_date - b.start_date).days, 1)} days)</p>
                            <p>💰 <b>Total Payout:</b> ₹{b.total_price:.2f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Approve / Reject actions
                    act_col1, act_col2, _ = st.columns([1, 1, 4])
                    with act_col1:
                        if st.button("Approve Request", key=f"app_req_{b.id}"):
                            b.status = 'Approved'
                            db.session.commit()
                            st.success("Approved successfully!")
                            st.rerun()
                    with act_col2:
                        if st.button("Reject Request", key=f"rej_req_{b.id}"):
                            b.status = 'Rejected'
                            db.session.commit()
                            st.success("Rejected successfully.")
                            st.rerun()


# Admin Panel Page
def render_admin_panel():
    st.markdown("<h1>🛡️ Administrative Control Panel</h1>", unsafe_allow_html=True)
    
    # Global statistics
    total_users = User.query.count()
    total_equip = Equipment.query.count()
    total_bookings = Booking.query.count()
    revenue_res = db.session.query(db.func.sum(Booking.total_price)).filter(Booking.status.in_(['Approved', 'Paid', 'Completed'])).scalar()
    total_revenue = revenue_res or 0.0

    st.markdown(f"**Status Metrics:** Users: **{total_users}** | Equipments: **{total_equip}** | Bookings: **{total_bookings}** | Revenue: **₹{total_revenue:.2f}**")
    st.markdown("---")

    tab_users, tab_equip, tab_bookings = st.tabs(["👥 Users List", "🚜 Equipment Catalog", "📅 All System Bookings"])

    with tab_users:
        users = User.query.order_by(User.created_at.desc()).all()
        user_table = []
        for u in users:
            user_table.append({
                "ID": u.id,
                "Name": u.name,
                "Email": u.email,
                "Phone": u.phone if u.phone else "N/A",
                "Role": u.role.upper(),
                "Joined": u.created_at.strftime('%d %b %Y')
            })
        st.dataframe(user_table, use_container_width=True)

    with tab_equip:
        equips = Equipment.query.order_by(Equipment.created_at.desc()).all()
        for eq in equips:
            col_eq1, col_eq2 = st.columns([3, 1])
            with col_eq1:
                st.markdown(f"**{eq.name}** ({eq.category}) in *{eq.location}* listed by **{eq.owner.name}** — ₹{eq.price_per_day:.2f}/day")
            with col_eq2:
                # Toggle switch
                state_text = "Enabled" if eq.availability else "Disabled"
                if st.button(f"{state_text} (Toggle)", key=f"adm_toggle_{eq.id}"):
                    eq.availability = not eq.availability
                    db.session.commit()
                    st.success(f"Toggled availability status for {eq.name}!")
                    st.rerun()

    with tab_bookings:
        all_b = Booking.query.order_by(Booking.booking_date.desc()).all()
        if not all_b:
            st.info("No bookings recorded in the system yet.")
        else:
            for b in all_b:
                st.markdown(f"""
                    <div style="background-color: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #2E7D32;">
                        <b>Booking #{b.id}</b> | Renter: {b.user.name} | Payout: ₹{b.total_price:.2f} | Status: <b>{b.status}</b>
                        <br><small>Dates: {b.start_date.strftime('%d %b %Y')} to {b.end_date.strftime('%d %b %Y')}</small>
                    </div>
                """, unsafe_allow_html=True)
                
                # Admin can force-approve pending bookings
                if b.status == 'Pending':
                    col_adm_act1, col_adm_act2, _ = st.columns([1, 1, 4])
                    with col_adm_act1:
                        if st.button("Force Approve", key=f"force_app_{b.id}"):
                            b.status = 'Approved'
                            db.session.commit()
                            st.success("Force Approved!")
                            st.rerun()
                    with col_adm_act2:
                        if st.button("Force Reject", key=f"force_rej_{b.id}"):
                            b.status = 'Rejected'
                            db.session.commit()
                            st.success("Force Rejected!")
                            st.rerun()


# Profile Management Page
def render_profile_page():
    st.markdown("<h1>👥 My Account Profile</h1>", unsafe_allow_html=True)
    
    user = db.session.get(User, st.session_state.user_id)
    
    if not user:
        st.error("Account user session details not found.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Edit Profile details")
        p_name = st.text_input("Full Name", value=user.name)
        p_phone = st.text_input("Phone Number", value=user.phone if user.phone else "")
        
        if st.button("Update Profile Info"):
            if not p_name:
                st.error("Name field is required.")
            else:
                user.name = p_name
                user.phone = p_phone
                db.session.commit()
                st.session_state.name = p_name
                st.success("Profile details updated successfully!")
                st.rerun()

    with col2:
        st.subheader("Change Account Password")
        cur_pass = st.text_input("Current Password", type="password", key="cur_pass")
        new_pass = st.text_input("New Password", type="password", key="new_pass")
        
        if st.button("Update Password"):
            if not cur_pass or not new_pass:
                st.error("Both current password and new password fields are required.")
            elif not user.check_password(cur_pass):
                st.error("The current password entered is incorrect.")
            else:
                user.set_password(new_pass)
                db.session.commit()
                st.success("Password updated successfully!")


# Run execution wrapping in active context
if __name__ == '__main__':
    # Initialize background context so db.session queries binds cleanly
    ctx = flask_app.app_context()
    ctx.push()
    try:
        main()
    finally:
        ctx.pop()
