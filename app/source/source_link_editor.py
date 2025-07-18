import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from app.config import DB_PATH
from app.source.sources import add_source

def open_source_link_editor(table_name, record_id, field_name=None):
    """Launch a popup window to manage Source_Link records."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS Source_Link (
            source_link_id INTEGER PRIMARY KEY,
            source_id INTEGER,
            table_name TEXT,
            record_id INTEGER,
            field_name TEXT,
            original_text TEXT,
            url_override TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()

    # Placeholder so nested functions can reference the widget before it's
    # created. The actual Treeview is assigned further below.
    tree = None

    def fetch_sources():
        cur.execute("SELECT id, title FROM Sources ORDER BY id")
        return cur.fetchall()

    def refresh_source_list(selected_id=None):
        """Reload the source dropdown and optionally select ``selected_id``."""
        sources = fetch_sources()
        source_dropdown['values'] = [title for _, title in sources]
        source_dropdown.ids = {title: sid for sid, title in sources}
        if selected_id:
            for title, sid in source_dropdown.ids.items():
                if sid == selected_id:
                    source_var.set(title)
                    break

    def add_new_source():
        new_id = add_source(win)
        refresh_source_list(new_id)

    def refresh_tree():
        """Reload the tree with Source_Link records for this table/record."""
        for i in tree.get_children():
            tree.delete(i)
        cur.execute(
            """
            SELECT sl.source_link_id, sl.field_name, s.title,
                   sl.original_text, sl.url_override, sl.created_at
              FROM Source_Link sl
              JOIN Sources s ON sl.source_id = s.id
             WHERE sl.table_name=? AND sl.record_id=?
             ORDER BY sl.created_at DESC
            """,
            (table_name, record_id),
        )
        for row in cur.fetchall():
            tree.insert("", "end", iid=row[0], values=row)

    current_id = None

    def clear_form():
        """Reset the entry widgets."""
        source_var.set("")
        field_var.set(field_name or "")
        original_text.delete("1.0", "end")
        url_entry.delete(0, "end")
        notes_text.delete("1.0", "end")

    def save_link():
        nonlocal current_id
        if not source_var.get():
            messagebox.showerror("Missing", "Please select a source", parent=win)
            return
        data = (
            field_var.get() or None,
            source_dropdown.ids[source_var.get()],
            original_text.get("1.0", "end").strip(),
            url_entry.get().strip() or None,
            notes_text.get("1.0", "end").strip() or None,
        )
        if current_id:
            cur.execute(
                """
                UPDATE Source_Link
                   SET field_name=?, source_id=?, original_text=?,
                       url_override=?, notes=?
                 WHERE source_link_id=?
                """,
                (*data, current_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO Source_Link (
                    table_name, record_id, field_name, source_id,
                    original_text, url_override, notes, created_at
                ) VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    table_name,
                    record_id,
                    *data,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        conn.commit()
        refresh_tree()
        clear_form()
        current_id = None

    def edit_link(event=None):
        nonlocal current_id
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record to edit.", parent=win)
            return
        current_id = selected[0]
        cur.execute(
            """
            SELECT source_id, field_name, original_text, url_override, notes
              FROM Source_Link WHERE source_link_id=?
            """,
            (current_id,),
        )
        row = cur.fetchone()
        if not row:
            return
        sid, fld, orig, url, notes = row
        for title, sid_val in source_dropdown.ids.items():
            if sid_val == sid:
                source_var.set(title)
                break
        field_var.set(fld or "")
        original_text.delete("1.0", "end")
        original_text.insert("1.0", orig or "")
        url_entry.delete(0, "end")
        if url:
            url_entry.insert(0, url)
        notes_text.delete("1.0", "end")
        if notes:
            notes_text.insert("1.0", notes)

    def delete_link():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record to delete.", parent=win)
            return
        link_id = selected[0]
        if messagebox.askyesno("Confirm Delete", "Delete selected source link?", parent=win):
            cur.execute("DELETE FROM Source_Link WHERE source_link_id=?", (link_id,))
            conn.commit()
            refresh_tree()

    win = tk.Toplevel()
    win.title("Source Links")
    ttk.Label(win, text=f"Table: {table_name}  ID: {record_id}").grid(row=0, column=0, columnspan=4, pady=(5,10))

    ttk.Label(win, text="Source:").grid(row=1, column=0, sticky="e")
    source_var = tk.StringVar()
    source_dropdown = ttk.Combobox(win, textvariable=source_var, width=40)
    source_dropdown.grid(row=1, column=1, columnspan=2, sticky="we", padx=5, pady=2)
    ttk.Button(win, text="+ New Source", command=add_new_source).grid(row=1, column=3, sticky="w", padx=5, pady=2)
    refresh_source_list()
    
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

    from app.context_menu import create_context_menu
    for widget in (source_dropdown, field_entry, original_text, url_entry, notes_text):
        create_context_menu(widget)

    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=8, column=0, columnspan=4, pady=5)
    ttk.Button(btn_frame, text="Save", command=save_link).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Edit", command=edit_link).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Delete", command=delete_link).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side="left", padx=5)
    
    columns = ("id", "Field", "Source", "Original Text", "URL", "Created")
    tree = ttk.Treeview(win, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.column("id", width=0, stretch=False)
    tree.grid(row=7, column=0, columnspan=4, padx=5, pady=10, sticky="nsew")
    tree.bind("<Double-1>", edit_link)
    win.grid_rowconfigure(7, weight=1)
    win.grid_columnconfigure(1, weight=1)

    refresh_tree()
    win.mainloop()