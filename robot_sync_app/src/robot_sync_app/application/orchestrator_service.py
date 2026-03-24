from datetime import datetime, timezone
from typing import Dict, Any

from robot_sync_app.domain.models import Utterance
from robot_sync_app.application.behavior_planner import BehaviorPlanner
from robot_sync_app.ports.speech_port import SpeechPort
from robot_sync_app.ports.gesture_port import GesturePort
from robot_sync_app.ports.face_port import FacePort
from robot_sync_app.ports.storage_port import StoragePort


class OrchestratorService:
    def __init__(
        self,
        planner: BehaviorPlanner,
        speech: SpeechPort,
        gesture: GesturePort,
        face: FacePort,
        storage: StoragePort,
        neutral_expression: str = "EE",
    ) -> None:
        self._planner = planner
        self._speech = speech
        self._gesture = gesture
        self._face = face
        self._storage = storage
        self._neutral = neutral_expression

    def set_gesture_adapter(self, gesture: GesturePort) -> None:
        """Switch to a different gesture adapter (e.g., from stub to arduino_serial)"""
        self._gesture = gesture

    def run_once(self, text: str, intent: str = "chat") -> None:
        utterance = Utterance(text=text, intent=intent)
        plan = self._planner.plan(utterance)

        started_at = datetime.now(timezone.utc).isoformat()

        def on_start() -> None:
            # Get audio duration from speech adapter (if available)
            audio_duration = 0.0
            if hasattr(self._speech, '_last_audio_duration'):
                audio_duration = self._speech._last_audio_duration
            
            # For lip-sync mode, start lip-sync animation
            if hasattr(self._face, 'speak'):
                self._face.speak(plan.speech_text, audio_duration)
            else:
                # For traditional mode, set expression
                self._face.set_expression(plan.face_expression, audio_duration)
            if plan.gesture_name:
                self._gesture.start_gesture(plan.gesture_name)

        def on_end() -> None:
            if plan.gesture_name:
                self._gesture.stop_gesture(plan.gesture_name)
            # For lip-sync mode, return to neutral
            if hasattr(self._face, 'speak_done'):
                self._face.speak_done()
            else:
                self._face.set_expression(self._neutral)

        self._speech.speak(plan.speech_text, on_start=on_start, on_end=on_end)

        self._storage.put_json(
            "sessions/latest_event.json",
            {
                "started_at": started_at,
                "intent": intent,
                "text": text,
                "gesture": plan.gesture_name,
                "face": plan.face_expression,
                "status": "done",
            },
        )

    def send_command(self, name: str, params: Dict[str, Any]) -> None:
        self._gesture.send_command(name=name, params=params)
