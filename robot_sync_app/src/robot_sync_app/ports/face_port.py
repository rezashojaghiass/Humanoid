from abc import ABC, abstractmethod


class FacePort(ABC):
    @abstractmethod
    def set_expression(self, expression: str) -> None:
        raise NotImplementedError
