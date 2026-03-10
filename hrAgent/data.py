"""Mock HR dataset stored in SQLite."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "hr.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed mock data. Idempotent — drops and recreates."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS time_off_upcoming;
        DROP TABLE IF EXISTS time_off;
        DROP TABLE IF EXISTS compensation;
        DROP TABLE IF EXISTS goals;
        DROP TABLE IF EXISTS performance_reviews;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS managers;

        CREATE TABLE managers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL
        );

        CREATE TABLE employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            manager_id TEXT NOT NULL REFERENCES managers(id),
            start_date TEXT NOT NULL,
            location TEXT NOT NULL,
            salary_band TEXT NOT NULL,
            email TEXT NOT NULL
        );

        CREATE TABLE performance_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL REFERENCES employees(id),
            period TEXT NOT NULL,
            rating TEXT NOT NULL,
            summary TEXT NOT NULL,
            areas_for_growth TEXT NOT NULL
        );

        CREATE TABLE goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL REFERENCES employees(id),
            goal TEXT NOT NULL,
            status TEXT NOT NULL,
            progress TEXT NOT NULL
        );

        CREATE TABLE time_off (
            employee_id TEXT PRIMARY KEY REFERENCES employees(id),
            pto_remaining_days INTEGER NOT NULL
        );

        CREATE TABLE time_off_upcoming (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL REFERENCES employees(id),
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            type TEXT NOT NULL
        );

        CREATE TABLE compensation (
            employee_id TEXT PRIMARY KEY REFERENCES employees(id),
            band TEXT NOT NULL,
            band_range TEXT NOT NULL,
            current_salary TEXT NOT NULL,
            last_adjustment TEXT NOT NULL,
            equity_vesting_next TEXT NOT NULL
        );
    """)

    # --- Seed data ---

    c.executemany("INSERT INTO managers VALUES (?, ?, ?)", [
        ("M001", "Frank Lee", "Engineering"),
        ("M002", "Grace Patel", "Design"),
    ])

    c.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        ("E001", "Alice Johnson", "Senior Software Engineer", "Engineering", "M001", "2021-03-15", "Austin, TX", "L5", "alice.johnson@company.com"),
        ("E002", "Bob Martinez", "Product Designer", "Design", "M002", "2022-07-01", "Remote", "L4", "bob.martinez@company.com"),
        ("E003", "Carol Chen", "Data Analyst", "Engineering", "M001", "2023-01-10", "Austin, TX", "L3", "carol.chen@company.com"),
        ("E004", "David Kim", "Backend Engineer", "Engineering", "M001", "2020-09-20", "New York, NY", "L4", "david.kim@company.com"),
        ("E005", "Eva Rossi", "UX Researcher", "Design", "M002", "2024-02-12", "Remote", "L3", "eva.rossi@company.com"),
    ])

    c.executemany("INSERT INTO performance_reviews (employee_id, period, rating, summary, areas_for_growth) VALUES (?, ?, ?, ?, ?)", [
        ("E001", "2024-H2", "Exceeds Expectations", "Alice consistently delivers high-quality work ahead of schedule. Led the migration to the new API framework. Strong mentorship of junior engineers.", "Could improve cross-team communication and stakeholder management."),
        ("E001", "2024-H1", "Meets Expectations", "Solid contributions to the payments service. Good code review practices.", "Take on more visible leadership opportunities."),
        ("E002", "2024-H2", "Meets Expectations", "Bob delivered strong design work for the onboarding redesign. Good collaboration with engineering.", "Work on presenting design rationale to non-design stakeholders."),
        ("E003", "2024-H2", "Meets Expectations", "Carol built reliable dashboards for the ops team. Growing SQL and Python skills.", "Develop more independence in scoping analytical projects."),
        ("E004", "2024-H2", "Below Expectations", "David struggled with deadlines on the inventory service project. Code quality has dipped, with several production incidents traced to his changes.", "Needs to improve testing practices, time management, and proactive communication when blocked."),
        ("E004", "2024-H1", "Meets Expectations", "Solid half. Contributed to the search service rewrite.", "Could take more ownership of project planning."),
        ("E005", "2024-H2", "Exceeds Expectations", "Eva ramped up quickly and ran 3 research studies that directly influenced product decisions. Great synthesis and presentation skills.", "Still new — build deeper relationships across the org."),
    ])

    c.executemany("INSERT INTO goals (employee_id, goal, status, progress) VALUES (?, ?, ?, ?)", [
        ("E001", "Lead the API v3 migration to completion by Q1 2026", "On Track", "75%"),
        ("E001", "Mentor 2 junior engineers through their first project", "Complete", "100%"),
        ("E001", "Reduce p95 latency on payments service by 30%", "At Risk", "40%"),
        ("E002", "Deliver design system component library v2", "On Track", "60%"),
        ("E002", "Run 2 usability studies per quarter", "On Track", "50%"),
        ("E003", "Build self-serve analytics dashboard for ops team", "Complete", "100%"),
        ("E003", "Complete Python data engineering course", "On Track", "80%"),
        ("E004", "Ship inventory service v2", "At Risk", "30%"),
        ("E004", "Reduce on-call incidents by 50%", "Off Track", "10%"),
        ("E004", "Write architecture doc for event-driven refactor", "Not Started", "0%"),
        ("E005", "Establish research repository and templates", "On Track", "70%"),
        ("E005", "Complete 6 user research studies in first year", "On Track", "50%"),
    ])

    c.executemany("INSERT INTO time_off VALUES (?, ?)", [
        ("E001", 12), ("E002", 8), ("E003", 15), ("E004", 3), ("E005", 18),
    ])

    c.executemany("INSERT INTO time_off_upcoming (employee_id, start_date, end_date, type) VALUES (?, ?, ?, ?)", [
        ("E001", "2026-03-20", "2026-03-24", "Vacation"),
        ("E003", "2026-04-01", "2026-04-05", "Vacation"),
        ("E005", "2026-03-10", "2026-03-11", "Personal"),
    ])

    c.executemany("INSERT INTO compensation VALUES (?, ?, ?, ?, ?, ?)", [
        ("E001", "L5", "$140k-$180k", "$165k", "2025-03-01", "2026-06-15"),
        ("E002", "L4", "$110k-$145k", "$125k", "2025-03-01", "2026-09-01"),
        ("E003", "L3", "$85k-$115k", "$95k", "2025-03-01", "N/A"),
        ("E004", "L4", "$110k-$145k", "$118k", "2024-03-01", "2026-04-01"),
        ("E005", "L3", "$85k-$115k", "$92k", "2025-03-01", "N/A"),
    ])

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database created at {DB_PATH}")
