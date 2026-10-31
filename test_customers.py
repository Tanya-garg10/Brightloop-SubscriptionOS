import pytest
from app import app, db, User, Customer, Product, Plan
from datetime import date

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

def test_create_customer(staff_client):
    """Test creating a customer"""
    response = staff_client.post('/api/customers', json={
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'Acme Corp',
        'phone': '+1234567890',
        'status': 'Active'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

def test_create_customer_minimal(staff_client):
    """Test creating a customer with minimal data"""
    response = staff_client.post('/api/customers', json={
        'name': 'Jane Doe',
        'email': 'jane@example.com'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

def test_list_customers(staff_client):
    """Test listing customers"""
    staff_client.post('/api/customers', json={
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'Acme Corp'
    })

    response = staff_client.get('/api/customers')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert data[0]['name'] == 'John Doe'

def test_customer_can_view_own_data(app_context):
    """Test that customers can only view their own data"""
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

        # Create customer record
        customer_record = Customer(
            name='Customer User',
            email='customer@example.com',
            company='Customer Company',
            user_id=customer.id
        )
        db.session.add(customer_record)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['uid'] = customer.id

        response = client.get('/api/customers')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['email'] == 'customer@example.com'

def test_customer_cannot_view_other_customers(app_context):
    """Test that customers cannot view other customers"""
    with app.test_client() as client:
        # Create two customers
        customer1 = User(
            name='Customer One',
            email='customer1@example.com',
            password='hashed_password',
            role='customer'
        )
        db.session.add(customer1)
        db.session.flush()

        customer_record1 = Customer(
            name='Customer One',
            email='customer1@example.com',
            user_id=customer1.id
        )
        db.session.add(customer_record1)

        customer2 = User(
            name='Customer Two',
            email='customer2@example.com',
            password='hashed_password',
            role='customer'
        )
        db.session.add(customer2)
        db.session.flush()

        customer_record2 = Customer(
            name='Customer Two',
            email='customer2@example.com',
            user_id=customer2.id
        )
        db.session.add(customer_record2)
        db.session.commit()

        # Login as customer1
        with client.session_transaction() as sess:
            sess['uid'] = customer1.id

        response = client.get('/api/customers')
        assert response.status_code == 200
        data = response.get_json()
        # Should only see own customer record
        assert len(data) == 1
        assert data[0]['email'] == 'customer1@example.com'

def test_update_customer(staff_client):
    """Test updating a customer"""
    # Create customer first
    create_response = staff_client.post('/api/customers', json={
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'Acme Corp'
    })
    customer_id = create_response.get_json()['id']

    # Update customer
    response = staff_client.patch(f'/api/customers/{customer_id}', json={
        'company': 'Updated Company',
        'phone': '+9876543210'
    })
    assert response.status_code == 200

    # Verify update
    get_response = staff_client.get('/api/customers')
    customers = get_response.get_json()
    updated_customer = next((c for c in customers if c['id'] == customer_id), None)
    assert updated_customer['company'] == 'Updated Company'
