# Government Agencies Subsystem

This subsystem manages government agencies, positions, personnel, and events for the Plymouth Project. It is modeled after the Institutions subsystem, with support for nested structures, elected and appointed positions, term records, and source documentation.

## Purpose

To document the historical record of Plymouth’s government up to approximately the 1950s. No current records are included.

## Components

- **GovAgency**: Main government units and departments.
- **GovPosition**: Positions or offices within agencies.
- **GovPersonnel**: Individuals who held each position, with term dates.
- **GovEvents**: Elections, ordinances, and other important events.

## Special Considerations for AI Integration

- **original_text**: This field stores the full transcription of historical documents or event descriptions. It allows the AI to reference the exact wording and supports retrieval-augmented generation in future interfaces.
- **tags** (optional): Keyword labels for classification or advanced search.
- **record_language** (optional): Indicates the language of the stored text.

## File Structure

- `create_gov_tables.sql` – SQL script to create tables.
- `gov_agencies_schema.md` – Field definitions.
- Future scripts:
  - `editgov.py`
  - `gov_position.py`
  - `gov_personnel.py`
  - `gov_events.py`
  - `gov_linkage.py`

## Example Use Cases

- Track who served as Township Supervisor between 1900–1905.
- Record election dates and full text from newspaper clippings.
- Show agency hierarchy over time.
- Enable AI-assisted queries: *"Show me all ordinances about road funding."*

## Conventions

- Dates include precision (`YEAR`, `MONTH`, `EXACT`, `ABOUT`, etc.).
- `original_text` preserves source verbatim.