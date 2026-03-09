from abc import ABC, abstractmethod


class GesturePort(ABC):
    @abstractmethod
    def start_gesture(self, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop_gesture(self, name: str) -> None:
        raise NotImplementedError
