"""Tool definitions and implementations for the HR agent."""

import json
from data import get_connection

# --- Tool schemas (provider-agnostic, matches Freeplay's ToolSchema format) ---

TOOL_DEFINITIONS = [
    {
        "name": "lookup_employee",
        "description": (
            "Look up an employee by name (partial match supported). "
            "Returns their profile info including title, department, manager, start date, and location."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full or partial name of the employee to look up.",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_performance_reviews",
        "description": (
            "Get performance review history for an employee. "
            "Returns ratings, summaries, and areas for growth for each review period."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID (e.g. E001).",
                }
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "get_goals",
        "description": (
            "Get current goals and their progress for an employee. "
            "Returns each goal with its status (On Track, At Risk, Off Track, Complete, Not Started) and progress percentage."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID (e.g. E001).",
                }
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "get_time_off",
        "description": (
            "Get PTO balance and upcoming scheduled time off for an employee."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID (e.g. E001).",
                }
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "get_compensation",
        "description": (
            "Get compensation details for an employee including salary band, "
            "current salary, band range, last adjustment date, and next equity vesting date."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID (e.g. E001).",
                }
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "list_direct_reports",
        "description": (
            "List all direct reports for a given manager. "
            "Accepts a manager name (partial match) or manager ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "manager": {
                    "type": "string",
                    "description": "Manager name (partial match) or manager ID (e.g. M001).",
                }
            },
            "required": ["manager"],
        },
    },
]


# --- Tool implementations ---


def lookup_employee(name: str) -> str:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT e.id, e.name, e.title, e.department, e.start_date, e.location,
               e.salary_band, e.email, m.name as manager_name
        FROM employees e
        JOIN managers m ON e.manager_id = m.id
        WHERE LOWER(e.name) LIKE LOWER(?)
        """,
        (f"%{name}%",),
    ).fetchall()
    conn.close()
    if not rows:
        return json.dumps({"error": f"No employee found matching '{name}'."})
    return json.dumps([dict(r) for r in rows])


def get_performance_reviews(employee_id: str) -> str:
    conn = get_connection()
    rows = conn.execute(
        "SELECT period, rating, summary, areas_for_growth FROM performance_reviews WHERE employee_id = ? ORDER BY period DESC",
        (employee_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return json.dumps({"error": f"No performance reviews found for {employee_id}."})
    return json.dumps([dict(r) for r in rows])


def get_goals(employee_id: str) -> str:
    conn = get_connection()
    rows = conn.execute(
        "SELECT goal, status, progress FROM goals WHERE employee_id = ?",
        (employee_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return json.dumps({"error": f"No goals found for {employee_id}."})
    return json.dumps([dict(r) for r in rows])


def get_time_off(employee_id: str) -> str:
    conn = get_connection()
    balance = conn.execute(
        "SELECT pto_remaining_days FROM time_off WHERE employee_id = ?",
        (employee_id,),
    ).fetchone()
    upcoming = conn.execute(
        "SELECT start_date, end_date, type FROM time_off_upcoming WHERE employee_id = ? ORDER BY start_date",
        (employee_id,),
    ).fetchall()
    conn.close()
    if not balance:
        return json.dumps({"error": f"No time-off data found for {employee_id}."})
    return json.dumps({
        "pto_remaining_days": balance["pto_remaining_days"],
        "upcoming": [dict(r) for r in upcoming],
    })


def get_compensation(employee_id: str) -> str:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM compensation WHERE employee_id = ?",
        (employee_id,),
    ).fetchone()
    conn.close()
    if not row:
        return json.dumps({"error": f"No compensation data found for {employee_id}."})
    return json.dumps(dict(row))


def list_direct_reports(manager: str) -> str:
    conn = get_connection()
    # Try matching by ID first, then by name
    if manager.upper().startswith("M"):
        manager_row = conn.execute("SELECT id, name FROM managers WHERE id = ?", (manager.upper(),)).fetchone()
    else:
        manager_row = None
    if not manager_row:
        manager_row = conn.execute("SELECT id, name FROM managers WHERE LOWER(name) LIKE LOWER(?)", (f"%{manager}%",)).fetchone()
    if not manager_row:
        conn.close()
        return json.dumps({"error": f"No manager found matching '{manager}'."})
    rows = conn.execute(
        "SELECT id, name, title, department, location FROM employees WHERE manager_id = ?",
        (manager_row["id"],),
    ).fetchall()
    conn.close()
    return json.dumps({
        "manager": dict(manager_row),
        "direct_reports": [dict(r) for r in rows],
    })


# Dispatch map
TOOL_HANDLERS = {
    "lookup_employee": lambda args: lookup_employee(args["name"]),
    "get_performance_reviews": lambda args: get_performance_reviews(args["employee_id"]),
    "get_goals": lambda args: get_goals(args["employee_id"]),
    "get_time_off": lambda args: get_time_off(args["employee_id"]),
    "get_compensation": lambda args: get_compensation(args["employee_id"]),
    "list_direct_reports": lambda args: list_direct_reports(args["manager"]),
}
