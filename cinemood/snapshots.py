"""Private content-addressed JSON snapshots; keys can become S3 object keys in T6."""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Protocol


class SnapshotStore(Protocol):
    def put(self, snapshot: dict[str, Any]) -> str: ...


class LocalSnapshotStore:
    def __init__(self, root: Path):
        self.root = root

    def put(self, snapshot: dict[str, Any]) -> str:
        data = json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode()
        key = "tmdb/v1/" + hashlib.sha256(data).hexdigest() + ".json"
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temporary = tempfile.mkstemp(dir=destination.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return key
