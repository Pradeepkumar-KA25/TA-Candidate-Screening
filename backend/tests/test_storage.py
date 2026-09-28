from pathlib import Path

import pytest

from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend


def test_local_storage_round_trip_and_delete(tmp_path: Path) -> None:
    storage = LocalStorageBackend(str(tmp_path))

    reference = storage.write_bytes("resumes/candidate-1/resume.pdf", b"%PDF-test")

    assert reference == "resumes/candidate-1/resume.pdf"
    assert storage.exists(reference)
    assert storage.read_bytes(reference) == b"%PDF-test"
    with storage.materialize(reference) as local_path:
        assert local_path.read_bytes() == b"%PDF-test"

    storage.delete_prefix("resumes/candidate-1")
    assert not storage.exists(reference)


def test_storage_rejects_parent_path_traversal() -> None:
    with pytest.raises(ValueError, match="Invalid storage key"):
        StorageBackend.normalize_key("../secret.txt")


def test_storage_accepts_legacy_upload_reference(tmp_path: Path) -> None:
    storage = LocalStorageBackend(str(tmp_path))
    storage.write_bytes("resumes/candidate-1/resume.pdf", b"resume")

    assert storage.read_bytes("uploads/resumes/candidate-1/resume.pdf") == b"resume"