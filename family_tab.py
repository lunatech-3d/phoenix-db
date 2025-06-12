import sys
from config import DB_PATH

def create_family_tab(notebook, person_id):

    # Add the Family tab
    frame_family = ttk.Frame(notebook)
    notebook.add(frame_family, text='Family')
    
    # Create a frame for the buttons
    frame_buttons = ttk.Frame(frame_family)
    frame_buttons.grid(column=0, row=0, sticky='ns')
    
    # Create a frame for the tree display
    frame_tree = ttk.Frame(frame_family)
    frame_tree.grid(column=1, row=0, sticky='nsew')

    # Create a new grid frame
    grid_frame = ttk.Frame(frame_tree)

    def prepare_for_tree(frame_tree, tree_text):
        nonlocal grid_frame
        # Remove the text widget from the grid if it's currently displayed
        if tree_text.winfo_ismapped():
            # Clear the text in the tree_text widget
            tree_text.delete("1.0", "end")
            tree_text.grid_remove()

        # Destroy the grid frame if it exists
        if grid_frame is not None and grid_frame.winfo_exists():
            grid_frame.destroy()
            grid_frame = None


    # Add the buttons to the buttons frame
    button_immediate_tree = ttk.Button(frame_buttons, text="Immediate Family", 
            command=lambda: [prepare_for_tree(frame_tree, tree_text), build_immediate_tree(person_id, cursor, frame_tree)])

    button_immediate_tree.pack(fill='x', padx=5, pady=5)  # fill the x direction, add some padding

    button_descendent_tree = ttk.Button(frame_buttons, text="Descendent Tree", 
            command=lambda: [prepare_for_tree(frame_tree, tree_text), build_family_tree(person_id, cursor, tree_text), tree_text.grid(row=0, column=0, sticky='nsew')])

    button_descendent_tree.pack(fill='x', padx=5, pady=5)  # fill the x direction, add some padding

    button_ancestor_tree = ttk.Button(frame_buttons, text="Ancestor Tree", 
    command=lambda: [prepare_for_tree(frame_tree, tree_text), build_ancestor_tree(person_id, cursor, tree_text), tree_text.grid(row=0, column=0, sticky='nsew')])

    button_ancestor_tree.pack(fill='x', padx=5, pady=5)  # fill the x direction, add some padding

    # Add a text widget to display the tree in the tree frame
    tree_text = tk.Text(frame_tree, width=80, height=40)
    tree_text.grid(row=0, column=0, sticky='nsew')  # fill both directions, allow widget to expand

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Function to recursively fetch and build the family tree
    def build_family_tree(person_id, cursor, tree_text, indent="", is_last_child=False):
        
        prepare_for_tree(frame_tree, tree_text)

        # Retrieve the information of the person
        cursor.execute(
            "SELECT id, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location, married_to FROM People WHERE id = ?",
            (person_id,),
        )
        person_info = cursor.fetchone()

        if person_info:
            id_, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location, married_to = person_info

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

            # Retrieve the children of the person in order of birth date
            cursor.execute(
                "SELECT id, birth_date FROM People WHERE (father = ? OR mother = ?) ORDER BY STRFTIME('%Y-%m-%d', birth_date) ASC",
                (person_id, person_id),
            )
            children = cursor.fetchall()

            # Build the family tree for each child
            for index, child in enumerate(children, start=1):
                child_id = child[0]
                is_last_child = index == len(children)
                build_family_tree(child_id, cursor, tree_text, indent + "   │", is_last_child)

    # Function to recursively fetch and build the ancestor tree
    def build_ancestor_tree(person_id, cursor, tree_text, indent="", is_last_child=False):
        
        prepare_for_tree(frame_tree, tree_text)
        
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
                    build_ancestor_tree(parent_id, cursor, tree_text, indent + "   │", is_last_child)
    
    # Close the connection when the notebook is closed
    notebook.winfo_toplevel().protocol("WM_DELETE_WINDOW", close_connection)

    # Function to fetch and build the immediate family grid
    def build_immediate_tree(person_id, cursor, frame_tree):
        prepare_for_tree(frame_tree, tree_text)
        
        # Create a new canvas and a vertical scrollbar for scrolling
        canvas = tk.Canvas(frame_tree)
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        nonlocal grid_frame
        
        # Create a new grid frame and clear it
        grid_frame = ttk.Frame(canvas)
        for widget in grid_frame.winfo_children():
            widget.destroy()

        # Add the grid frame to the canvas
        canvas.create_window((0,0), window=grid_frame, anchor="nw")

        # Configure the grid frame's size to update the scroll region
        grid_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

        # Pack the canvas and the scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        cursor.execute(
            "SELECT father, mother, married_to FROM People WHERE id = ?",
            (person_id,),
        )
        person_info = cursor.fetchone()
        father_id, mother_id, spouse_id = person_info

        # Fetch the person's father
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.id = ?""",
            (father_id,),
        )
        father_info = cursor.fetchone()

        # Fetch the person's mother
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.id = ?""",
            (mother_id,),
        )
        mother_info = cursor.fetchone()

        # Fetch the person's spouse
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.id = ?""",
            (spouse_id,),
        )
        spouse_info = cursor.fetchone()

        # Fetch the person's children
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.father = ? OR People.mother = ? 
            ORDER BY People.birth_date ASC""",
            (person_id, person_id),
        )
        children_info = cursor.fetchall()

        # Add a function to create a new row in the grid
        def add_grid_row(frame, info, row, is_separator=False,photo_height=100):
            if is_separator:
                separator = ttk.Frame(frame, height=2, relief='groove')
                separator.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)  

            elif info is not None:
                id_, first_name, middle_name, last_name, title, birth_date, death_date, image_path = info
                info_text = f"{first_name} {middle_name or ''} {last_name}\nBirth: {birth_date or ''}\nDeath: {death_date or ''}"

                # Add the image, if it exists
                if image_path is not None and os.path.isfile(image_path):
                    image = Image.open(image_path)
                    wpercent = (photo_height / float(image.size[1]))
                    width_size = int((float(image.size[0]) * float(wpercent)))
                    image = image.resize((width_size, photo_height), Image.ANTIALIAS)
                    photo = ImageTk.PhotoImage(image)
                    photo_label = tk.Label(frame, image=photo)
                    photo_label.image = photo  # keep a reference to the image
                    photo_label.grid(row=row, column=0)

                # Add the text
                text_label = tk.Label(frame, text=info_text)
                text_label.grid(row=row, column=1)

        # Add the family members to the grid
        add_grid_row(grid_frame, father_info, 0)
        add_grid_row(grid_frame, mother_info, 1)
        add_grid_row(grid_frame, None, 2, is_separator=True)
        add_grid_row(grid_frame, spouse_info, 3)
        add_grid_row(grid_frame, None, 4, is_separator=True)
        for i, child_info in enumerate(children_info, start=5):
            add_grid_row(grid_frame, child_info, i)