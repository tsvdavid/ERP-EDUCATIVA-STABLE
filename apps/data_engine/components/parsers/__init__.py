# apps/data_engine/components/parsers/__init__.py
"""Parsers package for MAC.

Exports the concrete parsers. Parsers are responsible for interpreting
the raw data structures produced by Readers.
"""

from .csv_parser import CSVParser, CSVParserComponent

__all__ = ["CSVParser", "CSVParserComponent"]
