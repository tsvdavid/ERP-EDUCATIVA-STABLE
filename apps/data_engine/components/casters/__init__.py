# apps/data_engine/components/casters/__init__.py
"""Casters package for MAC.

Casters are responsible for converting data types of mapped fields
(e.g., string to int, string to date) based on a schema configuration.
"""

from .type_caster import TypeCaster, TypeCasterComponent

__all__ = ["TypeCaster", "TypeCasterComponent"]
