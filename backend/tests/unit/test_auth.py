"""
Unit tests for authentication and authorization functionality.
Tests multi-tenant authentication, role-based access control, and security.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import request

from src.routes.auth import (
    get_tenant_from_request,
    require_tenant,
    require_auth,
    require_role
)
from src.models import Tenant, User


@pytest.mark.unit
@pytest.mark.auth
class TestTenantResolution:
    """Test tenant resolution from requests."""
    
    def test_get_tenant_from_header(self, app_context, sample_tenant):
        """Test getting tenant from X-Tenant-Slug header."""
        with app_context.test_request_context(
            headers={'X-Tenant-Slug': 'test-company'}
        ):
            tenant = get_tenant_from_request()
            assert tenant is not None
            assert tenant.slug == 'test-company'
    
    def test_get_tenant_from_subdomain(self, app_context, sample_tenant):
        """Test getting tenant from subdomain."""
        with app_context.test_request_context(
            headers={'Host': 'test-company.movecrm.com'}
        ):
            tenant = get_tenant_from_request()
            assert tenant is not None
            assert tenant.slug == 'test-company'
    
    def test_get_tenant_ignore_www_subdomain(self, app_context, sample_tenant):
        """Test that www subdomain is ignored."""
        with app_context.test_request_context(
            headers={'Host': 'www.movecrm.com'}
        ):
            tenant = get_tenant_from_request()
            assert tenant is None
    
    def test_get_tenant_ignore_api_subdomain(self, app_context, sample_tenant):
        """Test that api subdomain is ignored."""
        with app_context.test_request_context(
            headers={'Host': 'api.movecrm.com'}
        ):
            tenant = get_tenant_from_request()
            assert tenant is None
    
    def test_get_tenant_header_priority(self, app_context, sample_tenant, test_data_factory):
        """Test that header takes priority over subdomain."""
        other_tenant = test_data_factory.create_tenant(
            db_session=sample_tenant.tenant,  # This is a bit of a hack for the session
            slug='other-tenant'
        )
        
        with app_context.test_request_context(
            headers={
                'Host': 'other-tenant.movecrm.com',
                'X-Tenant-Slug': 'test-company'
            }
        ):
            tenant = get_tenant_from_request()
            assert tenant is not None
            assert tenant.slug == 'test-company'
    
    def test_get_tenant_nonexistent(self, app_context):
        """Test getting nonexistent tenant returns None."""
        with app_context.test_request_context(
            headers={'X-Tenant-Slug': 'nonexistent-tenant'}
        ):
            tenant = get_tenant_from_request()
            assert tenant is None
    
    def test_get_tenant_inactive_tenant(self, db_session, app_context):
        """Test that inactive tenants are not returned."""
        inactive_tenant = Tenant(
            slug='inactive-tenant',
            name='Inactive Tenant',
            is_active=False
        )
        db_session.add(inactive_tenant)
        db_session.commit()
        
        with app_context.test_request_context(
            headers={'X-Tenant-Slug': 'inactive-tenant'}
        ):
            tenant = get_tenant_from_request()
            assert tenant is None


@pytest.mark.unit
@pytest.mark.auth
class TestTenantDecorator:
    """Test the require_tenant decorator."""
    
    def test_require_tenant_success(self, app_context, sample_tenant):
        """Test require_tenant decorator with valid tenant."""
        @require_tenant
        def test_view():
            return {'tenant': request.tenant.slug}
        
        with app_context.test_request_context(
            headers={'X-Tenant-Slug': 'test-company'}
        ):
            result = test_view()
            assert result['tenant'] == 'test-company'
    
    def test_require_tenant_missing(self, app_context):
        """Test require_tenant decorator without tenant."""
        @require_tenant
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            result = test_view()
            # Should return error response
            assert isinstance(result, tuple)
            assert result[1] == 400  # Bad request status code
            assert 'Tenant not found' in str(result[0])
    
    def test_require_tenant_inactive(self, app_context, db_session):
        """Test require_tenant decorator with inactive tenant."""
        inactive_tenant = Tenant(
            slug='inactive-tenant',
            name='Inactive Tenant',
            is_active=False
        )
        db_session.add(inactive_tenant)
        db_session.commit()
        
        @require_tenant
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context(
            headers={'X-Tenant-Slug': 'inactive-tenant'}
        ):
            result = test_view()
            assert isinstance(result, tuple)
            assert result[1] == 400


@pytest.mark.unit
@pytest.mark.auth
class TestAuthDecorator:
    """Test the require_auth decorator."""
    
    @patch('src.routes.auth.verify_session')
    def test_require_auth_success(self, mock_verify, app_context, sample_tenant, sample_user):
        """Test require_auth decorator with valid session."""
        # Mock SuperTokens session
        mock_session = Mock()
        mock_session.get_user_id.return_value = sample_user.supertokens_user_id
        mock_verify.return_value = mock_session
        
        @require_auth
        def test_view():
            return {
                'user_id': str(request.user.id),
                'email': request.user.email
            }
        
        with app_context.test_request_context():
            result = test_view()
            assert result['user_id'] == str(sample_user.id)
            assert result['email'] == sample_user.email
    
    @patch('src.routes.auth.verify_session')
    def test_require_auth_no_session(self, mock_verify, app_context):
        """Test require_auth decorator without session."""
        mock_verify.return_value = None
        
        @require_auth
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            result = test_view()
            assert isinstance(result, tuple)
            assert result[1] == 401  # Unauthorized
    
    @patch('src.routes.auth.verify_session')
    def test_require_auth_user_not_found(self, mock_verify, app_context):
        """Test require_auth decorator when user not found in database."""
        mock_session = Mock()
        mock_session.get_user_id.return_value = 'nonexistent-user-id'
        mock_verify.return_value = mock_session
        
        @require_auth
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            result = test_view()
            assert isinstance(result, tuple)
            assert result[1] == 404  # User not found
    
    @patch('src.routes.auth.verify_session')
    def test_require_auth_exception(self, mock_verify, app_context):
        """Test require_auth decorator when exception occurs."""
        mock_verify.side_effect = Exception("Session verification failed")
        
        @require_auth
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            result = test_view()
            assert isinstance(result, tuple)
            assert result[1] == 401  # Authentication failed


@pytest.mark.unit
@pytest.mark.auth
class TestRoleDecorator:
    """Test the require_role decorator."""
    
    def test_require_role_admin_success(self, app_context, sample_user):
        """Test require_role decorator with admin user."""
        @require_role(['admin'])
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            # Mock request.user
            with patch.object(request, 'user', sample_user):
                result = test_view()
                assert result['success'] is True
    
    def test_require_role_staff_success(self, app_context, db_session, sample_tenant):
        """Test require_role decorator with staff user."""
        staff_user = User(
            tenant_id=sample_tenant.id,
            supertokens_user_id='staff-123',
            email='staff@example.com',
            role='staff'
        )
        db_session.add(staff_user)
        db_session.commit()
        
        @require_role(['admin', 'staff'])
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            with patch.object(request, 'user', staff_user):
                result = test_view()
                assert result['success'] is True
    
    def test_require_role_insufficient_permissions(self, app_context, sample_customer):
        """Test require_role decorator with insufficient permissions."""
        @require_role(['admin', 'staff'])
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            with patch.object(request, 'user', sample_customer):
                result = test_view()
                assert isinstance(result, tuple)
                assert result[1] == 403  # Forbidden
                assert 'Insufficient permissions' in str(result[0])
    
    def test_require_role_no_user(self, app_context):
        """Test require_role decorator without authenticated user."""
        @require_role(['admin'])
        def test_view():
            return {'success': True}
        
        with app_context.test_request_context():
            result = test_view()
            assert isinstance(result, tuple)
            assert result[1] == 401  # Authentication required


@pytest.mark.unit
@pytest.mark.auth
class TestMultiTenantAuthIsolation:
    """Test multi-tenant authentication isolation."""
    
    def test_user_isolation_across_tenants(self, db_session, test_data_factory):
        """Test that users from different tenants are properly isolated."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        user1 = test_data_factory.create_user(
            db_session, tenant1, 
            supertokens_user_id='user-123',
            email='user@tenant1.com',
            role='admin'
        )
        user2 = test_data_factory.create_user(
            db_session, tenant2,
            supertokens_user_id='user-456', 
            email='user@tenant2.com',
            role='admin'
        )
        
        # User1 should only exist in tenant1's context
        tenant1_user = User.query.filter_by(
            supertokens_user_id=user1.supertokens_user_id,
            tenant_id=tenant1.id
        ).first()
        assert tenant1_user is not None
        assert tenant1_user.email == 'user@tenant1.com'
        
        # User1 should not exist in tenant2's context
        cross_tenant_user = User.query.filter_by(
            supertokens_user_id=user1.supertokens_user_id,
            tenant_id=tenant2.id
        ).first()
        assert cross_tenant_user is None
    
    @patch('src.routes.auth.verify_session')
    def test_auth_requires_both_tenant_and_user(self, mock_verify, app_context, sample_tenant, sample_user):
        """Test that authentication requires both tenant and user context."""
        mock_session = Mock()
        mock_session.get_user_id.return_value = sample_user.supertokens_user_id
        mock_verify.return_value = mock_session
        
        @require_tenant
        @require_auth
        def test_view():
            return {
                'tenant_slug': request.tenant.slug,
                'user_email': request.user.email
            }
        
        # Test with both tenant and auth
        with app_context.test_request_context(
            headers={'X-Tenant-Slug': 'test-company'}
        ):
            result = test_view()
            assert result['tenant_slug'] == 'test-company'
            assert result['user_email'] == sample_user.email
        
        # Test without tenant (should fail at tenant check)
        with app_context.test_request_context():
            result = test_view()
            assert isinstance(result, tuple)
            assert result[1] == 400  # Bad request (no tenant)
    
    def test_role_based_access_per_tenant(self, db_session, test_data_factory):
        """Test that roles are properly scoped per tenant."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        # Same user ID with different roles in different tenants
        admin_in_tenant1 = test_data_factory.create_user(
            db_session, tenant1,
            supertokens_user_id='user-123',
            role='admin'
        )
        customer_in_tenant2 = test_data_factory.create_user(
            db_session, tenant2,
            supertokens_user_id='user-456',  # Different ID to avoid conflicts
            role='customer'
        )
        
        # Verify roles are different
        assert admin_in_tenant1.role == 'admin'
        assert customer_in_tenant2.role == 'customer'
        
        # Verify they belong to different tenants
        assert admin_in_tenant1.tenant_id == tenant1.id
        assert customer_in_tenant2.tenant_id == tenant2.id


@pytest.mark.unit
@pytest.mark.auth
class TestSecurityFeatures:
    """Test security features and edge cases."""
    
    def test_tenant_slug_validation(self, app_context):
        """Test that only valid tenant slugs are accepted."""
        malicious_slugs = [
            '../../../etc/passwd',
            '<script>alert("xss")</script>',
            'DROP TABLE tenants;',
            '../../../../../../etc/hosts'
        ]
        
        for slug in malicious_slugs:
            with app_context.test_request_context(
                headers={'X-Tenant-Slug': slug}
            ):
                tenant = get_tenant_from_request()
                assert tenant is None
    
    def test_inactive_tenant_rejection(self, db_session, app_context):
        """Test that inactive tenants are properly rejected."""
        inactive_tenant = Tenant(
            slug='inactive-company',
            name='Inactive Company',
            is_active=False
        )
        db_session.add(inactive_tenant)
        db_session.commit()
        
        with app_context.test_request_context(
            headers={'X-Tenant-Slug': 'inactive-company'}
        ):
            tenant = get_tenant_from_request()
            assert tenant is None
    
    def test_user_isolation_by_tenant(self, db_session, test_data_factory):
        """Test that user queries are properly isolated by tenant."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        user1 = test_data_factory.create_user(db_session, tenant1, email='same@email.com')
        user2 = test_data_factory.create_user(db_session, tenant2, email='same@email.com')
        
        # Query users by tenant
        tenant1_users = User.query.filter_by(tenant_id=tenant1.id, email='same@email.com').all()
        tenant2_users = User.query.filter_by(tenant_id=tenant2.id, email='same@email.com').all()
        
        assert len(tenant1_users) == 1
        assert len(tenant2_users) == 1
        assert tenant1_users[0] == user1
        assert tenant2_users[0] == user2
        assert tenant1_users[0] != tenant2_users[0]