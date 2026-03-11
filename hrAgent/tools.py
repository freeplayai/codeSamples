"""Tool implementations for the HR agent.

Tool schemas (names, descriptions, parameters) are managed in the Freeplay UI
on the HR-Manager prompt template. This file only contains the runtime handlers.
"""

import json

from data import get_connection
from llm import call_and_record


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
    return json.dumps(
        {
            "pto_remaining_days": balance["pto_remaining_days"],
            "upcoming": [dict(r) for r in upcoming],
        }
    )


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
        manager_row = conn.execute(
            "SELECT id, name FROM managers WHERE id = ?", (manager.upper(),)
        ).fetchone()
    else:
        manager_row = None
    if not manager_row:
        manager_row = conn.execute(
            "SELECT id, name FROM managers WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{manager}%",),
        ).fetchone()
    if not manager_row:
        conn.close()
        return json.dumps({"error": f"No manager found matching '{manager}'."})
    rows = conn.execute(
        "SELECT id, name, title, department, location FROM employees WHERE manager_id = ?",
        (manager_row["id"],),
    ).fetchall()
    conn.close()
    return json.dumps(
        {
            "manager": dict(manager_row),
            "direct_reports": [dict(r) for r in rows],
        }
    )


REPORT_TEMPLATE_NAME = "HR-Report-Generator"

def make_report_tool(fp_client, project_id, environment, session_info):
    """Create a generate_report tool handler bound to the current session."""

    def generate_report(args: dict, context: dict) -> str:
        result = call_and_record(
            fp_client=fp_client,
            project_id=project_id,
            template_name=REPORT_TEMPLATE_NAME,
            environment=environment,
            variables={
                "report_type": args.get("report_type", "meeting_agenda"),
                "context": args.get("context", ""),
            },
            session_info=session_info,
            parent_id=context.get("parent_id"),
        )
        return result["llm_response"]

    return generate_report


# Dispatch map: every handler has signature (args: dict, context: dict) -> str
TOOL_HANDLERS = {
    "lookup_employee": lambda args, context: lookup_employee(args["name"]),
    "get_performance_reviews": lambda args, context: get_performance_reviews(
        args["employee_id"]
    ),
    "get_goals": lambda args, context: get_goals(args["employee_id"]),
    "get_time_off": lambda args, context: get_time_off(args["employee_id"]),
    "get_compensation": lambda args, context: get_compensation(args["employee_id"]),
    "list_direct_reports": lambda args, context: list_direct_reports(args["manager"]),
}
