import os
from celery.schedules import crontab

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///ppa.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@ppa.com')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    CELERY_TASK_ALWAYS_EAGER = False
    beat_schedule = {
        'daily-reminders': {
            'task': 'tasks.reminders.send_deadline_reminders',
            'schedule': crontab(hour=8, minute=0),
        },
        'monthly-report': {
            'task': 'tasks.report.send_monthly_report',
            'schedule': crontab(day_of_month=1, hour=0, minute=0),
        },
    }

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-jwt-secret'
    CELERY_TASK_ALWAYS_EAGER = True
    MAIL_SUPPRESS_SEND = True
    REDIS_URL = None
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
