import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from app.config import DB_PATH
from app.source.sources import add_source


def open_source_link_editor(table_name, record_id, field_name=None):
    """Launch a popup window to manage Source_Link records."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS Source_Link (
            link_id INTEGER PRIMARY KEY,
            table_name TEXT,
            record_id INTEGER,
            field_name TEXT,
            source_id INTEGER,
            original_text TEXT,
            url_override TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()

    def fetch_sources():
        cur.execute("SELECT id, title FROM Sources ORDER BY title")
        return cur.fetchall()

    def refresh_tree():
        for i in tree.get_children():
            tree.delete(i)
        cur.execute(
            """SELECT sl.link_id, sl.field_name, s.title, sl.original_text,
                      sl.url_override, sl.created_at
                   FROM Source_Link sl
                   JOIN Sources s ON sl.source_id = s.id
                   WHERE sl.table_name=? AND sl.record_id=?
                   ORDER BY sl.created_at DESC""",
            (table_name, record_id),
        )
        for row in cur.fetchall():
            tree.insert("", "end", values=row[1:])

    def save_link():
        if not source_var.get():
            messagebox.showerror("Missing", "Please select a source")
            return
        cur.execute(
            "INSERT INTO Source_Link (table_name, record_id, field_name, source_id, original_text, url_override, notes)"
            " VALUES (?,?,?,?,?,?,?)",
            (
                table_name,
                record_id,
                field_var.get() or None,
                source_dropdown.ids[source_var.get()],
                original_text.get("1.0", "end").strip(),
                url_entry.get().strip() or None,
                notes_text.get("1.0", "end").strip() or None,
            ),
        )
        conn.commit()
        refresh_tree()
        original_text.delete("1.0", "end")
        url_entry.delete(0, "end")
        notes_text.delete("1.0", "end")

    win = tk.Toplevel()
    win.title("Source Links")
    ttk.Label(win, text=f"Table: {table_name}  ID: {record_id}").grid(row=0, column=0, columnspan=4, pady=(5,10))

    ttk.Label(win, text="Source:").grid(row=1, column=0, sticky="e")
    source_var = tk.StringVar()
    source_dropdown = ttk.Combobox(win, textvariable=source_var, width=40)
    sources = fetch_sources()
    source_dropdown['values'] = [title for _, title in sources]
    source_dropdown.ids = {title: sid for sid, title in sources}
    source_dropdown.grid(row=1, column=1, columnspan=3, sticky="we", padx=5, pady=2)

    ttk.Label(win, text="Field:").grid(row=2, column=0, sticky="e")
    field_var = tk.StringVar(value=field_name or "")
    field_entry = ttk.Entry(win, textvariable=field_var, width=40)
    field_entry.grid(row=2, column=1, columnspan=3, sticky="we", padx=5, pady=2)

    ttk.Label(win, text="Original Text:").grid(row=3, column=0, sticky="ne")
    original_text = tk.Text(win, width=50, height=4)
    original_text.grid(row=3, column=1, columnspan=3, padx=5, pady=2, sticky="we")

    ttk.Label(win, text="URL Override:").grid(row=4, column=0, sticky="e")
    url_entry = ttk.Entry(win, width=40)
    url_entry.grid(row=4, column=1, columnspan=3, sticky="we", padx=5, pady=2)

    ttk.Label(win, text="Notes:").grid(row=5, column=0, sticky="ne")
    notes_text = tk.Text(win, width=50, height=3)
    notes_text.grid(row=5, column=1, columnspan=3, padx=5, pady=2, sticky="we")

    ttk.Button(win, text="Save", command=save_link).grid(row=6, column=1, pady=5)
    ttk.Button(win, text="Close", command=win.destroy).grid(row=6, column=2, pady=5)

    columns = ("Field", "Source", "Original Text", "URL", "Created")
    tree = ttk.Treeview(win, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.grid(row=7, column=0, columnspan=4, padx=5, pady=10, sticky="nsew")
    win.grid_rowconfigure(7, weight=1)
    win.grid_columnconfigure(1, weight=1)

    refresh_tree()
    win.mainloop()