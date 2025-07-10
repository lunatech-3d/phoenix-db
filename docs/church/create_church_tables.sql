
-- Table: Church
CREATE TABLE Church (
    church_id INTEGER PRIMARY KEY,
    church_name TEXT NOT NULL,
    denomination TEXT NOT NULL,
    address_id INTEGER,
    start_date TEXT,
    start_date_precision TEXT,
    end_date TEXT,
    end_date_precision TEXT,
    notes TEXT,
    source_id INTEGER,
    url TEXT,
    image_path TEXT,
    FOREIGN KEY (address_id) REFERENCES Address(address_id),
    FOREIGN KEY (source_id) REFERENCES Sources(source_id)
);

CREATE TABLE Church_Event (
    church_event_id INTEGER PRIMARY KEY,
    church_id INTEGER NOT NULL,
    event_type TEXT,
    event_date TEXT,
    event_date_precision TEXT,
    end_date TEXT,
    end_date_precision TEXT,
    description TEXT,
    original_text TEXT,
    person_id INTEGER,
    source_id INTEGER,
    link_url TEXT,
    curator_summary TEXT,
    event_context_tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (church_id) REFERENCES Church(church_id),
    FOREIGN KEY (person_id) REFERENCES People(id),
    FOREIGN KEY (source_id) REFERENCES Sources(source_id)
);

CREATE TABLE Church_Group (
    church_group_id INTEGER PRIMARY KEY,
    church_id INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    year_active INTEGER,
    group_type TEXT,
    notes TEXT,
    FOREIGN KEY (church_id) REFERENCES Church(church_id)
);

CREATE TABLE Church_GroupMember (
    church_group_member_id INTEGER PRIMARY KEY,
    church_group_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    role TEXT,
    member_order INTEGER,
    start_date TEXT,
    end_date TEXT,
    notes TEXT,
    FOREIGN KEY (church_group_id) REFERENCES Church_Group(church_group_id),
    FOREIGN KEY (person_id) REFERENCES People(id)
);

CREATE TABLE Church_Staff (
    church_staff_id INTEGER PRIMARY KEY,
    church_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    title TEXT,
    start_date TEXT,
    start_date_precision TEXT,
    end_date TEXT,
    end_date_precision TEXT,
    notes TEXT,
    FOREIGN KEY (church_id) REFERENCES Church(church_id),
    FOREIGN KEY (person_id) REFERENCES People(id)
);

-- Table: ChurchLocHistory
CREATE TABLE ChurchLocHistory (
    church_id INTEGER NOT NULL,
    address_id INTEGER NOT NULL,
    start_date TEXT,
    start_date_precision TEXT,
    end_date TEXT,
    end_date_precision TEXT,
    notes TEXT,
    url TEXT,
    PRIMARY KEY (church_id, address_id, start_date),
    FOREIGN KEY (church_id) REFERENCES Church(church_id),
    FOREIGN KEY (address_id) REFERENCES Address(address_id)
);    

CREATE TABLE Baptism (
    baptism_id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL,
    church_id INTEGER,
    baptism_date TEXT,
    officiant_id INTEGER,
    notes TEXT,
    curator_summary TEXT,
    event_context_tags TEXT,
    FOREIGN KEY (person_id) REFERENCES People(id),
    FOREIGN KEY (church_id) REFERENCES Church(church_id),
    FOREIGN KEY (officiant_id) REFERENCES People(id)
);

CREATE TABLE Funeral (
    funeral_id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL,
    church_id INTEGER,
    funeral_date TEXT,
    officiant_id INTEGER,
    notes TEXT,
    curator_summary TEXT,
    event_context_tags TEXT,
    FOREIGN KEY (person_id) REFERENCES People(id),
    FOREIGN KEY (church_id) REFERENCES Church(church_id),
    FOREIGN KEY (officiant_id) REFERENCES People(id)
);