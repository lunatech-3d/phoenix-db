# findagrave_agent_direct.py

import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import messagebox, simpledialog
import webbrowser

def findagrave_direct_search(first_name, last_name, location="Plymouth, Wayne, Michigan, United States"):
    """
    Search FindAGrave directly using their public search form.
    Returns a list of matching memorials with basic details.
    """
    try:
        search_url = ("https://www.findagrave.com/memorial/search?"
                      f"firstName={first_name}&lastName={last_name}&location={location.replace(' ', '%20')}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            print("[FindAGrave Agent] Failed to fetch search page")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        memorials = []

        results = soup.find_all('div', class_='search-item')

        for result in results:
            link = result.find('a')
            if not link:
                continue

            href = link.get('href')
            name = link.get_text(strip=True)

            if href and href.startswith("/memorial/"):
                memorial_link = f"https://www.findagrave.com{href}"

                years_span = result.find('span', class_='search-bio')
                years = years_span.get_text(strip=True) if years_span else ""

                memorials.append({
                    "name": name,
                    "years": years,
                    "link": memorial_link
                })

        return memorials

    except Exception as e:
        print(f"[FindAGrave Agent] Error: {e}")
        return []

def show_findagrave_picker(memorials):
    """
    Show a simple Tkinter popup to pick a memorial from a list.
    """
    if not memorials:
        messagebox.showinfo("No Matches", "No matching memorials found on FindAGrave.")
        return None

    window = tk.Toplevel()
    window.title("Select a Memorial")
    window.geometry("600x400")

    listbox = tk.Listbox(window, width=80, height=20)
    listbox.pack(padx=10, pady=10)

    for idx, memorial in enumerate(memorials):
        display_text = f"{memorial['name']} {memorial['years']}"
        listbox.insert(idx, display_text)

    selected_memorial = {}

    def select():
        idx = listbox.curselection()
        if not idx:
            messagebox.showwarning("No Selection", "Please select a memorial.")
            return
        idx = idx[0]
        selected_memorial.update(memorials[idx])
        window.destroy()

    def cancel():
        window.destroy()

    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Select", command=select).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Cancel", command=cancel).pack(side="left", padx=10)

    window.transient()
    window.grab_set()
    window.wait_window()

    return selected_memorial if selected_memorial else None

def clean_location_for_findagrave(stored_location):
    """
    Takes stored location like 'Riverside Cemetery, Plymouth, Wayne, MI'
    and converts it to 'Plymouth, Wayne County, Michigan, USA'
    """
    try:
        parts = [p.strip() for p in stored_location.split(',')]

        if len(parts) >= 4:
            cemetery, city, county, state_abbr = parts[0], parts[1], parts[2], parts[3]
        else:
            return "Plymouth, Wayne County, Michigan, USA"

        state_full_names = {
            "MI": "Michigan",
            "OH": "Ohio",
            "IN": "Indiana",
            "IL": "Illinois"
        }

        state_full = state_full_names.get(state_abbr.upper(), state_abbr)

        corrected_location = f"{city}, {county} County, {state_full}, USA"
        return corrected_location

    except Exception as e:
        print(f"[FindAGrave Agent] Failed to clean location: {e}")
        return "Plymouth, Wayne County, Michigan, USA"

# Example main function for testing manually
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    first_name = simpledialog.askstring("Input", "Enter First Name:")
    last_name = simpledialog.askstring("Input", "Enter Last Name:")

    if first_name and last_name:
        results = findagrave_direct_search(first_name, last_name)
        selected = show_findagrave_picker(results)

        if selected:
            webbrowser.open(selected['link'])
            print("Selected Memorial:", selected)

    root.mainloop()