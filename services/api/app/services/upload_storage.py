from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


class UploadStorageError(Exception):
    pass


@dataclass(frozen=True)
class StoredUploadObject:
    storage_key: str
    content_type: str
    byte_size: int
    checksum_sha256: str
    local_path: Path


class LocalUploadStorage:
    def __init__(self, root: str | Path):
        self._root = Path(root)

    def save(self, storage_key: str, content_type: str, data: bytes) -> StoredUploadObject:
        target_path = self._path_for(storage_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        return StoredUploadObject(
            storage_key=storage_key,
            content_type=content_type,
            byte_size=len(data),
            checksum_sha256=hashlib.sha256(data).hexdigest(),
            local_path=target_path,
        )

    def exists(self, storage_key: str) -> bool:
        return self._path_for(storage_key).is_file()

    def read(self, storage_key: str) -> bytes:
        return self._path_for(storage_key).read_bytes()

    def _path_for(self, storage_key: str) -> Path:
        candidate = Path(storage_key)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise UploadStorageError("Invalid storage key.")
        return self._root / candidate
