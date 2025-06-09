# biz_ownership.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
from date_utils import parse_date_input, format_date_for_display
from biz_linkage import open_biz_linkage_popup


DB_PATH = "phoenix.db"

class OwnershipForm:
    def __init__(self, root, person_id=None, ownership_id=None):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.person_id = person_id
        self.ownership_id = ownership_id
        self.biz_id = biz_id
        self.root = root
        self.root.title("Edit Ownership" if ownership_id else "Add Ownership")
        self.entries = {}
        self.setup_form()
        if ownership_id:
            self.load_data()

    def setup_form(self):
        # Person name label
        if self.person_id:
            self.cursor.execute("""
                SELECT first_name, middle_name, last_name FROM People WHERE id = ?
            """, (self.person_id,))
            row = self.cursor.fetchone()
            full_name = " ".join(filter(None, row)) if row else "Unknown"
            ttk.Label(self.root, text=f"Owner: {full_name}", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(5, 15))

        # -- Business Lookup Section --
        # -- Business Display / Lookup Section --
        if self.biz_id:
            self.cursor.execute("SELECT biz_name FROM Biz WHERE biz_id = ?", (self.biz_id,))
            row = self.cursor.fetchone()
            name = row[0] if row else '(Unknown)'
            ttk.Label(self.root, text='Business:').grid(row=1, column=0, padx=5, pady=5, sticky='e')
            ttk.Label(self.root, text=name, width=40, relief='sunken', anchor='w').grid(row=1, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        else:
            ttk.Label(self.root, text='Business:').grid(row=1, column=0, padx=5, pady=5, sticky='e')
            self.biz_display = ttk.Label(self.root, text='(None Selected)', width=40, relief='sunken', anchor='w')
            self.biz_display.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            def set_business_id(biz_id):
                self.cursor.execute("SELECT biz_name FROM Biz WHERE biz_id = ?", (biz_id,))
                row = self.cursor.fetchone()
                if row:
                    self.biz_display.config(text=row[0])
                    self.biz_id = biz_id
            ttk.Button(self.root, text='Lookup', command=lambda: open_biz_linkage_popup(set_business_id)).grid(row=1, column=2, padx=5, pady=5)
        self.biz_display = ttk.Label(self.root, text="(None Selected)", width=40, relief="sunken", anchor="w")
        self.biz_display.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        def set_business_id(biz_id):
            self.cursor.execute("SELECT biz_name FROM Biz WHERE biz_id = ?", (biz_id,))
            row = self.cursor.fetchone()
            if row:
                self.biz_display.config(text=row[0])
                self.biz_id = biz_id  # Save the selected business ID

        ttk.Button(self.root, text="Lookup", command=lambda: open_biz_linkage_popup(set_business_id)).grid(
            row=1, column=2, padx=5, pady=5
        )

        # -- Input Fields --
        labels = ["Ownership Type", "Title", "Start Date", "End Date", "Notes"]
        for i, label in enumerate(labels, start=2):
            ttk.Label(self.root, text=label + ":").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(self.root, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            self.entries[label] = entry

        # -- Buttons --
        btn_frame = ttk.Frame(self.root)
        btn_frame.grid(row=len(labels)+2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.root.destroy).pack(side="left", padx=5)


    from date_utils import format_date_for_display  # Ensure this is imported

    def load_data(self):
        self.cursor.execute("""
            SELECT biz_id, ownership_type, title, start_date, start_date_precision,
                   end_date, end_date_precision, notes, person_id
            FROM BizOwnership
            WHERE biz_ownership_id = ?
        """, (self.ownership_id,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Ownership record not found.")
            self.root.destroy()
            return

        self.biz_id = row[0]
        self.cursor.execute("SELECT biz_name FROM Biz WHERE biz_id = ?", (self.biz_id,))
        biz_row = self.cursor.fetchone()
        self.biz_display.config(text=biz_row[0] if biz_row else "(Unknown Business)")

        ownership_type = row[1]
        title = row[2]
        start_date = format_date_for_display(row[3], row[4])
        end_date = format_date_for_display(row[5], row[6])
        notes = row[7]
        self.person_id = row[8]

        # Populate the fields correctly
        field_map = {
            "Ownership Type": ownership_type,
            "Title": title,
            "Start Date": start_date,
            "End Date": end_date,
            "Notes": notes
        }

        for key, value in field_map.items():
            entry = self.entries.get(key)
            if isinstance(entry, tk.Entry):
                entry.delete(0, tk.END)
                entry.insert(0, value if value else "")

    def save(self):
        try:
            biz_id = self.biz_id
            if not biz_id:
                messagebox.showerror("Missing Business", "Please select a business.")
                return
            ownership_type = self.entries["Ownership Type"].get().strip()
            title = self.entries["Title"].get().strip()
            notes = self.entries["Notes"].get().strip()
            start_date, start_prec = parse_date_input(self.entries["Start Date"].get().strip())
            end_date, end_prec = parse_date_input(self.entries["End Date"].get().strip()) if self.entries["End Date"].get().strip() else (None, None)
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        if not self.person_id:
            messagebox.showerror("Missing Person", "No person ID provided.")
            return

        if self.ownership_id:
            self.cursor.execute("""
                UPDATE BizOwnership SET biz_id=?, person_id=?, ownership_type=?, title=?,
                    start_date=?, start_date_precision=?,
                    end_date=?, end_date_precision=?,
                    notes=?
                WHERE biz_ownership_id=?
            """, (biz_id, self.person_id, ownership_type, title,
                  start_date, start_prec,
                  end_date, end_prec,
                  notes, self.ownership_id))
        else:
            self.cursor.execute("""
                INSERT INTO BizOwnership (
                    biz_id, person_id, ownership_type, title,
                    start_date, start_date_precision,
                    end_date, end_date_precision, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (biz_id, self.person_id, ownership_type, title,
                  start_date, start_prec, end_date, end_prec, notes))

        self.conn.commit()
        self.root.destroy()


def open_owner_editor(person_id=None, ownership_id=None, parent=None):
    win = tk.Toplevel(parent) if parent else tk.Tk()
    OwnershipForm(win, person_id=person_id, ownership_id=ownership_id)
    if not parent:
        win.mainloop()

def main():
    person_id = None
    ownership_id = None
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == "--for-person":
            person_id = int(args[i+1])
        if args[i] == "--edit-ownership":
            ownership_id = int(args[i+1])

    root = tk.Tk()
    app = OwnershipForm(root, person_id=person_id, ownership_id=ownership_id)
    root.mainloop()

if __name__ == "__main__":
    main()
