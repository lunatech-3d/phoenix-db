import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
import subprocess
import webbrowser

try:
    from PIL import Image, ImageTk
except Exception:  # Pillow not installed
    Image = ImageTk = None

from app.config import DB_PATH
from app.date_utils import parse_date_input, format_date_for_display

# Readable column widths for the showings list
COLUMN_WIDTHS = {
    "title": 120,
    "theater": 120,
    "start": 60,
    "end": 60,
    "format": 60,
    "event": 60,
    "movie_overview_url": 120,
}
from app.biz_linkage import open_biz_linkage_popup

# edit_showing will be created later
try:
    from app.movie.edit_showing import open_edit_showing_form
except Exception:
    open_edit_showing_form = None


class MovieShowingBrowser:
    """Tkinter window to browse and manage movie showings."""

    def __init__(self, master):
        self.master = master
        self.master.title("Movie Showings")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.filter_biz_id = None
        self.sort_column = None
        self.sort_reverse = False
        self._setup_filters()
        self._setup_tree()
        self._setup_buttons()
        self.load_showings()

    def _setup_filters(self):
        frame = ttk.LabelFrame(self.master, text="Filters")
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Theater:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.biz_display = ttk.Label(frame, text="(Any)", width=30, relief="sunken", anchor="w")
        self.biz_display.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ttk.Button(frame, text="Lookup", command=self.select_theater).grid(row=0, column=2, padx=5)
        ttk.Button(frame, text="Clear", command=self.clear_theater).grid(row=0, column=3, padx=5)

        ttk.Label(frame, text="Start ≥").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        self.start_entry = ttk.Entry(frame, width=12)
        self.start_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(frame, text="End ≤").grid(row=1, column=2, padx=5, pady=2, sticky="e")
        self.end_entry = ttk.Entry(frame, width=12)
        self.end_entry.grid(row=1, column=3, sticky="w", padx=5, pady=2)

        ttk.Button(frame, text="Search", command=self.load_showings).grid(row=0, column=4, padx=10)
        ttk.Button(frame, text="Reset", command=self.reset_filters).grid(row=1, column=4, padx=10)

    def select_theater(self):
        def callback(biz_id):
            self.filter_biz_id = biz_id
            cur = self.conn.cursor()
            cur.execute("SELECT biz_name FROM Biz WHERE biz_id=?", (biz_id,))
            row = cur.fetchone()
            self.biz_display.config(text=row[0] if row else "(Unknown)")
        open_biz_linkage_popup(callback)

    def clear_theater(self):
        self.filter_biz_id = None
        self.biz_display.config(text="(Any)")

    def reset_filters(self):
        self.start_entry.delete(0, tk.END)
        self.end_entry.delete(0, tk.END)
        self.clear_theater()
        self.load_showings()

    def _setup_tree(self):
        columns = (
            "id",
            "title",
            "theater",
            "start",
            "end",
            "format",
            "event",
            "movie_overview_url",
            "poster_url",
        )
        self.columns = columns
        frame = ttk.Frame(self.master)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.poster_label = ttk.Label(frame)
        self.poster_label.grid(row=1, column=0, pady=(10, 0), sticky="n")
        headings = {
            "title": "Movie",
            "theater": "Theater",
            "start": "Start Date",
            "end": "End Date",
            "format": "Format",
            "event": "Special Event",
            "movie_overview_url": "Overview URL",
        }
        for col in columns:
            if col in ("id", "poster_url"):
                self.tree.column(col, width=0, stretch=False)
                continue

            self.tree.heading(
                col,
                text=headings.get(col, col.title()),
                command=lambda c=col: self.sort_by_column(c),
            )
            width = COLUMN_WIDTHS.get(col, 100)
            anchor = "center" if col in ("start", "end", "format") else "w"
            self.tree.column(col, width=width, anchor=anchor)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

    
    def _setup_buttons(self):
        frame = ttk.Frame(self.master)
        frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame, text="Add", command=self.add_showing).pack(side="left", padx=5)
        ttk.Button(frame, text="Edit", command=self.edit_showing).pack(side="left", padx=5)
        ttk.Button(frame, text="Delete", command=self.delete_showing).pack(side="left", padx=5)

    
    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        reverse = self.sort_column == col and not self.sort_reverse
        items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
        self.sort_column = col
        self.sort_reverse = reverse

    
    def build_query(self):
        query = (
            "SELECT s.showing_id, s.title, b.biz_name, s.start_date, s.end_date, s.format, "
            "s.special_event, s.movie_overview_url, s.poster_url "
            "FROM MovieShowings s JOIN Biz b ON s.biz_id=b.biz_id WHERE 1=1"
        )
        params = []
        if self.filter_biz_id:
            query += " AND s.biz_id=?"
            params.append(self.filter_biz_id)
        start_val = self.start_entry.get().strip()
        if start_val:
            try:
                parsed, _ = parse_date_input(start_val)
                query += " AND s.start_date >= ?"
                params.append(parsed)
            except ValueError as e:
                messagebox.showerror("Start Date", str(e))
                return None, None
        end_val = self.end_entry.get().strip()
        if end_val:
            try:
                parsed, _ = parse_date_input(end_val)
                query += " AND s.end_date <= ?"
                params.append(parsed)
            except ValueError as e:
                messagebox.showerror("End Date", str(e))
                return None, None
        query += " ORDER BY s.start_date"
        return query, params

    
    def load_showings(self):
        query, params = self.build_query()
        if query is None:
            return
        self.tree.delete(*self.tree.get_children())
        try:
            self.cursor.execute(query, params)
            for row in self.cursor.fetchall():
                (
                    show_id,
                    title,
                    theater,
                    start,
                    end,
                    fmt,
                    event,
                    overview,
                    poster,
                ) = row
                start_disp = format_date_for_display(start, "EXACT") if start else ""
                end_disp = format_date_for_display(end, "EXACT") if end else ""
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        show_id,
                        title,
                        theater,
                        start_disp,
                        end_disp,
                        fmt,
                        event,
                        overview,
                        poster,
                    ),
                )
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    
    def get_selected_row(self, silent=False):
        sel = self.tree.selection()
        if not sel:
            if not silent:
                messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(sel[0])["values"]

    
    def on_tree_select(self, event=None):
        """Display poster image for the selected row if available."""
        row = self.get_selected_row(silent=True)
        if not row or not ImageTk:
            if hasattr(self, "poster_label"):
                self.poster_label.config(image="", text="")
                self.poster_label.image = None
            return
        poster_url = row[self.columns.index("poster_url")]
        if not poster_url:
            self.poster_label.config(image="", text="")
            self.poster_label.image = None
            return
        try:
            img = Image.open(poster_url)
            img.thumbnail((150, 200))
            photo = ImageTk.PhotoImage(img)
            self.poster_label.config(image=photo)
            self.poster_label.image = photo
        except Exception:
            self.poster_label.config(text="Preview unavailable", image="")
            self.poster_label.image = None

    
    def on_tree_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        if region == "cell" and column == f"#{self.columns.index('movie_overview_url')+1}":
            row = self.get_selected_row(silent=True)
            if not row:
                return
            url = row[self.columns.index("movie_overview_url")]
            if url and url.startswith("http"):
                webbrowser.open(url, new=2)
            else:
                messagebox.showinfo("No URL", "No valid link provided.")
        else:
            self.edit_showing()


    def add_showing(self):
        if open_edit_showing_form:
            win = open_edit_showing_form(parent=self.master, biz_id=self.filter_biz_id)
            if win:
                self.master.wait_window(win)
        else:
            args = [sys.executable, "-m", "app.movie.edit_showing"]
            if self.filter_biz_id:
                args.append(str(self.filter_biz_id))
            subprocess.Popen(args)
        self.load_showings()

    def edit_showing(self, event=None):
        row = self.get_selected_row()
        if not row:
            return
        showing_id = row[0]
        if open_edit_showing_form:
            win = open_edit_showing_form(showing_id, parent=self.master)
            if win:
                self.master.wait_window(win)
        else:
            subprocess.Popen([sys.executable, "-m", "app.movie.edit_showing", str(showing_id)])
        self.load_showings()

    def delete_showing(self):
        row = self.get_selected_row()
        if not row:
            return
        showing_id = row[0]
        if not messagebox.askyesno("Confirm Delete", "Delete selected showing?"):
            return
        try:
            self.cursor.execute("DELETE FROM MovieShowings WHERE showing_id=?", (showing_id,))
            self.conn.commit()
            self.load_showings()
        except Exception as e:
            messagebox.showerror("Delete Failed", str(e))


def open_movie_showings_browser(parent=None):
    """Launch the movie showings browser window."""
    if parent is None:
        root = tk.Tk()
        MovieShowingBrowser(root)
        root.geometry("950x600")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        MovieShowingBrowser(win)
        win.grab_set()
        return win


def main():
    open_movie_showings_browser()


if __name__ == "__main__":
    main()