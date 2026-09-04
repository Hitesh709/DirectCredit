"""Secure file-storage boundary.
Application code stores metadata in DocumentRecord and addresses files by an opaque
storage key. Production should provide an object-storage adapter; local storage is
explicitly development-only and never logs document contents or credentials.
"""
import os, secrets
from pathlib import Path

class StorageBackend:
    name = "abstract"
    def put(self, content: bytes, *, extension: str = "bin") -> str:
        raise NotImplementedError
    def get(self, key: str) -> bytes:
        raise NotImplementedError

class LocalStorage(StorageBackend):
    name = "local"
    def __init__(self, root=None):
        self.root = Path(root or os.getenv("LOCAL_STORAGE_ROOT", "./storage")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
    def put(self, content: bytes, *, extension: str = "bin") -> str:
        key = f"{secrets.token_urlsafe(24)}.{extension.lstrip('.')[:10]}"
        (self.root / key).write_bytes(content)
        return key
    def get(self, key: str) -> bytes:
        path = (self.root / Path(key).name).resolve()
        if path.parent != self.root: raise ValueError("Invalid storage key")
        return path.read_bytes()

def storage_status() -> dict:
    provider = os.getenv("FILE_STORAGE_PROVIDER", "local")
    return {"provider": provider, "configured": provider != "local" or bool(os.getenv("LOCAL_STORAGE_ROOT")),
            "production_required": provider not in {"local", ""}}
