
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
from config import DB_PATH
import os
from context_menu import create_context_menu


def create_embedded_bio_editor(parent, bio_text_from_db, person_id):
    section_frame = ttk.Frame(parent)
    section_frame.pack(fill="x", padx=10, pady=10)

    # Toggle button
    is_expanded = bool(bio_text_from_db and bio_text_from_db.strip())
    toggle_text = "▼ Biography" if is_expanded else "► Biography"
    toggle_btn = ttk.Button(section_frame, text=toggle_text)
    toggle_btn.pack(anchor="w", pady=(0, 5))

    # Content frame (initially shown or hidden)
    bio_content_frame = ttk.Frame(section_frame)
    if is_expanded:
        bio_content_frame.pack(fill="both", expand=True)

    def toggle_section():
        if bio_content_frame.winfo_ismapped():
            bio_content_frame.pack_forget()
            toggle_btn.config(text="► Biography")
        else:
            bio_content_frame.pack(fill="both", expand=True)
            toggle_btn.config(text="▼ Biography")

    toggle_btn.config(command=toggle_section)

    # Bio text + scrollbar
    text_frame = ttk.Frame(bio_content_frame)
    text_frame.pack(fill="both", expand=True)

    bio_text = tk.Text(text_frame, wrap='word', font=("Helvetica", 12), height=18)
    bio_text.pack(side="left", fill="both", expand=True)
    bio_text.insert("1.0", bio_text_from_db.replace('\n', os.linesep) if bio_text_from_db else "")
    bio_text.config(state="disabled")
    create_context_menu(bio_text)

    scroll = ttk.Scrollbar(text_frame, orient="vertical", command=bio_text.yview)
    scroll.pack(side="right", fill="y")
    bio_text.config(yscrollcommand=scroll.set)

    # Buttons
    btn_frame = ttk.Frame(bio_content_frame)
    btn_frame.pack(fill="x", pady=5)

    def enable_edit():
        bio_text.config(state="normal")
        btn_save.config(state="normal")
        btn_cancel.config(state="normal")
        btn_edit.config(state="disabled")

    def save_bio():
        updated_bio = bio_text.get("1.0", tk.END).strip()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE People SET bio = ? WHERE id = ?", (updated_bio, person_id))
        conn.commit()
        conn.close()
        bio_text.config(state="disabled")
        btn_save.config(state="disabled")
        btn_cancel.config(state="disabled")
        btn_edit.config(state="normal")

    def cancel_edit():
        bio_text.delete("1.0", tk.END)
        bio_text.insert("1.0", bio_text_from_db.replace('\n', os.linesep) if bio_text_from_db else "")
        bio_text.config(state="disabled")
        btn_save.config(state="disabled")
        btn_cancel.config(state="disabled")
        btn_edit.config(state="normal")

    btn_edit = ttk.Button(btn_frame, text="Edit", command=enable_edit)
    btn_save = ttk.Button(btn_frame, text="Save", command=save_bio, state="disabled")
    btn_cancel = ttk.Button(btn_frame, text="Cancel", command=cancel_edit, state="disabled")
    btn_edit.pack(side="left", padx=5)
    btn_save.pack(side="left", padx=5)
    btn_cancel.pack(side="left", padx=5)
