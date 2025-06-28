# Government Agencies Schema Documentation

---

## GovAgency
Stores government agencies or departments.

| Column             | Type     | Description                                         |
|--------------------|----------|-----------------------------------------------------|
| gov_agency_id      | INTEGER  | Primary key.                                        |
| name               | TEXT     | Name of the agency (e.g., "Township Clerk").        |
| parent_agency_id   | INTEGER  | References `GovAgency.gov_agency_id` for hierarchy. |
| jurisdiction       | TEXT     | City, Township, Village, etc.                       |
| type               | TEXT     | Department, Board, Body, etc.                       |
| notes              | TEXT     | Additional notes.                                   |

---

## GovPosition
Defines positions/offices within an agency.

| Column             | Type     | Description                                      |
|--------------------|----------|--------------------------------------------------|
| gov_position_id    | INTEGER  | Primary key.                                     |
| agency_id          | INTEGER  | FK to `GovAgency`.                               |
| title              | TEXT     | Title of the position (e.g., "Supervisor").      |
| description        | TEXT     | Description of the role.                         |
| is_elected         | BOOLEAN  | 1 if elected.                                    |
| is_appointed       | BOOLEAN  | 1 if appointed.                                  |
| is_historical      | BOOLEAN  | 1 if no longer active.                           |

---

## GovPersonnel
Stores records of who held each position and when.

| Column             | Type     | Description                                              |
|--------------------|----------|----------------------------------------------------------|
| gov_personnel_id   | INTEGER  | Primary key.                                             |
| person_id          | INTEGER  | FK to `People`.                                          |
| position_id        | INTEGER  | FK to `GovPosition`.                                     |
| start_date         | TEXT     | Start date.                                              |
| start_precision    | TEXT     | 'YEAR', 'MONTH', 'EXACT', 'ABOUT', etc.                  |
| end_date           | TEXT     | End date.                                                |
| end_precision      | TEXT     | Precision for end date.                                  |
| notes              | TEXT     | Notes about the term.                                    |
| source_id          | INTEGER  | FK to `Sources`.                                         |
| original_text      | TEXT     | Full transcription or record text.                      |

**Constraint:**
Unique (`person_id`, `position_id`, `start_date`)

---

## GovEvents
Tracks events like elections, ordinances, and other milestones.

| Column             | Type     | Description                                  |
|--------------------|----------|----------------------------------------------|
| gov_event_id       | INTEGER  | Primary key.                                 |
| agency_id          | INTEGER  | FK to `GovAgency`.                           |
| title              | TEXT     | Event title (e.g., "1924 Election").         |
| type               | TEXT     | 'Election', 'Ordinance', 'Meeting', etc.     |
| date               | TEXT     | Event date.                                  |
| date_precision     | TEXT     | Precision for date.                          |
| location           | TEXT     | Event location.                              |
| description        | TEXT     | Short summary.                               |
| original_text      | TEXT     | Full transcription or document text.         |
| link_url           | TEXT     | URL to supporting material.                  |
| source_id          | INTEGER  | FK to `Sources`.                             |