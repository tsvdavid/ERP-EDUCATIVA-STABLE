# apps/data_engine/components/mappers/__init__.py
"""Mappers package for MAC.

Mappers translate input dictionary keys (variable column names) into
standard internal MAC keys based on a configuration mapping.
"""

from .dynamic_mapper import DynamicMapper, DynamicMapperComponent

__all__ = ["DynamicMapper", "DynamicMapperComponent"]
