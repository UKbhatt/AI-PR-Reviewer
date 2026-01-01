from celery import Celery
from app.config import settings
import logging
import sys

logger = logging.getLogger(__name__)

# Detect Windows
IS_WINDOWS = sys.platform == "win32"

# Initialize Celery app
celery_app = Celery(
    "code_review_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.analysis_tasks"]
)

# Celery configuration
celery_config = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": settings.CELERY_TASK_TRACK_STARTED,
    "task_time_limit": settings.CELERY_TASK_TIME_LIMIT,
    "task_soft_time_limit": settings.CELERY_TASK_SOFT_TIME_LIMIT,
    "result_expires": settings.TASK_RESULT_TTL,
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "broker_connection_retry_on_startup": True,
}

# Windows-specific configuration
if IS_WINDOWS:
    # Use solo pool on Windows (runs tasks in same process, avoids multiprocessing issues)
    celery_config["worker_pool"] = "solo"
    logger.info("Windows detected: Using 'solo' worker pool (Windows-compatible)")
else:
    # Use prefork pool on Unix-like systems (better performance)
    celery_config["worker_prefetch_multiplier"] = 4
    celery_config["worker_max_tasks_per_child"] = 1000

celery_app.conf.update(celery_config)

# Task routes
celery_app.conf.task_routes = {
    "app.tasks.analysis_tasks.analyze_pr_task": {"queue": "analysis"},
}

logger.info("Celery app initialized successfully")