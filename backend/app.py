import redis as redis_lib
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_cors import CORS
from celery import Celery
from config import Config
from models.models import db

bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()
celery = Celery()
redis_client = None

def create_app(config=None):
    global redis_client
    app = Flask(__name__)
    if config is None:
        app.config.from_object(Config)
    elif isinstance(config, type):
        app.config.from_object(config)
    else:
        app.config.update(config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_always_eager=app.config.get('CELERY_TASK_ALWAYS_EAGER', False),
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    try:
        redis_url = app.config.get('REDIS_URL')
        if redis_url:
            redis_client = redis_lib.from_url(redis_url)
        else:
            redis_client = None
    except Exception:
        redis_client = None

    with app.app_context():
        db.create_all()
        _seed_admin()

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    return app

def _seed_admin():
    from models.models import User
    if not User.query.filter_by(role='admin').first():
        admin = User(
            email='admin@ppa.com',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin',
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
