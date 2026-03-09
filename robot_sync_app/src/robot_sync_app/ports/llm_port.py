from abc import ABC, abstractmethod


class LLMPort(ABC):
    @abstractmethod
    def generate_reply(self, user_text: str, intent: str = "chat") -> str:
        raise NotImplementedError
