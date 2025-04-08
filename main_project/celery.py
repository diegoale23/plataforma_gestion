# main_project/celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_project.settings')
app = Celery('main_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()