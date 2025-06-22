# findagrave_agent.py

import requests
import webbrowser
from bs4 import BeautifulSoup

def findagrave_scrape(first_name, last_name, location):
    """
    Search FindAGrave for a person by name and location,
    then scrape basic memorial details if found.

    Args:
        first_name (str): First name of the person
        last_name (str): Last name of the person
        location (str): Location (e.g., city, state)

    Returns:
        dict: Dictionary containing extracted fields, or None if not found.
    """
    query = f"{first_name} {last_name} {location} site:findagrave.com"
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        # Step 1: Perform Google search
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            print("[FindAGrave Agent] Failed to fetch search results")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Step 2: Find the first FindAGrave link
        memorial_url = None
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'findagrave.com/memorial/' in href:
                href = href.split('&')[0].replace('/url?q=', '')
                memorial_url = href
                break

        if not memorial_url:
            print("[FindAGrave Agent] No FindAGrave memorial found")
            print(f"[FindAGrave Agent] Opening Google search page for manual review...")
            webbrowser.open(search_url)
            return None

        # Step 3: Fetch memorial page
        memorial_response = requests.get(memorial_url, headers=headers)
        if memorial_response.status_code != 200:
            print("[FindAGrave Agent] Failed to fetch memorial page")
            return None

        memorial_soup = BeautifulSoup(memorial_response.text, 'html.parser')

        # Step 4: Extract fields
        data = {
            'full_name': None,
            'first_name': None,
            'middle_name': None,
            'last_name': None,
            'birth_date': None,
            'death_date': None,
            'burial_location': None,
            'photo_url': None,
            'memorial_link': memorial_url
        }

        # Extract full name
        name_tag = memorial_soup.find('h1', class_='memorial-name')
        if name_tag:
            full_name = name_tag.get_text(strip=True)
            data['full_name'] = full_name

            # Split name into first, middle, last
            name_parts = full_name.split()
            if len(name_parts) == 1:
                data['first_name'] = name_parts[0]
            elif len(name_parts) == 2:
                data['first_name'], data['last_name'] = name_parts
            else:
                data['first_name'] = name_parts[0]
                data['middle_name'] = " ".join(name_parts[1:-1])
                data['last_name'] = name_parts[-1]

        # Birth and death dates
        birth_death = memorial_soup.find_all('span', class_='birth-death')
        if birth_death:
            dates = birth_death[0].get_text(strip=True).split('—')
            if len(dates) >= 1:
                data['birth_date'] = dates[0].strip()
            if len(dates) == 2:
                data['death_date'] = dates[1].strip()

        # Burial location
        cemetery = memorial_soup.find('a', class_='cemetery-name')
        if cemetery:
            data['burial_location'] = cemetery.get_text(strip=True)

        # Main photo
        photo = memorial_soup.find('img', class_='main-photo')
        if photo:
            data['photo_url'] = photo['src']

        return data

    except Exception as e:
        print(f"[FindAGrave Agent] An error occurred: {e}")
        return None


# Test block (only runs if you run this file directly)
if __name__ == "__main__":
    sample = findagrave_scrape("Albert", "Chaffee", "Plymouth, Wayne County, Michigan, USA")
    print(sample)
