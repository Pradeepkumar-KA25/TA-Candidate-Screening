from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Iterator


class StorageBackend(ABC):
    @staticmethod
    def normalize_key(reference: str) -> str:
        normalized = reference.replace("\\", "/").lstrip("/")
        if normalized.startswith("uploads/"):
            normalized = normalized.removeprefix("uploads/")

        path = PurePosixPath(normalized)
        if not normalized or ".." in path.parts:
            raise ValueError("Invalid storage key")
        return path.as_posix()

    @abstractmethod
    def write_bytes(self, key: str, content: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_bytes(self, reference: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def exists(self, reference: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_prefix(self, prefix: str) -> None:
        raise NotImplementedError

    @contextmanager
    def materialize(self, reference: str) -> Iterator[Path]:
        suffix = Path(reference).suffix
        with NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(self.read_bytes(reference))
        try:
            yield temporary_path
        finally:
            temporary_path.unlink(missing_ok=True)