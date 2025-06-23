import sqlite3
from app.config import DB_PATH

def create_institution_tables():
    sql = """
-- Table: Institution
CREATE TABLE IF NOT EXISTS Institution (
    inst_id INTEGER PRIMARY KEY,
    inst_name TEXT NOT NULL,
    inst_type TEXT,
    inst_desc TEXT,
    address_id INTEGER,
    start_date TEXT,
    start_date_precision TEXT,
    end_date TEXT,
    end_date_precision TEXT,
    notes TEXT,
    source_id INTEGER,
    url TEXT,
    image_path TEXT
);

-- Table: Inst_Event
CREATE TABLE IF NOT EXISTS Inst_Event (
    inst_event_id INTEGER PRIMARY KEY,
    inst_id INTEGER NOT NULL,
    event_type TEXT,
    event_date TEXT,
    event_date_precision TEXT,
    end_date TEXT,
    end_date_precision TEXT,
    description TEXT,
    person_id INTEGER,
    source_id INTEGER,
    link_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Inst_Group
CREATE TABLE IF NOT EXISTS Inst_Group (
    inst_group_id INTEGER PRIMARY KEY,
    inst_id INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    year_active INTEGER,
    group_type TEXT,
    notes TEXT
);

-- Table: Inst_GroupMember
CREATE TABLE IF NOT EXISTS Inst_GroupMember (
    inst_group_member_id INTEGER PRIMARY KEY,
    inst_group_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    role TEXT,
    member_order INTEGER,
    start_date TEXT,
    end_date TEXT,
    notes TEXT
);

-- Table: Inst_Staff
CREATE TABLE IF NOT EXISTS Inst_Staff (
    inst_staff_id INTEGER PRIMARY KEY,
    inst_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    title TEXT,
    start_date TEXT,
    start_date_precision TEXT,
    end_date TEXT,
    end_date_precision TEXT,
    notes TEXT
);
"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(sql)
    conn.commit()
    conn.close()
    print("✅ Institution tables created successfully.")

if __name__ == "__main__":
    create_institution_tables()
