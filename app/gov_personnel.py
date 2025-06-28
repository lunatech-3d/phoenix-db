import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from app.config import DB_PATH
from app.context_menu import create_context_menu, apply_context_menu_to_all_entries
from app.date_utils import parse_date_input, format_date_for_display, date_sort_key, add_date_format_menu
from app.person_linkage import person_search_popup


class PersonnelForm:
    """Form for adding or editing a GovPersonnel record."""

    def __init__(self, master, position_id=None, personnel_id=None, person_id=None):
        self.master = master
        self.position_id = position_id
        self.personnel_id = personnel_id
        self.person_id = person_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}
        self.position_lookup = {}
        self.setup_form()
        if personnel_id:
            self.load_data()
        elif person_id:
            self.set_person_id(person_id)

    def setup_form(self):
        self.master.title("Edit Personnel" if self.personnel_id else "Add Personnel")
        row = 0

        ttk.Label(self.master, text="Selected Person:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        pframe = ttk.Frame(self.master)
        pframe.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        self.person_display = ttk.Label(pframe, text="(none)", width=40, relief="sunken", anchor="w")
        self.person_display.pack(side="left", padx=(0, 5))
        ttk.Button(pframe, text="Lookup", command=lambda: person_search_popup(self.set_person_id)).pack(side="left")
        ttk.Button(pframe, text="Clear", command=lambda: self.set_person_id(None)).pack(side="left")
        row += 1

        if self.position_id is None:
            ttk.Label(self.master, text="Position:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            self.position_combo = ttk.Combobox(self.master, state="readonly", width=40)
            self.position_combo.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="w")
            self.load_positions()
            row += 1
        else:
            self.cursor.execute(
                "SELECT title FROM GovPosition WHERE gov_position_id=?", (self.position_id,)
            )
            row_data = self.cursor.fetchone()
            title = row_data[0] if row_data else "Unknown"
            ttk.Label(self.master, text=f"Position: {title}").grid(
                row=row, column=0, columnspan=3, padx=5, pady=5, sticky="w"
            )
            row += 1

        for label in ["Start Date", "End Date", "Notes", "Source ID"]:
            ttk.Label(self.master, text=label + ":").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(self.master, width=40)
            entry.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="w")
            create_context_menu(entry)
            if label in ("Start Date", "End Date"):
                add_date_format_menu(entry)
            self.entries[label] = entry
            row += 1

        ttk.Label(self.master, text="Original Text:").grid(row=row, column=0, padx=5, pady=5, sticky="ne")
        otext = tk.Text(self.master, width=50, height=5)
        otext.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        create_context_menu(otext)
        self.entries["Original Text"] = otext
        row += 1

        btn = ttk.Frame(self.master)
        btn.grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(btn, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

        apply_context_menu_to_all_entries(self.master)
        self.master.resizable(False, False)

    def load_positions(self):
        self.cursor.execute("SELECT gov_position_id, title FROM GovPosition ORDER BY title")
        rows = self.cursor.fetchall()
        self.position_lookup = {title: pid for pid, title in rows}
        self.position_combo["values"] = list(self.position_lookup.keys())
        if self.position_id:
            for title, pid in self.position_lookup.items():
                if pid == self.position_id:
                    self.position_combo.set(title)
                    break

    def set_person_id(self, pid):
        if pid is None:
            self.person_display.config(text="(none)")
            self.person_id = None
            return
        self.cursor.execute(
            "SELECT first_name, middle_name, last_name, married_name FROM People WHERE id=?",
            (pid,),
        )
        row = self.cursor.fetchone()
        if row:
            parts = [row[0], row[1], row[2]]
            name = " ".join(part for part in parts if part)
            if row[3]:
                name += f" ({row[3]})"
            self.person_display.config(text=name)
            self.person_id = pid
        else:
            self.person_display.config(text="(not found)")
            self.person_id = None

    def load_data(self):
        self.cursor.execute(
            """SELECT person_id, position_id, start_date, start_precision,
                      end_date, end_precision, notes, original_text, source_id
                   FROM GovPersonnel WHERE gov_personnel_id=?""",
            (self.personnel_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Personnel record not found.", parent=self.master)
            self.master.destroy()
            return
        pid, pos_id, sdate, sprec, edate, eprec, notes, original, source_id = row
        self.set_person_id(pid)
        if self.position_id is None:
            self.position_id = pos_id
            for title, pid in self.position_lookup.items():
                if pid == pos_id:
                    self.position_combo.set(title)
                    break
        self.entries["Start Date"].insert(0, format_date_for_display(sdate, sprec) if sdate else "")
        self.entries["End Date"].insert(0, format_date_for_display(edate, eprec) if edate else "")
        self.entries["Notes"].insert(0, notes or "")
        self.entries["Source ID"].insert(0, source_id or "")
        if original:
            self.entries["Original Text"].insert("1.0", original)

    def save(self):
        if not self.person_id:
            messagebox.showerror("Missing", "Please select a person.", parent=self.master)
            return
        if self.position_id is None:
            title = self.position_combo.get()
            if not title or title not in self.position_lookup:
                messagebox.showerror("Missing", "Please select a position.", parent=self.master)
                return
            self.position_id = self.position_lookup[title]
        try:
            s_raw = self.entries["Start Date"].get().strip()
            e_raw = self.entries["End Date"].get().strip()
            start_date, start_prec = parse_date_input(s_raw) if s_raw else (None, None)
            end_date, end_prec = parse_date_input(e_raw) if e_raw else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e), parent=self.master)
            return
        notes = self.entries["Notes"].get().strip()
        source = self.entries["Source ID"].get().strip() or None
        original = self.entries["Original Text"].get("1.0", tk.END).strip()
        if self.personnel_id:
            self.cursor.execute(
                """UPDATE GovPersonnel
                   SET person_id=?, position_id=?, start_date=?, start_precision=?,
                       end_date=?, end_precision=?, notes=?, original_text=?, source_id=?
                 WHERE gov_personnel_id=?""",
                (
                    self.person_id,
                    self.position_id,
                    start_date,
                    start_prec,
                    end_date,
                    end_prec,
                    notes,
                    original,
                    source,
                    self.personnel_id,
                ),
            )
        else:
            self.cursor.execute(
                """INSERT INTO GovPersonnel
                        (person_id, position_id, start_date, start_precision,
                         end_date, end_precision, notes, original_text, source_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.person_id,
                    self.position_id,
                    start_date,
                    start_prec,
                    end_date,
                    end_prec,
                    notes,
                    original,
                    source,
                ),
            )
            self.personnel_id = self.cursor.lastrowid
        self.conn.commit()
        messagebox.showinfo("Saved", "Personnel record saved.", parent=self.master)
        self.master.destroy()


class PersonnelManager:
    """List window for GovPersonnel records of a single position."""

    def __init__(self, master, position_id):
        self.master = master
        self.position_id = position_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.sort_column = None
        self.sort_reverse = False
        self.position_title = self.get_position_title()
        self.setup_filters()
        self.setup_tree()
        self.setup_buttons()
        self.load_personnel()

    def get_position_title(self):
        self.cursor.execute("SELECT title FROM GovPosition WHERE gov_position_id=?", (self.position_id,))
        row = self.cursor.fetchone()
        return row[0] if row else "(Unknown)"

    def setup_filters(self):
        header = ttk.Label(self.master, text=f"Position: {self.position_title}", font=("Segoe UI", 10, "bold"))
        header.pack(padx=10, pady=(10, 0), anchor="w")
        filter_frame = ttk.Frame(self.master)
        filter_frame.pack(fill="x", padx=10, pady=(5, 0))
        ttk.Label(filter_frame, text="Last Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.last_entry = ttk.Entry(filter_frame, width=20)
        self.last_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        create_context_menu(self.last_entry)
        ttk.Button(filter_frame, text="Search", command=self.load_personnel).grid(row=0, column=2, padx=10)
        ttk.Button(filter_frame, text="Clear", command=self.reset_filters).grid(row=0, column=3, padx=5)

    def reset_filters(self):
        self.last_entry.delete(0, tk.END)
        self.load_personnel()

    def setup_tree(self):
        columns = ("id", "person", "start", "end", "notes", "source")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings", height=8)
        headings = {
            "person": "Person",
            "start": "Start",
            "end": "End",
            "notes": "Notes",
            "source": "Source",
        }
        for col in columns:
            if col == "id":
                self.tree.column("id", width=0, stretch=False)
            else:
                self.tree.heading(col, text=headings.get(col, col.title()), command=lambda c=col: self.sort_by_column(c))
        self.tree.column("person", width=200, anchor="w")
        self.tree.column("start", width=80, anchor="w")
        self.tree.column("end", width=80, anchor="w")
        self.tree.column("notes", width=150, anchor="w")
        self.tree.column("source", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_record)

    def setup_buttons(self):
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_record).pack(side="left", padx=5)

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        reverse = self.sort_column == col and not self.sort_reverse
        if col in ("start", "end"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self.sort_reverse = reverse
        self.sort_column = col

    def load_personnel(self):
        self.tree.delete(*self.tree.get_children())
        query = """
            SELECT gp.gov_personnel_id,
                   p.first_name || ' ' || IFNULL(p.middle_name||' ', '') || p.last_name ||
                       CASE WHEN p.married_name IS NOT NULL AND p.married_name != '' THEN ' ('||p.married_name||')' ELSE '' END,
                   gp.start_date, gp.start_precision,
                   gp.end_date, gp.end_precision,
                   gp.notes, gp.source_id
            FROM GovPersonnel gp
            JOIN People p ON gp.person_id = p.id
            WHERE gp.position_id=?
        """
        params = [self.position_id]
        last = self.last_entry.get().strip()
        if last:
            query += " AND p.last_name LIKE ?"
            params.append(f"%{last}%")
        query += " ORDER BY gp.start_date"
        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            pid, name, sd, sp, ed, ep, notes, source = row
            start = format_date_for_display(sd, sp) if sd else ""
            end = format_date_for_display(ed, ep) if ed else ""
            self.tree.insert("", "end", values=(pid, name, start, end, notes or "", source or ""))

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def add_record(self):
        win = tk.Toplevel(self.master)
        PersonnelForm(win, self.position_id)
        win.grab_set()
        self.master.wait_window(win)
        self.load_personnel()

    def edit_record(self, event=None):
        rid = self.get_selected_id()
        if not rid:
            return
        win = tk.Toplevel(self.master)
        PersonnelForm(win, self.position_id, personnel_id=rid)
        win.grab_set()
        self.master.wait_window(win)
        self.load_personnel()

    def delete_record(self):
        rid = self.get_selected_id()
        if not rid:
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected record?"):
            self.cursor.execute("DELETE FROM GovPersonnel WHERE gov_personnel_id=?", (rid,))
            self.conn.commit()
            self.load_personnel()


def open_personnel_editor(position_id=None, personnel_id=None, parent=None, person_id=None):
    if parent is None:
        root = tk.Tk()
        PersonnelForm(root, position_id=position_id, personnel_id=personnel_id, person_id=person_id)
        root.geometry("600x400")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        PersonnelForm(win, position_id=position_id, personnel_id=personnel_id, person_id=person_id)
        win.grab_set()
        return win


def open_personnel_manager(position_id, parent=None):
    if parent is None:
        root = tk.Tk()
        PersonnelManager(root, position_id)
        root.geometry("800x500")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        PersonnelManager(win, position_id)
        win.grab_set()
        return win


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage personnel assignments")
    parser.add_argument("position_id", type=int, help="GovPosition ID")
    args = parser.parse_args()
    open_personnel_manager(args.position_id)
