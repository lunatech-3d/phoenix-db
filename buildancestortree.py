import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sys

# Connect to the database
connection = sqlite3.connect('phoenix.db')
cursor = connection.cursor()

# Function to recursively fetch and build the ancestor tree
def build_ancestor_tree(person_id, indent="", is_last_child=False):
    # Retrieve the information of the person
    cursor.execute(
        "SELECT id, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location, married_to, father, mother FROM People WHERE id = ?",
        (person_id,),
    )
    person_info = cursor.fetchone()

    if person_info:
        id_, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location, married_to, father, mother = person_info

        # Prepare the name line
        name_line = indent
        if is_last_child:
            name_line += "└─ "
        else:
            name_line += "├─ "
        name_line += f"{first_name} {middle_name or ''} {last_name}"
        tree_text.insert(tk.END, name_line + "\n")

        # Prepare the details lines
        details_lines = []
        details_lines.append(indent + "   ├─ Birthdate: " + (birth_date if birth_date is not None else ''))
        details_lines.append(indent + "   │  Birthplace: " + (birth_location if birth_location is not None else ''))
        details_lines.append(indent + "   ├─ Death date: " + (death_date if death_date is not None else ''))
        details_lines.append(indent + "   │  Death place: " + (death_location if death_location is not None else ''))

        if married_to:
            # Retrieve the information of the spouse
            cursor.execute(
                "SELECT first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location FROM People WHERE id = ?",
                (married_to,),
            )
            spouse_info = cursor.fetchone()
            if spouse_info:
                spouse_first_name, spouse_middle_name, spouse_last_name, spouse_birth_date, spouse_birth_location, spouse_death_date, spouse_death_location = spouse_info

                details_lines.append(indent + "   │")
                details_lines.append(indent + "   │===Spouse: " + (spouse_first_name if spouse_first_name is not None else '') + " " + (spouse_middle_name if spouse_middle_name is not None else '') + " " + (spouse_last_name if spouse_last_name is not None else ''))
                details_lines.append(indent + "   │   Spouse Birthdate: " + (spouse_birth_date if spouse_birth_date is not None else ''))
                details_lines.append(indent + "   │   Spouse Birthplace: " + (spouse_birth_location if spouse_birth_location is not None else ''))
                details_lines.append(indent + "   │   Spouse Death date: " + (spouse_death_date if spouse_death_date is not None else ''))
                details_lines.append(indent + "   │   Spouse Death place: " + (spouse_death_location if spouse_death_location is not None else ''))

        # Insert the details lines into the tree
        for line in details_lines:
            tree_text.insert(tk.END, line + "\n")

        tree_text.insert(tk.END, "\n")  # Add a blank line

        # Retrieve the parents of the person
        parents = [(father, 'Father'), (mother, 'Mother')]

        # Build the ancestor tree for each parent
        for index, parent in enumerate(parents, start=1):
            parent_id = parent[0]
            parent_label = parent[1]
            is_last_child = index == len(parents)
            if parent_id is not None:
                tree_text.insert(tk.END, indent + f"---{parent_label}---\n")
                build_ancestor_tree(parent_id, indent + "   │", is_last_child)


def close_window():
    window.destroy()

# Check if the script is being called from the other script or the prompt
if len(sys.argv) > 1:
    # Running from the other script, use the provided ID
    person_id = int(sys.argv[1])
else:
    # Running from the prompt, prompt for the ID of the person
    person_id = int(input("Enter the ID of the person: "))

# Search for the person in the database
cursor.execute(
    "SELECT id FROM People WHERE id = ?",
    (person_id,),
)
result = cursor.fetchone()

if result:
    id_ = result[0]

    # Create the GUI window
    window = tk.Tk()
    window.title("Family Tree")

    # Set the window size and position
    window_width = 800
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    max_window_height = int(screen_height * 0.85)  # Maximum 85% of screen height

    # Create a frame for the family tree display
    frame_tree = tk.Frame(window)
    frame_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Create a text widget to display the tree
    tree_text = tk.Text(frame_tree, width=80)
    tree_text.pack(fill=tk.BOTH, expand=True)

    # Print the ancestor tree for the person and their ancestors
    tree_output = ""
    tree_output += "Ancestor Tree:\n"
    tree_output += "-------------\n"
    build_ancestor_tree(id_)


    # Set the content of the text widget
    tree_text.insert(tk.END, tree_output)

    # Determine the required height of the window based on the number of lines in the tree text
    line_height = 20  # Height of each line in the text widget
    padding = 20  # Additional padding
    required_window_height = line_height * (tree_text.get("1.0", tk.END).count("\n") + 1) + padding
    window_height = min(required_window_height, max_window_height)

    # Calculate the window position
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Update the window geometry
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Create a Close button
    button_close = tk.Button(window, text="Close", command=close_window)
    button_close.place(relx=0.95, rely=0.05, anchor=tk.NE)

    # Run the GUI window
    window.mainloop()
else:
    print("Person not found in the database.")


# Close the connection
connection.close()
