"""seed sample candidates for local testing

Revision ID: 202608110001
Revises: 202608070002
Create Date: 2026-08-11 00:01:00.000000
"""

from __future__ import annotations

from uuid import uuid5, NAMESPACE_DNS

from alembic import op
import sqlalchemy as sa


revision = "202608110001"
down_revision = "202608070002"
branch_labels = None
depends_on = None


def _build_seed_rows() -> list[dict]:
    statuses = ["active", "open_to_opportunities", "active", "active", "open_to_opportunities"]
    locations = ["Bengaluru", "Chennai", "Hyderabad", "Pune", "Mumbai"]
    skills_matrix = [
        ["Python", "FastAPI", "PostgreSQL"],
        ["Java", "Spring Boot", "MySQL"],
        ["Angular", "TypeScript", "RxJS"],
        ["Node.js", "Express", "MongoDB"],
        ["AWS", "Terraform", "Docker"],
    ]

    rows: list[dict] = []
    for index in range(1, 21):
        seed_uuid = uuid5(NAMESPACE_DNS, f"sample-candidate-{index}")
        status = statuses[(index - 1) % len(statuses)]
        location = locations[(index - 1) % len(locations)]
        skills = skills_matrix[(index - 1) % len(skills_matrix)]

        rows.append(
            {
                "id": seed_uuid,
                "zoho_record_id": f"sample_zoho_record_{index:03d}",
                "zoho_candidate_id": f"sample_zoho_candidate_{index:03d}",
                "full_name": f"Sample Candidate {index:02d}",
                "email": f"sample.candidate{index:02d}@example.com",
                "phone": f"900000{index:04d}",
                "total_experience_years": float(2 + (index % 8)),
                "relevant_experience_years": float(1 + (index % 6)),
                "current_company": f"Sample Company {(index % 7) + 1}",
                "current_location": location,
                "preferred_location": location,
                "notice_period_days": [15, 30, 45, 60][index % 4],
                "skills": skills,
                "degree": ["B.E", "B.Tech", "MCA", "M.Tech", "B.Sc"][(index - 1) % 5],
                "normalized_degree": ["be", "btech", "mca", "mtech", "bsc"][(index - 1) % 5],
                "current_ctc": float(5 + (index % 10)),
                "expected_ctc": float(6 + (index % 12)),
                "status": status,
                "source": "local_seed",
                "match_metadata": {"seed": True, "batch": "local_test"},
                "raw_payload": {"seed": True, "record_index": index},
            }
        )

    return rows


def upgrade() -> None:
    # Sample records were useful during initial UI development but must never be installed in an application database.
    return

    candidates = sa.table(
        "candidates",
        sa.column("id", sa.Uuid()),
        sa.column("zoho_record_id", sa.String(length=128)),
        sa.column("zoho_candidate_id", sa.String(length=128)),
        sa.column("full_name", sa.String(length=255)),
        sa.column("email", sa.String(length=255)),
        sa.column("phone", sa.String(length=64)),
        sa.column("total_experience_years", sa.Float()),
        sa.column("relevant_experience_years", sa.Float()),
        sa.column("current_company", sa.String(length=255)),
        sa.column("current_location", sa.String(length=255)),
        sa.column("preferred_location", sa.String(length=255)),
        sa.column("notice_period_days", sa.Integer()),
        sa.column("skills", sa.JSON()),
        sa.column("degree", sa.String(length=255)),
        sa.column("normalized_degree", sa.String(length=255)),
        sa.column("current_ctc", sa.Float()),
        sa.column("expected_ctc", sa.Float()),
        sa.column("status", sa.String(length=255)),
        sa.column("source", sa.String(length=64)),
        sa.column("match_metadata", sa.JSON()),
        sa.column("raw_payload", sa.JSON()),
    )

    op.bulk_insert(candidates, _build_seed_rows())


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM candidates WHERE zoho_record_id LIKE :prefix"),
        {"prefix": "sample_zoho_record_%"},
    )
