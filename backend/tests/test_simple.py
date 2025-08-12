"""
Simple test to verify testing infrastructure works.
"""
import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def test_basic_math():
    """Test basic mathematical operations."""
    assert 2 + 2 == 4
    assert 10 / 2 == 5
    assert 3 * 3 == 9


def test_string_operations():
    """Test basic string operations."""
    test_string = "MoveCRM Testing"
    assert len(test_string) == 15
    assert test_string.upper() == "MOVECRM TESTING"
    assert "Testing" in test_string


def test_flask_app_creation():
    """Test Flask app can be created."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Test a simple route
        @app.route('/test')
        def test_route():
            return {'message': 'Testing works!'}
        
        response = client.get('/test')
        assert response.status_code == 200


def test_sqlalchemy_basic():
    """Test SQLAlchemy basic functionality."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    class TestModel(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
    
    with app.app_context():
        db.create_all()
        
        # Create a record
        test_record = TestModel(name='Test Record')
        db.session.add(test_record)
        db.session.commit()
        
        # Query the record
        found_record = TestModel.query.filter_by(name='Test Record').first()
        assert found_record is not None
        assert found_record.name == 'Test Record'


def test_list_operations():
    """Test list operations."""
    test_list = [1, 2, 3, 4, 5]
    
    assert len(test_list) == 5
    assert 3 in test_list
    assert max(test_list) == 5
    assert sum(test_list) == 15
    
    # Test list comprehension
    squared = [x**2 for x in test_list]
    assert squared == [1, 4, 9, 16, 25]


def test_dictionary_operations():
    """Test dictionary operations."""
    test_dict = {
        'name': 'MoveCRM',
        'type': 'CRM System',
        'version': '1.0.0',
        'features': ['quotes', 'multi-tenant', 'auth']
    }
    
    assert test_dict['name'] == 'MoveCRM'
    assert len(test_dict['features']) == 3
    assert 'multi-tenant' in test_dict['features']
    assert 'version' in test_dict


@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
])
def test_double_function(input_val, expected):
    """Test a simple function with parametrized inputs."""
    def double(x):
        return x * 2
    
    assert double(input_val) == expected


def test_exception_handling():
    """Test exception handling."""
    def divide_by_zero():
        return 10 / 0
    
    with pytest.raises(ZeroDivisionError):
        divide_by_zero()


def test_multi_tenant_concept():
    """Test basic multi-tenant concept."""
    # Simulate tenant isolation
    tenant1_data = {'id': 1, 'name': 'Tenant 1', 'data': ['item1', 'item2']}
    tenant2_data = {'id': 2, 'name': 'Tenant 2', 'data': ['item3', 'item4']}
    
    # Data should be isolated
    assert tenant1_data['data'] != tenant2_data['data']
    assert len(tenant1_data['data']) == 2
    assert len(tenant2_data['data']) == 2
    
    # Test filtering by tenant
    all_data = [tenant1_data, tenant2_data]
    tenant1_filtered = [t for t in all_data if t['id'] == 1]
    
    assert len(tenant1_filtered) == 1
    assert tenant1_filtered[0]['name'] == 'Tenant 1'


def test_auth_concept():
    """Test basic authentication concept."""
    # Simulate user roles
    admin_user = {'id': 1, 'email': 'admin@test.com', 'role': 'admin'}
    staff_user = {'id': 2, 'email': 'staff@test.com', 'role': 'staff'}
    customer_user = {'id': 3, 'email': 'customer@test.com', 'role': 'customer'}
    
    def has_admin_access(user):
        return user['role'] == 'admin'
    
    def has_staff_access(user):
        return user['role'] in ['admin', 'staff']
    
    # Test role-based access
    assert has_admin_access(admin_user) is True
    assert has_admin_access(staff_user) is False
    assert has_admin_access(customer_user) is False
    
    assert has_staff_access(admin_user) is True
    assert has_staff_access(staff_user) is True
    assert has_staff_access(customer_user) is False


def test_quote_calculation_concept():
    """Test basic quote calculation concept."""
    # Simulate quote calculation
    def calculate_quote(cubic_feet, rate_per_cubic_foot, labor_hours, labor_rate, minimum_charge=0):
        cubic_cost = cubic_feet * rate_per_cubic_foot
        labor_cost = labor_hours * labor_rate
        subtotal = cubic_cost + labor_cost
        
        if subtotal < minimum_charge:
            subtotal = minimum_charge
        
        tax = subtotal * 0.085  # 8.5% tax
        total = subtotal + tax
        
        return {
            'cubic_cost': cubic_cost,
            'labor_cost': labor_cost,
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
    
    # Test calculation
    quote = calculate_quote(
        cubic_feet=100,
        rate_per_cubic_foot=8.50,
        labor_hours=5,
        labor_rate=85.00,
        minimum_charge=150.00
    )
    
    assert quote['cubic_cost'] == 850.00
    assert quote['labor_cost'] == 425.00
    assert quote['subtotal'] == 1275.00
    assert quote['tax'] == 108.375  # 8.5% of 1275
    assert abs(quote['total'] - 1383.375) < 0.01  # Allow for floating point precision


if __name__ == '__main__':
    pytest.main([__file__, '-v'])