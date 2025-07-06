🎬 Phoenix Database – Movie Module
Overview
This module tracks movies and their showings at local theaters. It integrates with the Biz table (your businesses/theaters) and follows the same modular structure as events.py, edit_event.py, etc.

Directory Structure
bash
Copy
Edit
app/
  movie/
    movies.py            # Movie catalog manager
    edit_movie.py        # Add/Edit movie records
    movie_showings.py    # Showings manager
    edit_showing.py      # Add/Edit showing records
    __init__.py          # (optional) marks as a package
Tables
🎥 Movies
Field	Description
movie_id	Primary key
title	Movie title
director	Director name
release_year	Year released
genre	Genre
runtime_minutes	Runtime in minutes
rating	MPAA rating
description	Short description or synopsis
poster_url	URL to poster image
imdb_url	IMDb link
notes	Additional notes

🎟️ MovieShowings
Field	Description
showing_id	Primary key
movie_id	FK to Movies
biz_id	FK to Biz (theater)
start_date	Showing start date
end_date	Showing end date
format	Format (e.g., 35mm, Digital)
special_event	Premiere, festival, etc.
ticket_price	Ticket price (historical)
attendance_estimate	Estimated attendance
notes	Additional notes

Modules
movies.py
Manages the movie catalog.

Search filters by title, director, release year.

Treeview listing all movies.

Add/Edit/Delete movie records.

Double-click to edit.

Optional: open IMDb link in browser.

edit_movie.py
Add or edit a movie record.

All fields from the Movies table.

Validates numeric fields (e.g., release year).

Optionally preview poster URL.

movie_showings.py
Lists all movie showings.

Filter by theater and date.

Treeview joins Movies and Biz names.

Add/Edit/Delete showings.

Double-click to edit.

edit_showing.py
Add or edit a showing.

Dropdown to select Movie.

Dropdown to select Biz.

Inputs for dates, format, events, ticket price, attendance.

Date validation.

Usage
Adding a Movie
Launch movies.py.

Click Add Movie.

Enter details.

Click Save.

Scheduling a Showing
Launch movie_showings.py (or the Showings tab in Biz).

Click Add Showing.

Select the Movie and Theater.

Fill in dates and details.

Click Save.

Example Queries
Show all movies at a specific theater in 1940:

sql
Copy
Edit
SELECT m.title, s.start_date, s.end_date
FROM MovieShowings s
JOIN Movies m ON s.movie_id = m.movie_id
WHERE s.biz_id = ?
  AND s.start_date BETWEEN '1940-01-01' AND '1940-12-31';
All showings of "Gone with the Wind":

sql
Copy
Edit
SELECT b.biz_name, s.start_date, s.end_date
FROM MovieShowings s
JOIN Biz b ON s.biz_id = b.biz_id
JOIN Movies m ON s.movie_id = m.movie_id
WHERE m.title = 'Gone with the Wind';
Integration Notes
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