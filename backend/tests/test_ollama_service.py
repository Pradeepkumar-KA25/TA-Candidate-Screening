import json

import pytest

from app.core.config import settings
from app.services import ollama_service


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_parse_resume_calls_selected_ollama_model(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_base_url", "http://ollama.test")
    monkeypatch.setattr(settings, "ollama_model", "llama3.1")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(
            {
                "response": json.dumps(
                    {
                        "contact": {"name": "Asha Sharma", "email": "asha@example.com"},
                        "experience": [{"title": "Engineer", "company": "Acme", "responsibilities": []}],
                        "projects": [{"name": "Portal", "description": "Built a portal", "technologies": ["Python"]}],
                    }
                )
            }
        )

    monkeypatch.setattr(ollama_service.urllib.request, "urlopen", fake_urlopen)

    result, model = ollama_service.parse_resume_with_ollama("Asha Sharma\nasha@example.com", "ollama:qwen3:14b")

    assert model == "qwen3:14b"
    assert captured["payload"]["model"] == "qwen3:14b"
    assert captured["payload"]["format"] == "json"
    assert captured["payload"]["options"] == {
        "temperature": 0,
        "num_predict": settings.ollama_num_predict,
    }
    assert result["experience"][0]["company"] == "Acme"
    assert result["projects"][0]["name"] == "Portal"


def test_parse_resume_rejects_invalid_ollama_json(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_base_url", "http://ollama.test")
    monkeypatch.setattr(settings, "ollama_model", "llama3.1")
    monkeypatch.setattr(
        ollama_service.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _Response({"response": "not-json"}),
    )

    with pytest.raises(ollama_service.OllamaResponseError):
        ollama_service.parse_resume_with_ollama("resume")


def test_model_options_come_from_settings(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_base_url", "http://ollama.test")
    monkeypatch.setattr(settings, "ollama_model", "llama3.1")
    monkeypatch.setattr(settings, "ollama_models", "llama3.1,qwen3:14b")

    assert [option["value"] for option in ollama_service.get_model_options()] == [
        "auto",
        "ollama:llama3.1",
        "ollama:qwen3:14b",
    ]


def test_generate_json_normalizes_timeout_cleanup_interrupt(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_base_url", "http://ollama.test")
    monkeypatch.setattr(settings, "ollama_model", "llama3.1")
    monkeypatch.setattr(
        ollama_service.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(ollama_service.OllamaUnavailableError):
        ollama_service.generate_json("prompt")