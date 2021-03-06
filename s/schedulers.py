"""
 # Copyright (c) 08 2016 | suryakencana
 # 8/14/16 nanang.ask@kubuskotak.com
 #  schedulers
"""
from pytz import timezone
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_ADDED


scheduler = BackgroundScheduler()


def start_scheduler(settings):
    assert settings['scheduler.store'] in ('redis', 'sqlalchemy', 'rethinkdb'), \
        'Uknown job store, must by one of redis or sqlalchemy'

    if settings['scheduler.store'] == 'redis':
        jobstores = {
            'default': RedisJobStore(
                host=settings['scheduler.host'],
                db=settings['scheduler.db'])
        }
    else:
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings['scheduler.url'])
        }

    executors = {
        'default': {
            'type': settings['scheduler.executors.type'],
            'max_workers': settings['scheduler.executors.max_workers']
        },
        'processpool': ProcessPoolExecutor(
            max_workers=settings['scheduler.executors.processpool.max_workers']
        )
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': settings['scheduler.job_defaults.max_instances']
    }
    scheduler.configure(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=timezone('UTC')
    )
    if settings['scheduler.autostart'] == 'true':
        scheduler.start()


def job_added_event(event):
    job = scheduler.get_job(event.job_id)
    if hasattr(job.func, 'scopped'):
        kwargs = job.kwargs
        kwargs['_job_id'] = job.id
        scheduler.modify_job(
            event.job_id, None, **{'kwargs': kwargs}
        )


scheduler.add_listener(job_added_event, EVENT_JOB_ADDED)


def scheduler_events(event):
    settings = event.app.registry.settings
    start_scheduler(settings)


def includeme(config):
    config.add_subscriber(
        '.schedulers.scheduler_events',
        'pyramid.events.ApplicationCreated'
    )
