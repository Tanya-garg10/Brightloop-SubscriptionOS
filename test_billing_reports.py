import pytest
from app import app, db, User, Customer, Product, Plan, Subscription, Invoice, Payment
from datetime import date, timedelta

@pytest.fixture
def staff_client(app_context):
    with app.test_client() as client:
        # Create staff user
        staff = User(
            name='Staff User',
            email='staff@example.com',
            password='hashed_password',
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['uid'] = staff.id
        yield client

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

        with client.session_transaction() as sess:
            sess['uid'] = admin.id
        yield client

def test_dashboard_access(staff_client):
    """Test accessing dashboard endpoint"""
    response = staff_client.get('/api/dashboard')
    assert response.status_code == 200
    data = response.get_json()
    assert 'active' in data
    assert 'revenue' in data
    assert 'outstanding' in data
    assert 'overdue' in data
    assert 'subscriptions' in data
    assert 'customers' in data
    assert 'invoices' in data
    assert 'monthly' in data

def test_dashboard_requires_staff_role(app_context):
    """Test that dashboard requires staff or admin role"""
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

        response = client.get('/api/dashboard')
        assert response.status_code == 403

def test_run_billing_cycle(admin_client):
    """Test running billing cycle"""
    # Create active subscription due for billing
    customer_response = admin_client.post('/api/customers', json={
        'name': 'John Doe',
        'email': 'john@example.com'
    })
    customer_id = customer_response.get_json()['id']

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

    admin_client.post('/api/subscriptions', json={
        'customer_id': customer_id,
        'plan_id': plan_id,
        'qty': 1,
        'start_date': date.today().isoformat(),
        'status': 'Active'
    })

    # Run billing
    response = admin_client.post('/api/billing/run', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert 'created' in data
    assert 'invoices' in data

def test_billing_idempotency(admin_client):
    """Test that billing doesn't create duplicate invoices for same cycle"""
    # Create subscription
    customer_response = admin_client.post('/api/customers', json={
        'name': 'John Doe',
        'email': 'john@example.com'
    })
    customer_id = customer_response.get_json()['id']

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

    admin_client.post('/api/subscriptions', json={
        'customer_id': customer_id,
        'plan_id': plan_id,
        'qty': 1,
        'start_date': date.today().isoformat(),
        'status': 'Active'
    })

    # Run billing twice
    admin_client.post('/api/billing/run', json={})
    response2 = admin_client.post('/api/billing/run', json={})

    data2 = response2.get_json()
    # Second run should not create new invoices
    assert data2['created'] == 0

def test_reports_access(staff_client):
    """Test accessing reports endpoint"""
    response = staff_client.get('/api/reports')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_billed' in data
    assert 'collected' in data
    assert 'outstanding' in data
    assert 'active' in data
    assert 'by_status' in data

def test_reports_with_data(admin_client):
    """Test reports with actual data"""
    # Create customer, product, plan, subscription
    customer_response = admin_client.post('/api/customers', json={
        'name': 'John Doe',
        'email': 'john@example.com'
    })
    customer_id = customer_response.get_json()['id']

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

    admin_client.post('/api/subscriptions', json={
        'customer_id': customer_id,
        'plan_id': plan_id,
        'qty': 1,
        'start_date': date.today().isoformat(),
        'status': 'Active'
    })

    admin_client.post('/api/billing/run', json={})

    response = admin_client.get('/api/reports')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_billed'] > 0

def test_quote_from_template(admin_client):
    """Test creating a quote from template"""
    # Create customer
    customer_response = admin_client.post('/api/customers', json={
        'name': 'John Doe',
        'email': 'john@example.com'
    })
    customer_id = customer_response.get_json()['id']

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

    # Create template
    template_response = admin_client.post('/api/templates', json={
        'name': 'Enterprise Proposal',
        'plan_id': plan_id,
        'validity_days': 21
    })
    template_id = template_response.get_json()['id']

    # Create quote from template
    response = admin_client.post(f'/api/templates/{template_id}/quote', json={
        'customer_id': customer_id,
        'start_date': date.today().isoformat()
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert 'number' in data
    assert data['status'] == 'Quotation'

def test_team_management_admin_only(app_context):
    """Test that only admins can manage team"""
    with app.test_client() as client:
        # Create staff user
        staff = User(
            name='Staff User',
            email='staff@example.com',
            password='hashed_password',
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['uid'] = staff.id

        # Staff trying to add team member
        response = client.post('/api/team', json={
            'name': 'New Staff',
            'email': 'newstaff@example.com',
            'password': 'Password@123'
        })
        assert response.status_code == 403

def test_admin_can_add_team_member(app_context):
    """Test that admins can add team members"""
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

        with client.session_transaction() as sess:
            sess['uid'] = admin.id

        response = client.post('/api/team', json={
            'name': 'New Staff',
            'email': 'newstaff@example.com',
            'password': 'Password@123'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data

def test_list_team_admin_only(app_context):
    """Test that only admins can list team"""
    with app.test_client() as client:
        # Create staff user
        staff = User(
            name='Staff User',
            email='staff@example.com',
            password='hashed_password',
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['uid'] = staff.id

        response = client.get('/api/team')
        assert response.status_code == 403
