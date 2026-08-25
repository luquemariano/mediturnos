from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.worker_config import AppointmentReminderWorkerSettings


def create_worker_engine(settings: AppointmentReminderWorkerSettings):
    options = {}
    if settings.database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(settings.database_url, **options)


def create_worker_session_factory(settings: AppointmentReminderWorkerSettings):
    return sessionmaker(
        bind=create_worker_engine(settings),
        autoflush=False,
        autocommit=False,
    )
