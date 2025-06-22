import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
from config import DB_PATH
import webbrowser
from datetime import datetime
from context_menu import create_context_menu
from date_utils import parse_date_input, format_date_for_display

def open_link(link):
    if link:
        webbrowser.open(link)

def create_embedded_life_events(parent, person_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    container = ttk.Frame(parent)
    container.pack(fill="x", expand=True, padx=10, pady=10)

    toggle_button = ttk.Button(container, text="Show Life Events")
    toggle_button.pack(anchor="w")

    frame = ttk.LabelFrame(container, text="Life Events")
    frame.pack(fill="both", expand=True, padx=5, pady=5)

    def toggle_frame():
        if frame.winfo_viewable():
            frame.pack_forget()
            toggle_button.config(text="Show Life Events")
        else:
            frame.pack(fill="both", expand=True, padx=5, pady=5)
            toggle_button.config(text="Hide Life Events")

    toggle_button.config(command=toggle_frame)

    tree = ttk.Treeview(frame, columns=("date", "type", "title"), show="headings")
    tree.heading("date", text="Date")
    tree.heading("type", text="Type")
    tree.heading("title", text="Title")
    tree.pack(fill="both", expand=True, padx=5, pady=5)

    def load_events():
        for row in tree.get_children():
            tree.delete(row)

        cursor.execute("""
            SELECT event_id, event_date, date_precision, event_type, event_title
            FROM LifeEvents
            WHERE person_id = ?
            ORDER BY event_date ASC
        """, (person_id,))
        for row in cursor.fetchall():
            event_id, date, precision, evt_type, title = row
            display_date = format_date_for_display(date, precision)
            tree.insert("", "end", iid=event_id, values=(display_date, evt_type, title))

    def add_event():
        EventEditorPopup(parent, conn, cursor, person_id, refresh_callback=load_events)

    def edit_event():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select an event to edit.")
            return
        event_id = selected[0]
        EventEditorPopup(parent, conn, cursor, person_id, event_id=event_id, refresh_callback=load_events)

    def delete_event():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select an event to delete.")
            return
        event_id = selected[0]
        if messagebox.askyesno("Confirm", "Delete this event?"):
            cursor.execute("DELETE FROM LifeEvents WHERE event_id = ?", (event_id,))
            conn.commit()
            load_events()

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=5)
    ttk.Button(btn_frame, text="Add", command=add_event).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Edit", command=edit_event).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Delete", command=delete_event).pack(side="left", padx=5)

    load_events()

class EventEditorPopup:
    def __init__(self, parent, conn, cursor, person_id, event_id=None, refresh_callback=None):
        self.conn = conn
        self.cursor = cursor
        self.person_id = person_id
        self.event_id = event_id
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Edit Life Event" if event_id else "Add Life Event")
        self.window.geometry("700x500")

        self.entries = {}

        labels = ["Type", "Title", "Date (MM-DD-YYYY, MM-YYYY, or YYYY)", "Location", "Source Title", "Source Link"]
        for i, label in enumerate(labels):
            ttk.Label(self.window, text=label + ":").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(self.window, width=60)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            create_context_menu(entry)
            self.entries[label] = entry

        ttk.Label(self.window, text="Description:").grid(row=6, column=0, padx=5, pady=5, sticky="ne")
        self.text_desc = tk.Text(self.window, width=60, height=10)
        self.text_desc.grid(row=6, column=1, padx=5, pady=5)
        create_context_menu(self.text_desc)

        btn_frame = ttk.Frame(self.window)
        btn_frame.grid(row=7, column=1, sticky="e", pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save_event).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side="left", padx=5)

        if event_id:
            self.load_event()

    def load_event(self):
        self.cursor.execute("""
            SELECT event_type, event_title, event_date, date_precision, location,
                   event_description, source_title, source_link
            FROM LifeEvents WHERE event_id = ?
        """, (self.event_id,))
        row = self.cursor.fetchone()
        if row:
            evt_type, title, date, prec, location, desc, source, link = row
            self.entries["Type"].insert(0, evt_type)
            self.entries["Title"].insert(0, title or "")
            self.entries["Date (MM-DD-YYYY, MM-YYYY, or YYYY)"].insert(0, format_date_for_display(date, prec))
            self.entries["Location"].insert(0, location or "")
            self.entries["Source Title"].insert(0, source or "")
            self.entries["Source Link"].insert(0, link or "")
            self.text_desc.insert("1.0", desc or "")

    def save_event(self):
        try:
            evt_type = self.entries["Type"].get().strip()
            evt_title = self.entries["Title"].get().strip()
            date_str = self.entries["Date (MM-DD-YYYY, MM-YYYY, or YYYY)"].get().strip()
            location = self.entries["Location"].get().strip()
            source = self.entries["Source Title"].get().strip()
            link = self.entries["Source Link"].get().strip()
            description = self.text_desc.get("1.0", tk.END).strip()
            event_date, date_prec = parse_date_input(date_str)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return

        if self.event_id:
            self.cursor.execute("""
                UPDATE LifeEvents SET event_type=?, event_title=?, event_date=?, date_precision=?,
                    location=?, event_description=?, source_title=?, source_link=?
                WHERE event_id = ?
            """, (evt_type, evt_title, event_date, date_prec, location, description, source, link, self.event_id))
        else:
            self.cursor.execute("""
                INSERT INTO LifeEvents (
                    person_id, event_type, event_title, event_date, date_precision,
                    location, event_description, source_title, source_link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.person_id, evt_type, evt_title, event_date, date_prec, location, description, source, link))

        self.conn.commit()
        if self.refresh_callback:
            self.refresh_callback()
        self.window.destroy()
