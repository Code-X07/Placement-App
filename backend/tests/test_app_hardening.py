import os
import pytest
from config import Config

def test_production_requires_secret(monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.delenv('FLASK_SECRET_KEY', raising=False)
    monkeypatch.delenv('JWT_SECRET_KEY', raising=False)
    from app import create_app
    with pytest.raises(RuntimeError):
        create_app(Config)

def test_unknown_api_route_returns_json_404(client):
    resp = client.get('/api/does/not/exist')
    assert resp.status_code == 404
    assert resp.is_json
    assert resp.json['code'] == 'NOT_FOUND'

def test_wrong_method_on_api_route_returns_json_405(client):
    # /api/auth/login exists for POST; GET should be a JSON 405
    resp = client.get('/api/auth/login')
    assert resp.status_code == 405
    assert resp.is_json
    assert resp.json['code'] == 'METHOD_NOT_ALLOWED'
