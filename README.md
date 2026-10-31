# Brightloop Subscription Management System

A full-stack subscription management platform built with Flask, PostgreSQL and vanilla JavaScript. It supports customer management, product and plan catalogs, subscription workflows, invoicing, payment recording and finance reporting.

## Technology Stack

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- PostgreSQL / Supabase
- HTML, CSS and JavaScript
- Werkzeug password hashing

## Features

- Role-based access: Admin, Staff and Customer
- Customer and product management
- Subscription plans and lifecycle management
- Quantity validation and subscription pricing
- Invoice generation and printing
- Tax and discount configuration
- Payment recording and outstanding balance tracking
- Dashboard and financial reports
- Customer self-service access
- Password reset token flow
- Responsive interface

## Setup on Windows

### 1. Database setup

Create your own PostgreSQL database or Supabase project.

For Supabase, obtain your PostgreSQL connection string from the database connection settings.

### 2. Environment configuration

Extract the complete project ZIP.

In the extracted outer folder, copy `.env.example` and rename the copy to `.env`.

Set your own values:

```env
DATABASE_URL=postgresql://username:password@host:5432/database
SECRET_KEY=replace-with-a-long-random-secret
```

## Installation

```bash
# Clone the repository
git clone https://github.com/Tanya-garg10/Brightloop-SubscriptionOS.git
cd Brightloop-Subscription-Management-System

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
# Ensure the .env file is configured
python app.py
```

The app will be available at `http://localhost:5000`.

## Testing

```bash
# Run the test suite
pytest
```

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request. Follow the existing code style and include tests for new features.

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

A full-stack subscription management platform built with Flask, PostgreSQL and vanilla JavaScript. It supports customer management, product and plan catalogs, subscription workflows, invoicing, payment recording and finance reporting.

## Technology Stack

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- PostgreSQL / Supabase
- HTML, CSS and JavaScript
- Werkzeug password hashing

## Features

- Role-based access: Admin, Staff and Customer
- Customer and product management
- Subscription plans and lifecycle management
- Quantity validation and subscription pricing
- Invoice generation and printing
- Tax and discount configuration
- Payment recording and outstanding balance tracking
- Dashboard and financial reports
- Customer self-service access
- Password reset token flow
- Responsive interface

## Setup on Windows

### 1. Database setup

Create your own PostgreSQL database or Supabase project.

For Supabase, obtain your PostgreSQL connection string from the database connection settings.

### 2. Environment configuration

Extract the complete project ZIP.

In the extracted outer folder, copy `.env.example` and rename the copy to `.env`.

Set your own values:

```env
DATABASE_URL=postgresql://username:password@host:5432/database
SECRET_KEY=replace-with-a-long-random-secret
```

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

