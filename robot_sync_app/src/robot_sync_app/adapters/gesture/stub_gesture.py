from typing import Any, Dict

from robot_sync_app.ports.gesture_port import GesturePort


class StubGestureAdapter(GesturePort):
    def start_gesture(self, name: str) -> None:
        # Stub: just print, don't actually control servos
        print(f"[GESTURE] start_gesture={name}")

    def stop_gesture(self, name: str) -> None:
        # Stub: just print, don't actually control servos
        print(f"[GESTURE] stop_gesture={name}")

    def send_command(self, name: str, params: Dict[str, Any]) -> None:
        # Stub: just print, don't actually send commands
        print(f"[GESTURE] send_command={name}, params={params}")
