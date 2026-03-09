import json
from typing import Any, Dict, List

import boto3

from robot_sync_app.ports.storage_port import StoragePort


class S3StorageAdapter(StoragePort):
    def __init__(self, bucket: str, prefix: str = "") -> None:
        self._bucket = bucket
        self._prefix = prefix.strip("/")
        self._s3 = boto3.client("s3")

    def _key(self, path: str) -> str:
        if self._prefix:
            return f"{self._prefix}/{path}"
        return path

    def put_text(self, path: str, data: str) -> None:
        self._s3.put_object(Bucket=self._bucket, Key=self._key(path), Body=data.encode("utf-8"))

    def get_text(self, path: str) -> str:
        obj = self._s3.get_object(Bucket=self._bucket, Key=self._key(path))
        return obj["Body"].read().decode("utf-8")

    def put_json(self, path: str, obj: Dict[str, Any]) -> None:
        self.put_text(path, json.dumps(obj, indent=2))

    def get_json(self, path: str) -> Dict[str, Any]:
        return json.loads(self.get_text(path))

    def exists(self, path: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=self._key(path))
            return True
        except Exception:
            return False

    def list(self, prefix: str) -> List[str]:
        out: List[str] = []
        key_prefix = self._key(prefix)
        resp = self._s3.list_objects_v2(Bucket=self._bucket, Prefix=key_prefix)
        for item in resp.get("Contents", []):
            out.append(item["Key"])
        return out
