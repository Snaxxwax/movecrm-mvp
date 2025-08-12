"""
Integration tests for authentication API endpoints.
Tests the full authentication flow including SuperTokens integration mocking.
"""
import pytest
import json
from unittest.mock import patch, Mock

from src.models import User, Tenant


@pytest.mark.integration
@pytest.mark.api
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_get_current_user_success(self, client, sample_tenant, sample_user, mock_supertokens):
        """Test getting current user information."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['email'] == sample_user.email
        assert data['first_name'] == sample_user.first_name
        assert data['role'] == sample_user.role
        assert 'tenant' in data
        assert data['tenant']['slug'] == sample_tenant.slug
    
    def test_get_current_user_no_tenant(self, client, mock_supertokens):
        """Test getting current user without tenant header."""
        headers = {'Authorization': 'Bearer fake-token'}
        
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Tenant not found' in data['error']
    
    def test_get_current_user_invalid_tenant(self, client, mock_supertokens):
        """Test getting current user with invalid tenant."""
        headers = {
            'X-Tenant-Slug': 'nonexistent-tenant',
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Tenant not found' in data['error']
    
    def test_get_current_user_no_auth(self, client, sample_tenant):
        """Test getting current user without authentication."""
        headers = {'X-Tenant-Slug': sample_tenant.slug}
        
        with patch('src.routes.auth.verify_session', return_value=None):
            response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'Authentication required' in data['error']


@pytest.mark.integration
@pytest.mark.api
class TestUserManagementAPI:
    """Test user management API endpoints."""
    
    def test_list_users_admin(self, client, sample_tenant, sample_user, sample_customer, mock_supertokens):
        """Test listing users as admin."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/auth/users', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert len(data['users']) == 2  # admin and customer
        
        # Check that both users belong to the same tenant
        for user in data['users']:
            assert user['tenant_id'] == str(sample_tenant.id)
    
    def test_list_users_with_role_filter(self, client, sample_tenant, sample_user, sample_customer, mock_supertokens):
        """Test listing users with role filter."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/auth/users?role=admin', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['users']) == 1
        assert data['users'][0]['role'] == 'admin'
        assert data['users'][0]['email'] == sample_user.email
    
    def test_list_users_pagination(self, client, sample_tenant, sample_user, mock_supertokens, db_session, test_data_factory):
        """Test user listing pagination."""
        # Create additional users
        for i in range(5):
            test_data_factory.create_user(
                db_session, sample_tenant,
                email=f'user{i}@example.com',
                role='customer'
            )
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/auth/users?page=1&per_page=3', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['users']) == 3
        assert data['current_page'] == 1
        assert data['per_page'] == 3
        assert data['total'] >= 6  # original user + customer + 5 new users
    
    def test_list_users_customer_forbidden(self, client, sample_tenant, sample_customer, mock_supertokens):
        """Test that customers cannot list users."""
        # Mock session to return customer user
        mock_supertokens['session'].get_user_id.return_value = sample_customer.supertokens_user_id
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/auth/users', headers=headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Insufficient permissions' in data['error']
    
    def test_get_specific_user_admin(self, client, sample_tenant, sample_user, sample_customer, mock_supertokens):
        """Test getting specific user as admin."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get(f'/api/auth/users/{sample_customer.id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(sample_customer.id)
        assert data['email'] == sample_customer.email
        assert data['role'] == sample_customer.role
    
    def test_get_user_cross_tenant_isolation(self, client, sample_tenant, sample_user, mock_supertokens, db_session, test_data_factory):
        """Test that users cannot access users from other tenants."""
        other_tenant = test_data_factory.create_tenant(db_session, slug='other-tenant')
        other_user = test_data_factory.create_user(db_session, other_tenant)
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        # Try to access user from other tenant
        response = client.get(f'/api/auth/users/{other_user.id}', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'User not found' in data['error']
    
    def test_create_user_admin(self, client, sample_tenant, sample_user, mock_supertokens):
        """Test creating a new user as admin."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        user_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '+1234567890',
            'role': 'staff'
        }
        
        response = client.post('/api/auth/users', 
                              headers=headers,
                              data=json.dumps(user_data))
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['email'] == 'newuser@example.com'
        assert data['first_name'] == 'New'
        assert data['role'] == 'staff'
        assert data['tenant_id'] == str(sample_tenant.id)
    
    def test_create_user_duplicate_email(self, client, sample_tenant, sample_user, sample_customer, mock_supertokens):
        """Test creating user with duplicate email in same tenant."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        user_data = {
            'email': sample_customer.email,  # Duplicate email
            'first_name': 'Duplicate',
            'last_name': 'User',
            'role': 'customer'
        }
        
        response = client.post('/api/auth/users',
                              headers=headers,
                              data=json.dumps(user_data))
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['error']
    
    def test_create_user_customer_forbidden(self, client, sample_tenant, sample_customer, mock_supertokens):
        """Test that customers cannot create users."""
        mock_supertokens['session'].get_user_id.return_value = sample_customer.supertokens_user_id
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        user_data = {
            'email': 'newuser@example.com',
            'role': 'customer'
        }
        
        response = client.post('/api/auth/users',
                              headers=headers,
                              data=json.dumps(user_data))
        
        assert response.status_code == 403
    
    def test_update_user_admin(self, client, sample_tenant, sample_user, sample_customer, mock_supertokens):
        """Test updating user as admin."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+1987654321',
            'role': 'staff'
        }
        
        response = client.put(f'/api/auth/users/{sample_customer.id}',
                             headers=headers,
                             data=json.dumps(update_data))
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['first_name'] == 'Updated'
        assert data['last_name'] == 'Name'
        assert data['phone'] == '+1987654321'
        assert data['role'] == 'staff'
    
    def test_update_user_cross_tenant_forbidden(self, client, sample_tenant, sample_user, mock_supertokens, db_session, test_data_factory):
        """Test that users cannot update users from other tenants."""
        other_tenant = test_data_factory.create_tenant(db_session, slug='other-tenant')
        other_user = test_data_factory.create_user(db_session, other_tenant)
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        update_data = {'first_name': 'Hacker'}
        
        response = client.put(f'/api/auth/users/{other_user.id}',
                             headers=headers,
                             data=json.dumps(update_data))
        
        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
class TestTenantManagementAPI:
    """Test tenant management API endpoints."""
    
    def test_get_current_tenant(self, client, sample_tenant, sample_user, mock_supertokens):
        """Test getting current tenant information."""
        headers = {'X-Tenant-Slug': sample_tenant.slug}
        
        response = client.get('/api/auth/tenants/current', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['slug'] == sample_tenant.slug
        assert data['name'] == sample_tenant.name
        assert data['domain'] == sample_tenant.domain
        assert data['is_active'] is True
    
    def test_get_current_tenant_no_tenant(self, client):
        """Test getting current tenant without tenant header."""
        response = client.get('/api/auth/tenants/current')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Tenant not found' in data['error']
    
    def test_update_tenant_admin(self, client, sample_tenant, sample_user, mock_supertokens):
        """Test updating tenant settings as admin."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        update_data = {
            'name': 'Updated Company Name',
            'logo_url': 'https://example.com/new-logo.png',
            'brand_colors': {'primary': '#ff0000', 'secondary': '#00ff00'},
            'settings': {'timezone': 'EST', 'currency': 'CAD'}
        }
        
        response = client.put('/api/auth/tenants/current',
                             headers=headers,
                             data=json.dumps(update_data))
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated Company Name'
        assert data['logo_url'] == 'https://example.com/new-logo.png'
        assert data['brand_colors']['primary'] == '#ff0000'
        assert data['settings']['timezone'] == 'EST'
    
    def test_update_tenant_customer_forbidden(self, client, sample_tenant, sample_customer, mock_supertokens):
        """Test that customers cannot update tenant settings."""
        mock_supertokens['session'].get_user_id.return_value = sample_customer.supertokens_user_id
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        update_data = {'name': 'Hacked Company'}
        
        response = client.put('/api/auth/tenants/current',
                             headers=headers,
                             data=json.dumps(update_data))
        
        assert response.status_code == 403


@pytest.mark.integration 
@pytest.mark.api
class TestMultiTenantIsolationAPI:
    """Test multi-tenant isolation at the API level."""
    
    def test_user_data_isolation(self, client, mock_supertokens, db_session, test_data_factory):
        """Test that API responses only include data for the current tenant."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        admin1 = test_data_factory.create_user(db_session, tenant1, role='admin')
        admin2 = test_data_factory.create_user(db_session, tenant2, role='admin')
        
        customer1 = test_data_factory.create_user(db_session, tenant1, role='customer')
        customer2 = test_data_factory.create_user(db_session, tenant2, role='customer')
        
        # Mock admin1 session
        mock_supertokens['session'].get_user_id.return_value = admin1.supertokens_user_id
        
        # Request as tenant1 admin
        headers1 = {
            'X-Tenant-Slug': 'tenant1',
            'Authorization': 'Bearer fake-token'
        }
        
        response1 = client.get('/api/auth/users', headers=headers1)
        assert response1.status_code == 200
        data1 = response1.get_json()
        
        # Should only see tenant1 users
        assert len(data1['users']) == 2
        user_emails = [user['email'] for user in data1['users']]
        assert admin1.email in user_emails
        assert customer1.email in user_emails
        assert admin2.email not in user_emails
        assert customer2.email not in user_emails
        
        # Mock admin2 session
        mock_supertokens['session'].get_user_id.return_value = admin2.supertokens_user_id
        
        # Request as tenant2 admin
        headers2 = {
            'X-Tenant-Slug': 'tenant2',
            'Authorization': 'Bearer fake-token'
        }
        
        response2 = client.get('/api/auth/users', headers=headers2)
        assert response2.status_code == 200
        data2 = response2.get_json()
        
        # Should only see tenant2 users
        assert len(data2['users']) == 2
        user_emails = [user['email'] for user in data2['users']]
        assert admin2.email in user_emails
        assert customer2.email in user_emails
        assert admin1.email not in user_emails
        assert customer1.email not in user_emails
    
    def test_cross_tenant_user_access_forbidden(self, client, mock_supertokens, db_session, test_data_factory):
        """Test that users cannot access resources from other tenants."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        admin1 = test_data_factory.create_user(db_session, tenant1, role='admin')
        user2 = test_data_factory.create_user(db_session, tenant2)
        
        mock_supertokens['session'].get_user_id.return_value = admin1.supertokens_user_id
        
        headers = {
            'X-Tenant-Slug': 'tenant1',
            'Authorization': 'Bearer fake-token'
        }
        
        # Try to access user from tenant2
        response = client.get(f'/api/auth/users/{user2.id}', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'User not found' in data['error']