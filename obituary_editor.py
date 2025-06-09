import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import webbrowser
from context_menu import create_context_menu
from date_utils import parse_date_input, format_date_for_display

DB_PATH = "phoenix.db"

def open_link(link):
    if link:
        webbrowser.open(link)

def create_embedded_obituary_editor(parent, person_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    section_frame = ttk.Frame(parent)
    section_frame.pack(fill="x", padx=10, pady=10)

    cursor.execute("""
        SELECT obit_id, source_title, obit_text, date_published, date_precision, source_link
        FROM Obituaries
        WHERE person_id = ?
        ORDER BY date_published ASC LIMIT 1
    """, (person_id,))
    record = cursor.fetchone()

    obit_id = None
    source_title = ""
    obit_text = ""
    date_published = ""
    date_precision = ""
    source_link = ""

    if record:
        obit_id = record[0]
        source_title = record[1] or ""
        obit_text = record[2] or ""
        date_published = record[3] or ""
        date_precision = record[4] or "EXACT"
        source_link = record[5] or ""

    is_expanded = bool(obit_text.strip())
    toggle_text = "▼ Obituary" if is_expanded else "► Obituary"
    toggle_btn = ttk.Button(section_frame, text=toggle_text)
    toggle_btn.pack(anchor="w", pady=(0, 5))

    obit_frame = ttk.Frame(section_frame)
    if is_expanded:
        obit_frame.pack(fill="both", expand=True)

    def toggle_section():
        if obit_frame.winfo_ismapped():
            obit_frame.pack_forget()
            toggle_btn.config(text="► Obituary")
        else:
            obit_frame.pack(fill="both", expand=True)
            toggle_btn.config(text="▼ Obituary")

    toggle_btn.config(command=toggle_section)

    # === Obituary Text ===
    text_frame = ttk.Frame(obit_frame)
    text_frame.pack(fill="both", expand=True)

    text_obit = tk.Text(text_frame, wrap="word", height=10, font=("Helvetica", 12))
    text_obit.pack(side="left", fill="both", expand=True)
    text_obit.insert("1.0", obit_text)
    text_obit.config(state="disabled")
    create_context_menu(text_obit)

    scroll = ttk.Scrollbar(text_frame, command=text_obit.yview)
    scroll.pack(side="right", fill="y")
    text_obit.config(yscrollcommand=scroll.set)

    # === Fields ===
    field_frame = ttk.Frame(obit_frame)
    field_frame.pack(fill="x", pady=5)

    ttk.Label(field_frame, text="Source Title:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    entry_source = ttk.Entry(field_frame, width=60)
    entry_source.grid(row=0, column=1, sticky="w", pady=2)
    entry_source.insert(0, source_title)
    create_context_menu(entry_source)

    ttk.Label(field_frame, text="Date Published:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    entry_date = ttk.Entry(field_frame, width=20)
    entry_date.grid(row=1, column=1, sticky="w", pady=2)
    entry_date.insert(0, format_date_for_display(date_published, date_precision))
    create_context_menu(entry_date)

    ttk.Label(field_frame, text="Source Link (optional):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    entry_link = ttk.Entry(field_frame, width=35)
    entry_link.grid(row=2, column=1, sticky="w", pady=2)
    entry_link.insert(0, source_link)
    create_context_menu(entry_link)

    open_link_button = ttk.Button(field_frame, text="Open Link", command=lambda: open_link(entry_link.get()))
    open_link_button.grid(row=2, column=2, padx=5, pady=2, sticky="w")

    # === Buttons ===
    button_frame = ttk.Frame(obit_frame)
    button_frame.pack(fill="x", pady=5)

    def enable_edit():
        text_obit.config(state="normal")
        btn_save.config(state="normal")
        btn_cancel.config(state="normal")
        btn_edit.config(state="disabled")

    def save_obit():
        new_obit = text_obit.get("1.0", tk.END).strip()
        new_source = entry_source.get().strip()
        new_date = entry_date.get().strip()
        new_link = entry_link.get().strip()

        try:
            parsed_date, precision = parse_date_input(new_date)
        except ValueError:
            messagebox.showerror("Invalid Date", "Date must be MM-DD-YYYY, MM-YYYY, or YYYY.")
            return

        conn2 = sqlite3.connect(DB_PATH)
        cur2 = conn2.cursor()

        if obit_id:
            cur2.execute("""
                UPDATE Obituaries
                SET source_title = ?, obit_text = ?, date_published = ?, source_link = ?, date_precision = ?
                WHERE obit_id = ?
            """, (new_source, new_obit, parsed_date, new_link, precision, obit_id))
        else:
            cur2.execute("""
                INSERT INTO Obituaries (person_id, source_title, obit_text, date_published, source_link, date_precision)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (person_id, new_source, new_obit, parsed_date, new_link, precision))

        conn2.commit()
        conn2.close()
        text_obit.config(state="disabled")
        btn_save.config(state="disabled")
        btn_cancel.config(state="disabled")
        btn_edit.config(state="normal")
        messagebox.showinfo("Saved", "Obituary information saved.")

    def cancel_edit():
        text_obit.delete("1.0", tk.END)
        text_obit.insert("1.0", obit_text)
        text_obit.config(state="disabled")
        btn_save.config(state="disabled")
        btn_cancel.config(state="disabled")
        btn_edit.config(state="normal")

    btn_edit = ttk.Button(button_frame, text="Edit", command=enable_edit)
    btn_save = ttk.Button(button_frame, text="Save", command=save_obit, state="disabled")
    btn_cancel = ttk.Button(button_frame, text="Cancel", command=cancel_edit, state="disabled")
    btn_edit.pack(side="left", padx=5)
    btn_save.pack(side="left", padx=5)
    btn_cancel.pack(side="left", padx=5)
