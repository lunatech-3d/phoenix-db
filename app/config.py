# config.py
import os
from pathlib import Path

# Root directory of the project (phoenix-db/)
REPO_DIR = Path(__file__).resolve().parent.parent
# Directory containing application scripts
APP_DIR = REPO_DIR / "app"

# Path to the SQLite database file
DB_PATH = str(REPO_DIR / "phoenix.db")  # ✅ Must be a string for sqlite3.connect

# Centralized access to helper scripts
class PATHS:
    """Centralized references to application scripts."""

    citations = str(APP_DIR / "citations.py")
    sources = str(APP_DIR / "source" / "sources.py")
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
    addresident = str(APP_DIR / "addresident.py")
    addmayor = str(APP_DIR / "addmayor.py")
    edit_event = str(APP_DIR / "edit_event.py")
    marriagerecord_add = str(APP_DIR / "marriagerecord_add.py")
    marriagerecord_handle = str(APP_DIR / "marriagerecord_handle.py")
    biz_ownership = str(APP_DIR / "biz_ownership.py")
    biz_employees = str(APP_DIR / "biz_employees.py")
    mapsections2 = str(APP_DIR / "mapsections2.py")

# Basic user preference flags
USER_PREFS = {
    "enable_institution_tab": True,
}