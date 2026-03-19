from abc import ABC, abstractmethod


class FacePort(ABC):
    @abstractmethod
    def set_expression(self, expression: str, audio_duration: float = 0.0) -> None:
        """Set the facial expression.
        
        Args:
            expression: The expression to display
            audio_duration: Duration of audio playback in seconds (for animation synchronization)
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass
