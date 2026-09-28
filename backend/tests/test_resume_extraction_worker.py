from uuid import uuid4

from app.background import resume_extraction
from app.repositories.kanini_resume_repository import KaniniResumeRepository
from app.storage.local import LocalStorageBackend


def test_worker_completes_job_and_cleans_source(sqlite_session, user_factory, monkeypatch, tmp_path) -> None:
    user = user_factory()
    storage = LocalStorageBackend(str(tmp_path))
    resume_id = uuid4()
    source_reference = storage.write_bytes(f"resume-jobs/{resume_id}/source.pdf", b"%PDF-test")
    repository = KaniniResumeRepository(sqlite_session)
    repository.create(
        id=resume_id,
        user_id=user.id,
        filename="resume.pdf",
        parsed_data={"contact": {"name": "Asha"}},
        extraction_status="pending",
        extraction_progress=5,
        extraction_model="ollama:llama3.1",
        source_reference=source_reference,
        source_file_type="pdf",
    )
    monkeypatch.setattr(resume_extraction, "get_session_factory", lambda: lambda: sqlite_session)
    monkeypatch.setattr(resume_extraction, "get_storage_backend", lambda: storage)
    monkeypatch.setattr(sqlite_session, "close", lambda: None)

    def fake_extract(_path, _type, _model, progress_callback):
        progress_callback(55)
        return (
            {
                "contact": {"name": "Asha"},
                "experience": [{"title": "Engineer", "company": "Acme"}],
                "projects": [{"name": "Portal"}, {"name": "Analytics"}],
            },
            "ollama:llama3.1+deterministic",
        )

    monkeypatch.setattr(resume_extraction, "parse_resume_completely", fake_extract)

    resume_extraction.process_resume_extraction_job(resume_id)

    completed = repository.get_job(resume_id)
    assert completed is not None
    assert completed.extraction_status == "completed"
    assert completed.extraction_progress == 100
    assert completed.extraction_model == "ollama:llama3.1+deterministic"
    assert len(completed.parsed_data["projects"]) == 2
    assert completed.source_reference is None
    assert not storage.exists(source_reference)