def get_current_institution(request):
    """Return the tenant attached to the request (or None)."""
    return getattr(request, "tenant", None)
