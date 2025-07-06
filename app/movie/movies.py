import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
import subprocess
import webbrowser

from app.config import DB_PATH
# edit_movie will be created in a later commit
try:
    from app.movie.edit_movie import open_edit_movie_form
except Exception:
    open_edit_movie_form = None

class MovieBrowser:
    """Tkinter window for browsing and managing movies."""

    def __init__(self, master):
        """Initialize the browser."""
        self.master = master
        self.master.title("Movie Catalog")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.sort_column = None
        self.sort_reverse = False

        self._setup_filters()
        self._setup_tree()
        self._setup_buttons()
        self.load_movies()

    def _setup_filters(self):
        """Create filter widgets for searching."""
        frame = ttk.Frame(self.master)
        frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(frame, text="Title:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.title_entry = ttk.Entry(frame, width=30)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Director:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.director_entry = ttk.Entry(frame, width=20)
        self.director_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Year:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.year_entry = ttk.Entry(frame, width=8)
        self.year_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(frame, text="Search", command=self.load_movies).grid(row=0, column=6, padx=5)
        ttk.Button(frame, text="Clear", command=self.reset_filters).grid(row=0, column=7, padx=5)

    def _setup_tree(self):
        """Configure the treeview widget."""
        columns = ("movie_id", "title", "director", "year", "genre", "runtime", "rating", "imdb")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings")

        headings = {
            "title": "Title",
            "director": "Director",
            "year": "Year",
            "genre": "Genre",
            "runtime": "Runtime",
            "rating": "Rating",
        }

        for col in columns:
            if col == "movie_id" or col == "imdb":
                self.tree.column(col, width=0, stretch=False)
            else:
                self.tree.heading(col, text=headings.get(col, col.title()), command=lambda c=col: self.sort_by_column(c))

        self.tree.column("title", width=200, anchor="w")
        self.tree.column("director", width=150, anchor="w")
        self.tree.column("year", width=60, anchor="center")
        self.tree.column("genre", width=100, anchor="w")
        self.tree.column("runtime", width=80, anchor="center")
        self.tree.column("rating", width=60, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_movie)

    def _setup_buttons(self):
        """Create action buttons."""
        frame = ttk.Frame(self.master)
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(frame, text="Add", command=self.add_movie).pack(side="left", padx=5)
        ttk.Button(frame, text="Edit", command=self.edit_movie).pack(side="left", padx=5)
        ttk.Button(frame, text="Delete", command=self.delete_movie).pack(side="left", padx=5)
        ttk.Button(frame, text="Open IMDb", command=self.open_imdb_url).pack(side="left", padx=5)

    def reset_filters(self):
        """Clear search fields and reload all movies."""
        for entry in (self.title_entry, self.director_entry, self.year_entry):
            entry.delete(0, tk.END)
        self.load_movies()

    def sort_by_column(self, col):
        """Sort the treeview by the specified column."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        reverse = self.sort_column == col and not self.sort_reverse
        items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
        self.sort_column = col
        self.sort_reverse = reverse

    def load_movies(self):
        """Load movies matching the search filters."""
        self.tree.delete(*self.tree.get_children())
        query = "SELECT movie_id, title, director, release_year, genre, runtime_minutes, rating, imdb_url FROM Movies WHERE 1=1"
        params = []
        title = self.title_entry.get().strip()
        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")
        director = self.director_entry.get().strip()
        if director:
            query += " AND director LIKE ?"
            params.append(f"%{director}%")
        year = self.year_entry.get().strip()
        if year.isdigit():
            query += " AND release_year = ?"
            params.append(int(year))
        query += " ORDER BY title"
        try:
            self.cursor.execute(query, tuple(params))
            for row in self.cursor.fetchall():
                self.tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def get_selected_row(self):
        """Return the values tuple for the selected movie."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(selected[0])["values"]

    def add_movie(self):
        """Launch the movie editor in add mode."""
        if open_edit_movie_form:
            win = open_edit_movie_form(parent=self.master)
            if win:
                self.master.wait_window(win)
        else:
            subprocess.Popen([sys.executable, "-m", "app.movie.edit_movie"])
        self.load_movies()

    def edit_movie(self, event=None):
        """Edit the currently selected movie."""
        row = self.get_selected_row()
        if not row:
            return
        movie_id = row[0]
        if open_edit_movie_form:
            win = open_edit_movie_form(movie_id, parent=self.master)
            if win:
                self.master.wait_window(win)
        else:
            subprocess.Popen([sys.executable, "-m", "app.movie.edit_movie", str(movie_id)])
        self.load_movies()

    def delete_movie(self):
        """Delete the selected movie after confirmation."""
        row = self.get_selected_row()
        if not row:
            return
        movie_id = row[0]
        if not messagebox.askyesno("Confirm Delete", "Delete selected movie?"):
            return
        try:
            self.cursor.execute("DELETE FROM Movies WHERE movie_id=?", (movie_id,))
            self.conn.commit()
            self.load_movies()
        except Exception as e:
            messagebox.showerror("Delete Failed", str(e))

    def open_imdb_url(self):
        """Open the selected movie's IMDb page in a browser."""
        row = self.get_selected_row()
        if not row:
            return
        url = row[7]
        if url and url.startswith("http"):
            webbrowser.open(url, new=2)
        else:
            messagebox.showinfo("No URL", "No valid IMDb link provided.")


def open_movie_browser(parent=None):
    """Open the movie browser window."""
    if parent is None:
        root = tk.Tk()
        MovieBrowser(root)
        root.geometry("900x600")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        MovieBrowser(win)
        win.grab_set()
        return win


def main():
    """Entry point for running as a script."""
    open_movie_browser()


if __name__ == "__main__":
    main()