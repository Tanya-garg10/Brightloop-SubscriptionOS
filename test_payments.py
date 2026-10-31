import pytest
from app import app, db, User, Customer, Product, Plan, Subscription, Invoice, Payment
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

        with client.session_transaction() as sess:
            sess['uid'] = admin.id
        yield client

def test_add_payment(admin_client):
    """Test recording a payment"""
    # Create customer, product, plan, subscription, invoice
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

        # Add payment
        response = admin_client.post('/api/payments', json={
            'invoice_id': invoice_id,
            'amount': 50.00,
            'method': 'Bank transfer',
            'paid_on': date.today().isoformat(),
            'note': 'Partial payment'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data

def test_add_payment_full_amount(admin_client):
    """Test recording a full payment"""
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
        invoice_total = invoices[0]['total']

        # Pay full amount
        response = admin_client.post('/api/payments', json={
            'invoice_id': invoice_id,
            'amount': invoice_total,
            'method': 'UPI',
            'paid_on': date.today().isoformat()
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'Paid'

def test_add_payment_exceeds_balance(admin_client):
    """Test that payment cannot exceed outstanding balance"""
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

        # Try to pay more than total
        response = admin_client.post('/api/payments', json={
            'invoice_id': invoice_id,
            'amount': 999999.00,
            'method': 'Bank transfer'
        })
        assert response.status_code == 400

def test_add_payment_negative_amount(admin_client):
    """Test that payment amount must be positive"""
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

        # Try negative payment
        response = admin_client.post('/api/payments', json={
            'invoice_id': invoice_id,
            'amount': -50.00,
            'method': 'Bank transfer'
        })
        assert response.status_code == 400

def test_list_payments(admin_client):
    """Test listing payments"""
    # Create invoice and payment
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

        admin_client.post('/api/payments', json={
            'invoice_id': invoice_id,
            'amount': 50.00,
            'method': 'Bank transfer'
        })

    response = admin_client.get('/api/payments')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
