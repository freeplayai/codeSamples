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

    c.executescript(
        """
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
    """
    )

    # --- Seed data ---

    c.executemany(
        "INSERT INTO managers VALUES (?, ?, ?)",
        [
            ("M001", "Frank Lee", "Engineering"),
            ("M002", "Grace Patel", "Design"),
            ("M003", "Morgan Cox", "Engineering"),
            ("M004", "Jeremy Silva", "Product"),
        ],
    )

    c.executemany(
        "INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                "E001",
                "Alice Johnson",
                "Senior Software Engineer",
                "Engineering",
                "M001",
                "2021-03-15",
                "Austin, TX",
                "L5",
                "alice.johnson@company.com",
            ),
            (
                "E002",
                "Bob Martinez",
                "Product Designer",
                "Design",
                "M002",
                "2022-07-01",
                "Remote",
                "L4",
                "bob.martinez@company.com",
            ),
            (
                "E003",
                "Carol Chen",
                "Data Analyst",
                "Engineering",
                "M001",
                "2023-01-10",
                "Austin, TX",
                "L3",
                "carol.chen@company.com",
            ),
            (
                "E004",
                "David Kim",
                "Backend Engineer",
                "Engineering",
                "M001",
                "2020-09-20",
                "New York, NY",
                "L4",
                "david.kim@company.com",
            ),
            (
                "E005",
                "Eva Rossi",
                "UX Researcher",
                "Design",
                "M002",
                "2024-02-12",
                "Remote",
                "L3",
                "eva.rossi@company.com",
            ),
            (
                "E006",
                "Felix Chen",
                "Frontend Engineer",
                "Engineering",
                "M003",
                "2025-01-01",
                "Austin, TX",
                "L4",
                "felix.chen@company.com",
            ),
            (
                "E007",
                "Grace W.",
                "Data Scientist",
                "Engineering",
                "M003",
                "2026-01-01",
                "Remote",
                "L4",
                "grace.w@company.com",
            ),
            (
                "E008",
                "Henry Z.",
                "Backend Engineer",
                "Engineering",
                "M003",
                "2026-01-01",
                "Remote",
                "L4",
                "henry.z@company.com",
            ),
            (
                "E009",
                "Ivy L.",
                "UX Designer",
                "Design",
                "M003",
                "2026-01-01",
                "Remote",
                "L3",
                "ivy.l@company.com",
            ),
            (
                "E010",
                "Jack Q.",
                "Product Manager",
                "Product",
                "M004",
                "2026-01-01",
                "Remote",
                "L4",
                "jack.q@company.com",
            ),
        ],
    )

    c.executemany(
        "INSERT INTO performance_reviews (employee_id, period, rating, summary, areas_for_growth) VALUES (?, ?, ?, ?, ?)",
        [
            (
                "E001",
                "2024-H2",
                "Exceeds Expectations",
                "Alice consistently delivers high-quality work ahead of schedule. Led the migration to the new API framework. Strong mentorship of junior engineers.",
                "Could improve cross-team communication and stakeholder management.",
            ),
            (
                "E001",
                "2024-H1",
                "Meets Expectations",
                "Solid contributions to the payments service. Good code review practices.",
                "Take on more visible leadership opportunities.",
            ),
            (
                "E002",
                "2024-H2",
                "Meets Expectations",
                "Bob delivered strong design work for the onboarding redesign. Good collaboration with engineering.",
                "Work on presenting design rationale to non-design stakeholders.",
            ),
            (
                "E003",
                "2024-H2",
                "Meets Expectations",
                "Carol built reliable dashboards for the ops team. Growing SQL and Python skills.",
                "Develop more independence in scoping analytical projects.",
            ),
            (
                "E004",
                "2024-H2",
                "Below Expectations",
                "David struggled with deadlines on the inventory service project. Code quality has dipped, with several production incidents traced to his changes.",
                "Needs to improve testing practices, time management, and proactive communication when blocked.",
            ),
            (
                "E004",
                "2024-H1",
                "Meets Expectations",
                "Solid half. Contributed to the search service rewrite.",
                "Could take more ownership of project planning.",
            ),
            (
                "E005",
                "2024-H2",
                "Exceeds Expectations",
                "Eva ramped up quickly and ran 3 research studies that directly influenced product decisions. Great synthesis and presentation skills.",
                "Still new — build deeper relationships across the org.",
            ),
            (
                "E006",
                "2025-H2",
                "Meets Expectations",
                "Felix delivered key frontend components for the customer dashboard redesign. Good eye for detail and consistent velocity.",
                "Needs to improve automated test coverage and take more initiative in architectural discussions.",
            ),
            (
                "E006",
                "2025-H1",
                "Meets Expectations",
                "Solid onboarding period. Quickly became productive on the design-system migration.",
                "Build deeper understanding of backend APIs to improve full-stack collaboration.",
            ),
            (
                "E007",
                "2026-H1",
                "Meets Expectations",
                "Grace is ramping up well. Built an initial churn-prediction prototype and started collaborating with the product team on experiment design.",
                "Still early — needs to establish a repeatable workflow for model validation and stakeholder communication.",
            ),
            (
                "E008",
                "2026-H1",
                "Meets Expectations",
                "Henry onboarded smoothly and has taken ownership of the notifications microservice. Good code quality so far.",
                "Needs to ramp on incident response processes and improve documentation habits.",
            ),
            (
                "E009",
                "2026-H1",
                "Meets Expectations",
                "Ivy completed an audit of the current design system and proposed accessibility improvements. Strong attention to interaction details.",
                "Should work on speed of iteration and balancing polish with delivery timelines.",
            ),
            (
                "E010",
                "2026-H1",
                "Meets Expectations",
                "Jack led discovery for two new feature areas and produced solid PRDs. Good stakeholder management instincts.",
                "Needs to sharpen prioritization frameworks and develop stronger data-informed decision-making.",
            ),
        ],
    )

    c.executemany(
        "INSERT INTO goals (employee_id, goal, status, progress) VALUES (?, ?, ?, ?)",
        [
            (
                "E001",
                "Lead the API v3 migration to completion by Q1 2026",
                "On Track",
                "75%",
            ),
            (
                "E001",
                "Mentor 2 junior engineers through their first project",
                "Complete",
                "100%",
            ),
            ("E001", "Reduce p95 latency on payments service by 30%", "At Risk", "40%"),
            ("E002", "Deliver design system component library v2", "On Track", "60%"),
            ("E002", "Run 2 usability studies per quarter", "On Track", "50%"),
            (
                "E003",
                "Build self-serve analytics dashboard for ops team",
                "Complete",
                "100%",
            ),
            ("E003", "Complete Python data engineering course", "On Track", "80%"),
            ("E004", "Ship inventory service v2", "At Risk", "30%"),
            ("E004", "Reduce on-call incidents by 50%", "Off Track", "10%"),
            (
                "E004",
                "Write architecture doc for event-driven refactor",
                "Not Started",
                "0%",
            ),
            ("E005", "Establish research repository and templates", "On Track", "70%"),
            (
                "E005",
                "Complete 6 user research studies in first year",
                "On Track",
                "50%",
            ),
            ("E006", "Ship customer dashboard v2 frontend", "On Track", "65%"),
            ("E006", "Increase frontend unit test coverage to 80%", "At Risk", "35%"),
            ("E006", "Contribute to design-system component library", "On Track", "50%"),
            ("E007", "Deliver churn-prediction model to production", "On Track", "30%"),
            ("E007", "Build A/B testing analysis pipeline", "Not Started", "0%"),
            ("E007", "Complete internal ML platform onboarding", "On Track", "60%"),
            ("E008", "Ship notifications service v2 with push support", "On Track", "45%"),
            ("E008", "Reduce notifications service p99 latency by 25%", "On Track", "20%"),
            ("E008", "Write runbooks for all owned services", "At Risk", "15%"),
            ("E009", "Complete accessibility audit and remediation plan", "On Track", "70%"),
            ("E009", "Redesign settings and preferences flows", "On Track", "40%"),
            ("E009", "Run 3 usability studies on core workflows", "On Track", "33%"),
            ("E010", "Launch feature-X discovery and PRD", "Complete", "100%"),
            ("E010", "Define Q2 product roadmap with engineering alignment", "On Track", "50%"),
            ("E010", "Establish product metrics dashboard for owned area", "Not Started", "0%"),
        ],
    )

    c.executemany(
        "INSERT INTO time_off VALUES (?, ?)",
        [
            ("E001", 12),
            ("E002", 8),
            ("E003", 15),
            ("E004", 3),
            ("E005", 18),
            ("E006", 10),
            ("E007", 20),
            ("E008", 20),
            ("E009", 20),
            ("E010", 20),
        ],
    )

    c.executemany(
        "INSERT INTO time_off_upcoming (employee_id, start_date, end_date, type) VALUES (?, ?, ?, ?)",
        [
            ("E001", "2026-03-20", "2026-03-24", "Vacation"),
            ("E003", "2026-04-01", "2026-04-05", "Vacation"),
            ("E005", "2026-03-10", "2026-03-11", "Personal"),
            ("E007", "2026-04-14", "2026-04-18", "Vacation"),
            ("E009", "2026-03-28", "2026-03-28", "Personal"),
        ],
    )

    c.executemany(
        "INSERT INTO compensation VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("E001", "L5", "$140k-$180k", "$165k", "2025-03-01", "2026-06-15"),
            ("E002", "L4", "$110k-$145k", "$125k", "2025-03-01", "2026-09-01"),
            ("E003", "L3", "$85k-$115k", "$95k", "2025-03-01", "N/A"),
            ("E004", "L4", "$110k-$145k", "$118k", "2024-03-01", "2026-04-01"),
            ("E005", "L3", "$85k-$115k", "$92k", "2025-03-01", "N/A"),
            ("E006", "L4", "$110k-$145k", "$120k", "2025-03-01", "2026-09-01"),
            ("E007", "L4", "$110k-$145k", "$115k", "2026-03-01", "N/A"),
            ("E008", "L4", "$110k-$145k", "$115k", "2026-03-01", "N/A"),
            ("E009", "L3", "$85k-$115k", "$90k", "2026-03-01", "N/A"),
            ("E010", "L4", "$110k-$145k", "$130k", "2026-03-01", "2027-01-01"),
        ],
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database created at {DB_PATH}")
