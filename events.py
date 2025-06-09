import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
from date_utils import format_date_for_display

DB_PATH = "phoenix.db"

class EventBrowser:
    def __init__(self, master):
        self.master = master
        self.master.title("Event Management")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.filters = {}
        self.setup_ui()
        self.load_events()

    def setup_ui(self):
        # Search Frame
        search_frame = ttk.LabelFrame(self.master, text="Search Events")
        search_frame.pack(fill="x", padx=10, pady=5)

        # Title
        ttk.Label(search_frame, text="Title:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.filters["title"] = ttk.Entry(search_frame, width=30)
        self.filters["title"].grid(row=0, column=1, padx=5, pady=2, sticky="w")

        # Type
        ttk.Label(search_frame, text="Type:").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        self.filters["type"] = ttk.Entry(search_frame, width=20)
        self.filters["type"].grid(row=0, column=3, padx=5, pady=2, sticky="w")

        # Scope
        ttk.Label(search_frame, text="Scope:").grid(row=0, column=4, padx=5, pady=2, sticky="e")
        self.filters["scope"] = ttk.Entry(search_frame, width=15)
        self.filters["scope"].grid(row=0, column=5, padx=5, pady=2, sticky="w")

        ttk.Button(search_frame, text="Search", command=self.load_events).grid(row=0, column=6, padx=5)
        ttk.Button(search_frame, text="Clear", command=self.clear_filters).grid(row=0, column=7, padx=5)

        # Treeview
        self.tree = ttk.Treeview(self.master, columns=("id", "title", "type", "scope", "date", "location"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("type", text="Type")
        self.tree.heading("scope", text="Scope")
        self.tree.heading("date", text="Date")
        self.tree.heading("location", text="Location")

        self.tree.column("id", width=40)
        self.tree.column("title", width=200)
        self.tree.column("type", width=100)
        self.tree.column("scope", width=80)
        self.tree.column("date", width=100)
        self.tree.column("location", width=180)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Button Frame
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_frame, text="Add", command=self.add_event).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_event).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_event).pack(side="left", padx=5)

    def clear_filters(self):
        for field in self.filters.values():
            field.delete(0, tk.END)
        self.load_events()

    def load_events(self):
        self.tree.delete(*self.tree.get_children())
        query = "SELECT id, title, type, scope, date, location FROM Events WHERE 1=1"
        params = []

        if self.filters["title"].get().strip():
            query += " AND title LIKE ?"
            params.append(f"%{self.filters['title'].get().strip()}%")
        if self.filters["type"].get().strip():
            query += " AND type LIKE ?"
            params.append(f"%{self.filters['type'].get().strip()}%")
        if self.filters["scope"].get().strip():
            query += " AND scope LIKE ?"
            params.append(f"%{self.filters['scope'].get().strip()}%")

        query += " ORDER BY date DESC"

        for row in self.cursor.execute(query, params):
            formatted_date = format_date_for_display(row[4]) if row[4] else ""
            self.tree.insert('', 'end', values=(row[0], row[1], row[2], row[3], formatted_date, row[5]))

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def add_event(self):
        subprocess.Popen(["python", "edit_event.py"])

    def edit_event(self):
        event_id = self.get_selected_id()
        if event_id:
            subprocess.Popen(["python", "edit_event.py", str(event_id)])

    def delete_event(self):
        event_id = self.get_selected_id()
        if not event_id:
            return
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this event?")
        if confirm:
            self.cursor.execute("DELETE FROM Events WHERE id = ?", (event_id,))
            self.conn.commit()
            self.load_events()

    def on_double_click(self, event):
        self.edit_event()

if __name__ == '__main__':
    root = tk.Tk()
    app = EventBrowser(root)
    root.mainloop()
