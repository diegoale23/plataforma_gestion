# main_project/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('main_project')
app.conf.beat_schedule = {
    'update-jobs-daily': {
        'task': 'market_analysis.tasks.update_job_offers',
        'schedule': crontab(hour=0, minute=0),  # Cada día a medianoche
    },
}