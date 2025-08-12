"""
Unit tests for MoveCRM database models.
Tests model validation, relationships, and data integrity.
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
import uuid

from src.models import db, Tenant, User, ItemCatalog, PricingRule, Quote, QuoteItem, QuoteMedia, DetectionJob


@pytest.mark.unit
class TestTenantModel:
    """Test the Tenant model."""
    
    def test_tenant_creation(self, db_session):
        """Test creating a new tenant."""
        tenant = Tenant(
            slug='acme-moving',
            name='Acme Moving Company',
            domain='acme.movecrm.com'
        )
        db_session.add(tenant)
        db_session.commit()
        
        assert tenant.id is not None
        assert tenant.slug == 'acme-moving'
        assert tenant.name == 'Acme Moving Company'
        assert tenant.domain == 'acme.movecrm.com'
        assert tenant.is_active is True
        assert tenant.created_at is not None
        assert tenant.updated_at is not None
    
    def test_tenant_to_dict(self, sample_tenant):
        """Test tenant serialization."""
        tenant_dict = sample_tenant.to_dict()
        
        assert 'id' in tenant_dict
        assert tenant_dict['slug'] == 'test-company'
        assert tenant_dict['name'] == 'Test Moving Company'
        assert tenant_dict['domain'] == 'test-company.movecrm.com'
        assert tenant_dict['is_active'] is True
        assert 'created_at' in tenant_dict
        assert 'updated_at' in tenant_dict
    
    def test_tenant_unique_slug(self, db_session):
        """Test that tenant slugs must be unique."""
        tenant1 = Tenant(slug='test-slug', name='Company 1')
        tenant2 = Tenant(slug='test-slug', name='Company 2')
        
        db_session.add(tenant1)
        db_session.commit()
        
        db_session.add(tenant2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


@pytest.mark.unit
class TestUserModel:
    """Test the User model."""
    
    def test_user_creation(self, db_session, sample_tenant):
        """Test creating a new user."""
        user = User(
            tenant_id=sample_tenant.id,
            supertokens_user_id='user-123',
            email='john@example.com',
            first_name='John',
            last_name='Doe',
            phone='+1234567890',
            role='admin'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.tenant_id == sample_tenant.id
        assert user.email == 'john@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.role == 'admin'
        assert user.is_active is True
    
    def test_user_to_dict(self, sample_user):
        """Test user serialization."""
        user_dict = sample_user.to_dict()
        
        assert 'id' in user_dict
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['first_name'] == 'John'
        assert user_dict['last_name'] == 'Doe'
        assert user_dict['role'] == 'admin'
        assert user_dict['is_active'] is True
    
    def test_user_tenant_relationship(self, sample_user, sample_tenant):
        """Test user-tenant relationship."""
        assert sample_user.tenant == sample_tenant
        assert sample_user in sample_tenant.users
    
    def test_user_unique_email_per_tenant(self, db_session, sample_tenant):
        """Test that email must be unique per tenant."""
        user1 = User(
            tenant_id=sample_tenant.id,
            email='test@example.com',
            role='customer'
        )
        user2 = User(
            tenant_id=sample_tenant.id,
            email='test@example.com',
            role='admin'
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_user_same_email_different_tenants(self, db_session, test_data_factory):
        """Test that same email can exist across different tenants."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        user1 = User(
            tenant_id=tenant1.id,
            email='same@example.com',
            role='customer'
        )
        user2 = User(
            tenant_id=tenant2.id,
            email='same@example.com',
            role='customer'
        )
        
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()  # Should not raise an error
        
        assert user1.id != user2.id
        assert user1.email == user2.email
        assert user1.tenant_id != user2.tenant_id


@pytest.mark.unit
class TestItemCatalogModel:
    """Test the ItemCatalog model."""
    
    def test_item_catalog_creation(self, db_session, sample_tenant):
        """Test creating an item catalog entry."""
        item = ItemCatalog(
            tenant_id=sample_tenant.id,
            name='Dining Table',
            aliases=['Table', 'Kitchen Table'],
            category='Furniture',
            base_cubic_feet=Decimal('25.5'),
            labor_multiplier=Decimal('1.3')
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.name == 'Dining Table'
        assert item.aliases == ['Table', 'Kitchen Table']
        assert item.category == 'Furniture'
        assert item.base_cubic_feet == Decimal('25.5')
        assert item.labor_multiplier == Decimal('1.3')
        assert item.is_active is True
    
    def test_item_catalog_to_dict(self, sample_item_catalog):
        """Test item catalog serialization."""
        item = sample_item_catalog[0]  # First item (Sofa)
        item_dict = item.to_dict()
        
        assert item_dict['name'] == 'Sofa'
        assert item_dict['aliases'] == ['Couch', 'Sectional']
        assert item_dict['category'] == 'Furniture'
        assert item_dict['base_cubic_feet'] == 35.5
        assert item_dict['labor_multiplier'] == 1.2
        assert item_dict['is_active'] is True
    
    def test_item_catalog_tenant_isolation(self, db_session, test_data_factory):
        """Test that item catalogs are isolated per tenant."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        item1 = ItemCatalog(
            tenant_id=tenant1.id,
            name='Sofa',
            category='Furniture',
            base_cubic_feet=Decimal('35.0')
        )
        item2 = ItemCatalog(
            tenant_id=tenant2.id,
            name='Sofa',
            category='Furniture',
            base_cubic_feet=Decimal('40.0')
        )
        
        db_session.add(item1)
        db_session.add(item2)
        db_session.commit()
        
        # Both tenants can have items with the same name
        assert item1.name == item2.name
        assert item1.tenant_id != item2.tenant_id
        assert item1.base_cubic_feet != item2.base_cubic_feet


@pytest.mark.unit
class TestPricingRuleModel:
    """Test the PricingRule model."""
    
    def test_pricing_rule_creation(self, db_session, sample_tenant):
        """Test creating a pricing rule."""
        rule = PricingRule(
            tenant_id=sample_tenant.id,
            name='Premium Pricing',
            rate_per_cubic_foot=Decimal('10.00'),
            labor_rate_per_hour=Decimal('95.00'),
            minimum_charge=Decimal('200.00'),
            distance_rate_per_mile=Decimal('3.00'),
            is_default=False
        )
        db_session.add(rule)
        db_session.commit()
        
        assert rule.id is not None
        assert rule.name == 'Premium Pricing'
        assert rule.rate_per_cubic_foot == Decimal('10.00')
        assert rule.labor_rate_per_hour == Decimal('95.00')
        assert rule.minimum_charge == Decimal('200.00')
        assert rule.distance_rate_per_mile == Decimal('3.00')
        assert rule.is_default is False
        assert rule.is_active is True
    
    def test_pricing_rule_to_dict(self, sample_pricing_rule):
        """Test pricing rule serialization."""
        rule_dict = sample_pricing_rule.to_dict()
        
        assert rule_dict['name'] == 'Standard Pricing'
        assert rule_dict['rate_per_cubic_foot'] == 8.5
        assert rule_dict['labor_rate_per_hour'] == 85.0
        assert rule_dict['minimum_charge'] == 150.0
        assert rule_dict['distance_rate_per_mile'] == 2.5
        assert rule_dict['is_default'] is True
        assert rule_dict['is_active'] is True


@pytest.mark.unit
class TestQuoteModel:
    """Test the Quote model."""
    
    def test_quote_creation(self, db_session, sample_tenant, sample_customer, sample_pricing_rule):
        """Test creating a quote."""
        quote = Quote(
            tenant_id=sample_tenant.id,
            customer_id=sample_customer.id,
            quote_number='Q-2024-TEST-001',
            customer_email=sample_customer.email,
            customer_name='Jane Customer',
            pickup_address='123 Start St',
            delivery_address='456 End Ave',
            move_date=date(2024, 6, 15),
            total_cubic_feet=Decimal('120.5'),
            total_labor_hours=Decimal('6.5'),
            distance_miles=Decimal('15.0'),
            subtotal=Decimal('950.00'),
            tax_amount=Decimal('76.00'),
            total_amount=Decimal('1026.00'),
            pricing_rule_id=sample_pricing_rule.id
        )
        db_session.add(quote)
        db_session.commit()
        
        assert quote.id is not None
        assert quote.quote_number == 'Q-2024-TEST-001'
        assert quote.status == 'pending'
        assert quote.customer_email == sample_customer.email
        assert quote.move_date == date(2024, 6, 15)
        assert quote.total_cubic_feet == Decimal('120.5')
        assert quote.total_amount == Decimal('1026.00')
    
    def test_quote_to_dict(self, sample_quote):
        """Test quote serialization."""
        quote_dict = sample_quote.to_dict()
        
        assert quote_dict['quote_number'] == 'Q-2024-0001'
        assert quote_dict['status'] == 'pending'
        assert quote_dict['customer_email'] == 'customer@example.com'
        assert quote_dict['pickup_address'] == '123 Main St, City, State 12345'
        assert quote_dict['delivery_address'] == '456 Oak Ave, Another City, State 67890'
        assert quote_dict['total_cubic_feet'] == 150.0
        assert quote_dict['total_amount'] == 1377.0
    
    def test_quote_tenant_isolation(self, db_session, test_data_factory):
        """Test that quotes are isolated per tenant."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        customer1 = test_data_factory.create_user(db_session, tenant1)
        customer2 = test_data_factory.create_user(db_session, tenant2)
        
        quote1 = Quote(
            tenant_id=tenant1.id,
            customer_id=customer1.id,
            quote_number='Q-001',
            customer_email=customer1.email,
            customer_name='Customer 1',
            subtotal=Decimal('1000.00')
        )
        quote2 = Quote(
            tenant_id=tenant2.id,
            customer_id=customer2.id,
            quote_number='Q-001',
            customer_email=customer2.email,
            customer_name='Customer 2',
            subtotal=Decimal('1500.00')
        )
        
        db_session.add(quote1)
        db_session.add(quote2)
        db_session.commit()
        
        # Both tenants can have quotes with the same number
        assert quote1.quote_number == quote2.quote_number
        assert quote1.tenant_id != quote2.tenant_id
        assert quote1.subtotal != quote2.subtotal
    
    def test_quote_customer_relationship(self, sample_quote, sample_customer):
        """Test quote-customer relationship."""
        assert sample_quote.customer == sample_customer
        assert sample_quote in sample_customer.quotes
    
    def test_quote_pricing_rule_relationship(self, sample_quote, sample_pricing_rule):
        """Test quote-pricing rule relationship."""
        assert sample_quote.pricing_rule == sample_pricing_rule
        assert sample_quote in sample_pricing_rule.quotes


@pytest.mark.unit
class TestQuoteItemModel:
    """Test the QuoteItem model."""
    
    def test_quote_item_creation(self, db_session, sample_quote, sample_item_catalog):
        """Test creating a quote item."""
        item = sample_item_catalog[0]  # Sofa
        quote_item = QuoteItem(
            quote_id=sample_quote.id,
            item_catalog_id=item.id,
            detected_name='Sectional Sofa',
            quantity=1,
            cubic_feet=Decimal('38.0'),
            labor_hours=Decimal('2.5'),
            unit_price=Decimal('323.00'),
            total_price=Decimal('323.00'),
            confidence_score=Decimal('0.92')
        )
        db_session.add(quote_item)
        db_session.commit()
        
        assert quote_item.id is not None
        assert quote_item.detected_name == 'Sectional Sofa'
        assert quote_item.quantity == 1
        assert quote_item.cubic_feet == Decimal('38.0')
        assert quote_item.confidence_score == Decimal('0.92')
    
    def test_quote_item_to_dict(self, db_session, sample_quote, sample_item_catalog):
        """Test quote item serialization."""
        item = sample_item_catalog[0]
        quote_item = QuoteItem(
            quote_id=sample_quote.id,
            item_catalog_id=item.id,
            detected_name='Living Room Sofa',
            quantity=2,
            cubic_feet=Decimal('35.5'),
            unit_price=Decimal('300.00'),
            total_price=Decimal('600.00')
        )
        db_session.add(quote_item)
        db_session.commit()
        
        item_dict = quote_item.to_dict()
        assert item_dict['detected_name'] == 'Living Room Sofa'
        assert item_dict['quantity'] == 2
        assert item_dict['cubic_feet'] == 35.5
        assert item_dict['unit_price'] == 300.0
        assert item_dict['total_price'] == 600.0
    
    def test_quote_item_relationships(self, db_session, sample_quote, sample_item_catalog):
        """Test quote item relationships."""
        catalog_item = sample_item_catalog[1]  # Refrigerator
        quote_item = QuoteItem(
            quote_id=sample_quote.id,
            item_catalog_id=catalog_item.id,
            detected_name='Large Fridge',
            quantity=1,
            cubic_feet=Decimal('28.0')
        )
        db_session.add(quote_item)
        db_session.commit()
        
        assert quote_item.quote == sample_quote
        assert quote_item.catalog_item == catalog_item
        assert quote_item in sample_quote.quote_items


@pytest.mark.unit
class TestDetectionJobModel:
    """Test the DetectionJob model."""
    
    def test_detection_job_creation(self, db_session, sample_tenant, sample_quote):
        """Test creating a detection job."""
        job = DetectionJob(
            tenant_id=sample_tenant.id,
            quote_id=sample_quote.id,
            media_ids=[uuid.uuid4(), uuid.uuid4()],
            job_type='auto',
            status='pending',
            runpod_job_id='runpod-123'
        )
        db_session.add(job)
        db_session.commit()
        
        assert job.id is not None
        assert job.job_type == 'auto'
        assert job.status == 'pending'
        assert job.runpod_job_id == 'runpod-123'
        assert len(job.media_ids) == 2
    
    def test_detection_job_to_dict(self, db_session, sample_tenant):
        """Test detection job serialization."""
        media_id = uuid.uuid4()
        job = DetectionJob(
            tenant_id=sample_tenant.id,
            media_ids=[media_id],
            job_type='text',
            prompt='Detect furniture items',
            status='completed',
            results={'items': ['sofa', 'table']},
            error_message=None
        )
        db_session.add(job)
        db_session.commit()
        
        job_dict = job.to_dict()
        assert job_dict['job_type'] == 'text'
        assert job_dict['prompt'] == 'Detect furniture items'
        assert job_dict['status'] == 'completed'
        assert job_dict['results'] == {'items': ['sofa', 'table']}
        assert job_dict['media_ids'] == [str(media_id)]
    
    def test_detection_job_tenant_isolation(self, db_session, test_data_factory):
        """Test that detection jobs are isolated per tenant."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        job1 = DetectionJob(
            tenant_id=tenant1.id,
            job_type='auto',
            status='pending'
        )
        job2 = DetectionJob(
            tenant_id=tenant2.id,
            job_type='auto',
            status='pending'
        )
        
        db_session.add(job1)
        db_session.add(job2)
        db_session.commit()
        
        assert job1.tenant_id != job2.tenant_id
        assert job1.tenant == tenant1
        assert job2.tenant == tenant2


@pytest.mark.unit
class TestMultiTenantIsolation:
    """Test multi-tenant data isolation across all models."""
    
    def test_cross_tenant_data_access_prevention(self, db_session, test_data_factory):
        """Test that tenants cannot access each other's data."""
        # Create two tenants with complete data sets
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        user1 = test_data_factory.create_user(db_session, tenant1, role='admin')
        user2 = test_data_factory.create_user(db_session, tenant2, role='admin')
        
        # Query users for each tenant
        tenant1_users = User.query.filter_by(tenant_id=tenant1.id).all()
        tenant2_users = User.query.filter_by(tenant_id=tenant2.id).all()
        
        assert len(tenant1_users) == 1
        assert len(tenant2_users) == 1
        assert user1 in tenant1_users
        assert user1 not in tenant2_users
        assert user2 in tenant2_users
        assert user2 not in tenant1_users
    
    def test_cascade_delete_isolation(self, db_session, test_data_factory):
        """Test that deleting a tenant properly cleans up all related data."""
        tenant = test_data_factory.create_tenant(db_session)
        user = test_data_factory.create_user(db_session, tenant)
        
        # Create related data
        item = ItemCatalog(
            tenant_id=tenant.id,
            name='Test Item',
            category='Test'
        )
        rule = PricingRule(
            tenant_id=tenant.id,
            name='Test Rule',
            rate_per_cubic_foot=Decimal('10.0'),
            labor_rate_per_hour=Decimal('50.0')
        )
        quote = Quote(
            tenant_id=tenant.id,
            customer_id=user.id,
            quote_number='Q-TEST',
            customer_email=user.email,
            customer_name='Test Customer',
            pricing_rule_id=rule.id
        )
        
        db_session.add(item)
        db_session.add(rule)
        db_session.commit()
        db_session.add(quote)
        db_session.commit()
        
        tenant_id = tenant.id
        
        # Verify data exists
        assert User.query.filter_by(tenant_id=tenant_id).count() == 1
        assert ItemCatalog.query.filter_by(tenant_id=tenant_id).count() == 1
        assert PricingRule.query.filter_by(tenant_id=tenant_id).count() == 1
        assert Quote.query.filter_by(tenant_id=tenant_id).count() == 1
        
        # Delete tenant
        db_session.delete(tenant)
        db_session.commit()
        
        # Verify all related data is deleted
        assert User.query.filter_by(tenant_id=tenant_id).count() == 0
        assert ItemCatalog.query.filter_by(tenant_id=tenant_id).count() == 0
        assert PricingRule.query.filter_by(tenant_id=tenant_id).count() == 0
        assert Quote.query.filter_by(tenant_id=tenant_id).count() == 0