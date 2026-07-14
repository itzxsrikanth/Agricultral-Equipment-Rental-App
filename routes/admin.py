from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.equipment import Equipment
from models.booking import Booking
from models.payment import Payment
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ── Role guard decorator ──────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ── Dashboard ─────────────────────────────────────────────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_equipment = Equipment.query.count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='Pending').count()

    # Revenue: sum of total_price for Approved/Paid bookings
    revenue_result = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.status.in_(['Approved', 'Paid', 'Completed'])
    ).scalar()
    total_revenue = revenue_result or 0.0

    # Last 6 bookings for activity feed
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(6).all()

    # Monthly booking counts for chart (last 6 months)
    all_bookings = Booking.query.all()
    from datetime import datetime
    monthly = {}
    for b in all_bookings:
        key = b.booking_date.strftime('%b %Y')
        monthly[key] = monthly.get(key, 0) + 1
    chart_labels = list(monthly.keys())[-6:]
    chart_data   = [monthly[k] for k in chart_labels]

    # Revenue by category for doughnut chart
    cat_revenue = {}
    for b in Booking.query.filter(Booking.status.in_(['Approved', 'Paid', 'Completed'])).all():
        cat = b.equipment.category
        cat_revenue[cat] = cat_revenue.get(cat, 0) + b.total_price
    cat_labels = list(cat_revenue.keys())
    cat_data   = [round(v, 2) for v in cat_revenue.values()]

    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_equipment=total_equipment,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        total_revenue=total_revenue,
        recent_bookings=recent_bookings,
        chart_labels=chart_labels,
        chart_data=chart_data,
        cat_labels=cat_labels,
        cat_data=cat_data
    )

# ── Users management ──────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

# ── Equipment management ──────────────────────────────────────────────────────
@admin_bp.route('/equipment')
@login_required
@admin_required
def equipment():
    all_equip = Equipment.query.order_by(Equipment.created_at.desc()).all()
    return render_template('admin/equipment.html', equipments=all_equip)

@admin_bp.route('/equipment/toggle/<int:equipment_id>', methods=['POST'])
@login_required
@admin_required
def toggle_equipment(equipment_id):
    equip = db.session.get(Equipment, equipment_id)
    if not equip:
        abort(404)
    equip.availability = not equip.availability
    db.session.commit()
    state = 'enabled' if equip.availability else 'disabled'
    flash(f'Equipment "{equip.name}" has been {state}.', 'success')
    return redirect(url_for('admin.equipment'))

# ── Booking approval / rejection ──────────────────────────────────────────────
@admin_bp.route('/booking/approve/<int:booking_id>', methods=['POST'])
@login_required
@admin_required
def approve_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
    if booking.status != 'Pending':
        flash('Only pending bookings can be approved.', 'error')
        return redirect(url_for('admin.dashboard'))
    booking.status = 'Approved'
    db.session.commit()
    flash(f'Booking #{booking.id} approved successfully.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/booking/reject/<int:booking_id>', methods=['POST'])
@login_required
@admin_required
def reject_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)
    if booking.status != 'Pending':
        flash('Only pending bookings can be rejected.', 'error')
        return redirect(url_for('admin.dashboard'))
    booking.status = 'Rejected'
    db.session.commit()
    flash(f'Booking #{booking.id} has been rejected.', 'success')
    return redirect(url_for('admin.dashboard'))
