import json
from pathlib import Path
from typing import Any, Dict, List

from robot_sync_app.ports.storage_port import StoragePort


class LocalStorageAdapter(StoragePort):
    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def _full(self, path: str) -> Path:
        out = self._base / path
        out.parent.mkdir(parents=True, exist_ok=True)
        return out

    def put_text(self, path: str, data: str) -> None:
        self._full(path).write_text(data, encoding="utf-8")

    def get_text(self, path: str) -> str:
        return self._full(path).read_text(encoding="utf-8")

    def put_json(self, path: str, obj: Dict[str, Any]) -> None:
        self._full(path).write_text(json.dumps(obj, indent=2), encoding="utf-8")

    def get_json(self, path: str) -> Dict[str, Any]:
        return json.loads(self._full(path).read_text(encoding="utf-8"))

    def exists(self, path: str) -> bool:
        return self._full(path).exists()

    def list(self, prefix: str) -> List[str]:
        root = self._base / prefix
        if not root.exists():
            return []
        return [str(p.relative_to(self._base)) for p in root.rglob("*") if p.is_file()]
