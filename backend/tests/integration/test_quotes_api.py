"""
Integration tests for quotes API endpoints.
Tests the complete quote management flow including pricing calculations.
"""
import pytest
import json
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch

from src.models import Quote, QuoteItem, PricingRule, ItemCatalog
from src.routes.quotes import generate_quote_number, calculate_quote_pricing


@pytest.mark.integration
@pytest.mark.api
class TestQuotesAPI:
    """Test quotes API endpoints."""
    
    def test_list_quotes_admin(self, client, sample_tenant, sample_user, sample_quote, mock_supertokens):
        """Test listing quotes as admin."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/quotes/', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'quotes' in data
        assert len(data['quotes']) >= 1
        assert data['quotes'][0]['quote_number'] == sample_quote.quote_number
        assert data['quotes'][0]['tenant_id'] == str(sample_tenant.id)
    
    def test_list_quotes_with_filters(self, client, sample_tenant, sample_user, mock_supertokens, db_session, test_data_factory):
        """Test listing quotes with status and email filters."""
        # Create additional quotes with different statuses
        customer1 = test_data_factory.create_user(db_session, sample_tenant, email='customer1@test.com')
        customer2 = test_data_factory.create_user(db_session, sample_tenant, email='customer2@test.com')
        
        quote1 = Quote(
            tenant_id=sample_tenant.id,
            customer_id=customer1.id,
            quote_number='Q-TEST-001',
            status='pending',
            customer_email=customer1.email,
            customer_name='Customer 1'
        )
        quote2 = Quote(
            tenant_id=sample_tenant.id,
            customer_id=customer2.id,
            quote_number='Q-TEST-002',
            status='approved',
            customer_email=customer2.email,
            customer_name='Customer 2'
        )
        
        db_session.add(quote1)
        db_session.add(quote2)
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        # Test status filter
        response = client.get('/api/quotes/?status=pending', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        pending_quotes = data['quotes']
        assert all(quote['status'] == 'pending' for quote in pending_quotes)
        
        # Test email filter
        response = client.get('/api/quotes/?customer_email=customer1', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        filtered_quotes = data['quotes']
        assert len(filtered_quotes) >= 1
        assert any('customer1@test.com' in quote['customer_email'] for quote in filtered_quotes)
    
    def test_list_quotes_pagination(self, client, sample_tenant, sample_user, mock_supertokens, db_session):
        """Test quotes pagination."""
        # Create multiple quotes
        for i in range(25):
            quote = Quote(
                tenant_id=sample_tenant.id,
                quote_number=f'Q-TEST-{i:03d}',
                customer_email=f'customer{i}@test.com',
                customer_name=f'Customer {i}'
            )
            db_session.add(quote)
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/quotes/?page=1&per_page=10', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        
        assert len(data['quotes']) == 10
        assert data['current_page'] == 1
        assert data['per_page'] == 10
        assert data['total'] >= 25
        assert data['pages'] >= 3
    
    def test_list_quotes_customer_forbidden(self, client, sample_tenant, sample_customer, mock_supertokens):
        """Test that customers cannot list all quotes."""
        mock_supertokens['session'].get_user_id.return_value = sample_customer.supertokens_user_id
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get('/api/quotes/', headers=headers)
        assert response.status_code == 403
    
    def test_get_quote_with_details(self, client, sample_tenant, sample_user, sample_quote, mock_supertokens, db_session):
        """Test getting a specific quote with items and media."""
        # Add quote items
        quote_item = QuoteItem(
            quote_id=sample_quote.id,
            detected_name='Test Sofa',
            quantity=1,
            cubic_feet=Decimal('35.5'),
            labor_hours=Decimal('2.0'),
            unit_price=Decimal('300.00'),
            total_price=Decimal('300.00')
        )
        db_session.add(quote_item)
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.get(f'/api/quotes/{sample_quote.id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(sample_quote.id)
        assert data['quote_number'] == sample_quote.quote_number
        assert 'items' in data
        assert len(data['items']) == 1
        assert data['items'][0]['detected_name'] == 'Test Sofa'
        assert 'media' in data
    
    def test_get_quote_cross_tenant_isolation(self, client, sample_tenant, sample_user, mock_supertokens, db_session, test_data_factory):
        """Test that quotes are isolated by tenant."""
        other_tenant = test_data_factory.create_tenant(db_session, slug='other-tenant')
        other_customer = test_data_factory.create_user(db_session, other_tenant)
        
        other_quote = Quote(
            tenant_id=other_tenant.id,
            customer_id=other_customer.id,
            quote_number='Q-OTHER-001',
            customer_email=other_customer.email,
            customer_name='Other Customer'
        )
        db_session.add(other_quote)
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        # Try to access quote from other tenant
        response = client.get(f'/api/quotes/{other_quote.id}', headers=headers)
        assert response.status_code == 404
    
    def test_create_quote_success(self, client, sample_tenant, sample_user, sample_pricing_rule, mock_supertokens):
        """Test creating a new quote successfully."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        quote_data = {
            'customer_email': 'newcustomer@example.com',
            'customer_name': 'New Customer',
            'customer_phone': '+1234567890',
            'pickup_address': '123 Start St, City, State',
            'delivery_address': '456 End Ave, City, State',
            'move_date': '2024-07-01',
            'notes': 'Handle with care',
            'distance_miles': 15.5,
            'items': [
                {
                    'detected_name': 'Large Sofa',
                    'quantity': 1,
                    'cubic_feet': 40.0,
                    'labor_hours': 2.5,
                    'unit_price': 340.00,
                    'total_price': 340.00
                },
                {
                    'detected_name': 'Dining Table',
                    'quantity': 1,
                    'cubic_feet': 25.0,
                    'labor_hours': 1.5,
                    'unit_price': 212.50,
                    'total_price': 212.50
                }
            ]
        }
        
        response = client.post('/api/quotes/', 
                              headers=headers,
                              data=json.dumps(quote_data))
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['customer_email'] == 'newcustomer@example.com'
        assert data['customer_name'] == 'New Customer'
        assert data['pickup_address'] == '123 Start St, City, State'
        assert data['move_date'] == '2024-07-01'
        assert data['distance_miles'] == 15.5
        assert data['status'] == 'pending'
        assert 'quote_number' in data
        
        # Check that pricing was calculated
        assert float(data['total_cubic_feet']) == 65.0
        assert float(data['total_labor_hours']) == 4.0
        assert float(data['subtotal']) > 0
        assert float(data['total_amount']) > float(data['subtotal'])  # Including tax
    
    def test_create_quote_no_pricing_rule(self, client, sample_tenant, sample_user, mock_supertokens, db_session):
        """Test creating quote when no default pricing rule exists."""
        # Remove default pricing rule
        PricingRule.query.filter_by(tenant_id=sample_tenant.id).delete()
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        quote_data = {
            'customer_email': 'test@example.com',
            'customer_name': 'Test Customer'
        }
        
        response = client.post('/api/quotes/',
                              headers=headers,
                              data=json.dumps(quote_data))
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'No default pricing rule found' in data['error']
    
    def test_create_quote_with_catalog_matching(self, client, sample_tenant, sample_user, sample_pricing_rule, sample_item_catalog, mock_supertokens):
        """Test creating quote with catalog item matching."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        quote_data = {
            'customer_email': 'catalog@example.com',
            'customer_name': 'Catalog Customer',
            'items': [
                {
                    'detected_name': 'Couch',  # Should match 'Sofa' alias
                    'quantity': 1
                }
            ]
        }
        
        response = client.post('/api/quotes/',
                              headers=headers,
                              data=json.dumps(quote_data))
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify the item was matched with catalog
        quote = Quote.query.filter_by(id=data['id']).first()
        quote_items = quote.quote_items
        assert len(quote_items) == 1
        
        item = quote_items[0]
        assert item.detected_name == 'Couch'
        assert item.item_catalog_id is not None
        assert float(item.cubic_feet) == 35.5  # From catalog
    
    def test_update_quote_success(self, client, sample_tenant, sample_user, sample_quote, mock_supertokens):
        """Test updating a quote successfully."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        update_data = {
            'customer_name': 'Updated Customer Name',
            'pickup_address': '789 New Address, City, State',
            'move_date': '2024-08-15',
            'status': 'approved',
            'distance_miles': 25.0,
            'notes': 'Updated notes'
        }
        
        response = client.put(f'/api/quotes/{sample_quote.id}',
                             headers=headers,
                             data=json.dumps(update_data))
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['customer_name'] == 'Updated Customer Name'
        assert data['pickup_address'] == '789 New Address, City, State'
        assert data['move_date'] == '2024-08-15'
        assert data['status'] == 'approved'
        assert data['distance_miles'] == 25.0
        assert data['notes'] == 'Updated notes'
    
    def test_update_quote_cross_tenant_forbidden(self, client, sample_tenant, sample_user, mock_supertokens, db_session, test_data_factory):
        """Test that users cannot update quotes from other tenants."""
        other_tenant = test_data_factory.create_tenant(db_session, slug='other-tenant')
        other_customer = test_data_factory.create_user(db_session, other_tenant)
        
        other_quote = Quote(
            tenant_id=other_tenant.id,
            customer_id=other_customer.id,
            quote_number='Q-OTHER-001',
            customer_email=other_customer.email,
            customer_name='Other Customer'
        )
        db_session.add(other_quote)
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        update_data = {'customer_name': 'Hacked Name'}
        
        response = client.put(f'/api/quotes/{other_quote.id}',
                             headers=headers,
                             data=json.dumps(update_data))
        
        assert response.status_code == 404
    
    def test_add_quote_item_success(self, client, sample_tenant, sample_user, sample_quote, mock_supertokens):
        """Test adding an item to a quote."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        item_data = {
            'detected_name': 'New Item',
            'quantity': 2,
            'cubic_feet': 15.0,
            'labor_hours': 1.0,
            'unit_price': 127.50,
            'total_price': 255.00
        }
        
        response = client.post(f'/api/quotes/{sample_quote.id}/items',
                              headers=headers,
                              data=json.dumps(item_data))
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['detected_name'] == 'New Item'
        assert data['quantity'] == 2
        assert data['cubic_feet'] == 15.0
        assert data['total_price'] == 255.0
    
    def test_add_quote_item_with_catalog(self, client, sample_tenant, sample_user, sample_quote, sample_item_catalog, mock_supertokens):
        """Test adding an item using catalog reference."""
        catalog_item = sample_item_catalog[0]  # Sofa
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        item_data = {
            'catalog_item_id': str(catalog_item.id),
            'quantity': 1
        }
        
        response = client.post(f'/api/quotes/{sample_quote.id}/items',
                              headers=headers,
                              data=json.dumps(item_data))
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['detected_name'] == catalog_item.name
        assert data['cubic_feet'] == float(catalog_item.base_cubic_feet)
        assert data['item_catalog_id'] == str(catalog_item.id)
    
    def test_remove_quote_item_success(self, client, sample_tenant, sample_user, sample_quote, mock_supertokens, db_session):
        """Test removing an item from a quote."""
        # Add an item first
        quote_item = QuoteItem(
            quote_id=sample_quote.id,
            detected_name='Item to Remove',
            quantity=1,
            cubic_feet=Decimal('20.0'),
            total_price=Decimal('170.00')
        )
        db_session.add(quote_item)
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.delete(f'/api/quotes/{sample_quote.id}/items/{quote_item.id}',
                                headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'successfully' in data['message']
        
        # Verify item was deleted
        deleted_item = QuoteItem.query.filter_by(id=quote_item.id).first()
        assert deleted_item is None
    
    def test_recalculate_quote_pricing(self, client, sample_tenant, sample_user, sample_quote, mock_supertokens, db_session):
        """Test recalculating quote pricing."""
        # Add some items to the quote
        item1 = QuoteItem(
            quote_id=sample_quote.id,
            detected_name='Item 1',
            quantity=1,
            cubic_feet=Decimal('30.0'),
            labor_hours=Decimal('2.0')
        )
        item2 = QuoteItem(
            quote_id=sample_quote.id,
            detected_name='Item 2',
            quantity=2,
            cubic_feet=Decimal('15.0'),
            labor_hours=Decimal('1.0')
        )
        db_session.add(item1)
        db_session.add(item2)
        db_session.commit()
        
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token'
        }
        
        response = client.post(f'/api/quotes/{sample_quote.id}/recalculate',
                              headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check that totals were recalculated
        assert float(data['total_cubic_feet']) == 60.0  # 30 + (15 * 2)
        assert float(data['total_labor_hours']) == 4.0   # 2 + (1 * 2)
        assert float(data['subtotal']) > 0
        assert float(data['total_amount']) > float(data['subtotal'])


@pytest.mark.integration
@pytest.mark.api
class TestQuotePricingLogic:
    """Test quote pricing calculation logic."""
    
    def test_pricing_calculation_basic(self, db_session, sample_tenant, sample_pricing_rule):
        """Test basic pricing calculation."""
        quote = Quote(
            tenant_id=sample_tenant.id,
            quote_number='Q-PRICE-001',
            customer_email='price@test.com',
            distance_miles=Decimal('20.0'),
            pricing_rule_id=sample_pricing_rule.id
        )
        
        # Add items
        item1 = QuoteItem(
            quote=quote,
            detected_name='Item 1',
            quantity=1,
            cubic_feet=Decimal('25.0'),
            labor_hours=Decimal('2.0')
        )
        item2 = QuoteItem(
            quote=quote,
            detected_name='Item 2',
            quantity=2,
            cubic_feet=Decimal('15.0'),
            labor_hours=Decimal('1.5')
        )
        
        quote.quote_items = [item1, item2]
        
        # Calculate pricing
        updated_quote = calculate_quote_pricing(quote, sample_pricing_rule)
        
        # Verify totals
        assert updated_quote.total_cubic_feet == Decimal('55.0')  # 25 + (15 * 2)
        assert updated_quote.total_labor_hours == Decimal('5.0')  # 2 + (1.5 * 2)
        
        # Verify cost calculation
        expected_cubic_cost = Decimal('55.0') * sample_pricing_rule.rate_per_cubic_foot  # 55 * 8.50
        expected_labor_cost = Decimal('5.0') * sample_pricing_rule.labor_rate_per_hour    # 5 * 85.00
        expected_distance_cost = Decimal('20.0') * sample_pricing_rule.distance_rate_per_mile  # 20 * 2.50
        expected_subtotal = expected_cubic_cost + expected_labor_cost + expected_distance_cost
        
        assert updated_quote.subtotal == expected_subtotal
        
        # Check tax calculation (8.5%)
        expected_tax = expected_subtotal * Decimal('0.085')
        assert updated_quote.tax_amount == expected_tax
        assert updated_quote.total_amount == expected_subtotal + expected_tax
    
    def test_pricing_minimum_charge_applied(self, db_session, sample_tenant, sample_pricing_rule):
        """Test that minimum charge is applied when subtotal is too low."""
        quote = Quote(
            tenant_id=sample_tenant.id,
            quote_number='Q-PRICE-002',
            customer_email='minprice@test.com',
            pricing_rule_id=sample_pricing_rule.id
        )
        
        # Add a small item that would result in cost below minimum
        item = QuoteItem(
            quote=quote,
            detected_name='Small Item',
            quantity=1,
            cubic_feet=Decimal('5.0'),
            labor_hours=Decimal('0.5')
        )
        
        quote.quote_items = [item]
        
        updated_quote = calculate_quote_pricing(quote, sample_pricing_rule)
        
        # Calculate what the cost would be without minimum
        cubic_cost = Decimal('5.0') * sample_pricing_rule.rate_per_cubic_foot
        labor_cost = Decimal('0.5') * sample_pricing_rule.labor_rate_per_hour
        calculated_cost = cubic_cost + labor_cost
        
        # Should be below minimum charge
        assert calculated_cost < sample_pricing_rule.minimum_charge
        
        # Subtotal should be the minimum charge
        assert updated_quote.subtotal == sample_pricing_rule.minimum_charge
    
    def test_quote_number_generation(self, db_session, sample_tenant):
        """Test quote number generation is unique and sequential."""
        # Generate first quote number
        quote_num1 = generate_quote_number(sample_tenant.id)
        
        # Create a quote with this number
        quote1 = Quote(
            tenant_id=sample_tenant.id,
            quote_number=quote_num1,
            customer_email='test1@example.com'
        )
        db_session.add(quote1)
        db_session.commit()
        
        # Generate second quote number
        quote_num2 = generate_quote_number(sample_tenant.id)
        
        # Should be sequential
        assert quote_num1 != quote_num2
        
        # Extract sequence numbers (assuming format Q[YYYY][MM][NNNN])
        sequence1 = int(quote_num1[-4:])
        sequence2 = int(quote_num2[-4:])
        assert sequence2 == sequence1 + 1
    
    def test_quote_number_isolation_by_tenant(self, db_session, test_data_factory):
        """Test that quote numbers are isolated by tenant."""
        tenant1 = test_data_factory.create_tenant(db_session, slug='tenant1')
        tenant2 = test_data_factory.create_tenant(db_session, slug='tenant2')
        
        # Generate quote numbers for both tenants
        quote_num1 = generate_quote_number(tenant1.id)
        quote_num2 = generate_quote_number(tenant2.id)
        
        # Should both start at sequence 1 for their respective tenants
        assert quote_num1[-4:] == '0001'
        assert quote_num2[-4:] == '0001'
        
        # Create quotes
        quote1 = Quote(
            tenant_id=tenant1.id,
            quote_number=quote_num1,
            customer_email='test1@tenant1.com'
        )
        quote2 = Quote(
            tenant_id=tenant2.id,
            quote_number=quote_num2,
            customer_email='test1@tenant2.com'
        )
        
        db_session.add(quote1)
        db_session.add(quote2)
        db_session.commit()
        
        # Generate next numbers
        next_num1 = generate_quote_number(tenant1.id)
        next_num2 = generate_quote_number(tenant2.id)
        
        # Should be sequential within each tenant
        assert next_num1[-4:] == '0002'
        assert next_num2[-4:] == '0002'


@pytest.mark.integration
@pytest.mark.api
class TestQuoteBusinessLogic:
    """Test quote business logic and edge cases."""
    
    def test_quote_with_existing_customer_link(self, client, sample_tenant, sample_user, sample_pricing_rule, sample_customer, mock_supertokens):
        """Test that quotes are linked to existing customers."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        quote_data = {
            'customer_email': sample_customer.email,  # Existing customer
            'customer_name': 'Different Name'  # Different from customer's actual name
        }
        
        response = client.post('/api/quotes/',
                              headers=headers,
                              data=json.dumps(quote_data))
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should link to existing customer
        assert data['customer_id'] == str(sample_customer.id)
        assert data['customer_email'] == sample_customer.email
    
    def test_quote_without_existing_customer(self, client, sample_tenant, sample_user, sample_pricing_rule, mock_supertokens):
        """Test creating quote for non-existing customer."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        quote_data = {
            'customer_email': 'nonexistent@example.com',
            'customer_name': 'New Customer'
        }
        
        response = client.post('/api/quotes/',
                              headers=headers,
                              data=json.dumps(quote_data))
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should not link to any customer
        assert data['customer_id'] is None
        assert data['customer_email'] == 'nonexistent@example.com'
    
    def test_quote_expiration_set(self, client, sample_tenant, sample_user, sample_pricing_rule, mock_supertokens):
        """Test that quote expiration is automatically set."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        quote_data = {
            'customer_email': 'expiry@example.com',
            'customer_name': 'Expiry Test'
        }
        
        response = client.post('/api/quotes/',
                              headers=headers,
                              data=json.dumps(quote_data))
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should have expiration date set
        assert data['expires_at'] is not None
        
        # Parse and verify it's approximately 30 days from now
        from datetime import datetime
        expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
        created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        delta = expires_at - created_at
        assert 29 <= delta.days <= 31  # Allow some variance
    
    def test_quote_status_validation(self, client, sample_tenant, sample_user, sample_quote, mock_supertokens):
        """Test that only valid statuses are accepted."""
        headers = {
            'X-Tenant-Slug': sample_tenant.slug,
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        }
        
        # Test valid status
        valid_statuses = ['pending', 'approved', 'rejected', 'expired']
        for status in valid_statuses:
            update_data = {'status': status}
            response = client.put(f'/api/quotes/{sample_quote.id}',
                                 headers=headers,
                                 data=json.dumps(update_data))
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == status
        
        # Test invalid status (should be ignored, not cause error)
        invalid_update = {'status': 'invalid_status'}
        response = client.put(f'/api/quotes/{sample_quote.id}',
                             headers=headers,
                             data=json.dumps(invalid_update))
        assert response.status_code == 200
        # Status should remain unchanged from last valid update
        data = response.get_json()
        assert data['status'] in valid_statuses