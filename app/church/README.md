# Church Subsystem

Tracks churches and life events (baptisms, funerals, marriages) that occurred in them.

Includes:
- Full mirror of Institution table structures
- Denomination field (REQUIRED)
- Marriage records enhanced to support Church, Officiant, and AI curation
- Supports AI curation via `curator_summary` and `event_context_tags` in all event tables
- `recognition` in Church_GroupMember captures informal honors
- Church, group, staff, and member tables include curator summaries and tags for AI-driven storytelling
- Baptism and funeral records can be added, edited, and deleted from the church form