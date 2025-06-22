import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox

# ----------------------------
# Legal Notices Functions
# ----------------------------

def initialize_legal_notice_section(frame_records, connection, person_id):
    cursor = connection.cursor()

    # Section frame
    notice_frame = ttk.LabelFrame(frame_records, text="Legal Notices")
    notice_frame.pack(fill='x', padx=5, pady=5)

    # Buttons frame
    button_frame = ttk.Frame(notice_frame)
    button_frame.pack(fill='x', padx=5, pady=5)

    ttk.Button(button_frame, text="Add", command=lambda: add_legal_notice(cursor, tree, person_id)).pack(side='left', padx=2)
    ttk.Button(button_frame, text="Edit", command=lambda: edit_legal_notice(cursor, tree, person_id)).pack(side='left', padx=2)
    ttk.Button(button_frame, text="Delete", command=lambda: delete_legal_notice(cursor, tree, person_id)).pack(side='left', padx=2)

    # Treeview for notices
    columns = ("notice_id", "Type", "Date Published", "Execution Date", "Description", "Notes")
    tree = ttk.Treeview(notice_frame, columns=columns, show='headings', height=5)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120 if col != "Description" else 300, stretch=False)

    tree.column("notice_id", width=0, stretch=False)  # hide ID
    tree.heading("notice_id", text="")

    scrollbar = ttk.Scrollbar(notice_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="x", expand=True)
    scrollbar.pack(side="right", fill="y")

    return tree

def load_legal_notices(cursor, tree, person_id):
    tree.delete(*tree.get_children())
    cursor.execute("""
        SELECT ln.notice_id, ln.notice_type, ln.date_published, ln.execution_date,
               ln.property_description, ln.notes
        FROM LegalNotices ln
        JOIN LegalNoticeParties lnp ON ln.notice_id = lnp.notice_id
        WHERE lnp.person_id = ?
        ORDER BY ln.date_published
    """, (person_id,))

    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

def add_legal_notice(cursor, tree, person_id):
    window = tk.Toplevel()
    window.title("Add Legal Notice")
    form_frame = ttk.Frame(window, padding=10)
    form_frame.pack(fill='both', expand=True)

    fields = [
        ("Type", ""), ("Date Published", ""), ("Execution Date", ""),
        ("Description", ""), ("Notes", "")
    ]
    entries = {}
    for i, (label, _) in enumerate(fields):
        ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=5)
        entry = ttk.Entry(form_frame, width=60)
        entry.grid(row=i, column=1, padx=5, pady=5)
        entries[label] = entry

    def save():
        try:
            cursor.execute("""
                INSERT INTO LegalNotices (notice_type, date_published, execution_date, property_description, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entries["Type"].get(), entries["Date Published"].get(), entries["Execution Date"].get(),
                entries["Description"].get(), entries["Notes"].get()
            ))
            notice_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO LegalNoticeParties (notice_id, person_id, party_role)
                VALUES (?, ?, ?)
            """, (notice_id, person_id, "Mentioned"))

            cursor.connection.commit()
            load_legal_notices(cursor, tree, person_id)
            window.destroy()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    ttk.Button(form_frame, text="Save", command=save).grid(row=len(fields), column=0, padx=5, pady=10)
    ttk.Button(form_frame, text="Cancel", command=window.destroy).grid(row=len(fields), column=1, padx=5, pady=10)

def edit_legal_notice(cursor, tree, person_id):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Select Record", "Please select a legal notice to edit.")
        return

    values = tree.item(selected[0])["values"]
    notice_id = values[0]

    window = tk.Toplevel()
    window.title("Edit Legal Notice")
    form_frame = ttk.Frame(window, padding=10)
    form_frame.pack(fill='both', expand=True)

    labels = ["Type", "Date Published", "Execution Date", "Description", "Notes"]
    entries = {}
    for i, label in enumerate(labels):
        ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=5)
        entry = ttk.Entry(form_frame, width=60)
        entry.grid(row=i, column=1, padx=5, pady=5)
        entry.insert(0, values[i+1])
        entries[label] = entry

    def update():
        try:
            cursor.execute("""
                UPDATE LegalNotices SET
                    notice_type = ?, date_published = ?, execution_date = ?,
                    property_description = ?, notes = ?
                WHERE notice_id = ?
            """, (
                entries["Type"].get(), entries["Date Published"].get(), entries["Execution Date"].get(),
                entries["Description"].get(), entries["Notes"].get(), notice_id
            ))
            cursor.connection.commit()
            load_legal_notices(cursor, tree, person_id)
            window.destroy()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    ttk.Button(form_frame, text="Update", command=update).grid(row=len(labels), column=0, padx=5, pady=10)
    ttk.Button(form_frame, text="Cancel", command=window.destroy).grid(row=len(labels), column=1, padx=5, pady=10)

def delete_legal_notice(cursor, tree, person_id):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Select Record", "Please select a legal notice to delete.")
        return

    notice_id = tree.item(selected[0])["values"][0]
    if messagebox.askyesno("Confirm", "Are you sure you want to delete this legal notice?"):
        try:
            cursor.execute("DELETE FROM LegalNoticeParties WHERE notice_id = ?", (notice_id,))
            cursor.execute("DELETE FROM LegalNotices WHERE notice_id = ?", (notice_id,))
            cursor.connection.commit()
            load_legal_notices(cursor, tree, person_id)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
