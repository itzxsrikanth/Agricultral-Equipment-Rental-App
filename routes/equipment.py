from flask import Blueprint, render_template
from models.equipment import Equipment

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/equipment')
def list_equipment():
    # Placeholder: fetch all available equipment
    equipments = Equipment.query.filter_by(availability=True).all()
    return render_template('equipment.html', equipments=equipments)

@equipment_bp.route('/equipment/<int:equipment_id>')
def equipment_detail(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template('equipment_detail.html', equipment=equipment)
