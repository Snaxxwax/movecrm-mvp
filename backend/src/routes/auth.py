from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import jwt
from supertokens_python import get_user_by_id
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.flask import verify_session
from src.models import db, User, Tenant

auth_bp = Blueprint('auth', __name__)

def get_tenant_from_request():
    """Extract tenant from request headers or subdomain"""
    # Try to get tenant from header first
    tenant_slug = request.headers.get('X-Tenant-Slug')
    
    # If not in header, try to extract from subdomain
    if not tenant_slug:
        host = request.headers.get('Host', '')
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www' and subdomain != 'api':
                tenant_slug = subdomain
    
    if tenant_slug:
        tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
        return tenant
    
    return None

def require_tenant(f):
    """Decorator to ensure tenant context is available"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = get_tenant_from_request()
        if not tenant:
            return jsonify({'error': 'Tenant not found or not specified'}), 400
        
        request.tenant = tenant
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            session = verify_session()
            if not session:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get user from SuperTokens
            user_id = session.get_user_id()
            user = User.query.filter_by(supertokens_user_id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            request.user = user
            request.session = session
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication failed', 'details': str(e)}), 401
    
    return decorated_function

def require_role(roles):
    """Decorator to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            if request.user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/me', methods=['GET'])
@require_tenant
@require_auth
def get_current_user():
    """Get current authenticated user"""
    try:
        user_data = request.user.to_dict()
        user_data['tenant'] = request.tenant.to_dict()
        return jsonify(user_data)
    except Exception as e:
        return jsonify({'error': 'Failed to get user data', 'details': str(e)}), 500

@auth_bp.route('/users', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def list_users():
    """List users for the current tenant"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role_filter = request.args.get('role')
        
        query = User.query.filter_by(tenant_id=request.tenant.id)
        
        if role_filter:
            query = query.filter_by(role=role_filter)
        
        users = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'error': 'Failed to list users', 'details': str(e)}), 500

@auth_bp.route('/users/<user_id>', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def get_user(user_id):
    """Get specific user by ID"""
    try:
        user = User.query.filter_by(
            id=user_id, 
            tenant_id=request.tenant.id
        ).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({'error': 'Failed to get user', 'details': str(e)}), 500

@auth_bp.route('/users/<user_id>', methods=['PUT'])
@require_tenant
@require_auth
@require_role(['admin'])
def update_user(user_id):
    """Update user information"""
    try:
        user = User.query.filter_by(
            id=user_id, 
            tenant_id=request.tenant.id
        ).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'role' in data and data['role'] in ['admin', 'staff', 'customer']:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user', 'details': str(e)}), 500

@auth_bp.route('/users', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin'])
def create_user():
    """Create a new user (admin only)"""
    try:
        data = request.get_json()
        
        # Check if user already exists
        existing_user = User.query.filter_by(
            email=data['email'],
            tenant_id=request.tenant.id
        ).first()
        
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        user = User(
            tenant_id=request.tenant.id,
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            role=data.get('role', 'customer')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user', 'details': str(e)}), 500

@auth_bp.route('/tenants/current', methods=['GET'])
@require_tenant
def get_current_tenant():
    """Get current tenant information"""
    try:
        return jsonify(request.tenant.to_dict())
    except Exception as e:
        return jsonify({'error': 'Failed to get tenant data', 'details': str(e)}), 500

@auth_bp.route('/tenants/current', methods=['PUT'])
@require_tenant
@require_auth
@require_role(['admin'])
def update_current_tenant():
    """Update current tenant settings"""
    try:
        data = request.get_json()
        tenant = request.tenant
        
        # Update allowed fields
        if 'name' in data:
            tenant.name = data['name']
        if 'domain' in data:
            tenant.domain = data['domain']
        if 'logo_url' in data:
            tenant.logo_url = data['logo_url']
        if 'brand_colors' in data:
            tenant.brand_colors = data['brand_colors']
        if 'settings' in data:
            tenant.settings = data['settings']
        
        db.session.commit()
        
        return jsonify(tenant.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update tenant', 'details': str(e)}), 500

