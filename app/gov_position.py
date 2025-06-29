import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu, apply_context_menu_to_all_entries
from app.gov_personnel import open_personnel_manager

class PositionForm:
    """Form for adding or editing a position within a government agency."""

    def __init__(self, master, agency_id, position_id=None):
        self.master = master
        self.agency_id = agency_id
        self.position_id = position_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.vars = {
            "is_elected": tk.BooleanVar(),
            "is_appointed": tk.BooleanVar(),
            "is_historical": tk.BooleanVar(),
        }
        self.entries = {}
        self.setup_form()
        if position_id:
            self.load_data()

    def setup_form(self):
        self.master.title("Edit Position" if self.position_id else "Add Position")
        row = 0

        ttk.Label(self.master, text="Title:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        title_entry = ttk.Entry(self.master, width=40)
        title_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        create_context_menu(title_entry)
        self.entries["title"] = title_entry
        row += 1

        ttk.Label(self.master, text="Description:").grid(row=row, column=0, sticky="ne", padx=5, pady=5)
        desc_text = tk.Text(self.master, width=50, height=4)
        desc_text.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        create_context_menu(desc_text)
        self.entries["description"] = desc_text
        row += 1

        check_frame = ttk.Frame(self.master)
        check_frame.grid(row=row, column=0, columnspan=2, pady=5)
        ttk.Checkbutton(check_frame, text="Elected", variable=self.vars["is_elected"]).pack(side="left", padx=5)
        ttk.Checkbutton(check_frame, text="Appointed", variable=self.vars["is_appointed"]).pack(side="left", padx=5)
        ttk.Checkbutton(check_frame, text="Historical", variable=self.vars["is_historical"]).pack(side="left", padx=5)
        row += 1

        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        if self.position_id:
            ttk.Button(btn_frame, text="Delete", command=self.delete).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

        apply_context_menu_to_all_entries(self.master)
        self.master.resizable(False, False)

    def load_data(self):
        self.cursor.execute(
            "SELECT title, description, is_elected, is_appointed, is_historical FROM GovPosition WHERE gov_position_id=?",
            (self.position_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Position record not found.", parent=self.master)
            self.master.destroy()
            return
        title, desc, elected, appointed, historical = row
        self.entries["title"].insert(0, title or "")
        if desc:
            self.entries["description"].insert("1.0", desc)
        self.vars["is_elected"].set(bool(elected))
        self.vars["is_appointed"].set(bool(appointed))
        self.vars["is_historical"].set(bool(historical))

    def save(self):
        title = self.entries["title"].get().strip()
        if not title:
            messagebox.showerror("Missing", "Title is required.", parent=self.master)
            return
        description = self.entries["description"].get("1.0", tk.END).strip()
        elected = 1 if self.vars["is_elected"].get() else 0
        appointed = 1 if self.vars["is_appointed"].get() else 0
        historical = 1 if self.vars["is_historical"].get() else 0

        if self.position_id:
            self.cursor.execute(
                """UPDATE GovPosition
                   SET title=?, description=?, is_elected=?, is_appointed=?, is_historical=?
                   WHERE gov_position_id=?""",
                (title, description, elected, appointed, historical, self.position_id),
            )
        else:
            self.cursor.execute(
                """INSERT INTO GovPosition (agency_id, title, description, is_elected, is_appointed, is_historical)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (self.agency_id, title, description, elected, appointed, historical),
            )
            self.position_id = self.cursor.lastrowid
        self.conn.commit()
        messagebox.showinfo("Saved", "Position saved.", parent=self.master)
        self.master.destroy()

    def delete(self):
        if not self.position_id:
            return
        self.cursor.execute("SELECT COUNT(*) FROM GovPersonnel WHERE position_id=?", (self.position_id,))
        count = self.cursor.fetchone()[0]
        if count:
            messagebox.showwarning(
                "Cannot Delete",
                f"Related personnel records exist ({count}). Remove them first.",
                parent=self.master,
            )
            return
        if messagebox.askyesno("Confirm Delete", "Delete this position?", parent=self.master):
            self.cursor.execute("DELETE FROM GovPosition WHERE gov_position_id=?", (self.position_id,))
            self.conn.commit()
            self.master.destroy()


class PositionManager:
    """List window showing all positions for an agency."""

    def __init__(self, master, agency_id):
        self.master = master
        self.agency_id = agency_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.sort_column = None
        self.sort_reverse = False
        self.setup_tree()
        self.setup_buttons()
        self.load_positions()

    def setup_tree(self):
        columns = ("id", "title", "elected", "appointed", "historical")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings", height=8)
        headings = {
            "title": "Title",
            "elected": "Elected",
            "appointed": "Appointed",
            "historical": "Historical",
        }
        for col in columns:
            if col == "id":
                self.tree.column("id", width=0, stretch=False)
            else:
                self.tree.heading(col, text=headings.get(col, col.title()), command=lambda c=col: self.sort_by_column(c))
        self.tree.column("title", width=240, anchor="w")
        for c in ("elected", "appointed", "historical"):
            self.tree.column(c, width=80, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_position)

    def setup_buttons(self):
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_position).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_position).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_position).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Personnel", command=self.open_personnel).pack(side="left", padx=5)

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(reverse=self.sort_column == col and not self.sort_reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self.sort_reverse = self.sort_column == col and not self.sort_reverse
        self.sort_column = col

    def load_positions(self):
        self.tree.delete(*self.tree.get_children())
        self.cursor.execute(
            "SELECT gov_position_id, title, is_elected, is_appointed, is_historical FROM GovPosition WHERE agency_id=? ORDER BY title",
            (self.agency_id,),
        )
        for pid, title, elected, appointed, historical in self.cursor.fetchall():
            self.tree.insert(
                "",
                "end",
                values=(pid, title, "Yes" if elected else "", "Yes" if appointed else "", "Yes" if historical else ""),
            )

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def add_position(self):
        win = tk.Toplevel(self.master)
        PositionForm(win, self.agency_id)
        win.grab_set()
        self.master.wait_window(win)
        self.load_positions()

    def edit_position(self, event=None):
        pid = self.get_selected_id()
        if not pid:
            return
        win = tk.Toplevel(self.master)
        PositionForm(win, self.agency_id, position_id=pid)
        win.grab_set()
        self.master.wait_window(win)
        self.load_positions()

    def delete_position(self):
        pid = self.get_selected_id()
        if not pid:
            return
        self.cursor.execute("SELECT COUNT(*) FROM GovPersonnel WHERE position_id=?", (pid,))
        count = self.cursor.fetchone()[0]
        if count:
            messagebox.showwarning(
                "Cannot Delete",
                f"Related personnel records exist ({count}). Remove them first.",
            )
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected position?"):
            self.cursor.execute("DELETE FROM GovPosition WHERE gov_position_id=?", (pid,))
            self.conn.commit()
            self.load_positions()

    def open_personnel(self):
        pid = self.get_selected_id()
        if not pid:
            return
        win = open_personnel_manager(pid, parent=self.master)
        if win:
            self.master.wait_window(win)

def open_position_manager(agency_id, parent=None):
    if parent is None:
        root = tk.Tk()
        PositionManager(root, agency_id)
        root.geometry("600x400")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        PositionManager(win, agency_id)
        win.grab_set()
        return win


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage government positions")
    parser.add_argument("agency_id", type=int, help="Agency ID")
    args = parser.parse_args()
    open_position_manager(args.agency_id)
