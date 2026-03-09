from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class EventType(str, Enum):
    SPEAK_START = "SPEAK_START"
    SPEAK_END = "SPEAK_END"
    GESTURE_START = "GESTURE_START"
    GESTURE_STOP = "GESTURE_STOP"
    FACE_SET = "FACE_SET"


@dataclass
class TimelineEvent:
    at_ms: int
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
