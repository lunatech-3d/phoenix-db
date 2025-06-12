from pathlib import Path

# Base directory for the project (directory containing this file)
BASE_DIR = Path(__file__).resolve().parent

# Path to the SQLite database
DB_PATH = BASE_DIR / "phoenix.db"

# Paths to helper scripts
class PATHS:
    citations = BASE_DIR / "citations.py"
    sources = BASE_DIR / "sources.py"
