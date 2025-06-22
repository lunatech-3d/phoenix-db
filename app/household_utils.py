import sqlite3

def get_or_create_household(cursor, census_housenumber, record_year, address_id=None, notes=None):
    """
    Get or create a household based on the census_housenumber and record_year.

    Args:
        cursor: SQLite cursor object.
        census_housenumber (str): The census household number (key identifier).
        record_year (int): The year the record is from.
        address_id (int, optional): The address ID, if available.
        notes (str, optional): Additional notes about the household.

    Returns:
        int: The household_id of the existing or newly created household.
    """
    # Check if the household already exists
    cursor.execute("""
        SELECT id FROM Households 
        WHERE household_number = ? AND record_year = ?
    """, (census_housenumber, record_year))
    result = cursor.fetchone()

    if result:
        # Household already exists, return the household_id
        return result[0]

    # Create a new household record
    cursor.execute("""
        INSERT INTO Households (household_number, record_year, address_id, household_notes, household_start_date, event_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        census_housenumber,
        record_year,
        address_id,
        notes or f"Generated from Census Record ({record_year})",
        f"{record_year}-01-01",
        "Census"
    ))
    return cursor.lastrowid


def add_household_member(cursor, household_id, person_id, role=""):
    """
    Add a person to the HouseholdMembers table if they are not already linked.

    Args:
        cursor: SQLite cursor object.
        household_id (int): The ID of the household.
        person_id (int): The ID of the person to add.
        role (str, optional): The role of the person in the household (e.g., "Head", "Wife").

    Returns:
        bool: True if a new member was added, False if they were already linked.
    """
    # Check if the person is already linked to the household
    cursor.execute("""
        SELECT 1 FROM HouseholdMembers 
        WHERE household_id = ? AND household_member = ?
    """, (household_id, person_id))
    result = cursor.fetchone()

    if result:
        # Member already exists
        return False

    # Add the person to the household
    cursor.execute("""
        INSERT INTO HouseholdMembers (household_id, household_member, role)
        VALUES (?, ?, ?)
    """, (household_id, person_id, role))
    return True


def update_household_address(cursor, household_id, address_id):
    """
    Update the address_id for a household.

    Args:
        cursor: SQLite cursor object.
        household_id (int): The ID of the household to update.
        address_id (int): The new address ID to set.
    """
    cursor.execute("""
        UPDATE Households 
        SET address_id = ? 
        WHERE id = ?
    """, (address_id, household_id))