import pytest
from app import app, db, User, Customer, Product, Plan, Subscription, Invoice, Payment
from datetime import date, timedelta

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

def test_list_invoices(admin_client):
    """Test listing invoices"""
    response = admin_client.get('/api/invoices')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_invoice_action_confirm(admin_client):
    """Test confirming an invoice"""
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

    sub_response = admin_client.post('/api/subscriptions', json={
        'customer_id': customer_id,
        'plan_id': plan_id,
        'qty': 1,
        'start_date': date.today().isoformat(),
        'status': 'Active'
    })
    sub_id = sub_response.get_json()['id']

    # Run billing to create invoice
    admin_client.post('/api/billing/run', json={})

    # Get invoice
    invoices_response = admin_client.get('/api/invoices')
    invoices = invoices_response.get_json()
    if invoices:
        invoice_id = invoices[0]['id']

        # Confirm invoice
        response = admin_client.post(f'/api/invoices/{invoice_id}/action', json={
            'action': 'confirm'
        })
        assert response.status_code == 200

def test_invoice_action_send(admin_client):
    """Test sending an invoice"""
    # Create invoice through billing
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

    invoices_response = admin_client.get('/api/invoices')
    invoices = invoices_response.get_json()
    if invoices:
        invoice_id = invoices[0]['id']

        response = admin_client.post(f'/api/invoices/{invoice_id}/action', json={
            'action': 'send'
        })
        assert response.status_code == 200

def test_invoice_action_cancel(admin_client):
    """Test cancelling an unpaid invoice"""
    # Create invoice
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

    invoices_response = admin_client.get('/api/invoices')
    invoices = invoices_response.get_json()
    if invoices:
        invoice_id = invoices[0]['id']

        response = admin_client.post(f'/api/invoices/{invoice_id}/action', json={
            'action': 'cancel'
        })
        assert response.status_code == 200

def test_invoice_action_print(admin_client):
    """Test print action returns print URL"""
    # Create invoice
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

    invoices_response = admin_client.get('/api/invoices')
    invoices = invoices_response.get_json()
    if invoices:
        invoice_id = invoices[0]['id']

        response = admin_client.post(f'/api/invoices/{invoice_id}/action', json={
            'action': 'print'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'print_url' in data

def test_print_invoice_page(admin_client):
    """Test accessing invoice print page"""
    # Create invoice
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

    invoices_response = admin_client.get('/api/invoices')
    invoices = invoices_response.get_json()
    if invoices:
        invoice_id = invoices[0]['id']

        response = admin_client.get(f'/invoice/{invoice_id}/print')
        assert response.status_code == 200

def test_customer_can_view_own_invoices(app_context):
    """Test that customers can only view their own invoices"""
    with app.test_client() as client:
        # Create customer user
        customer = User(
            name='Customer User',
            email='customer@example.com',
            password='hashed_password',
            role='customer'
        )
        db.session.add(customer)
        db.session.flush()

        customer_record = Customer(
            name='Customer User',
            email='customer@example.com',
            user_id=customer.id
        )
        db.session.add(customer_record)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['uid'] = customer.id

        response = client.get('/api/invoices')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
