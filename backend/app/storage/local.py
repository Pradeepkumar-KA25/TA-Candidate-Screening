from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: str) -> None:
        configured_root = Path(root)
        self.root = configured_root if configured_root.is_absolute() else Path.cwd() / configured_root

    def _path(self, reference: str) -> Path:
        return self.root / self.normalize_key(reference)

    def write_bytes(self, key: str, content: bytes) -> str:
        normalized_key = self.normalize_key(key)
        path = self._path(normalized_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return normalized_key

    def read_bytes(self, reference: str) -> bytes:
        return self._path(reference).read_bytes()

    def exists(self, reference: str) -> bool:
        return self._path(reference).is_file()

    def delete_prefix(self, prefix: str) -> None:
        path = self._path(prefix)
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    @contextmanager
    def materialize(self, reference: str) -> Iterator[Path]:
        yield self._path(reference)