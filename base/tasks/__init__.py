# Import .py file which contains tasks to be executed
from . import check_academic_calendar
from . import extend_learning_units
from . import synchronize_entities


from celery.schedules import crontab
from backoffice.celery import app as celery_app
celery_app.conf.beat_schedule.update({
    'Extend learning units': {
        'task': 'base.tasks.extend_learning_units.run',
        'schedule': crontab(minute=0, hour=0, day_of_month=15, month_of_year=7)
    },
    'Check academic calendar': {
        'task': 'base.tasks.check_academic_calendar.run',
        'schedule': crontab(minute=0, hour=1)
    },
    'Synchronize entities': {
        'task': 'base.tasks.synchronize_entities.run',
        'schedule': crontab(minute=1)
    },
})
