from datetime import datetime, date
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, make_response
from flask_login import login_required, current_user
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from models import db
from models.equipment import Equipment
from models.booking import Booking

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/book/<int:equipment_id>', methods=['POST'])
@login_required
def create_booking(equipment_id):
    equipment = db.session.get(Equipment, equipment_id)
    if not equipment:
        abort(404)
    
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
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
    
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


@booking_bp.route('/booking/invoice/<int:booking_id>')
@login_required
def download_invoice(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
    
    # Only the booking owner or an admin can download the invoice
    if booking.user_id != current_user.id and current_user.role != 'admin':
        abort(403)

    if booking.status not in ['Approved', 'Paid', 'Completed']:
        flash('Invoice is only available for Approved or Paid bookings.', 'error')
        return redirect(url_for('booking.list_bookings'))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>AgriRent</b> — Agricultural Equipment Rental", styles['Title']))
    elements.append(Paragraph("www.agrirent.com | support@agrirent.com", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Invoice #{booking.id:04d}</b>", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Invoice meta table
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

    # Equipment & Rental Details table
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
            f'${booking.equipment.price_per_day:.2f}',
            f'${booking.total_price:.2f}',
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

    # Total amount
    total_data = [['', '', '', '', '', '', 'Grand Total:', f'${booking.total_price:.2f}']]
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

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=agrirent_invoice_{booking.id:04d}.pdf'
    return response
