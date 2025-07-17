import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys

from app.config import DB_PATH
from app.date_utils import parse_date_input

class EditShowingForm:
    """Form to add or edit a movie showing."""

    def __init__(self, master, showing_id=None, biz_id=None):
        self.master = master
        self.master.title("Edit Showing" if showing_id else "Add Showing")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.showing_id = showing_id
        self.biz_id = biz_id
        self.entries = {}
        self._setup_form()
        if showing_id:
            self.load_showing()

    def _setup_form(self):
        frame = ttk.Frame(self.master)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Movie title
        ttk.Label(frame, text="Title:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entries["title"] = ttk.Entry(frame, width=40)
        self.entries["title"].grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Theater selection via Biz lookup
        ttk.Label(frame, text="Theater:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.biz_display = ttk.Label(frame, text="(None)", width=40, relief="sunken", anchor="w")
        self.biz_display.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Start/End Dates
        ttk.Label(frame, text="Start Date:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entries["start_date"] = ttk.Entry(frame, width=20)
        self.entries["start_date"].grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame, text="End Date:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entries["end_date"] = ttk.Entry(frame, width=20)
        self.entries["end_date"].grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Format
        ttk.Label(frame, text="Format:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entries["format"] = ttk.Entry(frame, width=20)
        self.entries["format"].grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # Special Event
        ttk.Label(frame, text="Special Event:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.entries["special_event"] = ttk.Entry(frame, width=30)
        self.entries["special_event"].grid(row=5, column=1, padx=5, pady=5, sticky="w")

        # Ticket Price
        ttk.Label(frame, text="Ticket Price:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.entries["ticket_price"] = ttk.Entry(frame, width=20)
        self.entries["ticket_price"].grid(row=6, column=1, padx=5, pady=5, sticky="w")

        # Attendance Estimate
        ttk.Label(frame, text="Attendance Est.:").grid(row=7, column=0, padx=5, pady=5, sticky="e")
        self.entries["attendance_estimate"] = ttk.Entry(frame, width=20)
        self.entries["attendance_estimate"].grid(row=7, column=1, padx=5, pady=5, sticky="w")

        # Poster URL
        ttk.Label(frame, text="Poster URL:").grid(row=8, column=0, padx=5, pady=5, sticky="e")
        self.entries["poster_url"] = ttk.Entry(frame, width=40)
        self.entries["poster_url"].grid(row=8, column=1, padx=5, pady=5, sticky="w")

        # Overview URL
        ttk.Label(frame, text="Overview URL:").grid(row=9, column=0, padx=5, pady=5, sticky="e")
        self.entries["movie_overview_url"] = ttk.Entry(frame, width=40)
        self.entries["movie_overview_url"].grid(row=9, column=1, padx=5, pady=5, sticky="w")

        # Source ID
        ttk.Label(frame, text="Source ID:").grid(row=10, column=0, padx=5, pady=5, sticky="e")
        self.entries["source_id"] = ttk.Entry(frame, width=20)
        self.entries["source_id"].grid(row=10, column=1, padx=5, pady=5, sticky="w")

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=11, column=0, padx=5, pady=5, sticky="ne")
        self.entries["notes"] = tk.Text(frame, width=45, height=4)
        self.entries["notes"].grid(row=11, column=1, padx=5, pady=5, sticky="w")
        
        btn = ttk.Frame(self.master)
        btn.pack(pady=10)
        ttk.Button(btn, text="Save", command=self.save_showing).pack(side="left", padx=5)
        ttk.Button(btn, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

        if self.biz_id:
            cur = self.conn.cursor()
            cur.execute("SELECT biz_name FROM Biz WHERE biz_id=?", (self.biz_id,))
            row = cur.fetchone()
            self.biz_display.config(text=row[0] if row else "(Unknown)")


    def load_showing(self):
        try:
            self.cursor.execute(
                """SELECT title, biz_id, start_date, end_date, format,
                          special_event, ticket_price, attendance_estimate, notes,
                          poster_url, movie_overview_url, source_id
                       FROM MovieShowings WHERE showing_id=?""",
                (self.showing_id,),
            )
            row = self.cursor.fetchone()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.master.destroy()
            return
        if row:
            (
                title,
                self.biz_id,
                start_date,
                end_date,
                fmt,
                special,
                price,
                attendance,
                notes,
                poster,
                overview,
                source_id,
            ) = row
            self.entries["title"].insert(0, title or "")
            self.entries["poster_url"].insert(0, poster or "")
            self.entries["movie_overview_url"].insert(0, overview or "")
            self.entries["source_id"].insert(0, source_id or "")
            if self.biz_id:
                cur = self.conn.cursor()
                cur.execute("SELECT biz_name FROM Biz WHERE biz_id=?", (self.biz_id,))
                br = cur.fetchone()
                self.biz_display.config(text=br[0] if br else "(Unknown)")
            self.entries["start_date"].insert(0, start_date or "")
            self.entries["end_date"].insert(0, end_date or "")
            self.entries["format"].insert(0, fmt or "")
            self.entries["special_event"].insert(0, special or "")
            self.entries["ticket_price"].insert(0, price or "")
            self.entries["attendance_estimate"].insert(0, attendance if attendance is not None else "")
            self.entries["notes"].insert("1.0", notes or "")

    def save_showing(self):
        if not self.entries["title"].get().strip():
            messagebox.showerror("Validation Error", "Enter a title.")
            return
        if not self.biz_id:
            messagebox.showerror("Validation Error", "Select a theater.")
            return
        data = {
            "title": self.entries["title"].get().strip(),
            "biz_id": self.biz_id,
        }
        try:
            start_val = self.entries["start_date"].get().strip()
            end_val = self.entries["end_date"].get().strip()
            data["start_date"], _ = parse_date_input(start_val) if start_val else (None, None)
            data["end_date"], _ = parse_date_input(end_val) if end_val else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return
        data.update({
            "format": self.entries["format"].get().strip(),
            "special_event": self.entries["special_event"].get().strip(),
            "ticket_price": self.entries["ticket_price"].get().strip(),
            "attendance_estimate": self.entries["attendance_estimate"].get().strip() or None,
            "poster_url": self.entries["poster_url"].get().strip(),
            "movie_overview_url": self.entries["movie_overview_url"].get().strip(),
            "source_id": self.entries["source_id"].get().strip() or None,
            "notes": self.entries["notes"].get("1.0", tk.END).strip(),
        })

        # Validate numeric fields
        if data["ticket_price"]:
            try:
                data["ticket_price"] = float(data["ticket_price"])
            except ValueError:
                messagebox.showerror("Validation Error", "Ticket price must be a number.")
                return

        if data["attendance_estimate"]:
            if not data["attendance_estimate"].isdigit():
                messagebox.showerror("Validation Error", "Attendance estimate must be an integer.")
                return
            data["attendance_estimate"] = int(data["attendance_estimate"])
        cols = [
            "title",
            "biz_id",
            "start_date",
            "end_date",
            "format",
            "special_event",
            "ticket_price",
            "attendance_estimate",
            "poster_url",
            "movie_overview_url",
            "source_id",
            "notes",
        ]
        try:
            if self.showing_id:
                set_clause = ", ".join(f"{c}=?" for c in cols)
                self.cursor.execute(
                    f"UPDATE MovieShowings SET {set_clause} WHERE showing_id=?",
                    (*[data[c] for c in cols], self.showing_id)
                )
            else:
                placeholders = ", ".join("?" for _ in cols)
                self.cursor.execute(
                    f"INSERT INTO MovieShowings ({', '.join(cols)}) VALUES ({placeholders})",
                    tuple(data[c] for c in cols)
                )
                self.showing_id = self.cursor.lastrowid
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))
            return
        messagebox.showinfo("Saved", "Showing saved successfully.")
        self.master.destroy()


def open_edit_showing_form(showing_id=None, parent=None, biz_id=None):
    """Open the movie showing editor."""
    if parent is None:
        root = tk.Tk()
        EditShowingForm(root, showing_id, biz_id=biz_id)
        root.geometry("600x500")
        root.mainloop()
        return None
    else:
        win = tk.Toplevel(parent)
        EditShowingForm(win, showing_id, biz_id=biz_id)
        win.grab_set()
        return win


def main():
    showing_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    biz_id = None
    if len(sys.argv) > 2:
        biz_id = int(sys.argv[2])
    open_edit_showing_form(showing_id, biz_id=biz_id)


if __name__ == "__main__":
    main()