# Church Subsystem

Tracks churches and life events (baptisms, funerals, marriages) that occurred in them.

Includes:
- Full mirror of Institution table structures
- Denomination field (REQUIRED)
- Marriage records enhanced to support Church, Officiant, and AI curation
- Supports AI curation via `curator_summary` and `event_context_tags` in all event tables
- `ChurchLocHistory` table tracks address history for each church
- `migrate_church_data.py` script for moving existing Institution records to the Church tables

Run the migration after creating the Church tables:
```bash
python app/migrate_church_data.py
```