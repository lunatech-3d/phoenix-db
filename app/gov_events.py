import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu, apply_context_menu_to_all_entries
from app.date_utils import (
    parse_date_input,
    format_date_for_display,
    add_date_format_menu,
    date_sort_key,
)


class EventForm:
    """Form for adding or editing a government event."""

    def __init__(self, master, agency_id, event_id=None):
        self.master = master
        self.agency_id = agency_id
        self.event_id = event_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}
        self.setup_form()
        if event_id:
            self.load_data()

    def setup_form(self):
        self.master.title("Edit Event" if self.event_id else "Add Event")
        row = 0

        ttk.Label(self.master, text="Title:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        title_entry = ttk.Entry(self.master, width=60)
        title_entry.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        create_context_menu(title_entry)
        self.entries["title"] = title_entry
        row += 1

        ttk.Label(self.master, text="Type:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        type_entry = ttk.Entry(self.master, width=40)
        type_entry.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        create_context_menu(type_entry)
        self.entries["type"] = type_entry
        row += 1

        ttk.Label(self.master, text="Date:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        date_entry = ttk.Entry(self.master, width=20)
        date_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        create_context_menu(date_entry)
        add_date_format_menu(date_entry)
        self.entries["date"] = date_entry
        row += 1

        ttk.Label(self.master, text="Location:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        loc_entry = ttk.Entry(self.master, width=60)
        loc_entry.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        create_context_menu(loc_entry)
        self.entries["location"] = loc_entry
        row += 1

        ttk.Label(self.master, text="Source ID:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        source_entry = ttk.Entry(self.master, width=20)
        source_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        create_context_menu(source_entry)
        self.entries["source_id"] = source_entry
        row += 1

        ttk.Label(self.master, text="Link URL:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        link_entry = ttk.Entry(self.master, width=60)
        link_entry.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        create_context_menu(link_entry)
        self.entries["link_url"] = link_entry
        row += 1

        ttk.Label(self.master, text="Description:").grid(row=row, column=0, sticky="ne", padx=5, pady=5)
        desc_text = tk.Text(self.master, width=60, height=4)
        desc_text.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        create_context_menu(desc_text)
        self.entries["description"] = desc_text
        row += 1

        ttk.Label(self.master, text="Original Text:").grid(row=row, column=0, sticky="ne", padx=5, pady=5)
        orig_text = tk.Text(self.master, width=60, height=6)
        orig_text.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        create_context_menu(orig_text)
        self.entries["original_text"] = orig_text
        row += 1

        btn = ttk.Frame(self.master)
        btn.grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(btn, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

        apply_context_menu_to_all_entries(self.master)
        self.master.resizable(False, False)

    def load_data(self):
        self.cursor.execute(
            """SELECT agency_id, title, type, date, date_precision, location, description,
                       original_text, link_url, source_id
                   FROM GovEvents WHERE gov_event_id=?""",
            (self.event_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Event record not found.", parent=self.master)
            self.master.destroy()
            return
        (
            self.agency_id,
            title,
            typ,
            dt,
            prec,
            loc,
            desc,
            original,
            link,
            source,
        ) = row
        self.entries["title"].insert(0, title or "")
        self.entries["type"].insert(0, typ or "")
        self.entries["date"].insert(0, format_date_for_display(dt, prec) if dt else "")
        self.entries["location"].insert(0, loc or "")
        if desc:
            self.entries["description"].insert("1.0", desc)
        if original:
            self.entries["original_text"].insert("1.0", original)
        self.entries["link_url"].insert(0, link or "")
        self.entries["source_id"].insert(0, source or "")

    def save(self):
        try:
            date_raw = self.entries["date"].get().strip()
            date_val, date_prec = parse_date_input(date_raw) if date_raw else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e), parent=self.master)
            return
        data = {
            "agency_id": self.agency_id,
            "title": self.entries["title"].get().strip(),
            "type": self.entries["type"].get().strip(),
            "date": date_val,
            "date_precision": date_prec,
            "location": self.entries["location"].get().strip(),
            "description": self.entries["description"].get("1.0", tk.END).strip(),
            "original_text": self.entries["original_text"].get("1.0", tk.END).strip(),
            "link_url": self.entries["link_url"].get().strip(),
            "source_id": self.entries["source_id"].get().strip() or None,
        }
        if self.event_id:
            placeholders = ", ".join(f"{k}=?" for k in data.keys())
            self.cursor.execute(
                f"UPDATE GovEvents SET {placeholders} WHERE gov_event_id=?",
                (*data.values(), self.event_id),
            )
        else:
            columns = ", ".join(data.keys())
            marks = ", ".join("?" for _ in data)
            self.cursor.execute(
                f"INSERT INTO GovEvents ({columns}) VALUES ({marks})",
                tuple(data.values()),
            )
            self.event_id = self.cursor.lastrowid
        self.conn.commit()
        messagebox.showinfo("Saved", "Event record saved.", parent=self.master)
        self.master.destroy()


class EventManager:
    """List window for GovEvents records of a single agency."""

    def __init__(self, master, agency_id):
        self.master = master
        self.agency_id = agency_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.sort_column = None
        self.sort_reverse = False
        self.agency_name = self.get_agency_name()
        self.setup_filters()
        self.setup_tree()
        self.setup_buttons()
        self.load_events()

    def get_agency_name(self):
        self.cursor.execute(
            "SELECT name FROM GovAgency WHERE gov_agency_id=?", (self.agency_id,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else "(Unknown)"

    def setup_filters(self):
        header = ttk.Label(
            self.master, text=f"Agency: {self.agency_name}", font=("Segoe UI", 10, "bold")
        )
        header.pack(padx=10, pady=(10, 0), anchor="w")
        frame = ttk.Frame(self.master)
        frame.pack(fill="x", padx=10, pady=(5, 0))
        ttk.Label(frame, text="Title:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.title_entry = ttk.Entry(frame, width=30)
        self.title_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        create_context_menu(self.title_entry)
        ttk.Button(frame, text="Search", command=self.load_events).grid(row=0, column=2, padx=10)
        ttk.Button(frame, text="Clear", command=self.reset_filters).grid(row=0, column=3, padx=5)

    def reset_filters(self):
        self.title_entry.delete(0, tk.END)
        self.load_events()

    def setup_tree(self):
        columns = ("id", "title", "type", "date", "location", "source")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings", height=8)
        headings = {
            "title": "Title",
            "type": "Type",
            "date": "Date",
            "location": "Location",
            "source": "Source",
        }
        for col in columns:
            if col == "id":
                self.tree.column("id", width=0, stretch=False)
            else:
                self.tree.heading(col, text=headings.get(col, col.title()), command=lambda c=col: self.sort_by_column(c))
        self.tree.column("title", width=200, anchor="w")
        self.tree.column("type", width=120, anchor="w")
        self.tree.column("date", width=80, anchor="w")
        self.tree.column("location", width=150, anchor="w")
        self.tree.column("source", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_record)

    def setup_buttons(self):
        btn = ttk.Frame(self.master)
        btn.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn, text="Add", command=self.add_record).pack(side="left", padx=5)
        ttk.Button(btn, text="Edit", command=self.edit_record).pack(side="left", padx=5)
        ttk.Button(btn, text="Delete", command=self.delete_record).pack(side="left", padx=5)

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        reverse = self.sort_column == col and not self.sort_reverse
        if col == "date":
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self.sort_reverse = reverse
        self.sort_column = col

    def load_events(self):
        self.tree.delete(*self.tree.get_children())
        query = (
            "SELECT gov_event_id, title, type, date, date_precision, location, source_id "
            "FROM GovEvents WHERE agency_id=?"
        )
        params = [self.agency_id]
        title_filter = self.title_entry.get().strip()
        if title_filter:
            query += " AND title LIKE ?"
            params.append(f"%{title_filter}%")
        query += " ORDER BY date"
        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            eid, title, typ, dt, prec, loc, source = row
            disp_date = format_date_for_display(dt, prec) if dt else ""
            self.tree.insert("", "end", values=(eid, title, typ, disp_date, loc or "", source or ""))

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def add_record(self):
        win = tk.Toplevel(self.master)
        EventForm(win, self.agency_id)
        win.grab_set()
        self.master.wait_window(win)
        self.load_events()

    def edit_record(self, event=None):
        rid = self.get_selected_id()
        if not rid:
            return
        win = tk.Toplevel(self.master)
        EventForm(win, self.agency_id, event_id=rid)
        win.grab_set()
        self.master.wait_window(win)
        self.load_events()

    def delete_record(self):
        rid = self.get_selected_id()
        if not rid:
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected event?"):
            self.cursor.execute("DELETE FROM GovEvents WHERE gov_event_id=?", (rid,))
            self.conn.commit()
            self.load_events()


def open_event_editor(agency_id, event_id=None, parent=None):
    if parent is None:
        root = tk.Tk()
        EventForm(root, agency_id, event_id=event_id)
        root.geometry("700x500")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        EventForm(win, agency_id, event_id=event_id)
        win.grab_set()
        return win


def open_event_manager(agency_id, parent=None):
    if parent is None:
        root = tk.Tk()
        EventManager(root, agency_id)
        root.geometry("800x500")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        EventManager(win, agency_id)
        win.grab_set()
        return win


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage government events")
    parser.add_argument("agency_id", type=int, help="GovAgency ID")
    args = parser.parse_args()
    open_event_manager(args.agency_id)
    