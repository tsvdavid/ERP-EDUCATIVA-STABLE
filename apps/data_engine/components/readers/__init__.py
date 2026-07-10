# apps/data_engine/components/readers/__init__.py
"""Reader package for MAC.

Exports the concrete CSVReader component that will be registered via the generic
adapter. The reader is deliberately stateless and only knows how to turn a CSV
source (string or file‑like) into a list of dictionaries.
"""

from .csv_reader import CSVReader, CSVReaderComponent

__all__ = ["CSVReader", "CSVReaderComponent"]
