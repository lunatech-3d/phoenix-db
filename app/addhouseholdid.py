import sqlite3
import sys
from .config import DB_PATH, PATHS

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Enable foreign key constraint
cursor.execute("PRAGMA foreign_keys = ON;")

# Create new table with the same structure as Census but with an additional household_id column
cursor.execute("""
    CREATE TABLE Census_new (
        id INTEGER PRIMARY KEY,
        person_age TEXT,
        person_occupation TEXT,
        census_year INTEGER,
        census_housenumber INTEGER,
        real_estate_value TEXT,
        estate_value TEXT,
        person_id INTEGER,
        household_id INTEGER,
        FOREIGN KEY (person_id) REFERENCES People(id),
        FOREIGN KEY (household_id) REFERENCES Households(id)
    );
""")

# Copy all data from Census to Census_new
cursor.execute("""
    INSERT INTO Census_new (id, person_age, person_occupation, census_year, 
                            census_housenumber, real_estate_value, estate_value, person_id)
    SELECT id, person_age, person_occupation, census_year, 
           census_housenumber, real_estate_value, estate_value, person_id
    FROM Census;
""")

# Drop the old Census table
cursor.execute("""
    DROP TABLE Census;
""")

# Rename the new table to Census
cursor.execute("""
    ALTER TABLE Census_new RENAME TO Census;
""")

# Commit the changes and close the connection
connection.commit()
connection.close()
