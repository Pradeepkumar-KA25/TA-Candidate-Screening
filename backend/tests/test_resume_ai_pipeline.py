from app.core.config import settings
from app.services import resume_ai_pipeline


def test_pipeline_uses_ollama_result(monkeypatch, tmp_path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"resume")
    deterministic = {
        "contact": {"name": "Regex Name"},
        "experience": [],
        "projects": [],
    }
    ai_result = {
        "contact": {"name": "AI Name", "email": "ai@example.com"},
        "experience": [{"title": "Engineer", "company": "Acme", "responsibilities": ["Built APIs"]}],
        "projects": [{"name": "Portal", "technologies": ["Python"]}],
    }
    monkeypatch.setattr(resume_ai_pipeline, "extract_text", lambda *_args: "AI Name\nai@example.com")
    monkeypatch.setattr(resume_ai_pipeline, "parse_resume", lambda *_args: deterministic)
    monkeypatch.setattr(resume_ai_pipeline, "split_sections", lambda *_args: {"experience": []})
    monkeypatch.setattr(
        resume_ai_pipeline,
        "parse_resume_with_ollama",
        lambda *_args, **_kwargs: (ai_result, "llama3.1"),
    )

    result, used = resume_ai_pipeline.parse_resume_with_fallback(str(resume_path), "pdf", "auto")

    assert used == "ollama:llama3.1"
    assert result["experience"][0]["company"] == "Acme"
    assert result["projects"][0]["name"] == "Portal"


def test_pipeline_falls_back_when_ollama_fails(monkeypatch, tmp_path) -> None:
    resume_path = tmp_path / "resume.docx"
    resume_path.write_bytes(b"resume")
    deterministic = {
        "contact": {"name": "Regex Name", "email": "regex@example.com"},
        "experience": [{"title": "Developer", "company": "Fallback Inc"}],
    }
    monkeypatch.setattr(resume_ai_pipeline, "extract_text", lambda *_args: "Regex Name\nregex@example.com")
    monkeypatch.setattr(resume_ai_pipeline, "parse_resume", lambda *_args: deterministic)
    monkeypatch.setattr(resume_ai_pipeline, "split_sections", lambda *_args: {"experience": []})
    monkeypatch.setattr(
        resume_ai_pipeline,
        "parse_resume_with_ollama",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("offline")),
    )

    result, used = resume_ai_pipeline.parse_resume_with_fallback(str(resume_path), "docx", "auto")

    assert used == "deterministic"
    assert result["experience"][0]["company"] == "Fallback Inc"


def test_pipeline_stages_long_experience_sections(monkeypatch, tmp_path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"resume")
    deterministic = {"contact": {"name": "Asha"}, "experience": [], "projects": []}
    monkeypatch.setattr(settings, "ollama_staged_line_threshold", 2)
    monkeypatch.setattr(resume_ai_pipeline, "extract_text", lambda *_args: "long resume")
    monkeypatch.setattr(resume_ai_pipeline, "parse_resume", lambda *_args: deterministic)
    monkeypatch.setattr(resume_ai_pipeline, "split_sections", lambda *_args: {"experience": ["a", "b"]})
    monkeypatch.setattr(
        resume_ai_pipeline,
        "parse_experience_chunks_with_ollama",
        lambda *_args, **_kwargs: (
            {
                "experience": [{"title": "Engineer", "company": "Acme"}],
                "projects": [{"name": "Portal"}],
            },
            "llama3.1",
        ),
    )

    result, used = resume_ai_pipeline.parse_resume_with_fallback(str(resume_path), "pdf", "auto")

    assert used == "ollama:llama3.1+deterministic"
    assert result["experience"][0]["company"] == "Acme"
    assert result["projects"][0]["name"] == "Portal"


def test_staged_pipeline_keeps_higher_quality_deterministic_experience(monkeypatch, tmp_path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"resume")
    deterministic = {
        "contact": {"name": "Asha"},
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Acme Technologies",
                "dates": "2020 - Present",
                "responsibilities": ["Built APIs", "Led delivery"],
            }
        ],
        "projects": [],
    }
    monkeypatch.setattr(settings, "ollama_staged_line_threshold", 1)
    monkeypatch.setattr(resume_ai_pipeline, "extract_text", lambda *_args: "long resume")
    monkeypatch.setattr(resume_ai_pipeline, "parse_resume", lambda *_args: deterministic)
    monkeypatch.setattr(resume_ai_pipeline, "split_sections", lambda *_args: {"experience": ["line"]})
    monkeypatch.setattr(
        resume_ai_pipeline,
        "parse_experience_chunks_with_ollama",
        lambda *_args, **_kwargs: (
            {"experience": [{"title": "Engineer", "company": ""}], "projects": [{"name": "Portal"}]},
            "llama3.1",
        ),
    )

    result, _ = resume_ai_pipeline.parse_resume_with_fallback(str(resume_path), "pdf", "auto")

    assert result["experience"][0]["title"] == "Senior Engineer"
    assert result["projects"][0]["name"] == "Portal"


def test_experience_merge_preserves_unmatched_deterministic_jobs() -> None:
    deterministic = [
        {"title": "Engineer", "company": "Acme", "dates": "2020-2022"},
        {"title": "Analyst", "company": "Contoso", "dates": "2018-2020"},
    ]
    ai = [
        {
            "title": "Senior Engineer",
            "company": "Acme Technologies",
            "dates": "2020-2022",
            "responsibilities": ["Built APIs"],
        }
    ]

    merged = resume_ai_pipeline._merge_experience_sections(deterministic, ai)

    assert len(merged) == 2
    assert merged[0]["title"] == "Senior Engineer"
    assert merged[1]["company"] == "Contoso"