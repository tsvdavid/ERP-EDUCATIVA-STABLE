# apps/data_engine/jobs/tasks.py
"""Celery Task Wrapper for Background Processing & Distributed Job Framework (TAREA 24).

Defines the worker task (`run_mac_job`) that Celery workers invoke when executing
an enqueued MAC import session job. Fully decoupled from Django ORM (`Zero-ORM` policy).
"""

from typing import Any, Dict


def run_mac_job(job_id: str, **kwargs: Any) -> Dict[str, Any]:
    """Execute a background MAC job by ID inside a Celery worker process.

    Resolves the global `JobManager` singleton and triggers execution.
    """
    from .manager import JobManager
    manager = JobManager.global_instance()
    return manager.run_job(job_id, **kwargs)
