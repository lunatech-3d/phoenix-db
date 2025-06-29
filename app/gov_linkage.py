"""Popup selector for Government Agencies.

Provides a search interface for GovAgency records. Users can filter by name,
jurisdiction, or type and choose an agency from a tree view list. The
selected agency ID and name are returned and optionally passed to a callback.
"""

import tkinter as tk
from tkinter import ttk
import sqlite3
from typing import Callable, Optional, Tuple

from app.config import DB_PATH
from app.context_menu import create_context_menu


def open_gov_linkage_popup(
    callback: Optional[Callable[[int, str], None]] = None,
) -> Optional[Tuple[int, str]]:
    """Open a popup to select a government agency.

    Parameters
    ----------
    callback:
        Optional function to call with ``(agency_id, agency_name)`` once the
        user selects an agency. If not provided, the function simply returns the
        values.

    Returns
    -------
    tuple | None
        ``(agency_id, agency_name)`` if a selection was made, otherwise ``None``.
    """

    conn = sqlite3.connect(DB_PATH)

    popup = tk.Toplevel()
    popup.title("Select Government Agency")
    popup.geometry("700x450")

    # ------- search fields -------
    search_frame = ttk.Frame(popup)
    search_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(search_frame, text="Name:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
    name_var = tk.StringVar()
    name_entry = ttk.Entry(search_frame, textvariable=name_var, width=25)
    name_entry.grid(row=0, column=1, padx=5, pady=2)
    create_context_menu(name_entry)

    ttk.Label(search_frame, text="Jurisdiction:").grid(row=0, column=2, padx=5, pady=2, sticky="e")
    juris_var = tk.StringVar()
    juris_entry = ttk.Entry(search_frame, textvariable=juris_var, width=20)
    juris_entry.grid(row=0, column=3, padx=5, pady=2)
    create_context_menu(juris_entry)

    ttk.Label(search_frame, text="Type:").grid(row=0, column=4, padx=5, pady=2, sticky="e")
    type_var = tk.StringVar()
    type_entry = ttk.Entry(search_frame, textvariable=type_var, width=20)
    type_entry.grid(row=0, column=5, padx=5, pady=2)
    create_context_menu(type_entry)

    def refresh_tree() -> None:
        """Reload the treeview based on filter fields."""
        query = (
            "SELECT gov_agency_id, name, jurisdiction, type "
            "FROM GovAgency WHERE 1=1"
        )
        params = []
        name_filter = name_var.get().strip().lower()
        if name_filter:
            query += " AND LOWER(name) LIKE ?"
            params.append(f"%{name_filter}%")
        juris_filter = juris_var.get().strip().lower()
        if juris_filter:
            query += " AND LOWER(jurisdiction) LIKE ?"
            params.append(f"%{juris_filter}%")
        type_filter = type_var.get().strip().lower()
        if type_filter:
            query += " AND LOWER(type) LIKE ?"
            params.append(f"%{type_filter}%")
        query += " ORDER BY name"

        tree.delete(*tree.get_children())
        cur = conn.cursor()
        cur.execute(query, params)
        for row in cur.fetchall():
            tree.insert("", "end", values=row)

    ttk.Button(search_frame, text="Search", command=refresh_tree).grid(
        row=0, column=6, padx=5
    )

    # ------- treeview -------
    columns = ("id", "name", "jurisdiction", "type")
    tree = ttk.Treeview(popup, columns=columns, show="headings", selectmode="browse")
    for col in columns:
        tree.heading(col, text=col.title())
        width = 220 if col == "name" else 140
        tree.column(col, width=width)
    tree.column("id", width=0, stretch=False)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    selected: Optional[Tuple[int, str]] = None

    def choose_and_close() -> None:
        nonlocal selected
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0])["values"]
        selected = (int(vals[0]), str(vals[1]))
        if callback:
            try:
                from inspect import signature

                param_count = len(signature(callback).parameters)
                if param_count == 1:
                    callback(selected[0])
                else:
                    callback(*selected)
            except Exception:
                callback(*selected)
        popup.destroy()

    tree.bind("<Double-1>", lambda _e: choose_and_close())

    # ------- buttons -------
    btn_frame = ttk.Frame(popup)
    btn_frame.pack(pady=5)
    ttk.Button(btn_frame, text="Select", command=choose_and_close).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=popup.destroy).pack(side="left", padx=5)

    refresh_tree()

    popup.transient()
    popup.grab_set()
    popup.wait_window(popup)

    return selected

if __name__ == "__main__":
    # Example usage when run directly
    result = open_gov_linkage_popup()
    if result:
        print("Selected:", result)