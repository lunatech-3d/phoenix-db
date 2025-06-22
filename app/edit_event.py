import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
from .config import PATHS, DB_PATH
from date_utils import parse_date_input, format_date_for_display

class EditEventForm:
    def __init__(self, master, event_id=None):
        self.master = master
        self.master.title("Edit Event" if event_id else "Add Event")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.event_id = event_id

        self.entries = {}
        self.setup_form()
        if event_id:
            self.load_event()

    def setup_form(self):
        frame = ttk.Frame(self.master)
        frame.pack(padx=10, pady=10, fill="x")

        labels = [
            ("title", "Title"),
            ("type", "Type"),
            ("scope", "Scope"),
            ("date", "Start Date"),
            ("date_precision", "Date Precision"),
            ("end_date", "End Date"),
            ("end_date_precision", "End Date Precision"),
            ("location", "Location"),
            ("link_url", "Link URL")
        ]

        for i, (field, label) in enumerate(labels):
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame, width=60)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.entries[field] = entry

        # Address dropdown placeholder (can be replaced with search popup)
        ttk.Label(frame, text="Address ID:").grid(row=len(labels), column=0, sticky="e", pady=2)
        self.address_entry = ttk.Entry(frame, width=20)
        self.address_entry.grid(row=len(labels), column=1, sticky="w", pady=2)

        # Source ID field
        ttk.Label(frame, text="Source ID:").grid(row=len(labels)+1, column=0, sticky="e", pady=2)
        self.source_entry = ttk.Entry(frame, width=20)
        self.source_entry.grid(row=len(labels)+1, column=1, sticky="w", pady=2)

        # Description and Summary text fields
        for j, field in enumerate(["description", "summary"]):
            ttk.Label(frame, text=field.capitalize() + ":").grid(row=len(labels)+2+j, column=0, sticky="ne", pady=2)
            text_box = tk.Text(frame, height=4, width=60)
            text_box.grid(row=len(labels)+2+j, column=1, pady=2, sticky="w")
            self.entries[field] = text_box

        # Save + Cancel Buttons
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save_event).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

    def load_event(self):
        self.cursor.execute("""
            SELECT title, type, scope, date, date_precision, end_date, end_date_precision,
                   location, address_id, description, summary, source_id, link_url
            FROM Events WHERE id = ?
        """, (self.event_id,))
        row = self.cursor.fetchone()
        if row:
            fields = ["title", "type", "scope", "date", "date_precision", "end_date", "end_date_precision",
                      "location", "address_id", "description", "summary", "source_id", "link_url"]
            for key, value in zip(fields, row):
                if key in ["description", "summary"]:
                    self.entries[key].delete("1.0", tk.END)
                    self.entries[key].insert("1.0", value or "")
                elif key == "address_id":
                    self.address_entry.delete(0, tk.END)
                    self.address_entry.insert(0, value or "")
                elif key == "source_id":
                    self.source_entry.delete(0, tk.END)
                    self.source_entry.insert(0, value or "")
                else:
                    self.entries[key].delete(0, tk.END)
                    self.entries[key].insert(0, value or "")

    def save_event(self):
        try:
            parsed_date, date_prec = parse_date_input(self.entries["date"].get().strip()) if self.entries["date"].get().strip() else (None, None)
            end_date_input = self.entries["end_date"].get().strip()
            parsed_end, end_prec = parse_date_input(end_date_input) if end_date_input else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return

        data = {
            "title": self.entries["title"].get().strip(),
            "type": self.entries["type"].get().strip(),
            "scope": self.entries["scope"].get().strip(),
            "date": parsed_date,
            "date_precision": date_prec,
            "end_date": parsed_end,
            "end_date_precision": end_prec,
            "location": self.entries["location"].get().strip(),
            "address_id": self.address_entry.get().strip() or None,
            "description": self.entries["description"].get("1.0", tk.END).strip(),
            "summary": self.entries["summary"].get("1.0", tk.END).strip(),
            "source_id": self.source_entry.get().strip() or None,
            "link_url": self.entries["link_url"].get().strip()
        }

        if self.event_id:
            placeholders = ", ".join(f"{k}=?" for k in data.keys())
            self.cursor.execute(f"UPDATE Events SET {placeholders} WHERE id = ?", (*data.values(), self.event_id))
        else:
            columns = ", ".join(data.keys())
            qmarks = ", ".join(["?"] * len(data))
            self.cursor.execute(f"INSERT INTO Events ({columns}) VALUES ({qmarks})", tuple(data.values()))
            self.event_id = self.cursor.lastrowid

        self.conn.commit()
        messagebox.showinfo("Saved", "Event record saved successfully.")
        self.master.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = EditEventForm(root)
    root.mainloop()
