# apps/data_engine/events/tests/conftest.py
"""Path configuration for pytest collection.

Ensures the workspace root and backend directories are on sys.path
before any test module or package __init__ is imported, allowing
absolute imports like ``apps.data_engine.*`` to resolve correctly.
"""

import os
import sys

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
backend_dir = os.path.join(workspace_root, "backend")
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
