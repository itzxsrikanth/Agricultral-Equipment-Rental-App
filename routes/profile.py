from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        phone    = request.form.get('phone', '').strip()
        new_pass = request.form.get('new_password', '').strip()
        cur_pass = request.form.get('current_password', '').strip()

        if not name:
            flash('Name cannot be empty.', 'error')
            return render_template('profile.html')

        # Password change requested
        if new_pass:
            if not cur_pass:
                flash('Please enter your current password to change it.', 'error')
                return render_template('profile.html')
            if not current_user.check_password(cur_pass):
                flash('Current password is incorrect.', 'error')
                return render_template('profile.html')
            current_user.set_password(new_pass)
            flash('Password updated successfully.', 'success')

        current_user.name  = name
        current_user.phone = phone
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.profile'))

    return render_template('profile.html')
