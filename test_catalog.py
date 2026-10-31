import pytest
from app import app, db, User, Product, Plan, Tax, Discount, QuoteTemplate
from datetime import date

@pytest.fixture
def admin_client(app_context):
    with app.test_client() as client:
        # Create admin user
        admin = User(
            name='Admin User',
            email='admin@example.com',
            password='hashed_password',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

        # Login as admin
        with client.session_transaction() as sess:
            sess['uid'] = admin.id
        yield client

def test_create_product(admin_client):
    """Test creating a product"""
    response = admin_client.post('/api/products', json={
        'name': 'Test Product',
        'kind': 'Software',
        'price': 99.99,
        'cost': 50.00,
        'notes': 'Test notes',
        'variants': 'Standard:0, Premium:+20'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

def test_create_product_as_customer(app_context):
    """Test that customers cannot create products"""
    with app.test_client() as client:
        # Create customer user
        customer = User(
            name='Customer User',
            email='customer@example.com',
            password='hashed_password',
            role='customer'
        )
        db.session.add(customer)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['uid'] = customer.id

        response = client.post('/api/products', json={
            'name': 'Test Product',
            'kind': 'Software',
            'price': 99.99
        })
        assert response.status_code == 403

def test_list_products(admin_client):
    """Test listing products"""
    # Create a product first
    admin_client.post('/api/products', json={
        'name': 'Test Product',
        'kind': 'Software',
        'price': 99.99
    })

    response = admin_client.get('/api/products')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert data[0]['name'] == 'Test Product'

def test_create_plan(admin_client):
    """Test creating a plan"""
    # First create a product
    product_response = admin_client.post('/api/products', json={
        'name': 'Test Product',
        'kind': 'Software',
        'price': 99.99
    })
    product_id = product_response.get_json()['id']

    # Create plan
    response = admin_client.post('/api/plans', json={
        'name': 'Monthly Plan',
        'product_id': product_id,
        'price': 99.99,
        'interval': 'monthly',
        'min_qty': 1,
        'allow_pause': True,
        'allow_renew': True
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

def test_list_plans(admin_client):
    """Test listing plans"""
    # Create product and plan
    product_response = admin_client.post('/api/products', json={
        'name': 'Test Product',
        'kind': 'Software',
        'price': 99.99
    })
    product_id = product_response.get_json()['id']

    admin_client.post('/api/plans', json={
        'name': 'Monthly Plan',
        'product_id': product_id,
        'price': 99.99,
        'interval': 'monthly'
    })

    response = admin_client.get('/api/plans')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1

def test_create_tax(admin_client):
    """Test creating a tax rule"""
    response = admin_client.post('/api/taxes', json={
        'name': 'GST',
        'rate': 18.0
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

def test_list_taxes(admin_client):
    """Test listing tax rules"""
    admin_client.post('/api/taxes', json={
        'name': 'GST',
        'rate': 18.0
    })

    response = admin_client.get('/api/taxes')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1

def test_create_discount(admin_client):
    """Test creating a discount"""
    response = admin_client.post('/api/discounts', json={
        'name': 'Summer Sale',
        'kind': 'percent',
        'value': 10.0,
        'min_qty': 5,
        'max_uses': 100
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

def test_list_discounts(admin_client):
    """Test listing discounts"""
    admin_client.post('/api/discounts', json={
        'name': 'Summer Sale',
        'kind': 'percent',
        'value': 10.0
    })

    response = admin_client.get('/api/discounts')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1

def test_create_quote_template(admin_client):
    """Test creating a quote template"""
    # Create product and plan first
    product_response = admin_client.post('/api/products', json={
        'name': 'Test Product',
        'kind': 'Software',
        'price': 99.99
    })
    product_id = product_response.get_json()['id']

    plan_response = admin_client.post('/api/plans', json={
        'name': 'Monthly Plan',
        'product_id': product_id,
        'price': 99.99,
        'interval': 'monthly'
    })
    plan_id = plan_response.get_json()['id']

    # Create template
    response = admin_client.post('/api/templates', json={
        'name': 'Enterprise Proposal',
        'plan_id': plan_id,
        'validity_days': 21
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

def test_list_templates(admin_client):
    """Test listing quote templates"""
    # Create product and plan
    product_response = admin_client.post('/api/products', json={
        'name': 'Test Product',
        'kind': 'Software',
        'price': 99.99
    })
    product_id = product_response.get_json()['id']

    plan_response = admin_client.post('/api/plans', json={
        'name': 'Monthly Plan',
        'product_id': product_id,
        'price': 99.99,
        'interval': 'monthly'
    })
    plan_id = plan_response.get_json()['id']

    admin_client.post('/api/templates', json={
        'name': 'Enterprise Proposal',
        'plan_id': plan_id,
        'validity_days': 21
    })

    response = admin_client.get('/api/templates')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
