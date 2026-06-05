import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app import create_app
from models.models import db as _db
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_headers(client):
    resp = client.post('/api/auth/login', json={
        'email': 'admin@ppa.com', 'password': 'admin123'
    })
    return {'Authorization': f"Bearer {resp.json['token']}"}

@pytest.fixture
def student_user(client):
    resp = client.post('/api/auth/register', json={
        'email': 'stu@test.com', 'password': 'pw123', 'role': 'student', 'name': 'Stu'
    })
    return resp.json

@pytest.fixture
def company_user(client):
    resp = client.post('/api/auth/register', json={
        'email': 'co@test.com', 'password': 'pw123', 'role': 'company', 'company_name': 'Corp'
    })
    return resp.json

@pytest.fixture
def approved_company_headers(client, admin_headers, app):
    resp = client.post('/api/auth/register', json={
        'email': 'approvedco@test.com', 'password': 'pw123',
        'role': 'company', 'company_name': 'ApprovedCorp'
    })
    token = resp.json['token']
    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='ApprovedCorp').first()
        client.put(f'/api/admin/companies/{cp.id}/approve', headers=admin_headers)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def approved_drive(client, admin_headers, approved_company_headers):
    from datetime import date, timedelta
    resp = client.post('/api/company/drives', headers=approved_company_headers, json={
        'title': 'Test Drive',
        'description': 'Open for CS/IT',
        'ctc': 10.0, 'location': 'Pune',
        'eligibility_cgpa': 6.0,
        'eligibility_branch': ['CS', 'IT'],
        'application_deadline': str(date.today() + timedelta(days=30))
    })
    drive_id = resp.json['id']
    client.put(f'/api/admin/drives/{drive_id}/approve', headers=admin_headers)
    return drive_id
