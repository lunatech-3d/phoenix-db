import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu
from app.date_utils import parse_date_input, format_date_for_display
from app.person_linkage import person_search_popup


def edit_event(master, church_id, event_id=None, refresh=None):
    win = tk.Toplevel(master)
    EventEditor(win, church_id, event_id, refresh)
    win.grab_set()
    win.transient(master)
    return win


class EventEditor:
    def __init__(self, master, church_id, event_id=None, refresh=None):
        self.master = master
        self.church_id = church_id
        self.event_id = event_id
        self.refresh = refresh
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.person_id = None
        self.setup_form()
        if event_id:
            self.load_data()

    def setup_form(self):
        # Basic entry fields shown at the top of the form
        top_labels = [
            "Event Type",
            "Event Date",
            "End Date",
            "Description",
            "Link URL",
        ]

        self.entries = {}
        
        row = 0
        for label in top_labels:
            ttk.Label(self.master, text=label + ":").grid(
                row=row, column=0, sticky="e", padx=5, pady=5
            )
            entry = ttk.Entry(self.master, width=40)
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            create_context_menu(entry)
            self.entries[label] = entry
            row += 1

        # Original text should appear after the Link URL field
        ttk.Label(self.master, text="Original Text:").grid(
            row=row, column=0, sticky="ne", padx=5, pady=5
        )
        otext = tk.Text(self.master, width=40, height=6, wrap="word")
        otext.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        create_context_menu(otext)
        self.entries["Original Text"] = otext
        row += 1

        # Remaining entry fields
        for label in ["Curator Summary", "Tags"]:
            ttk.Label(self.master, text=label + ":").grid(
                row=row, column=0, sticky="e", padx=5, pady=5
            )
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            create_context_menu(entry)
            self.entries[label] = entry
            row += 1

        ttk.Label(self.master, text="Person:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        pframe = ttk.Frame(self.master)
        pframe.grid(row=row, column=1, sticky="w")
        self.person_label = ttk.Label(pframe, text="(none)", width=30, relief="sunken")
        self.person_label.pack(side="left")
        ttk.Button(pframe, text="Lookup", command=lambda: person_search_popup(self.set_person)).pack(side="left", padx=5)

        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=row+1, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

    def set_person(self, pid):
        if pid is None:
            self.person_label.config(text="(none)")
            self.person_id = None
            return
        self.cursor.execute("SELECT first_name, last_name FROM People WHERE id=?", (pid,))
        row = self.cursor.fetchone()
        if row:
            self.person_label.config(text=f"{row[0]} {row[1]}")
            self.person_id = pid

    def load_data(self):
        self.cursor.execute(
            """SELECT event_type, event_date, event_date_precision, end_date, end_date_precision,
                      description, original_text, person_id, link_url, curator_summary, event_context_tags
               FROM Church_Event WHERE church_event_id=?""",
            (self.event_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            return
        etype, sdate, sp, edate, ep, desc, original, pid, link, summ, tags = row
        self.entries["Event Type"].insert(0, etype or "")
        self.entries["Event Date"].insert(0, format_date_for_display(sdate, sp) if sdate else "")
        self.entries["End Date"].insert(0, format_date_for_display(edate, ep) if edate else "")
        self.entries["Description"].insert(0, desc or "")
        if original:
            self.entries["Original Text"].insert("1.0", original)
        self.entries["Link URL"].insert(0, link or "")
        self.entries["Curator Summary"].insert(0, summ or "")
        self.entries["Tags"].insert(0, tags or "")
        if pid:
            self.set_person(pid)

    def save(self):
        try:
            sdate_raw = self.entries["Event Date"].get().strip()
            edate_raw = self.entries["End Date"].get().strip()
            sdate, sp = parse_date_input(sdate_raw) if sdate_raw else (None, None)
            edate, ep = parse_date_input(edate_raw) if edate_raw else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return
        data = (
            self.entries["Event Type"].get().strip(),
            sdate,
            sp,
            edate,
            ep,
            self.entries["Description"].get().strip(),
            self.entries["Original Text"].get("1.0", tk.END).strip(),
            self.person_id,
            self.entries["Link URL"].get().strip(),
            self.entries["Curator Summary"].get().strip(),
            self.entries["Tags"].get().strip(),
            self.church_id,
        )
        if self.event_id:
            self.cursor.execute(
                """UPDATE Church_Event SET event_type=?, event_date=?, event_date_precision=?, end_date=?, end_date_precision=?,
                       description=?, original_text=?, person_id=?, link_url=?, curator_summary=?, event_context_tags=? WHERE church_event_id=?""",
                data[:-1] + (self.event_id,),
            )
        else:
            self.cursor.execute(
                """INSERT INTO Church_Event (event_type, event_date, event_date_precision, end_date, end_date_precision,
                       description, original_text, person_id, link_url, curator_summary, event_context_tags, church_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                data,
            )
            self.event_id = self.cursor.lastrowid
        self.conn.commit()
        if self.refresh:
            self.refresh()
        self.master.destroy()