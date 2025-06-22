import sqlite3
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from .config import DB_PATH, PATHS

# Retrieve the arguments
person_id = int(sys.argv[1])
first_name = sys.argv[2]
middle_name = sys.argv[3]
last_name = sys.argv[4]
married_name = sys.argv[5]

# Print the values for debugging
print("Person ID:", person_id)
print("First Name:", first_name)
print("Middle Name:", middle_name)
print("Last Name:", last_name)
print("Married Name:", married_name)

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

def add_census_record():
    # Use the retrieved person_id from the command line arguments
    person_id = str(sys.argv[1])

    # Set the value of the person ID entry widget
    #entry_person_id.delete(0, tk.END)
    #entry_person_id.insert(0, person_id)

    # Retrieve the information of the person
    person_info = (first_name, middle_name, last_name, married_name)
    print("The person-info variable contains:", person_info)

    # Get the values from the form
    person_age = entry_person_age.get()
    person_occupation = entry_person_occupation.get()
    census_year = selected_census_year.get()
    census_housenumber = entry_census_housenumber.get()
    real_estate_value = entry_real_estate_value.get()
    estate_value = entry_estate_value.get()

    # Validate the required fields
    if not person_age or not person_occupation or not census_year or not census_housenumber:
        messagebox.showerror("Error", "Please fill in all the required fields.")
        return

    # Insert the census record into the database
    cursor.execute(
        "INSERT INTO Census (person_id, person_age, person_occupation, census_year, census_housenumber, real_estate_value, estate_value) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (person_id, person_age, person_occupation, census_year, census_housenumber, real_estate_value, estate_value),
    )
    connection.commit()

    messagebox.showinfo("Success", "Census record added successfully.")

    # Clear the form fields
    entry_person_age.delete(0, tk.END)
    entry_person_occupation.delete(0, tk.END)
    entry_census_housenumber.delete(0, tk.END)
    entry_real_estate_value.delete(0, tk.END)
    entry_estate_value.delete(0, tk.END)


def cancel_add_census():
    # Clear the form fields
    entry_person_age.delete(0, tk.END)
    entry_person_occupation.delete(0, tk.END)
    entry_census_housenumber.delete(0, tk.END)
    entry_real_estate_value.delete(0, tk.END)
    entry_estate_value.delete(0, tk.END)

    # Close the Add Census form
    window.destroy()


# Create the GUI window
window = tk.Tk()
window.title("Add Census Record")

# Create a tkinter variable for selected_person_id
selected_person_id = tk.IntVar(value=person_id)

# Print the value of the selected_person_id variable
print("The Value of the selected_person_id variable for tk is:", selected_person_id.get())


# Set the window size and position
window_width = 400
window_height = 400
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a frame for the form
frame_form = ttk.Frame(window)
frame_form.pack(pady=20, padx=10)

# Person ID label and entry
label_person_id = ttk.Label(frame_form, text="Person ID:")
label_person_id.grid(row=0, column=0, padx=5, pady=5)

label_person_id_value = ttk.Label(frame_form, text=str(person_id))
label_person_id_value.grid(row=0, column=1, padx=5, pady=5)


# Fetch the person ID from the previous form
person_id = selected_person_id.get()

# Update the label_person_name to include the person's name
name_parts = []

if first_name:
    name_parts.append(first_name)
if middle_name:
    name_parts.append(middle_name)
if last_name:
    name_parts.append(last_name)
if married_name:
    name_parts.append(married_name)

name_label = ' '.join(name_parts)

label_person_name = ttk.Label(
    frame_form, text=f"Person: {name_label}"
)
label_person_name.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

# Person Age
label_person_age = ttk.Label(frame_form, text="Person Age:")
label_person_age.grid(row=2, column=0, padx=5, pady=5)
entry_person_age = ttk.Entry(frame_form)
entry_person_age.grid(row=2, column=1, padx=5, pady=5)

# Person Occupation
label_person_occupation = ttk.Label(frame_form, text="Person Occupation:")
label_person_occupation.grid(row=3, column=0, padx=5, pady=5)
entry_person_occupation = ttk.Entry(frame_form)
entry_person_occupation.grid(row=3, column=1, padx=5, pady=5)

# Census Year
label_census_year = ttk.Label(frame_form, text="Census Year:")
label_census_year.grid(row=4, column=0, padx=5, pady=5)
selected_census_year = tk.StringVar()
census_year_options = ["1840", "1850", "1860", "1870", "1880", "1900", "1910", "1920", "1930", "1940", "1950"]
dropdown_census_year = ttk.Combobox(frame_form, textvariable=selected_census_year, values=census_year_options, state="readonly")
dropdown_census_year.grid(row=4, column=1, padx=5, pady=5)
dropdown_census_year.current(0)

# Census House Number
label_census_housenumber = ttk.Label(frame_form, text="Census House Number:")
label_census_housenumber.grid(row=5, column=0, padx=5, pady=5)
entry_census_housenumber = ttk.Entry(frame_form)
entry_census_housenumber.grid(row=5, column=1, padx=5, pady=5)

# Real Estate Value
label_real_estate_value = ttk.Label(frame_form, text="Real Estate Value:")
label_real_estate_value.grid(row=6, column=0, padx=5, pady=5)
entry_real_estate_value = ttk.Entry(frame_form)
entry_real_estate_value.grid(row=6, column=1, padx=5, pady=5)

# Estate Value
label_estate_value = ttk.Label(frame_form, text="Estate Value:")
label_estate_value.grid(row=7, column=0, padx=5, pady=5)
entry_estate_value = ttk.Entry(frame_form)
entry_estate_value.grid(row=7, column=1, padx=5, pady=5)

# Add Census Record button
button_add_census = ttk.Button(frame_form, text="Add Census Record", command=add_census_record)
button_add_census.grid(row=8, column=0, columnspan=2, padx=5, pady=10)

# Cancel button
button_cancel = ttk.Button(frame_form, text="Cancel", command=cancel_add_census)
button_cancel.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

# Run the GUI window
window.mainloop()

# Close the connection
connection.close()
