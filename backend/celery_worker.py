from app import create_app, celery  # noqa: F401 — imports register ContextTask

flask_app = create_app()
flask_app.app_context().push()

import tasks.export  # noqa: F401,E402 — registers @celery.task
import tasks.reminders  # noqa: F401,E402
import tasks.report  # noqa: F401,E402
