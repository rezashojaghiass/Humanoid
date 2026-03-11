from abc import ABC, abstractmethod
from typing import Any, Dict


class GesturePort(ABC):
    @abstractmethod
    def start_gesture(self, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop_gesture(self, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_command(self, name: str, params: Dict[str, Any]) -> None:
        raise NotImplementedError
