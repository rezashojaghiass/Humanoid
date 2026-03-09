from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Utterance:
    text: str
    intent: str = "chat"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorPlan:
    speech_text: str
    gesture_name: str
    face_expression: str
    metadata: Dict[str, Any] = field(default_factory=dict)
