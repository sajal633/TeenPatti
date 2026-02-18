from __future__ import annotations

from pathlib import Path

APP_NAME = "Teen Patti Production Platform"
APP_VERSION = "1.1.0"
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"
STATIC_DIR = BASE_DIR / "static"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Admin@12345"
