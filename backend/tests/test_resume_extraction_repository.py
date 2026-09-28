from app.repositories.kanini_resume_repository import KaniniResumeRepository


def test_resume_extraction_status_lifecycle(sqlite_session, user_factory) -> None:
    user = user_factory()
    repository = KaniniResumeRepository(sqlite_session)
    resume = repository.create(
        user_id=user.id,
        filename="resume.pdf",
        parsed_data={"contact": {"name": "Asha"}},
        extraction_status="pending",
        extraction_progress=10,
        extraction_model="ollama:llama3.1",
        source_reference="resume-jobs/source.pdf",
        source_file_type="pdf",
    )

    updated = repository.update_extraction(
        resume.id,
        status="completed",
        progress=100,
        parsed_data={"contact": {"name": "Asha"}, "projects": [{"name": "Portal"}]},
        model="ollama:llama3.1+deterministic",
    )

    assert updated is not None
    assert updated.extraction_status == "completed"
    assert updated.extraction_progress == 100
    assert updated.parsed_data["projects"][0]["name"] == "Portal"