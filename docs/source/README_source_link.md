# Source Linking System

This document describes the Source Linking subsystem which allows any record or field in the database to be associated with one or more sources.

## Purpose
- Provide fine‑grained citations for individual fields
- Record verbatim quotes from the original material
- Keep an audit trail via timestamps

## Table: `Source_Link`
| Column | Type | Notes |
|-------|------|------|
| `source_link_id` | INTEGER PRIMARY KEY |
| `source_id` | INTEGER | References `Sources.id` |
| `table_name` | TEXT | Name of the table containing the record |
| `record_id` | INTEGER | Identifier of the row being cited |
| `field_name` | TEXT | Optional field being cited (NULL if record level) |
| `original_text` | TEXT | Verbatim excerpt from the source |
| `url_override` | TEXT | Optional direct link to the exact page |
| `notes` | TEXT | Curator notes |
| `created_at` | TIMESTAMP | Auto‑filled timestamp |

## UI Workflow
1. Right‑click on a field and choose **Add/View Source**.
2. A popup window shows all existing links and a form to add a new one.
3. Use the **Add Source** button next to the dropdown to create a new Source on the fly.
4. Double‑click an entry in the list (or use the **Edit** button) to load it for editing. Use **Delete** to remove a link.
5. Right‑click any field in the popup to Cut, Copy or Paste text.

The popup is implemented in `app/source/source_link_editor.py` and is launched from `context_menu.py`.