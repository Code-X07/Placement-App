def test_register_student(client):
    resp = client.post('/api/auth/register', json={
        'email': 'student@test.com', 'password': 'password123',
        'role': 'student', 'name': 'Alice'
    })
    assert resp.status_code == 201
    assert 'token' in resp.json

def test_register_company(client):
    resp = client.post('/api/auth/register', json={
        'email': 'co@test.com', 'password': 'password123',
        'role': 'company', 'company_name': 'Acme Corp'
    })
    assert resp.status_code == 201

def test_register_admin_rejected(client):
    resp = client.post('/api/auth/register', json={
        'email': 'admin2@test.com', 'password': 'pw', 'role': 'admin'
    })
    assert resp.status_code == 400
    assert resp.json['code'] == 'ADMIN_FORBIDDEN'

def test_register_duplicate_email(client):
    data = {'email': 'dup@test.com', 'password': 'pw', 'role': 'student', 'name': 'Bob'}
    client.post('/api/auth/register', json=data)
    resp = client.post('/api/auth/register', json=data)
    assert resp.status_code == 409

def test_login_success(client):
    client.post('/api/auth/register', json={
        'email': 'log@test.com', 'password': 'pw123', 'role': 'student', 'name': 'C'
    })
    resp = client.post('/api/auth/login', json={
        'email': 'log@test.com', 'password': 'pw123'
    })
    assert resp.status_code == 200
    assert 'token' in resp.json
    assert resp.json['role'] == 'student'

def test_login_bad_password(client):
    client.post('/api/auth/register', json={
        'email': 'log2@test.com', 'password': 'pw123', 'role': 'student', 'name': 'D'
    })
    resp = client.post('/api/auth/login', json={
        'email': 'log2@test.com', 'password': 'wrong'
    })
    assert resp.status_code == 401

def test_admin_seed_login(client):
    resp = client.post('/api/auth/login', json={
        'email': 'admin@ppa.com', 'password': 'admin123'
    })
    assert resp.status_code == 200
    assert resp.json['role'] == 'admin'

def test_me_returns_fresh_user(client):
    client.post('/api/auth/register', json={
        'email': 'me@test.com', 'password': 'pw123', 'role': 'student', 'name': 'E'
    })
    login = client.post('/api/auth/login', json={
        'email': 'me@test.com', 'password': 'pw123'
    })
    headers = {'Authorization': f"Bearer {login.json['token']}"}
    resp = client.get('/api/auth/me', headers=headers)
    assert resp.status_code == 200
    assert resp.json['email'] == 'me@test.com'

def test_cors_preflight(client):
    resp = client.options('/api/auth/login',
                          headers={'Origin': 'http://localhost:5173',
                                   'Access-Control-Request-Method': 'POST'})
    assert 'Access-Control-Allow-Origin' in resp.headers
