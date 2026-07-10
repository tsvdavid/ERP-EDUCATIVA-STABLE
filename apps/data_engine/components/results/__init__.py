# apps/data_engine/components/results/__init__.py
"""Results package for MAC.

Exports the ProcessingResult class which encapsulates the final state 
of a pipeline execution.
"""

from .processing_result import ProcessingResult

__all__ = ["ProcessingResult"]
