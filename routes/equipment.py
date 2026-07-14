from flask import Blueprint, render_template, request, abort
from models import db
from models.equipment import Equipment

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/equipment')
def list_equipment():
    query = Equipment.query.filter_by(availability=True)
    
    search_query = request.args.get('search', '').strip()
    category_query = request.args.getlist('category')
    single_category = request.args.get('category')
    location_query = request.args.get('location', 'All Regions').strip()
    
    # Apply search filter
    if search_query:
        query = query.filter(
            (Equipment.name.like(f"%{search_query}%")) | 
            (Equipment.description.like(f"%{search_query}%"))
        )
    
    # Consolidate category filters
    categories = []
    if category_query:
        categories.extend([c for c in category_query if c])
    if single_category and single_category not in categories:
        categories.append(single_category)
        
    if categories and 'All' not in categories:
        query = query.filter(Equipment.category.in_(categories))
        
    # Apply location filter
    if location_query and location_query != 'All Regions':
        query = query.filter(Equipment.location == location_query)
        
    equipments = query.all()
    
    return render_template('equipment.html', 
                           equipments=equipments,
                           search=search_query,
                           selected_categories=categories,
                           selected_location=location_query)

@equipment_bp.route('/equipment/<int:equipment_id>')
def equipment_detail(equipment_id):
    equipment = db.session.get(Equipment, equipment_id)
    if not equipment:
        abort(404)
    return render_template('equipment_detail.html', equipment=equipment)
