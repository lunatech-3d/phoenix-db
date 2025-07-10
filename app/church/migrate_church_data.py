import sqlite3
from pathlib import Path

from app.config import DB_PATH, REPO_DIR

# Resolve the SQL path from the repository root so the script can be executed
# from any location.  The file lives under docs/church.
SQL_PATH = REPO_DIR / "docs" / "church" / "create_church_tables.sql"


def ensure_church_tables(cursor):
    """Create Church subsystem tables if they do not already exist."""
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # make sure the new tables exist
    ensure_church_tables(cur)

    # fetch institutions marked as churches
    cur.execute(
        """
        SELECT inst_id, inst_name, inst_desc, address_id,
               start_date, start_date_precision,
               end_date, end_date_precision, notes,
               source_id, url, image_path
          FROM Institution
         WHERE inst_type = 'Church'
        """
    )
    institutions = cur.fetchall()

    for row in institutions:
        (
            inst_id,
            name,
            desc,
            address_id,
            start_date,
            start_prec,
            end_date,
            end_prec,
            notes,
            source_id,
            url,
            image_path,
        ) = row

        # Use the existing description as denomination if available
        denom = desc or "Unknown"

        cur.execute(
            """
            INSERT OR IGNORE INTO Church (
                church_id, church_name, denomination, address_id,
                start_date, start_date_precision,
                end_date, end_date_precision, notes,
                source_id, url, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inst_id,
                name,
                denom,
                address_id,
                start_date,
                start_prec,
                end_date,
                end_prec,
                notes,
                source_id,
                url,
                image_path,
            ),
        )

        # migrate associated events
        cur.execute(
            """
            SELECT event_type, event_date, event_date_precision,
                   end_date, end_date_precision, description,
                   original_text, person_id, source_id, link_url
              FROM Inst_Event
             WHERE inst_id = ?
            """,
            (inst_id,),
        )
        for ev in cur.fetchall():
            cur.execute(
                """
                INSERT INTO Church_Event (
                    church_id, event_type, event_date, event_date_precision,
                    end_date, end_date_precision, description,
                    original_text, person_id, source_id, link_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (inst_id, *ev),
            )

        # migrate staff entries
        cur.execute(
            """
            SELECT person_id, title, start_date, start_date_precision,
                   end_date, end_date_precision, notes
              FROM Inst_Staff
             WHERE inst_id = ?
            """,
            (inst_id,),
        )
        for st in cur.fetchall():
            cur.execute(
                """
                INSERT INTO Church_Staff (
                    church_id, person_id, title,
                    start_date, start_date_precision,
                    end_date, end_date_precision, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (inst_id, *st),
            )

        # migrate location history
        cur.execute(
            """SELECT address_id, start_date, start_date_precision,
                       end_date, end_date_precision, notes, url
                   FROM InstLocHistory WHERE inst_id=?""",
            (inst_id,),
        )
        for loc in cur.fetchall():
            cur.execute(
                """INSERT INTO ChurchLocHistory (
                        church_id, address_id,
                        start_date, start_date_precision,
                        end_date, end_date_precision,
                        notes, url
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (inst_id, *loc),
            )

    conn.commit()
    conn.close()
    print(f"Migrated {len(institutions)} church records.")


if __name__ == "__main__":
    migrate()