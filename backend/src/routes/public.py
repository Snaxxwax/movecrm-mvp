from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import os
from werkzeug.utils import secure_filename
from src.models import db, Quote, QuoteMedia, Tenant, PricingRule, RateLimit, User
from src.utils.rate_limiter import check_rate_limit
from src.utils.file_upload import upload_file_to_s3

public_bp = Blueprint('public', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_tenant_by_slug(slug):
    """Get tenant by slug"""
    return Tenant.query.filter_by(slug=slug, is_active=True).first()

def generate_quote_number(tenant_id):
    """Generate a unique quote number for the tenant"""
    now = datetime.now()
    prefix = f"Q{now.year}{now.month:02d}"
    
    latest_quote = Quote.query.filter(
        Quote.tenant_id == tenant_id,
        Quote.quote_number.like(f"{prefix}%")
    ).order_by(Quote.quote_number.desc()).first()
    
    if latest_quote:
        try:
            sequence = int(latest_quote.quote_number[len(prefix):]) + 1
        except ValueError:
            sequence = 1
    else:
        sequence = 1
    
    return f"{prefix}{sequence:04d}"

@public_bp.route('/quote', methods=['POST'])
def submit_quote():
    """Public endpoint for quote submissions from widget"""
    try:
        # Get tenant from request
        tenant_slug = request.form.get('tenant_slug') or request.headers.get('X-Tenant-Slug')
        
        if not tenant_slug:
            return jsonify({'error': 'Tenant not specified'}), 400
        
        tenant = get_tenant_by_slug(tenant_slug)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        # Check rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not check_rate_limit(tenant.id, client_ip, '/public/quote'):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Validate required fields
        required_fields = ['customer_email', 'customer_name']
        for field in required_fields:
            if not request.form.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get default pricing rule
        pricing_rule = PricingRule.query.filter_by(
            tenant_id=tenant.id,
            is_default=True,
            is_active=True
        ).first()
        
        if not pricing_rule:
            return jsonify({'error': 'Service temporarily unavailable'}), 503
        
        # Create quote
        quote = Quote(
            tenant_id=tenant.id,
            quote_number=generate_quote_number(tenant.id),
            customer_email=request.form.get('customer_email'),
            customer_phone=request.form.get('customer_phone'),
            customer_name=request.form.get('customer_name'),
            pickup_address=request.form.get('pickup_address'),
            delivery_address=request.form.get('delivery_address'),
            notes=request.form.get('notes'),
            pricing_rule_id=pricing_rule.id,
            expires_at=datetime.now() + timedelta(days=30)
        )
        
        # Parse move date if provided
        move_date_str = request.form.get('move_date')
        if move_date_str:
            try:
                quote.move_date = datetime.fromisoformat(move_date_str).date()
            except ValueError:
                pass  # Invalid date format, ignore
        
        # Check if customer exists, if not create them
        customer = User.query.filter_by(
            email=quote.customer_email,
            tenant_id=tenant.id
        ).first()
        
        if not customer:
            customer = User(
                tenant_id=tenant.id,
                email=quote.customer_email,
                first_name=quote.customer_name.split(' ')[0] if quote.customer_name else '',
                last_name=' '.join(quote.customer_name.split(' ')[1:]) if quote.customer_name and ' ' in quote.customer_name else '',
                phone=quote.customer_phone,
                role='customer'
            )
            db.session.add(customer)
            db.session.flush()
        
        quote.customer_id = customer.id
        
        db.session.add(quote)
        db.session.flush()  # Get the quote ID
        
        # Handle file uploads
        uploaded_files = []
        files = request.files.getlist('files')
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    continue  # Skip files that are too large
                
                filename = secure_filename(file.filename)
                
                # Upload to S3 or local storage
                try:
                    file_path = upload_file_to_s3(
                        file, 
                        f"quotes/{quote.id}/{filename}",
                        current_app.config
                    )
                    
                    quote_media = QuoteMedia(
                        quote_id=quote.id,
                        file_name=filename,
                        file_path=file_path,
                        file_size=file_size,
                        mime_type=file.content_type
                    )
                    
                    db.session.add(quote_media)
                    uploaded_files.append(filename)
                    
                except Exception as e:
                    current_app.logger.error(f"Failed to upload file {filename}: {str(e)}")
                    continue
        
        db.session.commit()
        
        # Return success response
        response_data = {
            'quote_number': quote.quote_number,
            'message': 'Quote submitted successfully',
            'uploaded_files': uploaded_files
        }
        
        # Include quote ID for internal tracking (not exposed to public)
        if current_app.debug:
            response_data['quote_id'] = str(quote.id)
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Quote submission error: {str(e)}")
        return jsonify({'error': 'Failed to submit quote. Please try again.'}), 500

@public_bp.route('/quote/<quote_number>', methods=['GET'])
def get_public_quote(quote_number):
    """Get quote by quote number (public access)"""
    try:
        # Get tenant from request
        tenant_slug = request.args.get('tenant_slug') or request.headers.get('X-Tenant-Slug')
        
        if not tenant_slug:
            return jsonify({'error': 'Tenant not specified'}), 400
        
        tenant = get_tenant_by_slug(tenant_slug)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        # Find quote
        quote = Quote.query.filter_by(
            quote_number=quote_number,
            tenant_id=tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        # Return limited quote information for public access
        quote_data = {
            'quote_number': quote.quote_number,
            'status': quote.status,
            'customer_name': quote.customer_name,
            'move_date': quote.move_date.isoformat() if quote.move_date else None,
            'pickup_address': quote.pickup_address,
            'delivery_address': quote.delivery_address,
            'total_amount': float(quote.total_amount) if quote.total_amount else None,
            'expires_at': quote.expires_at.isoformat() if quote.expires_at else None,
            'created_at': quote.created_at.isoformat() if quote.created_at else None
        }
        
        return jsonify(quote_data)
        
    except Exception as e:
        current_app.logger.error(f"Public quote retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve quote'}), 500

@public_bp.route('/tenant/<tenant_slug>/config', methods=['GET'])
def get_tenant_config(tenant_slug):
    """Get public tenant configuration for widget"""
    try:
        tenant = get_tenant_by_slug(tenant_slug)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        # Return public configuration
        config = {
            'tenant_slug': tenant.slug,
            'tenant_name': tenant.name,
            'brand_colors': tenant.brand_colors,
            'logo_url': tenant.logo_url,
            'settings': {
                'allow_customer_login': tenant.settings.get('allow_customer_login', False),
                'max_file_uploads': tenant.settings.get('max_file_uploads', 5),
                'max_file_size_mb': tenant.settings.get('max_file_size_mb', 50)
            }
        }
        
        return jsonify(config)
        
    except Exception as e:
        current_app.logger.error(f"Tenant config error: {str(e)}")
        return jsonify({'error': 'Failed to get tenant configuration'}), 500

@public_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@public_bp.route('/widget.js', methods=['GET'])
def serve_widget():
    """Serve the embeddable widget JavaScript"""
    # This would serve the compiled widget JavaScript
    # For now, return a placeholder
    widget_js = """
    // MoveCRM Widget v1.0.0
    // This would contain the actual widget JavaScript code
    console.log('MoveCRM Widget loaded');
    """
    
    response = current_app.response_class(
        widget_js,
        mimetype='application/javascript'
    )
    
    # Add CORS headers for widget embedding
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response

