from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.equipment import Equipment
from models.booking import Booking

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/book/<int:equipment_id>', methods=['POST'])
@login_required
def create_booking(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # 1. Renter cannot be the owner of the equipment
    if equipment.owner_id == current_user.id:
        flash('You cannot rent your own equipment!', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    
    # 2. Date input validation
    if not start_date_str or not end_date_str:
        flash('Please select both start and end dates.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please try again.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
    today = date.today()
    if start_date < today:
        flash('Start date cannot be in the past.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
    if end_date < start_date:
        flash('End date must be on or after the start date.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))
        
    # Calculate total days (minimum 1 day)
    delta_days = (end_date - start_date).days
    rental_days = max(delta_days, 1)
    
    total_price = rental_days * equipment.price_per_day
    
    # Create booking record
    booking = Booking(
        user_id=current_user.id,
        equipment_id=equipment.id,
        start_date=start_date,
        end_date=end_date,
        total_price=total_price,
        status='Pending'
    )
    
    try:
        db.session.add(booking)
        db.session.commit()
        flash('Booking request submitted successfully! The owner will review it shortly.', 'success')
        return redirect(url_for('booking.list_bookings'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while submitting your booking. Please try again.', 'error')
        return redirect(url_for('equipment.equipment_detail', equipment_id=equipment_id))

@booking_bp.route('/history')
@login_required
def list_bookings():
    # Fetch user's bookings ordered by date descending
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('history.html', bookings=bookings)

@booking_bp.route('/booking/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check permissions (only owner of the booking can cancel)
    if booking.user_id != current_user.id:
        flash('You are not authorized to cancel this booking.', 'error')
        return redirect(url_for('booking.list_bookings'))
        
    if booking.status != 'Pending':
        flash('Only pending bookings can be cancelled.', 'error')
        return redirect(url_for('booking.list_bookings'))
        
    booking.status = 'Cancelled'
    try:
        db.session.commit()
        flash('Booking cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Could not cancel booking. Please try again.', 'error')
        
    return redirect(url_for('booking.list_bookings'))
