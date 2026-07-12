# apps/data_engine/api/__init__.py
"""REST API & Integration Gateway Framework (TAREA 23).

Provides the official presentation and adaptation layer for the Motor de Análisis
y Carga (MAC). Exposes endpoints via Django REST Framework (DRF) viewsets and views
while delegating 100% of business logic to the `MacApplicationFacade`.
"""
