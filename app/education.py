import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

def open_add_education_window(person_id, connection):
    def save_education_record():
        school_name = entry_school_name.get().strip()
        record_year = entry_record_year.get().strip()
        degree = entry_degree.get().strip()
        position = entry_position.get().strip()
        notes = entry_notes.get().strip()
        field_of_study = entry_field_of_study.get().strip()

        if not record_year.isdigit():
            messagebox.showerror("Validation Error", "Record year must be a valid year.")
            return

        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO Education (person_id, school_name, record_year, degree, position, notes, field_of_study)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (person_id, school_name, record_year, degree, position, notes, field_of_study))
            connection.commit()
            messagebox.showinfo("Success", "Education record added successfully.")
            education_window.destroy()
            # Refresh the education tab if needed
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the education record: {e}")

    # Create a new top-level window
    education_window = tk.Toplevel()
    education_window.title("Add Education Record")

    # Create and configure the form fields
    frame_education_form = ttk.Frame(education_window, padding="10")
    frame_education_form.grid(row=0, column=0, sticky='nsew')

    # School Name entry with dropdown
    label_school_name = ttk.Label(frame_education_form, text="School Name:")
    label_school_name.grid(row=0, column=0, padx=5, pady=5, sticky='e')
    entry_school_name = ttk.Entry(frame_education_form)
    entry_school_name.grid(row=0, column=1, padx=5, pady=5, sticky='w')

    # Record Year entry
    label_record_year = ttk.Label(frame_education_form, text="Record Year:")
    label_record_year.grid(row=1, column=0, padx=5, pady=5, sticky='e')
    entry_record_year = ttk.Entry(frame_education_form)
    entry_record_year.grid(row=1, column=1, padx=5, pady=5, sticky='w')

    # Degree entry
    label_degree = ttk.Label(frame_education_form, text="Degree:")
    label_degree.grid(row=2, column=0, padx=5, pady=5, sticky='e')
    entry_degree = ttk.Entry(frame_education_form)
    entry_degree.grid(row=2, column=1, padx=5, pady=5, sticky='w')

    # Position entry
    label_position = ttk.Label(frame_education_form, text="Position:")
    label_position.grid(row=3, column=0, padx=5, pady=5, sticky='e')
    entry_position = ttk.Entry(frame_education_form)
    entry_position.grid(row=3, column=1, padx=5, pady=5, sticky='w')

    # Notes entry
    label_notes = ttk.Label(frame_education_form, text="Notes:")
    label_notes.grid(row=4, column=0, padx=5, pady=5, sticky='e')
    entry_notes = ttk.Entry(frame_education_form, width=50)
    entry_notes.grid(row=4, column=1, padx=5, pady=5, sticky='w')

    # Field of Study entry
    label_field_of_study = ttk.Label(frame_education_form, text="Field of Study:")
    label_field_of_study.grid(row=5, column=0, padx=5, pady=5, sticky='e')
    entry_field_of_study = ttk.Entry(frame_education_form)
    entry_field_of_study.grid(row=5, column=1, padx=5, pady=5, sticky='w')

    # Save Button
    save_button = ttk.Button(frame_education_form, text="Save", command=save_education_record)
    save_button.grid(row=6, column=0, columnspan=2, pady=10)
