import sqlite3
from tkinter import Toplevel, ttk, BooleanVar, Checkbutton, Button
from app.config import DB_PATH

# Default visibility for optional tabs
DEFAULT_TABS = {
    "family": False,
    "residence": False,
    "education": False,
    "business": False,
    "records": False,
    "orgs": True,
    "media": False,
    "sources": False,
}


def _get_conn():
    return sqlite3.connect(DB_PATH)


def create_table():
    """Create the UserPrefs table if it doesn't exist and populate defaults."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS UserPrefs (key TEXT PRIMARY KEY, value TEXT)"
    )
    # Insert default prefs if missing
    for tab, visible in DEFAULT_TABS.items():
        cur.execute(
            "INSERT OR IGNORE INTO UserPrefs (key, value) VALUES (?, ?)",
            (f"tab_{tab}", "1" if visible else "0"),
        )
    conn.commit()
    conn.close()


def load_tab_prefs():
    """Return dictionary of tab visibility preferences."""
    create_table()
    conn = _get_conn()
    cur = conn.cursor()
    prefs = {}
    for tab in DEFAULT_TABS:
        cur.execute("SELECT value FROM UserPrefs WHERE key=?", (f"tab_{tab}",))
        row = cur.fetchone()
        prefs[tab] = row[0] == "1" if row else DEFAULT_TABS[tab]
    conn.close()
    return prefs


def save_tab_prefs(prefs):
    """Persist tab visibility settings."""
    conn = _get_conn()
    cur = conn.cursor()
    for tab, visible in prefs.items():
        cur.execute(
            "REPLACE INTO UserPrefs (key, value) VALUES (?, ?)",
            (f"tab_{tab}", "1" if visible else "0"),
        )
    conn.commit()
    conn.close()


def open_options_dialog(parent=None):
    """Display dialog allowing the user to toggle default tab visibility."""
    prefs = load_tab_prefs()
    win = Toplevel(parent)
    win.title("Tab Options")

    vars = {}
    row = 0
    for tab in DEFAULT_TABS:
        var = BooleanVar(value=prefs.get(tab, True))
        vars[tab] = var
        Checkbutton(win, text=tab.capitalize(), variable=var).grid(
            row=row, column=0, sticky="w", padx=10, pady=2
        )
        row += 1

    def save():
        new_prefs = {k: v.get() for k, v in vars.items()}
        save_tab_prefs(new_prefs)
        win.destroy()

    Button(win, text="Save", command=save).grid(row=row, column=0, pady=10)
    win.grab_set()
    win.focus_set()
    win.wait_window()