# Government Agencies Subsystem (AGENTS.md)

## Purpose
This subsystem manages historical records of government agencies, positions, personnel, and events. It is part of the Phoenix historical database project.

## Scope
- Covers records up to approximately the 1950s.
- Excludes any current or modern government data.

## Files
| File Name           | Purpose                                      |
|---------------------|----------------------------------------------|
| gov.py              | Main listing and search window for agencies |
| editgov.py          | Add/Edit form for an agency                  |
| gov_position.py     | Manage positions within an agency            |
| gov_personnel.py    | Manage personnel assignments                 |
| gov_events.py       | Manage government events                     |
| gov_linkage.py      | Popup selector for agencies                  |

## Design Standards
- Follow the same conventions as `institutions.py`, `editinst.py`, etc.
- Use consistent Tkinter layout:
  - Treeview listing
  - Search fields
  - Add/Edit/Delete buttons
  - Sorting on column headers

## Shared Support Modules
Scripts **must** use these existing modules:
- `config.py` (`DB_PATH`, `PATHS`)
- `context_menu.py` (right-click menus)
- `date_utils.py` (date parsing, formatting)
- `person_linkage.py` (selecting People records)
- `person_search.py` (searching People)

## Notes
- Use `original_text` fields for storing verbatim transcriptions of source material.
- All date fields should support precision values (`YEAR`, `MONTH`, `EXACT`, etc.).
- Naming conventions must follow:
  - `gov_*` prefix
  - Lowercase filenames