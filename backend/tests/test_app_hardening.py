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
