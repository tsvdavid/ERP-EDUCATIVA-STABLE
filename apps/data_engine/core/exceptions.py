# apps/data_engine/core/exceptions.py
"""Custom exceptions for the MAC core subsystem."""

class MacError(Exception):
    """Base class for all MAC‑related errors."""
    pass

class ComponentNotFoundError(MacError):
    """Raised when a requested component is not present in the registry."""
    pass

class ComponentExecutionError(MacError):
    """Raised when a component fails during execution within the MAC pipeline."""
    pass

class ConnectorError(MacError):
    """Raised for errors specific to connector components."""
    pass

class ExporterError(MacError):
    """Raised for errors specific to exporter components."""
    pass
