# config.py
import os
from pathlib import Path

# Root directory of the project (phoenix-db/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to the SQLite database file
DB_PATH = str(BASE_DIR / "phoenix.db")  # ✅ Must be a string for sqlite3.connect

# Centralized access to helper scripts
class PATHS:
    citations = str(BASE_DIR / "citations.py")
    sources = str(BASE_DIR / "sources.py")
    editme = str(BASE_DIR / "editme.py")
    business = str(BASE_DIR / "business.py")
    # Add more as needed...
    people = str(BASE_DIR / "people.py")
    deeds = str(BASE_DIR / "deeds.py")
    events = str(BASE_DIR / "events.py")
