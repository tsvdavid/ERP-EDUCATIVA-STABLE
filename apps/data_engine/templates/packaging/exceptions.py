# apps/data_engine/templates/packaging/exceptions.py
"""Domain exception hierarchy for the Template Packaging system."""

from apps.data_engine.templates.exceptions import TemplateException


class PackageException(TemplateException):
    """Base exception for all template packaging and deployment operations."""
    pass


class InvalidPackageException(PackageException):
    """Raised when a package has an invalid structure, missing files, or bad configuration."""
    pass


class SignatureVerificationException(PackageException):
    """Raised when package cryptographic integrity verification or signature check fails."""
    pass


class MigrationException(PackageException):
    """Raised when a data migration script or translation fails between version boundaries."""
    pass
