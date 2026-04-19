"""WSGI entrypoint for production servers (Gunicorn/Render)."""

import os
import sys

# Ensure the project root is importable when launched by a process manager.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app  # noqa: E402
