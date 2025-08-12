from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from src.models import db, Quote, QuoteItem, QuoteMedia, User, PricingRule, ItemCatalog
from src.routes.auth import require_tenant, require_auth, require_role

quotes_bp = Blueprint('quotes', __name__)

def generate_quote_number(tenant_id):
    """Generate a unique quote number for the tenant"""
    # Get current year and month
    now = datetime.now()
    prefix = f"Q{now.year}{now.month:02d}"
    
    # Find the highest quote number for this month
    latest_quote = Quote.query.filter(
        Quote.tenant_id == tenant_id,
        Quote.quote_number.like(f"{prefix}%")
    ).order_by(Quote.quote_number.desc()).first()
    
    if latest_quote:
        # Extract the sequence number and increment
        try:
            sequence = int(latest_quote.quote_number[len(prefix):]) + 1
        except ValueError:
            sequence = 1
    else:
        sequence = 1
    
    return f"{prefix}{sequence:04d}"

def calculate_quote_pricing(quote, pricing_rule):
    """Calculate pricing for a quote based on items and pricing rules"""
    total_cubic_feet = Decimal('0')
    total_labor_hours = Decimal('0')
    subtotal = Decimal('0')
    
    for item in quote.quote_items:
        if item.cubic_feet:
            total_cubic_feet += item.cubic_feet * item.quantity
        if item.labor_hours:
            total_labor_hours += item.labor_hours * item.quantity
        if item.total_price:
            subtotal += item.total_price
    
    # Calculate based on pricing rule
    cubic_feet_cost = total_cubic_feet * pricing_rule.rate_per_cubic_foot
    labor_cost = total_labor_hours * pricing_rule.labor_rate_per_hour
    distance_cost = Decimal('0')
    
    if quote.distance_miles and pricing_rule.distance_rate_per_mile:
        distance_cost = quote.distance_miles * pricing_rule.distance_rate_per_mile
    
    calculated_subtotal = cubic_feet_cost + labor_cost + distance_cost
    
    # Apply minimum charge
    if calculated_subtotal < pricing_rule.minimum_charge:
        calculated_subtotal = pricing_rule.minimum_charge
    
    # Update quote totals
    quote.total_cubic_feet = total_cubic_feet
    quote.total_labor_hours = total_labor_hours
    quote.subtotal = calculated_subtotal
    
    # Calculate tax (assuming 8.5% for now, should be configurable)
    tax_rate = Decimal('0.085')
    quote.tax_amount = calculated_subtotal * tax_rate
    quote.total_amount = calculated_subtotal + quote.tax_amount
    
    return quote

@quotes_bp.route('/', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def list_quotes():
    """List quotes for the current tenant"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        customer_email = request.args.get('customer_email')
        
        query = Quote.query.filter_by(tenant_id=request.tenant.id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if customer_email:
            query = query.filter(Quote.customer_email.ilike(f"%{customer_email}%"))
        
        quotes = query.order_by(Quote.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes.items],
            'total': quotes.total,
            'pages': quotes.pages,
            'current_page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'error': 'Failed to list quotes', 'details': str(e)}), 500

@quotes_bp.route('/<quote_id>', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def get_quote(quote_id):
    """Get specific quote with items and media"""
    try:
        quote = Quote.query.filter_by(
            id=quote_id, 
            tenant_id=request.tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        quote_data = quote.to_dict()
        quote_data['items'] = [item.to_dict() for item in quote.quote_items]
        quote_data['media'] = [media.to_dict() for media in quote.quote_media]
        
        return jsonify(quote_data)
    except Exception as e:
        return jsonify({'error': 'Failed to get quote', 'details': str(e)}), 500

@quotes_bp.route('/', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def create_quote():
    """Create a new quote"""
    try:
        data = request.get_json()
        
        # Get default pricing rule
        pricing_rule = PricingRule.query.filter_by(
            tenant_id=request.tenant.id,
            is_default=True,
            is_active=True
        ).first()
        
        if not pricing_rule:
            return jsonify({'error': 'No default pricing rule found'}), 400
        
        # Create quote
        quote = Quote(
            tenant_id=request.tenant.id,
            quote_number=generate_quote_number(request.tenant.id),
            customer_email=data['customer_email'],
            customer_phone=data.get('customer_phone'),
            customer_name=data.get('customer_name'),
            pickup_address=data.get('pickup_address'),
            delivery_address=data.get('delivery_address'),
            move_date=datetime.fromisoformat(data['move_date']) if data.get('move_date') else None,
            notes=data.get('notes'),
            distance_miles=Decimal(str(data.get('distance_miles', 0))),
            pricing_rule_id=pricing_rule.id,
            expires_at=datetime.now() + timedelta(days=30)  # 30 day expiration
        )
        
        # Check if customer exists
        customer = User.query.filter_by(
            email=data['customer_email'],
            tenant_id=request.tenant.id
        ).first()
        
        if customer:
            quote.customer_id = customer.id
        
        db.session.add(quote)
        db.session.flush()  # Get the quote ID
        
        # Add items if provided
        if 'items' in data:
            for item_data in data['items']:
                quote_item = QuoteItem(
                    quote_id=quote.id,
                    detected_name=item_data.get('detected_name'),
                    quantity=item_data.get('quantity', 1),
                    cubic_feet=Decimal(str(item_data.get('cubic_feet', 0))),
                    labor_hours=Decimal(str(item_data.get('labor_hours', 0))),
                    unit_price=Decimal(str(item_data.get('unit_price', 0))),
                    total_price=Decimal(str(item_data.get('total_price', 0)))
                )
                
                # Try to match with catalog item
                if item_data.get('detected_name'):
                    catalog_item = ItemCatalog.query.filter(
                        ItemCatalog.tenant_id == request.tenant.id,
                        ItemCatalog.aliases.any(item_data['detected_name'].lower())
                    ).first()
                    
                    if catalog_item:
                        quote_item.item_catalog_id = catalog_item.id
                        quote_item.cubic_feet = catalog_item.base_cubic_feet
                        quote_item.labor_hours = catalog_item.base_cubic_feet * catalog_item.labor_multiplier / 10  # Rough estimate
                
                db.session.add(quote_item)
        
        # Calculate pricing
        quote = calculate_quote_pricing(quote, pricing_rule)
        
        db.session.commit()
        
        return jsonify(quote.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create quote', 'details': str(e)}), 500

@quotes_bp.route('/<quote_id>', methods=['PUT'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def update_quote(quote_id):
    """Update quote information"""
    try:
        quote = Quote.query.filter_by(
            id=quote_id, 
            tenant_id=request.tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'customer_email' in data:
            quote.customer_email = data['customer_email']
        if 'customer_phone' in data:
            quote.customer_phone = data['customer_phone']
        if 'customer_name' in data:
            quote.customer_name = data['customer_name']
        if 'pickup_address' in data:
            quote.pickup_address = data['pickup_address']
        if 'delivery_address' in data:
            quote.delivery_address = data['delivery_address']
        if 'move_date' in data:
            quote.move_date = datetime.fromisoformat(data['move_date']) if data['move_date'] else None
        if 'notes' in data:
            quote.notes = data['notes']
        if 'distance_miles' in data:
            quote.distance_miles = Decimal(str(data['distance_miles']))
        if 'status' in data and data['status'] in ['pending', 'approved', 'rejected', 'expired']:
            quote.status = data['status']
        
        # Recalculate pricing if needed
        if quote.pricing_rule:
            quote = calculate_quote_pricing(quote, quote.pricing_rule)
        
        db.session.commit()
        
        return jsonify(quote.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update quote', 'details': str(e)}), 500

@quotes_bp.route('/<quote_id>/items', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def add_quote_item(quote_id):
    """Add item to quote"""
    try:
        quote = Quote.query.filter_by(
            id=quote_id, 
            tenant_id=request.tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        data = request.get_json()
        
        quote_item = QuoteItem(
            quote_id=quote.id,
            detected_name=data.get('detected_name'),
            quantity=data.get('quantity', 1),
            cubic_feet=Decimal(str(data.get('cubic_feet', 0))),
            labor_hours=Decimal(str(data.get('labor_hours', 0))),
            unit_price=Decimal(str(data.get('unit_price', 0))),
            total_price=Decimal(str(data.get('total_price', 0)))
        )
        
        # Try to match with catalog item
        if data.get('catalog_item_id'):
            catalog_item = ItemCatalog.query.filter_by(
                id=data['catalog_item_id'],
                tenant_id=request.tenant.id
            ).first()
            
            if catalog_item:
                quote_item.item_catalog_id = catalog_item.id
                quote_item.detected_name = catalog_item.name
                quote_item.cubic_feet = catalog_item.base_cubic_feet
                quote_item.labor_hours = catalog_item.base_cubic_feet * catalog_item.labor_multiplier / 10
        
        db.session.add(quote_item)
        
        # Recalculate quote pricing
        if quote.pricing_rule:
            quote = calculate_quote_pricing(quote, quote.pricing_rule)
        
        db.session.commit()
        
        return jsonify(quote_item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add quote item', 'details': str(e)}), 500

@quotes_bp.route('/<quote_id>/items/<item_id>', methods=['DELETE'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def remove_quote_item(quote_id, item_id):
    """Remove item from quote"""
    try:
        quote = Quote.query.filter_by(
            id=quote_id, 
            tenant_id=request.tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        quote_item = QuoteItem.query.filter_by(
            id=item_id,
            quote_id=quote.id
        ).first()
        
        if not quote_item:
            return jsonify({'error': 'Quote item not found'}), 404
        
        db.session.delete(quote_item)
        
        # Recalculate quote pricing
        if quote.pricing_rule:
            quote = calculate_quote_pricing(quote, quote.pricing_rule)
        
        db.session.commit()
        
        return jsonify({'message': 'Quote item removed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove quote item', 'details': str(e)}), 500

@quotes_bp.route('/<quote_id>/recalculate', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def recalculate_quote(quote_id):
    """Recalculate quote pricing"""
    try:
        quote = Quote.query.filter_by(
            id=quote_id, 
            tenant_id=request.tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        if not quote.pricing_rule:
            return jsonify({'error': 'No pricing rule associated with quote'}), 400
        
        quote = calculate_quote_pricing(quote, quote.pricing_rule)
        db.session.commit()
        
        return jsonify(quote.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to recalculate quote', 'details': str(e)}), 500

