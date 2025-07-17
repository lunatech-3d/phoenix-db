🎬 Phoenix Database – Movie Module
Overview
This module tracks movies and their showings at local theaters. It integrates with the Biz table (your businesses/theaters) and follows the same modular structure as events.py, edit_event.py, etc.

Directory Structure
bash
Copy
Edit
app/
  movie/
    movie_showings.py    # Showings manager
    edit_showing.py      # Add/Edit showing records
    __init__.py          # (optional) marks as a package
Tables


🎟️ MovieShowings
Field	Description
showing_id	Primary key
title   Movie title
biz_id  FK to Biz (theater)
start_date      Showing start date
end_date        Showing end date
format  Format (e.g., 35mm, Digital)
special_event   Premiere, festival, etc.
ticket_price    Ticket price (historical)
attendance_estimate     Estimated attendance
poster_url      Poster image path
movie_overview_url      IMDb or other overview link
source_id       FK to Sources
notes   Additional notes

Modules

movie_showings.py
Lists all movie showings.

Filter by theater and date.

Treeview shows Biz names.

Add/Edit/Delete showings.

Double-click to edit.

edit_showing.py
Add or edit a showing.

Inputs for dates, format, events, ticket price, attendance.

Date validation.

Usage

Scheduling a Showing

Click Add Showing.

Select the Theater.
Enter title, dates, and details.

Click Save.

Example Queries
Show all movies at a specific theater in 1940:

sql
Copy
Edit
SELECT title, start_date, end_date
FROM MovieShowings
WHERE biz_id = ?
  AND start_date BETWEEN '1940-01-01' AND '1940-12-31';
All showings of "Gone with the Wind":

sql
Copy
Edit
SELECT b.biz_name, s.start_date, s.end_date
FROM MovieShowings s
JOIN Biz b ON s.biz_id = b.biz_id
WHERE s.title = 'Gone with the Wind';
Use date_utils.py for date formatting and validation.

Follow the modular structure consistent with other modules (events.py, edit_event.py).

Keep each script independent for easier maintenance.

Validate dates and numeric fields before saving records.

Use clear error messages.

AI and Storytelling
This module supports:

Historical queries (which movies played where and when).

Storytelling about Plymouth theaters.

Future AI integrations (e.g., generating timelines, answering questions).