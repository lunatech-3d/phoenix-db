# config.py
import os
from pathlib import Path

# Root directory of the project (phoenix-db/)
BASE_DIR = Path(__file__).resolve().parent

# Path to the SQLite database file
DB_PATH = str(BASE_DIR / "phoenix.db")  # ✅ Must be a string for sqlite3.connect

# Centralized access to helper scripts
class PATHS:
    """Centralized references to application scripts."""

    citations = str(APP_DIR / "citations.py")
    sources = str(APP_DIR / "sources.py")
    editme = str(APP_DIR / "editme.py")
    business = str(APP_DIR / "business.py")
    people = str(APP_DIR / "people.py")
    deeds = str(APP_DIR / "deeds.py")
    events = str(APP_DIR / "events.py")

    # Scripts referenced by mainmenu2.py
    addcensus = str(APP_DIR / "addcensus.py")
    addme = str(APP_DIR / "addme.py")
    address_management = str(APP_DIR / "address_management.py")
    buildancestortree = str(APP_DIR / "buildancestortree.py")
    buildatree = str(APP_DIR / "buildatree.py")
    censusform = str(APP_DIR / "censusform.py")
    doctypesupport = str(APP_DIR / "doctypesupport.py")
    editme_script = str(APP_DIR / "editme.py")  # alias for clarity
    events_script = str(APP_DIR / "events.py")
    matchgraverecords = str(APP_DIR / "matchgraverecords.py")
    members = str(APP_DIR / "members.py")
    orgs = str(APP_DIR / "orgs.py")
    showbusinesses = str(APP_DIR / "showbusinesses.py")
    showcensusrecs = str(APP_DIR / "showcensusrecs.py")
    showmayors = str(APP_DIR / "showmayors.py")
    showresidents = str(APP_DIR / "showresidents.py")
    viewtheaddresses = str(APP_DIR / "viewtheaddresses.py")
