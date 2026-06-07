def test_admin_dashboard(client, admin_headers, student_user, company_user):
    resp = client.get('/api/admin/dashboard', headers=admin_headers)
    assert resp.status_code == 200
    for key in ('students', 'companies', 'drives', 'applications'):
        assert key in resp.json

def test_non_admin_blocked(client, student_user):
    headers = {'Authorization': f"Bearer {student_user['token']}"}
    resp = client.get('/api/admin/dashboard', headers=headers)
    assert resp.status_code == 403

def test_list_companies(client, admin_headers, company_user):
    resp = client.get('/api/admin/companies', headers=admin_headers)
    assert resp.status_code == 200
    assert any(c['company_name'] == 'Corp' for c in resp.json)

def test_approve_company(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='Corp').first()
        resp = client.put(f'/api/admin/companies/{cp.id}/approve', headers=admin_headers)
        assert resp.status_code == 200
        from models.models import db
        db.session.expire_all()
        assert CompanyProfile.query.get(cp.id).approval_status == 'approved'

def test_reject_company(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='Corp').first()
        resp = client.put(f'/api/admin/companies/{cp.id}/reject', headers=admin_headers)
        assert resp.status_code == 200

def test_blacklist_company(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import CompanyProfile, User
        cp = CompanyProfile.query.filter_by(company_name='Corp').first()
        resp = client.put(f'/api/admin/companies/{cp.id}/blacklist', headers=admin_headers)
        assert resp.status_code == 200
        from models.models import db
        db.session.expire_all()
        u = User.query.get(cp.user_id)
        assert u.is_active == False

def test_deactivate_student(client, admin_headers, student_user, app):
    with app.app_context():
        from models.models import User
        u = User.query.filter_by(email='stu@test.com').first()
        resp = client.put(f'/api/admin/students/{u.id}/deactivate', headers=admin_headers)
        assert resp.status_code == 200
        from models.models import db
        db.session.expire_all()
        assert User.query.get(u.id).is_active == False

def test_search_student(client, admin_headers, student_user):
    resp = client.get('/api/admin/search?q=Stu&type=student', headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json, list)

def test_list_drives(client, admin_headers, approved_drive):
    resp = client.get('/api/admin/drives', headers=admin_headers)
    assert resp.status_code == 200
    assert any(d['title'] == 'Test Drive' for d in resp.json)

def test_deactivate_non_student_blocked(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import User
        u = User.query.filter_by(email='co@test.com').first()
        resp = client.put(f'/api/admin/students/{u.id}/deactivate', headers=admin_headers)
        assert resp.status_code == 400
        assert resp.json['code'] == 'NOT_STUDENT'

def test_blacklisted_company_drives_hidden(client, admin_headers,
                                           approved_company_headers, approved_drive,
                                           student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    # Confirm drive visible before blacklist
    before = client.get('/api/student/drives', headers=stu_headers)
    assert any(d['id'] == approved_drive for d in before.json)

    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='ApprovedCorp').first()
        client.put(f'/api/admin/companies/{cp.id}/blacklist', headers=admin_headers)

    after = client.get('/api/student/drives', headers=stu_headers)
    assert all(d['id'] != approved_drive for d in after.json)


def test_rejected_company_drives_hidden(client, admin_headers,
                                        approved_company_headers, approved_drive,
                                        student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='ApprovedCorp').first()
        client.put(f'/api/admin/companies/{cp.id}/reject', headers=admin_headers)

    after = client.get('/api/student/drives', headers=stu_headers)
    assert all(d['id'] != approved_drive for d in after.json)
