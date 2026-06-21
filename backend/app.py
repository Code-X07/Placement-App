import os
import redis as redis_lib
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from models.models import db
from extensions import bcrypt, jwt, mail, celery

redis_client = None

def create_app(config=None):
    global redis_client
    app = Flask(__name__, static_folder=None)
    if config is None:
        app.config.from_object(Config)
    elif isinstance(config, type):
        app.config.from_object(config)
    else:
        app.config.update(config)

    if os.environ.get('FLASK_ENV') == 'production':
        for key in ('SECRET_KEY', 'JWT_SECRET_KEY'):
            if app.config.get(key) in (None, '', 'dev-secret-key', 'dev-jwt-secret'):
                raise RuntimeError(f'{key} must be set via environment in production')

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    cors_origins = os.environ.get('CORS_ORIGINS', '*')
    CORS(app, resources={r"/api/*": {"origins": cors_origins.split(',')}})

    # Load beat_schedule from the config class (Flask only auto-loads uppercase keys)
    beat_schedule_value = {}
    if isinstance(config, type):
        beat_schedule_value = getattr(config, 'beat_schedule', {})
    elif config is None:
        from config import Config as DefaultConfig
        beat_schedule_value = getattr(DefaultConfig, 'beat_schedule', {})

    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_always_eager=app.config.get('CELERY_TASK_ALWAYS_EAGER', False),
        beat_schedule=beat_schedule_value,
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            from flask import current_app, has_app_context
            # If already in an app context, use that; otherwise use the one we have
            if has_app_context():
                return self.run(*args, **kwargs)
            else:
                with app.app_context():
                    return self.run(*args, **kwargs)

    celery.Task = ContextTask

    try:
        redis_url = app.config.get('REDIS_URL')
        if redis_url:
            redis_client = redis_lib.from_url(redis_url)
        else:
            redis_client = None
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning('Redis unavailable, caching disabled: %s', e)
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

    @app.route('/')
    def index():
        template_dir = os.path.join(app.root_path, '..', 'frontend', 'templates')
        return send_from_directory(template_dir, 'index.html')

    @app.route('/static/<path:path>')
    def static_files(path):
        static_dir = os.path.join(app.root_path, '..', 'frontend', 'static')
        return send_from_directory(static_dir, path)

    return app

def _seed_admin():
    from models.models import User
    if not User.query.filter_by(role='admin').first():
        from flask import current_app
        admin = User(
            email=current_app.config.get('ADMIN_EMAIL', 'admin@ppa.com'),
            password_hash=bcrypt.generate_password_hash(
                os.environ.get('ADMIN_PASSWORD', 'admin123')).decode('utf-8'),
            role='admin',
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app = create_app()
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, port=5000)
