# Phoenix Database: Institution Schema Summary

This document outlines all tables related to the `Institution` subsystem for the Phoenix community history project. It is designed for use by both humans and AI coding agents (e.g., Codex) to understand and extend the schema safely.

---

## Naming Conventions

- **Table Names** use `Inst_*` (capital I, lowercase nst).
- **Field Names** use snake_case starting with `inst_` where applicable.
- **Date Fields** follow standard Phoenix formats:
  - `*_start_date` and `*_end_date` for ranges
  - If needed, use `*_date_precision` for values like `Year`, `Month`, or `Approx`.

---

## Tables

### 1. `Institution`

Stores core identity and classification of institutions.

Fields:
- `inst_id` (PK)
- `inst_name`, `inst_type`
- `inst_founding_date`, `inst_closing_date`
- `inst_description`, `inst_website`, `inst_image_path`, `inst_external_url`
- `inst_notes`

---

### 2. `Inst_Lineage`

Tracks historical transformations between institutions.

Fields:
- `lineage_id` (PK)
- `inst_id`, `related_inst_id`
- `lineage_type` (e.g., "Renamed From", "Merged Into")
- `lineage_notes`

---

### 3. `Inst_Location`

Tracks address history of institutions.

Fields:
- `inst_location_id` (PK)
- `inst_id`, `address_id`
- `location_start_date`, `location_end_date`
- `location_notes`

---

### 4. `Inst_Affiliation`

Links people to institutions (e.g., pastors, principals, students).

Fields:
- `inst_affiliation_id` (PK)
- `inst_id`, `person_id`
- `inst_affiliation_role`
- `inst_affiliation_start_date`, `inst_affiliation_end_date`
- `inst_affiliation_notes`, `source_id`

---

### 5. `InstRole` (Lookup)

Defines standardized roles used in affiliations.

Fields:
- `inst_role` (PK)
- `role_category` (e.g., Staff, Student)
- `role_description`

---

## Usage Notes

- All institutional relationships reference `inst_id` from the `Institution` table.
- Roles and dates are always contextualized for time-based queries and historical accuracy.
- Source tracking should be included where possible.