from abc import ABC, abstractmethod


class ASRPort(ABC):
    @abstractmethod
    def listen_and_transcribe(self) -> str:
        raise NotImplementedError
