from abc import ABC, abstractmethod
from typing import Any, Dict, List


class StoragePort(ABC):
    @abstractmethod
    def put_text(self, path: str, data: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_text(self, path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def put_json(self, path: str, obj: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_json(self, path: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list(self, prefix: str) -> List[str]:
        raise NotImplementedError
