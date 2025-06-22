# context_menu.py

import tkinter as tk
from tkinter import ttk
import sys
from config import PATHS, DB_PATH
import subprocess

def paste_from_clipboard(entry):
    try:
        clipboard_text = entry.clipboard_get()
        entry.insert(tk.INSERT, clipboard_text)
    except tk.TclError:
        pass

def add_a_source(id, first_name, middle_name, last_name, married_name):
    full_name = f"{first_name} {' ' + middle_name if middle_name else ''} {last_name}"
    if married_name:
        full_name += f" (née {married_name})"
    command = [sys.executable, str(PATHS.citations), str(id), full_name]
    subprocess.run(command)  


def insert_custom_entry(entry, text):
    entry.delete(0, tk.END)
    entry.insert(0, text)

def create_context_menu(entry, entries=None):
    """
    Create a context menu for a given entry or text widget.
    If 'entries' are provided, add them to the menu for special fields.
    """
    edit_menu = tk.Menu(entry, tearoff=0)
    edit_menu.add_command(label="Cut", command=lambda: entry.event_generate("<<Cut>>"))
    edit_menu.add_command(label="Copy", command=lambda: entry.event_generate("<<Copy>>"))

    def paste():
        try:
            text = entry.clipboard_get()
            if isinstance(entry, tk.Text):
                entry.insert(entry.index(tk.INSERT), text)
            else:
                entry.insert(entry.index(tk.INSERT), text)
        except tk.TclError:
            pass  # Handle clipboard or insert issues gracefully

    edit_menu.add_command(label="Paste", command=paste)
    edit_menu.add_separator()

    # NOTE: Commented out until `add_a_source` is restructured to receive correct args
    # edit_menu.add_command(label="Add a Source", command=lambda: add_a_source(id, first_name, middle_name, last_name, married_name))

    if entries:
        edit_menu.add_separator()
        for text in entries:
            edit_menu.add_command(label=text, command=lambda text=text: insert_custom_entry(entry, text))

    def show_context_menu(event):
        entry.focus_set()
        try:
            edit_menu.tk_popup(event.x_root, event.y_root)
        finally:
            edit_menu.grab_release()

    entry.bind("<Button-3>", show_context_menu)

    # Keyboard shortcuts for clipboard
    entry.bind("<Control-v>", lambda e: paste())
    entry.bind("<Shift-Insert>", lambda e: paste())
    entry.bind("<Control-c>", lambda e: entry.event_generate("<<Copy>>"))
    entry.bind("<Control-x>", lambda e: entry.event_generate("<<Cut>>"))
    entry.bind("<Control-Insert>", lambda e: entry.event_generate("<<Copy>>"))



def apply_context_menu_to_all_entries(container):
    from context_menu import create_context_menu
    for widget in container.winfo_children():
        if isinstance(widget, ttk.Entry) or isinstance(widget, tk.Text):
            create_context_menu(widget)
        elif widget.winfo_children():
            apply_context_menu_to_all_entries(widget)