"""Regression tests for gaps found during live E2E verification (2026-06-24)."""
from models.models import CompanyProfile


def test_blacklisted_company_login_returns_suspended_message(client, admin_headers, app):
    # register a company, then blacklist it as admin
    client.post('/api/auth/register', json={
        'email': 'blacklisted@test.com', 'password': 'pw1234',
        'role': 'company', 'name': 'BlacklistCorp',
    })
    with app.app_context():
        cp = CompanyProfile.query.filter_by(company_name='BlacklistCorp').first()
        cp_id = cp.id
    client.put(f'/api/admin/companies/{cp_id}/blacklist', headers=admin_headers)

    resp = client.post('/api/auth/login', json={
        'email': 'blacklisted@test.com', 'password': 'pw1234',
    })
    assert resp.status_code == 403
    assert resp.json['code'] == 'SUSPENDED'
    assert 'suspend' in resp.json['error'].lower()


def test_deactivated_student_login_still_returns_inactive(client, admin_headers, app):
    reg = client.post('/api/auth/register', json={
        'email': 'deact@test.com', 'password': 'pw1234',
        'role': 'student', 'name': 'Deact',
    })
    user_id = reg.json['user']['id']
    client.put(f'/api/admin/students/{user_id}/deactivate', headers=admin_headers)

    resp = client.post('/api/auth/login', json={
        'email': 'deact@test.com', 'password': 'pw1234',
    })
    assert resp.status_code == 403
    assert resp.json['code'] == 'INACTIVE'
