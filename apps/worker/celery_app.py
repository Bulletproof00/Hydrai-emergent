from celery import Celery

from packages.core.config.settings import get_settings

settings = get_settings()
celery_app = Celery("chainalyze", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "ingest-candles-minute": {"task": "apps.worker.tasks.ingest_candles", "schedule": 60.0},
    "compute-features": {"task": "apps.worker.tasks.compute_features_incremental", "schedule": 120.0},
    "run-analysis-5m": {"task": "apps.worker.tasks.run_analysis", "schedule": 300.0},
}
