from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

app = Celery('server')
app.conf.enable_utc = False
# app.conf.broker_url = 'redis://localhost:6379'
app.conf.update(timezone='Asia/Kolkata')

app.config_from_object(settings, namespace='CELERY')


# CELERY BEAT SETTINGS

app.conf.beat_schedule = {
    # 'notify-in-every-5-seconds': {
    #     'task':'notifications.tasks.'
    # }
}

# 'add-every-10-seconds': {
#         'task': 'chat.tasks.add',
#        'schedule': 10.0,
#         'args': (16, 16)
#     }
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self, *args, **kewargs):
    print(f"Request : {self.request!r}")
