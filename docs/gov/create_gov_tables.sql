- Government Agencies Schema with AI-friendly fields

CREATE TABLE IF NOT EXISTS GovAgency (
    gov_agency_id     INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    parent_agency_id  INTEGER REFERENCES GovAgency(gov_agency_id),
    jurisdiction      TEXT,
    type              TEXT,
    notes             TEXT,
    start_date        TEXT,
    start_date_precision TEXT,
    end_date          TEXT,
    end_date_precision TEXT
);

CREATE TABLE IF NOT EXISTS GovPosition (
    gov_position_id   INTEGER PRIMARY KEY,
    agency_id         INTEGER NOT NULL REFERENCES GovAgency(gov_agency_id),
    title             TEXT NOT NULL,
    description       TEXT,
    is_elected        BOOLEAN DEFAULT 0,
    is_appointed      BOOLEAN DEFAULT 0,
    is_historical     BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS GovPersonnel (
    gov_personnel_id  INTEGER PRIMARY KEY,
    person_id         INTEGER NOT NULL REFERENCES People(id),
    position_id       INTEGER NOT NULL REFERENCES GovPosition(gov_position_id),
    start_date        TEXT,
    start_precision   TEXT,
    end_date          TEXT,
    end_precision     TEXT,
    notes             TEXT,
    original_text     TEXT,
    source_id         INTEGER REFERENCES Sources(id),
    UNIQUE(person_id, position_id, start_date)
);

CREATE TABLE IF NOT EXISTS GovEvents (
    gov_event_id      INTEGER PRIMARY KEY,
    agency_id         INTEGER REFERENCES GovAgency(gov_agency_id),
    title             TEXT NOT NULL,
    type              TEXT,
    date              TEXT,
    date_precision    TEXT,
    location          TEXT,
    description       TEXT,
    original_text     TEXT,
    link_url          TEXT,
    source_id         INTEGER REFERENCES Sources(id)
);