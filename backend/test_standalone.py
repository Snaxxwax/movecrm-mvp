#!/usr/bin/env python3
"""
Standalone test demonstrating MoveCRM testing infrastructure.
This test showcases critical functionality without complex dependencies.
"""

import pytest
import sqlite3
import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from decimal import Decimal
import uuid


# --- TEST SETUP ---

# Create Flask app for testing
def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    return app


# --- MODEL DEFINITIONS FOR TESTING ---

def create_models(db):
    """Create test models that mirror MoveCRM structure."""
    
    class Tenant(db.Model):
        __tablename__ = 'tenants'
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        slug = db.Column(db.String(50), unique=True, nullable=False)
        name = db.Column(db.String(255), nullable=False)
        domain = db.Column(db.String(255))
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relationships
        users = db.relationship('User', backref='tenant', cascade='all, delete-orphan')
        quotes = db.relationship('Quote', backref='tenant', cascade='all, delete-orphan')
        
        def to_dict(self):
            return {
                'id': self.id,
                'slug': self.slug,
                'name': self.name,
                'domain': self.domain,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
        email = db.Column(db.String(255), nullable=False)
        first_name = db.Column(db.String(100))
        last_name = db.Column(db.String(100))
        role = db.Column(db.String(50), default='customer')  # admin, staff, customer
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        __table_args__ = (db.UniqueConstraint('tenant_id', 'email'),)
        
        def to_dict(self):
            return {
                'id': self.id,
                'tenant_id': self.tenant_id,
                'email': self.email,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'role': self.role,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    class Quote(db.Model):
        __tablename__ = 'quotes'
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
        customer_id = db.Column(db.String(36), db.ForeignKey('users.id'))
        quote_number = db.Column(db.String(50), unique=True, nullable=False)
        status = db.Column(db.String(50), default='pending')
        customer_email = db.Column(db.String(255), nullable=False)
        customer_name = db.Column(db.String(255))
        pickup_address = db.Column(db.Text)
        delivery_address = db.Column(db.Text)
        total_cubic_feet = db.Column(db.Numeric(10, 2), default=0)
        total_amount = db.Column(db.Numeric(10, 2), default=0)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        def to_dict(self):
            return {
                'id': self.id,
                'tenant_id': self.tenant_id,
                'customer_id': self.customer_id,
                'quote_number': self.quote_number,
                'status': self.status,
                'customer_email': self.customer_email,
                'customer_name': self.customer_name,
                'pickup_address': self.pickup_address,
                'delivery_address': self.delivery_address,
                'total_cubic_feet': float(self.total_cubic_feet) if self.total_cubic_feet else None,
                'total_amount': float(self.total_amount) if self.total_amount else None,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    return Tenant, User, Quote


# --- API ENDPOINTS FOR TESTING ---

def create_test_routes(app, db, Tenant, User, Quote):
    """Create test API routes."""
    
    @app.route('/api/tenants', methods=['GET'])
    def list_tenants():
        tenants = Tenant.query.all()
        return jsonify([t.to_dict() for t in tenants])
    
    @app.route('/api/tenants', methods=['POST'])
    def create_tenant():
        data = request.get_json()
        tenant = Tenant(
            slug=data['slug'],
            name=data['name'],
            domain=data.get('domain')
        )
        db.session.add(tenant)
        db.session.commit()
        return jsonify(tenant.to_dict()), 201
    
    @app.route('/api/users', methods=['GET'])
    def list_users():
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if not tenant_slug:
            return jsonify({'error': 'Tenant header required'}), 400
        
        tenant = Tenant.query.filter_by(slug=tenant_slug).first()
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        users = User.query.filter_by(tenant_id=tenant.id).all()
        return jsonify([u.to_dict() for u in users])
    
    @app.route('/api/users', methods=['POST'])
    def create_user():
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if not tenant_slug:
            return jsonify({'error': 'Tenant header required'}), 400
        
        tenant = Tenant.query.filter_by(slug=tenant_slug).first()
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        data = request.get_json()
        
        # Check for duplicate email within tenant
        existing = User.query.filter_by(
            tenant_id=tenant.id,
            email=data['email']
        ).first()
        if existing:
            return jsonify({'error': 'User already exists'}), 400
        
        user = User(
            tenant_id=tenant.id,
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=data.get('role', 'customer')
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    
    @app.route('/api/quotes', methods=['GET'])
    def list_quotes():
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if not tenant_slug:
            return jsonify({'error': 'Tenant header required'}), 400
        
        tenant = Tenant.query.filter_by(slug=tenant_slug).first()
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        quotes = Quote.query.filter_by(tenant_id=tenant.id).all()
        return jsonify([q.to_dict() for q in quotes])
    
    @app.route('/api/quotes', methods=['POST'])
    def create_quote():
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if not tenant_slug:
            return jsonify({'error': 'Tenant header required'}), 400
        
        tenant = Tenant.query.filter_by(slug=tenant_slug).first()
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        data = request.get_json()
        
        quote = Quote(
            tenant_id=tenant.id,
            quote_number=data['quote_number'],
            customer_email=data['customer_email'],
            customer_name=data.get('customer_name'),
            pickup_address=data.get('pickup_address'),
            delivery_address=data.get('delivery_address'),
            total_cubic_feet=data.get('total_cubic_feet', 0),
            total_amount=data.get('total_amount', 0)
        )
        db.session.add(quote)
        db.session.commit()
        return jsonify(quote.to_dict()), 201


# --- TEST CLASSES ---

class TestMoveCRMCore:
    """Test core MoveCRM functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        app = create_test_app()
        return app
    
    @pytest.fixture
    def db_models(self, app):
        """Create database and models."""
        db = SQLAlchemy(app)
        Tenant, User, Quote = create_models(db)
        
        with app.app_context():
            db.create_all()
            create_test_routes(app, db, Tenant, User, Quote)
            yield db, Tenant, User, Quote
            db.drop_all()
    
    @pytest.fixture
    def client(self, app, db_models):
        """Create test client."""
        return app.test_client()
    
    def test_app_creation(self, app):
        """Test app creates successfully."""
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_tenant_creation(self, app, db_models):
        """Test tenant creation and isolation."""
        db, Tenant, User, Quote = db_models
        
        with app.app_context():
            # Create tenants
            tenant1 = Tenant(slug='company1', name='Company 1', domain='company1.example.com')
            tenant2 = Tenant(slug='company2', name='Company 2', domain='company2.example.com')
            
            db.session.add(tenant1)
            db.session.add(tenant2)
            db.session.commit()
            
            # Verify tenants exist
            assert Tenant.query.count() == 2
            assert Tenant.query.filter_by(slug='company1').first() is not None
            assert Tenant.query.filter_by(slug='company2').first() is not None
            
            # Verify tenant isolation
            found_tenant1 = Tenant.query.filter_by(slug='company1').first()
            found_tenant2 = Tenant.query.filter_by(slug='company2').first()
            
            assert found_tenant1.id != found_tenant2.id
            assert found_tenant1.name == 'Company 1'
            assert found_tenant2.name == 'Company 2'
    
    def test_user_multi_tenant_isolation(self, app, db_models):
        """Test user isolation between tenants."""
        db, Tenant, User, Quote = db_models
        
        with app.app_context():
            # Create tenants
            tenant1 = Tenant(slug='tenant1', name='Tenant 1')
            tenant2 = Tenant(slug='tenant2', name='Tenant 2')
            db.session.add(tenant1)
            db.session.add(tenant2)
            db.session.commit()
            
            # Create users in different tenants with same email
            user1 = User(tenant_id=tenant1.id, email='same@email.com', role='admin')
            user2 = User(tenant_id=tenant2.id, email='same@email.com', role='customer')
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # Verify isolation
            tenant1_users = User.query.filter_by(tenant_id=tenant1.id).all()
            tenant2_users = User.query.filter_by(tenant_id=tenant2.id).all()
            
            assert len(tenant1_users) == 1
            assert len(tenant2_users) == 1
            assert tenant1_users[0].role == 'admin'
            assert tenant2_users[0].role == 'customer'
            assert tenant1_users[0].id != tenant2_users[0].id
    
    def test_quote_business_logic(self, app, db_models):
        """Test quote creation and business logic."""
        db, Tenant, User, Quote = db_models
        
        with app.app_context():
            # Create tenant and user
            tenant = Tenant(slug='test-company', name='Test Company')
            db.session.add(tenant)
            db.session.commit()
            
            customer = User(
                tenant_id=tenant.id,
                email='customer@test.com',
                first_name='John',
                last_name='Customer',
                role='customer'
            )
            db.session.add(customer)
            db.session.commit()
            
            # Create quote
            quote = Quote(
                tenant_id=tenant.id,
                customer_id=customer.id,
                quote_number='Q-2024-001',
                customer_email=customer.email,
                customer_name=f'{customer.first_name} {customer.last_name}',
                pickup_address='123 Start St',
                delivery_address='456 End Ave',
                total_cubic_feet=Decimal('150.00'),
                total_amount=Decimal('1275.00')
            )
            db.session.add(quote)
            db.session.commit()
            
            # Verify quote
            found_quote = Quote.query.filter_by(quote_number='Q-2024-001').first()
            assert found_quote is not None
            assert found_quote.customer_email == 'customer@test.com'
            assert float(found_quote.total_cubic_feet) == 150.00
            assert float(found_quote.total_amount) == 1275.00
    
    def test_api_tenant_isolation(self, client, app, db_models):
        """Test API endpoints respect tenant isolation."""
        db, Tenant, User, Quote = db_models
        
        with app.app_context():
            # Create tenants via API
            tenant1_data = {'slug': 'api-tenant1', 'name': 'API Tenant 1'}
            tenant2_data = {'slug': 'api-tenant2', 'name': 'API Tenant 2'}
            
            response1 = client.post('/api/tenants', 
                                  json=tenant1_data,
                                  content_type='application/json')
            response2 = client.post('/api/tenants',
                                  json=tenant2_data, 
                                  content_type='application/json')
            
            assert response1.status_code == 201
            assert response2.status_code == 201
            
            # Create users in each tenant
            user1_data = {'email': 'user1@tenant1.com', 'first_name': 'User', 'role': 'admin'}
            user2_data = {'email': 'user1@tenant2.com', 'first_name': 'User', 'role': 'customer'}
            
            client.post('/api/users',
                       json=user1_data,
                       headers={'X-Tenant-Slug': 'api-tenant1'},
                       content_type='application/json')
            
            client.post('/api/users',
                       json=user2_data,
                       headers={'X-Tenant-Slug': 'api-tenant2'},
                       content_type='application/json')
            
            # Verify isolation by querying users
            tenant1_users = client.get('/api/users', headers={'X-Tenant-Slug': 'api-tenant1'})
            tenant2_users = client.get('/api/users', headers={'X-Tenant-Slug': 'api-tenant2'})
            
            assert tenant1_users.status_code == 200
            assert tenant2_users.status_code == 200
            
            tenant1_data = tenant1_users.get_json()
            tenant2_data = tenant2_users.get_json()
            
            assert len(tenant1_data) == 1
            assert len(tenant2_data) == 1
            assert tenant1_data[0]['email'] == 'user1@tenant1.com'
            assert tenant2_data[0]['email'] == 'user1@tenant2.com'
            assert tenant1_data[0]['role'] == 'admin'
            assert tenant2_data[0]['role'] == 'customer'
    
    def test_quote_api_workflow(self, client, app, db_models):
        """Test complete quote workflow via API."""
        db, Tenant, User, Quote = db_models
        
        with app.app_context():
            # Create tenant
            tenant_data = {'slug': 'quote-test', 'name': 'Quote Test Company'}
            client.post('/api/tenants', json=tenant_data, content_type='application/json')
            
            # Create quote
            quote_data = {
                'quote_number': 'Q-API-001',
                'customer_email': 'quote.customer@test.com',
                'customer_name': 'Quote Customer',
                'pickup_address': '123 Pickup St',
                'delivery_address': '456 Delivery Ave',
                'total_cubic_feet': 200.0,
                'total_amount': 1700.0
            }
            
            response = client.post('/api/quotes',
                                 json=quote_data,
                                 headers={'X-Tenant-Slug': 'quote-test'},
                                 content_type='application/json')
            
            assert response.status_code == 201
            created_quote = response.get_json()
            assert created_quote['quote_number'] == 'Q-API-001'
            assert created_quote['customer_email'] == 'quote.customer@test.com'
            assert created_quote['total_cubic_feet'] == 200.0
            
            # List quotes to verify
            quotes_response = client.get('/api/quotes', headers={'X-Tenant-Slug': 'quote-test'})
            assert quotes_response.status_code == 200
            quotes_list = quotes_response.get_json()
            assert len(quotes_list) == 1
            assert quotes_list[0]['quote_number'] == 'Q-API-001'
    
    def test_error_handling(self, client):
        """Test API error handling."""
        # Test missing tenant header
        response = client.get('/api/users')
        assert response.status_code == 400
        assert 'Tenant header required' in response.get_json()['error']
        
        # Test invalid tenant
        response = client.get('/api/users', headers={'X-Tenant-Slug': 'nonexistent'})
        assert response.status_code == 404
        assert 'Tenant not found' in response.get_json()['error']
    
    def test_data_validation(self, client, app, db_models):
        """Test data validation and constraints."""
        db, Tenant, User, Quote = db_models
        
        with app.app_context():
            # Create tenant
            tenant_data = {'slug': 'validation-test', 'name': 'Validation Test'}
            client.post('/api/tenants', json=tenant_data, content_type='application/json')
            
            # Create first user
            user_data = {'email': 'test@example.com', 'first_name': 'Test'}
            response1 = client.post('/api/users',
                                  json=user_data,
                                  headers={'X-Tenant-Slug': 'validation-test'},
                                  content_type='application/json')
            assert response1.status_code == 201
            
            # Try to create duplicate user (should fail)
            response2 = client.post('/api/users',
                                  json=user_data,
                                  headers={'X-Tenant-Slug': 'validation-test'},
                                  content_type='application/json')
            assert response2.status_code == 400
            assert 'User already exists' in response2.get_json()['error']


class TestMoveCRMBusiness:
    """Test business logic specific to moving companies."""
    
    def test_quote_number_generation(self):
        """Test quote number generation logic."""
        def generate_quote_number(year, month, sequence):
            return f"Q{year}{month:02d}{sequence:04d}"
        
        # Test various quote numbers
        assert generate_quote_number(2024, 1, 1) == "Q2024010001"
        assert generate_quote_number(2024, 12, 99) == "Q2024120099"
        assert generate_quote_number(2024, 6, 1234) == "Q2024061234"
    
    def test_pricing_calculation(self):
        """Test moving quote pricing calculation."""
        def calculate_quote_pricing(cubic_feet, rate_per_cubic_foot, 
                                  labor_hours, labor_rate, 
                                  distance_miles=0, distance_rate=0,
                                  minimum_charge=0, tax_rate=0.085):
            cubic_cost = cubic_feet * rate_per_cubic_foot
            labor_cost = labor_hours * labor_rate
            distance_cost = distance_miles * distance_rate
            
            subtotal = cubic_cost + labor_cost + distance_cost
            
            if subtotal < minimum_charge:
                subtotal = minimum_charge
            
            tax = subtotal * tax_rate
            total = subtotal + tax
            
            return {
                'cubic_cost': cubic_cost,
                'labor_cost': labor_cost,
                'distance_cost': distance_cost,
                'subtotal': subtotal,
                'tax': tax,
                'total': total
            }
        
        # Test normal pricing
        quote = calculate_quote_pricing(
            cubic_feet=100,
            rate_per_cubic_foot=8.50,
            labor_hours=6,
            labor_rate=85.00,
            distance_miles=20,
            distance_rate=2.50,
            minimum_charge=150.00
        )
        
        assert quote['cubic_cost'] == 850.00
        assert quote['labor_cost'] == 510.00
        assert quote['distance_cost'] == 50.00
        assert quote['subtotal'] == 1410.00
        assert abs(quote['tax'] - 119.85) < 0.01  # 8.5% tax
        assert abs(quote['total'] - 1529.85) < 0.01
        
        # Test minimum charge
        small_quote = calculate_quote_pricing(
            cubic_feet=5,
            rate_per_cubic_foot=8.50,
            labor_hours=0.5,
            labor_rate=85.00,
            minimum_charge=150.00
        )
        
        assert small_quote['subtotal'] == 150.00  # Minimum applied
    
    def test_role_based_access(self):
        """Test role-based access control logic."""
        def can_access_admin(user_role):
            return user_role == 'admin'
        
        def can_access_staff(user_role):
            return user_role in ['admin', 'staff']
        
        def can_manage_quotes(user_role):
            return user_role in ['admin', 'staff']
        
        def can_view_own_quotes(user_role):
            return user_role in ['admin', 'staff', 'customer']
        
        # Test admin access
        assert can_access_admin('admin') is True
        assert can_access_admin('staff') is False
        assert can_access_admin('customer') is False
        
        # Test staff access  
        assert can_access_staff('admin') is True
        assert can_access_staff('staff') is True
        assert can_access_staff('customer') is False
        
        # Test quote management
        assert can_manage_quotes('admin') is True
        assert can_manage_quotes('staff') is True
        assert can_manage_quotes('customer') is False
        
        # Test quote viewing
        assert can_view_own_quotes('admin') is True
        assert can_view_own_quotes('staff') is True
        assert can_view_own_quotes('customer') is True


# Run tests if called directly
if __name__ == '__main__':
    print("🧪 Running MoveCRM Test Suite...")
    print("=" * 60)
    
    # Run the tests
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])
    
    if exit_code == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 MoveCRM testing infrastructure is working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔧 Check the output above for details.")
    
    exit(exit_code)