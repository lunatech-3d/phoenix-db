# common_utils.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3


def load_townships(cursor):
    """
    Fetch and format townships for dropdown selection.
    Returns:
        tuple: (list of formatted township strings, forward mapping dict, reverse mapping dict)
    """
    township_details = []
    township_map = {}
    reverse_township_map = {}

    try:
        # Query all townships
        cursor.execute("""
            SELECT 
                township_id, 
                township_name, 
                township_number, 
                township_direction, 
                range_number, 
                range_direction, 
                start_date, 
                end_date, 
                county, 
                state, 
                notes
            FROM Townships
            ORDER BY township_id
        """)
        townships = cursor.fetchall()

        for township in townships:
            township_id = township[0]
            name = township[1] or ""
            t_num = township[2] or ""
            t_dir = township[3] or ""
            r_num = township[4] or ""
            r_dir = township[5] or ""
            start_date = township[6] or ""
            end_date = township[7] or "Present"
            county = township[8] or ""
            state = township[9] or ""

            # Create a formatted string for display
            detail = f"{name} - T{t_num}{t_dir}, R{r_num}{r_dir} ({county}, {state}) - {start_date} to {end_date}"
            township_details.append(detail)
            township_map[detail] = township_id
            reverse_township_map[township_id] = detail

    except sqlite3.Error as e:
        print(f"Database error in load_townships: {e}")
        return [], {}, {}

    return township_details, township_map, reverse_township_map
