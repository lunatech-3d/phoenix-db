import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from date_utils import parse_date_input, format_date_for_display
from biz_linkage import open_biz_linkage_popup

DB_PATH = "phoenix.db"

class EmployeeForm:
    def __init__(self, root, person_id=None, employment_id=None):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.person_id = person_id
        self.employment_id = employment_id
        self.root = root
        self.root.title("Edit Employment" if employment_id else "Add Employment")
        self.entries = {}
        self.biz_id = None
        self.setup_form()
        if employment_id:
            self.load_data()

    def setup_form(self):
        row_num = 0

        # Person display label (if coming from person record)
        if self.person_id:
            self.cursor.execute("SELECT first_name, middle_name, last_name FROM People WHERE id = ?", (self.person_id,))
            row = self.cursor.fetchone()
            full_name = " ".join(filter(None, row)) if row else "Unknown"
            ttk.Label(self.root, text=f"Employee: {full_name}", font=("Segoe UI", 10, "bold")).grid(row=row_num, column=0, columnspan=3, pady=(5, 15))
            row_num += 1

        # Business selection row
        ttk.Label(self.root, text="Business:").grid(row=row_num, column=0, padx=5, pady=5, sticky="e")
        self.biz_display = ttk.Label(self.root, text="(None Selected)", width=40, relief="sunken", anchor="w")
        self.biz_display.grid(row=row_num, column=1, padx=5, pady=5, sticky="w")

        def set_business_id(biz_id):
            self.cursor.execute("SELECT biz_name FROM Biz WHERE biz_id = ?", (biz_id,))
            row = self.cursor.fetchone()
            if row:
                self.biz_display.config(text=row[0])
                self.biz_id = biz_id

        ttk.Button(self.root, text="Lookup", command=lambda: open_biz_linkage_popup(set_business_id)).grid(
            row=row_num, column=2, padx=5, pady=5
        )
        row_num += 1

        # Fields: Job Title, Start/End Date, Notes, URL
        labels = ["Position", "Start Date", "End Date", "Notes", "URL"]
        for i, label in enumerate(labels):
            ttk.Label(self.root, text=label + ":").grid(row=row_num + i, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(self.root, width=40)
            entry.grid(row=row_num + i, column=1, padx=5, pady=5, sticky="w")
            self.entries[label] = entry

        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.grid(row=row_num + len(labels), column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.root.destroy).pack(side="left", padx=5)

    def load_data(self):
        self.cursor.execute("""
            SELECT biz_id, job_title, start_date, start_date_precision,
                   end_date, end_date_precision, notes, url, person_id
            FROM BizEmployment
            WHERE id = ?
        """, (self.employment_id,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Employment record not found.")
            self.root.destroy()
            return

        self.biz_id = row[0]
        self.person_id = row[8]

        self.cursor.execute("SELECT biz_name FROM Biz WHERE biz_id = ?", (self.biz_id,))
        biz_row = self.cursor.fetchone()
        if biz_row:
            self.biz_display.config(text=biz_row[0])

        fields = ["Position", "Start Date", "End Date", "Notes", "URL"]
        values = [row[1], format_date_for_display(row[2], row[3]),
                  format_date_for_display(row[4], row[5]), row[6], row[7]]

        for key, value in zip(fields, values):
            self.entries[key].insert(0, value)

    def save(self):
        try:
            if not self.biz_id:
                messagebox.showerror("Missing Business", "Please select a business.")
                return

            job_title = self.entries["Position"].get().strip()
            notes = self.entries["Notes"].get().strip()
            url = self.entries["URL"].get().strip()
            start_date, start_prec = parse_date_input(self.entries["Start Date"].get().strip())
            end_input = self.entries["End Date"].get().strip()
            end_date, end_prec = parse_date_input(end_input) if end_input else (None, None)

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        if not self.person_id:
            messagebox.showerror("Missing Person", "No person ID provided.")
            return

        if self.employment_id:
            self.cursor.execute("""
                UPDATE BizEmployment SET biz_id=?, person_id=?, job_title=?,
                    start_date=?, start_date_precision=?,
                    end_date=?, end_date_precision=?,
                    notes=?, url=?
                WHERE id=?
            """, (
                self.biz_id, self.person_id, job_title,
                start_date, start_prec,
                end_date, end_prec,
                notes, url, self.employment_id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO BizEmployment (
                    biz_id, person_id, job_title,
                    start_date, start_date_precision,
                    end_date, end_date_precision,
                    notes, url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.biz_id, self.person_id, job_title,
                start_date, start_prec,
                end_date, end_prec,
                notes, url
            ))

        self.conn.commit()
        self.root.destroy()


def open_employee_editor(person_id=None, employment_id=None):
    root = tk.Tk()
    app = EmployeeForm(root, person_id=person_id, employment_id=employment_id)
    root.mainloop()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Employee Editor")
    parser.add_argument("--for-person", type=int, help="Person ID to add employment for")
    parser.add_argument("--edit-employment", type=int, help="Employment ID to edit")
    args = parser.parse_args()

    root = tk.Tk()
    app = EmployeeForm(root, person_id=args.for_person, employment_id=args.edit_employment)
    root.geometry("600x300")
    root.mainloop()


if __name__ == "__main__":
    main()
