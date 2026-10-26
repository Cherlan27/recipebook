"""Reuse the real migration environment so the fixtures exercise it as well."""

from pathlib import Path
from runpy import run_path

import app.db.migrations

run_path(str(Path(app.db.migrations.__file__).parent / "env.py"))
