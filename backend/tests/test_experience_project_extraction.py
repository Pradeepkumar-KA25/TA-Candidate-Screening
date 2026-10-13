from app.services.multi_line_experience_parser import (
    parse_experience_multiline,
    parse_projects_multiline,
)
from app.services.resume_ai_pipeline import _merge_experience_sections


def test_multiline_experience_keeps_bulleted_responsibilities_in_one_job() -> None:
    lines = [
        "Wipro Limited",
        "Senior Project Engineer | May 2021 - February 2026",
        "\uf0b7",
        "Coordinated service operations for a production support environment.",
        "\uf0b7",
        "Managed monthly shift rosters for the support team.",
        "Project Engineer | March 2017 - April 2021",
        "\uf0b7",
        "Monitored production incidents and coordinated with technical teams.",
    ]

    experiences = parse_experience_multiline(lines)

    assert [(item["company"], item["title"]) for item in experiences] == [
        ("Wipro Limited", "Senior Project Engineer"),
        ("Wipro Limited", "Project Engineer"),
    ]
    assert len(experiences[0]["responsibilities"]) == 2


def test_inline_experience_rows_keep_each_job() -> None:
    lines = [
        "Full Stack Developer (Trainee Associate) Jan 2026 - Present | Kanini Software Solutions Pvt. Ltd. | Bengaluru, India",
        "\u2022",
        "Built Java RESTful endpoints.",
        "Full Stack Development Intern Jul 2025 - Dec 2025 | Kanini Software Solutions Pvt. Ltd. | Bengaluru, India",
        "\u2022",
        "Developed ASP.NET Core APIs.",
    ]

    experiences = parse_experience_multiline(lines)

    assert len(experiences) == 2
    assert [item["title"] for item in experiences] == [
        "Full Stack Developer (Trainee Associate)",
        "Full Stack Development Intern",
    ]
    assert all(item["company"] == "Kanini Software Solutions Pvt. Ltd." for item in experiences)


def test_pipe_separated_project_titles_are_not_dropped_or_named_as_bullets() -> None:
    lines = [
        "ATM Simulation System Angular 17 | ASP.NET Core | SQL Server | JWT | GitHub",
        "\u2022",
        "Devised comprehensive banking operations.",
        "\u2022",
        "Food Recipe & Meal Planner React | ASP.NET Core | SQL Server | JWT | GitHub",
        "\u2022",
        "Built personalized nutrition tracking.",
        "Real-Time Audit Compliance Platform React 18 | Type Script | Spring Boot | PostgreSQL",
        "\u2022",
        "Implemented compliance workflows.",
    ]

    projects = parse_projects_multiline(lines)

    assert [project["name"] for project in projects] == [
        "ATM Simulation System Angular 17",
        "Food Recipe & Meal Planner React",
        "Real-Time Audit Compliance Platform React 18",
    ]
    assert all(project["name"] != "\u2022" for project in projects)


def test_ai_experience_merge_preserves_deterministic_nested_projects() -> None:
    deterministic = [
        {
            "company": "Acme",
            "title": "Engineer",
            "dates": "2020 - Present",
            "projects": [{"name": "Billing Platform", "description": "Existing details"}],
        }
    ]
    ai = [
        {
            "company": "Acme",
            "title": "Engineer",
            "dates": "2020 - Present",
            "projects": [{"name": "Recruitment Portal", "description": "AI details"}],
        }
    ]

    merged = _merge_experience_sections(deterministic, ai)

    assert [project["name"] for project in merged[0]["projects"]] == [
        "Billing Platform",
        "Recruitment Portal",
    ]
