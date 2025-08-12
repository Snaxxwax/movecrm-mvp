from flask import Blueprint, request, jsonify
from decimal import Decimal
from src.models import db, PricingRule, ItemCatalog, Tenant, User, Quote
from src.routes.auth import require_tenant, require_auth, require_role

admin_bp = Blueprint('admin', __name__)

# Pricing Rules Management
@admin_bp.route('/pricing-rules', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def list_pricing_rules():
    """List pricing rules for the tenant"""
    try:
        rules = PricingRule.query.filter_by(
            tenant_id=request.tenant.id
        ).order_by(PricingRule.is_default.desc(), PricingRule.name).all()
        
        return jsonify([rule.to_dict() for rule in rules])
        
    except Exception as e:
        return jsonify({'error': 'Failed to list pricing rules', 'details': str(e)}), 500

@admin_bp.route('/pricing-rules', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin'])
def create_pricing_rule():
    """Create new pricing rule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'rate_per_cubic_foot', 'labor_rate_per_hour']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # If this is set as default, unset other defaults
        if data.get('is_default', False):
            PricingRule.query.filter_by(
                tenant_id=request.tenant.id,
                is_default=True
            ).update({'is_default': False})
        
        rule = PricingRule(
            tenant_id=request.tenant.id,
            name=data['name'],
            rate_per_cubic_foot=Decimal(str(data['rate_per_cubic_foot'])),
            labor_rate_per_hour=Decimal(str(data['labor_rate_per_hour'])),
            minimum_charge=Decimal(str(data.get('minimum_charge', 0))),
            distance_rate_per_mile=Decimal(str(data.get('distance_rate_per_mile', 0))),
            is_default=data.get('is_default', False),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify(rule.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create pricing rule', 'details': str(e)}), 500

@admin_bp.route('/pricing-rules/<rule_id>', methods=['PUT'])
@require_tenant
@require_auth
@require_role(['admin'])
def update_pricing_rule(rule_id):
    """Update pricing rule"""
    try:
        rule = PricingRule.query.filter_by(
            id=rule_id,
            tenant_id=request.tenant.id
        ).first()
        
        if not rule:
            return jsonify({'error': 'Pricing rule not found'}), 404
        
        data = request.get_json()
        
        # If this is set as default, unset other defaults
        if data.get('is_default', False) and not rule.is_default:
            PricingRule.query.filter_by(
                tenant_id=request.tenant.id,
                is_default=True
            ).update({'is_default': False})
        
        # Update fields
        if 'name' in data:
            rule.name = data['name']
        if 'rate_per_cubic_foot' in data:
            rule.rate_per_cubic_foot = Decimal(str(data['rate_per_cubic_foot']))
        if 'labor_rate_per_hour' in data:
            rule.labor_rate_per_hour = Decimal(str(data['labor_rate_per_hour']))
        if 'minimum_charge' in data:
            rule.minimum_charge = Decimal(str(data['minimum_charge']))
        if 'distance_rate_per_mile' in data:
            rule.distance_rate_per_mile = Decimal(str(data['distance_rate_per_mile']))
        if 'is_default' in data:
            rule.is_default = data['is_default']
        if 'is_active' in data:
            rule.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify(rule.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update pricing rule', 'details': str(e)}), 500

@admin_bp.route('/pricing-rules/<rule_id>', methods=['DELETE'])
@require_tenant
@require_auth
@require_role(['admin'])
def delete_pricing_rule(rule_id):
    """Delete pricing rule"""
    try:
        rule = PricingRule.query.filter_by(
            id=rule_id,
            tenant_id=request.tenant.id
        ).first()
        
        if not rule:
            return jsonify({'error': 'Pricing rule not found'}), 404
        
        # Check if rule is in use
        quotes_using_rule = Quote.query.filter_by(pricing_rule_id=rule.id).count()
        if quotes_using_rule > 0:
            return jsonify({
                'error': f'Cannot delete pricing rule. It is used by {quotes_using_rule} quotes.'
            }), 400
        
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({'message': 'Pricing rule deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete pricing rule', 'details': str(e)}), 500

# Item Catalog Management
@admin_bp.route('/item-catalog', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def list_catalog_items():
    """List item catalog for the tenant"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        category_filter = request.args.get('category')
        search = request.args.get('search')
        
        query = ItemCatalog.query.filter_by(tenant_id=request.tenant.id)
        
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        if search:
            query = query.filter(ItemCatalog.name.ilike(f"%{search}%"))
        
        items = query.order_by(ItemCatalog.category, ItemCatalog.name).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'items': [item.to_dict() for item in items.items],
            'total': items.total,
            'pages': items.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to list catalog items', 'details': str(e)}), 500

@admin_bp.route('/item-catalog', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin'])
def create_catalog_item():
    """Create new catalog item"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Item name is required'}), 400
        
        item = ItemCatalog(
            tenant_id=request.tenant.id,
            name=data['name'],
            aliases=data.get('aliases', []),
            category=data.get('category'),
            base_cubic_feet=Decimal(str(data.get('base_cubic_feet', 0))),
            labor_multiplier=Decimal(str(data.get('labor_multiplier', 1.0))),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify(item.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create catalog item', 'details': str(e)}), 500

@admin_bp.route('/item-catalog/<item_id>', methods=['PUT'])
@require_tenant
@require_auth
@require_role(['admin'])
def update_catalog_item(item_id):
    """Update catalog item"""
    try:
        item = ItemCatalog.query.filter_by(
            id=item_id,
            tenant_id=request.tenant.id
        ).first()
        
        if not item:
            return jsonify({'error': 'Catalog item not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            item.name = data['name']
        if 'aliases' in data:
            item.aliases = data['aliases']
        if 'category' in data:
            item.category = data['category']
        if 'base_cubic_feet' in data:
            item.base_cubic_feet = Decimal(str(data['base_cubic_feet']))
        if 'labor_multiplier' in data:
            item.labor_multiplier = Decimal(str(data['labor_multiplier']))
        if 'is_active' in data:
            item.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update catalog item', 'details': str(e)}), 500

@admin_bp.route('/item-catalog/<item_id>', methods=['DELETE'])
@require_tenant
@require_auth
@require_role(['admin'])
def delete_catalog_item(item_id):
    """Delete catalog item"""
    try:
        item = ItemCatalog.query.filter_by(
            id=item_id,
            tenant_id=request.tenant.id
        ).first()
        
        if not item:
            return jsonify({'error': 'Catalog item not found'}), 404
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'message': 'Catalog item deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete catalog item', 'details': str(e)}), 500

# Dashboard Statistics
@admin_bp.route('/dashboard/stats', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get basic counts
        total_quotes = Quote.query.filter_by(tenant_id=request.tenant.id).count()
        pending_quotes = Quote.query.filter_by(
            tenant_id=request.tenant.id,
            status='pending'
        ).count()
        approved_quotes = Quote.query.filter_by(
            tenant_id=request.tenant.id,
            status='approved'
        ).count()
        total_customers = User.query.filter_by(
            tenant_id=request.tenant.id,
            role='customer'
        ).count()
        
        # Get recent quotes
        recent_quotes = Quote.query.filter_by(
            tenant_id=request.tenant.id
        ).order_by(Quote.created_at.desc()).limit(5).all()
        
        # Calculate total revenue (approved quotes)
        approved_quotes_query = Quote.query.filter_by(
            tenant_id=request.tenant.id,
            status='approved'
        ).all()
        
        total_revenue = sum(
            float(quote.total_amount) for quote in approved_quotes_query 
            if quote.total_amount
        )
        
        return jsonify({
            'total_quotes': total_quotes,
            'pending_quotes': pending_quotes,
            'approved_quotes': approved_quotes,
            'total_customers': total_customers,
            'total_revenue': total_revenue,
            'recent_quotes': [quote.to_dict() for quote in recent_quotes]
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to get dashboard stats', 'details': str(e)}), 500

# Categories Management
@admin_bp.route('/categories', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def list_categories():
    """List all categories used in item catalog"""
    try:
        categories = db.session.query(ItemCatalog.category).filter_by(
            tenant_id=request.tenant.id
        ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify(category_list)
        
    except Exception as e:
        return jsonify({'error': 'Failed to list categories', 'details': str(e)}), 500

# Bulk Operations
@admin_bp.route('/item-catalog/bulk-import', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin'])
def bulk_import_catalog():
    """Bulk import catalog items"""
    try:
        data = request.get_json()
        
        if not data.get('items') or not isinstance(data['items'], list):
            return jsonify({'error': 'Items array is required'}), 400
        
        created_items = []
        errors = []
        
        for idx, item_data in enumerate(data['items']):
            try:
                if not item_data.get('name'):
                    errors.append(f"Row {idx + 1}: Item name is required")
                    continue
                
                item = ItemCatalog(
                    tenant_id=request.tenant.id,
                    name=item_data['name'],
                    aliases=item_data.get('aliases', []),
                    category=item_data.get('category'),
                    base_cubic_feet=Decimal(str(item_data.get('base_cubic_feet', 0))),
                    labor_multiplier=Decimal(str(item_data.get('labor_multiplier', 1.0))),
                    is_active=item_data.get('is_active', True)
                )
                
                db.session.add(item)
                created_items.append(item_data['name'])
                
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        
        if created_items:
            db.session.commit()
        
        return jsonify({
            'created_count': len(created_items),
            'created_items': created_items,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Bulk import failed', 'details': str(e)}), 500

