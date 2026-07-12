# apps/data_engine/application/__init__.py
"""MAC Application & Service Layer Framework (TAREA 22).

Encapsulates the 10-layer MAC pipeline behind a cohesive, high-level Facade
and set of application use-case services. Adheres strictly to Zero-ORM and
exposes only immutable DTO contracts to external consumers (API REST, Celery,
CLI, and schedulers).
"""
