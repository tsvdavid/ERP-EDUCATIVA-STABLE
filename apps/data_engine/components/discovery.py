# apps/data_engine/components/discovery.py
"""Component discovery utilities for the MAC subsystem.

The ``auto_register`` function scans the ``apps.data_engine.components`` package,
identifies concrete subclasses of :class:`BaseComponent` and registers them in a
provided :class:`MacRegistry` using a snake_case name derived from the class.
"""

import importlib
import inspect
import pkgutil
from typing import Type

from .base import BaseComponent, component_name
from ..core.registry import MacRegistry


def auto_register(registry: MacRegistry) -> None:
    """Automatically register all ``BaseComponent`` subclasses found in the
    ``apps.data_engine.components`` package.

    The function walks the package and its specific sub-packages,
    imports each module, and registers any concrete subclass of ``BaseComponent``
    using its snake_case name as provided by ``component_name``.
    """
    package = importlib.import_module(__name__.rsplit('.', 1)[0])
    
    # Define the sub-packages to scan in sorted order
    sub_packages = sorted(["", "connectors", "exporters", "transformers", "readers", "parsers", "validators", "mappers", "casters", "schemas", "rules", "staging", "importers", "reconciliation", "loaders"])
    
    for sub in sub_packages:
        pkg_name = package.__name__ if not sub else f"{package.__name__}.{sub}"
        try:
            pkg_module = importlib.import_module(pkg_name)
        except ImportError:
            continue
            
        for _, module_name, is_pkg in pkgutil.iter_modules(pkg_module.__path__):
            if is_pkg or module_name.startswith('test') or module_name == '__pycache__':
                continue
                
            try:
                module = importlib.import_module(f"{pkg_name}.{module_name}")
            except (ImportError, AttributeError):
                continue
            for _, obj in inspect.getmembers(module, inspect.isclass):
                # Ensure it's a subclass of BaseComponent but not an abstract base class
                if issubclass(obj, BaseComponent) and not inspect.isabstract(obj) and obj is not BaseComponent:
                    if obj.__name__.startswith('Base'):
                        continue
                    name = component_name(obj)
                    registry.register(name, obj())
