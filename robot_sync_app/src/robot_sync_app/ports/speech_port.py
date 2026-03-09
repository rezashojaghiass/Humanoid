from abc import ABC, abstractmethod
from typing import Callable


class SpeechPort(ABC):
    @abstractmethod
    def speak(self, text: str, on_start: Callable[[], None], on_end: Callable[[], None]) -> None:
        raise NotImplementedError
