from app import create_app, celery  # noqa: F401 — imports register ContextTask

flask_app = create_app()
flask_app.app_context().push()
