import sqlite3
from typing import List, Any, Tuple, Union

def search_people(
    cursor: sqlite3.Cursor,
    columns: str = "*",
    return_query: bool = False,
    **criteria,
) -> Union[List[tuple], Tuple[List[tuple], str, List[Any]]]:
    
    """Search the People table using dynamic criteria.

    Parameters
    ----------
    cursor : sqlite3.Cursor
        Cursor connected to the database.
    columns : str, optional
        Comma-separated list of columns to select. Defaults to ``"*"``
        which returns every field.
    **criteria : dict
        Fields to filter by. Supported keys include ``first_name``,
        ``middle_name``, ``last_name``, ``married_name`` and ``record_id``.
        Additional fields are matched exactly.

    Returns
    -------
    list of tuple
        Matching rows ordered by last and first name.
    """
    query = f"SELECT {columns} FROM People WHERE 1=1"
    params: List[Any] = []

    # Record ID (exact match)
    record_id = criteria.pop("record_id", None)
    if record_id:
        query += " AND id = ?"
        params.append(record_id)

    # Last name / married name
    last_name = criteria.pop("last_name", None)
    if last_name:
        query += " AND (last_name LIKE ? OR married_name LIKE ?)"
        params.extend([f"{last_name}%", f"{last_name}%"])

    # Standard prefix-like fields
    for key in ("first_name", "middle_name", "married_name"):
        value = criteria.pop(key, None)
        if value:
            query += f" AND {key} LIKE ?"
            params.append(f"{value}%")

    # Any additional criteria are matched exactly
    for key, value in list(criteria.items()):
        if value is not None and value != "":
            query += f" AND {key} = ?"
            params.append(value)

    query += " ORDER BY last_name, first_name"
    cursor.execute(query, params)
    results = cursor.fetchall()

    if return_query:
        return results, query, params

    return results