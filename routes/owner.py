import os
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, current_app
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from models import db
from models.equipment import Equipment
from models.booking import Booking

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'owner':
            abort(403)
        return f(*args, **kwargs)
    return decorated

@owner_bp.route('/')
@login_required
@owner_required
def dashboard():
    # 1. Fetch equipment listed by the owner
    my_equipment = Equipment.query.filter_by(owner_id=current_user.id).order_by(Equipment.created_at.desc()).all()
    
    # 2. Fetch incoming bookings for the owner's equipment
    equipment_ids = [eq.id for eq in my_equipment]
    incoming_bookings = Booking.query.filter(Booking.equipment_id.in_(equipment_ids)).order_by(Booking.booking_date.desc()).all()

    # 3. Calculate earnings (Approved, Paid, or Completed bookings)
    earnings = sum([b.total_price for b in incoming_bookings if b.status in ['Approved', 'Paid', 'Completed']])

    return render_template('owner/dashboard.html', 
                           my_equipment=my_equipment, 
                           incoming_bookings=incoming_bookings, 
                           earnings=earnings)

@owner_bp.route('/booking/approve/<int:booking_id>', methods=['POST'])
@login_required
@owner_required
def approve_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
        
    # Verify the owner actually owns the equipment being booked
    if booking.equipment.owner_id != current_user.id:
        abort(403)

    if booking.status != 'Pending':
        flash('Only pending bookings can be approved.', 'error')
        return redirect(url_for('owner.dashboard'))
        
    booking.status = 'Approved'
    db.session.commit()
    flash(f'Booking #{booking.id} approved successfully.', 'success')
    return redirect(url_for('owner.dashboard'))

@owner_bp.route('/booking/reject/<int:booking_id>', methods=['POST'])
@login_required
@owner_required
def reject_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
        
    # Verify the owner actually owns the equipment being booked
    if booking.equipment.owner_id != current_user.id:
        abort(403)

    if booking.status != 'Pending':
        flash('Only pending bookings can be rejected.', 'error')
        return redirect(url_for('owner.dashboard'))
        
    booking.status = 'Rejected'
    db.session.commit()
    flash(f'Booking #{booking.id} has been rejected.', 'success')
    return redirect(url_for('owner.dashboard'))

@owner_bp.route('/equipment/add', methods=['GET', 'POST'])
@login_required
@owner_required
def add_equipment():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category')
        location = request.form.get('location')
        price = request.form.get('price_per_day')
        
        if not name or not description or not category or not location or not price:
            flash('All fields are required.', 'error')
            return render_template('owner/add_equipment.html')
            
        try:
            price = float(price)
        except ValueError:
            flash('Invalid price.', 'error')
            return render_template('owner/add_equipment.html')

        # Handle image upload
        image_file = request.files.get('image')
        image_filename = 'default.jpg'
        
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'images', filename)
            image_file.save(upload_path)
            image_filename = filename

        new_equip = Equipment(
            name=name,
            description=description,
            category=category,
            location=location,
            price_per_day=price,
            image=image_filename,
            owner_id=current_user.id,
            availability=True
        )
        db.session.add(new_equip)
        db.session.commit()
        
        flash(f'Equipment "{name}" has been successfully listed!', 'success')
        return redirect(url_for('owner.dashboard'))
        
    return render_template('owner/add_equipment.html')
