import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys

from app.config import DB_PATH

try:
    from PIL import Image, ImageTk
except Exception:  # Pillow not installed
    Image = ImageTk = None


class EditMovieForm:
    """Tkinter form to add or edit a movie record."""

    def __init__(self, master, movie_id=None):
        self.master = master
        self.master.title("Edit Movie" if movie_id else "Add Movie")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.movie_id = movie_id
        self.entries = {}
        self.poster_label = None
        self._setup_form()
        if movie_id:
            self.load_movie()

    def _setup_form(self):
        frame = ttk.Frame(self.master)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        fields = [
            ("title", "Title", 40),
            ("director", "Director", 30),
            ("release_year", "Release Year", 10),
            ("genre", "Genre", 20),
            ("runtime_minutes", "Runtime (min)", 10),
            ("rating", "Rating", 10),
            ("poster_url", "Poster URL", 40),
            ("imdb_url", "IMDb URL", 40),
        ]

        for i, (key, label, width) in enumerate(fields):
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(frame, width=width)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.entries[key] = entry
            if key == "poster_url":
                entry.bind("<FocusOut>", self.show_poster_preview)

        # Description and Notes text boxes
        ttk.Label(frame, text="Description:").grid(row=len(fields), column=0, sticky="ne", pady=2)
        desc = tk.Text(frame, width=45, height=4)
        desc.grid(row=len(fields), column=1, sticky="w", pady=2)
        self.entries["description"] = desc

        ttk.Label(frame, text="Notes:").grid(row=len(fields)+1, column=0, sticky="ne", pady=2)
        notes = tk.Text(frame, width=45, height=4)
        notes.grid(row=len(fields)+1, column=1, sticky="w", pady=2)
        self.entries["notes"] = notes

        # Poster preview
        if ImageTk:
            self.poster_label = ttk.Label(frame)
            self.poster_label.grid(row=0, column=2, rowspan=8, padx=10)

        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save_movie).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

    def show_poster_preview(self, event=None):
        """Display a thumbnail of the poster image if available."""
        if not ImageTk or not self.poster_label:
            return
        path = self.entries["poster_url"].get().strip()
        if not path:
            self.poster_label.config(image="", text="")
            self.poster_label.image = None
            return
        try:
            img = Image.open(path)
            img.thumbnail((150, 200))
            photo = ImageTk.PhotoImage(img)
            self.poster_label.config(image=photo)
            self.poster_label.image = photo
        except Exception:
            self.poster_label.config(text="Preview unavailable", image="")
            self.poster_label.image = None

    def load_movie(self):
        """Populate form fields with movie data."""
        try:
            self.cursor.execute(
                """SELECT title, director, release_year, genre, runtime_minutes,
                          rating, description, poster_url, imdb_url, notes
                       FROM Movies WHERE movie_id=?""",
                (self.movie_id,),
            )
            row = self.cursor.fetchone()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.master.destroy()
            return
        if row:
            keys = [
                "title",
                "director",
                "release_year",
                "genre",
                "runtime_minutes",
                "rating",
                "description",
                "poster_url",
                "imdb_url",
                "notes",
            ]
            for key, value in zip(keys, row):
                widget = self.entries[key]
                if isinstance(widget, tk.Text):
                    widget.delete("1.0", tk.END)
                    widget.insert("1.0", value or "")
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, value if value is not None else "")
            self.show_poster_preview()

    def save_movie(self):
        """Validate and save the movie record."""
        data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, tk.Text):
                data[key] = widget.get("1.0", tk.END).strip()
            else:
                data[key] = widget.get().strip()

        if not data["title"]:
            messagebox.showerror("Validation Error", "Title is required.")
            return
        for int_field in ("release_year", "runtime_minutes"):
            if data[int_field] and not data[int_field].isdigit():
                messagebox.showerror("Validation Error", f"{int_field.replace('_', ' ').title()} must be an integer.")
                return
            data[int_field] = int(data[int_field]) if data[int_field] else None

        cols = [
            "title",
            "director",
            "release_year",
            "genre",
            "runtime_minutes",
            "rating",
            "description",
            "poster_url",
            "imdb_url",
            "notes",
        ]
        try:
            if self.movie_id:
                set_clause = ", ".join(f"{c}=?" for c in cols)
                self.cursor.execute(
                    f"UPDATE Movies SET {set_clause} WHERE movie_id=?",
                    (*[data[c] for c in cols], self.movie_id),
                )
            else:
                placeholders = ", ".join("?" for _ in cols)
                self.cursor.execute(
                    f"INSERT INTO Movies ({', '.join(cols)}) VALUES ({placeholders})",
                    tuple(data[c] for c in cols),
                )
                self.movie_id = self.cursor.lastrowid
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))
            return
        messagebox.showinfo("Saved", "Movie record saved.")
        self.master.destroy()


def open_edit_movie_form(movie_id=None, parent=None):
    """Open the movie editor window."""
    if parent is None:
        root = tk.Tk()
        EditMovieForm(root, movie_id)
        root.geometry("650x550")
        root.mainloop()
        return None
    else:
        win = tk.Toplevel(parent)
        EditMovieForm(win, movie_id)
        win.grab_set()
        return win


def main():
    movie_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    open_edit_movie_form(movie_id)


if __name__ == "__main__":
    main()