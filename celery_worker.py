# Celery Worker Entry Point
# This file is used to start the Celery worker

from app import create_app
from app.tasks import celery

# Create Flask app and configure Celery
app = create_app()
celery.conf.update(
    broker_url=app.config['CELERY_BROKER_URL'],
    result_backend=app.config['CELERY_RESULT_BACKEND'],
)

# Push app context for tasks
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

if __name__ == '__main__':
    celery.start()
