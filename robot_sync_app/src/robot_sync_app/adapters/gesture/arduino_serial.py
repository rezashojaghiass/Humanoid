import json
import time
from typing import Dict, Any, List

try:
    import serial
except Exception:  # pragma: no cover
    serial = None

from robot_sync_app.ports.gesture_port import GesturePort


class ArduinoSerialGestureAdapter(GesturePort):
    """
    Sends gesture commands to Arduino as JSON lines.

    SAFETY RULE:
    - Main arm servos are blocked by default.
    - Only finger gestures pass when enable_main_arms is False.
    """

    ARM_PREFIXES = ("arm_", "l_sh", "r_sh", "l_elb", "r_elb")

    def __init__(self, port: str, baud_rate: int, enable_main_arms: bool, allowed_finger_gestures: List[str]) -> None:
        self._enable_main_arms = enable_main_arms
        self._allowed_fingers = set(allowed_finger_gestures)
        self._serial = None

        if serial is not None:
            self._serial = serial.Serial(port=port, baudrate=baud_rate, timeout=1)
            self._wait_for_arduino_ready()

    def _wait_for_arduino_ready(self) -> None:
        if self._serial is None:
            return

        # Opening serial resets many Arduino boards; wait so first command is not lost.
        time.sleep(2.2)
        try:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
        except Exception:
            pass

        deadline = time.time() + 3.0
        while time.time() < deadline:
            try:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
            except Exception:
                line = ""
            if line.startswith("READY:"):
                break

        # Safety sync to known idle state.
        try:
            self._serial.write(("STOP_ALL\n").encode("utf-8"))
        except Exception:
            pass

    def _wait_for_animation_complete(self, timeout: float = 6.0) -> None:
        """Wait for Arduino to send ANIMATION:COMPLETE message after finger animation."""
        if self._serial is None:
            return
        
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("ANIMATION:COMPLETE"):
                    return  # Animation is done, proceed
            except Exception:
                pass
        
        # Timeout - just proceed anyway
        print("[GESTURE] Warning: ANIMATION:COMPLETE not received within timeout")

    def _is_arm_command(self, name: str) -> bool:
        n = name.lower()
        return n.startswith(self.ARM_PREFIXES)

    def _validate(self, name: str) -> None:
        n = name.lower()
        if self._is_arm_command(n) and not self._enable_main_arms:
            raise RuntimeError("Safety block: main arm servo command is disabled")
        if not self._is_arm_command(n) and n not in self._allowed_fingers:
            raise RuntimeError(f"Gesture not whitelisted: {name}")

    def _send(self, payload: Dict[str, Any]) -> None:
        line = json.dumps(payload)
        if self._serial is None:
            print(f"[GESTURE-MOCK] {line}")
            return
        self._serial.write((line + "\\n").encode("utf-8"))

    def start_gesture(self, name: str) -> None:
        self._validate(name)
        self._send({"type": "gesture_start", "name": name})

    def stop_gesture(self, name: str) -> None:
        self._validate(name)
        self._send({"type": "gesture_stop", "name": name})

    def send_command(self, name: str, params: Dict[str, Any]) -> None:
        if name == "stop_all":
            if self._serial is None:
                print("[GESTURE-MOCK] STOP_ALL")
                return
            self._serial.write(("STOP_ALL\n").encode("utf-8"))
            return

        if name == "finger_command":
            action = str(params.get("action", "")).upper()
            side = str(params.get("side", "BOTH")).upper()
            if action not in {"OPEN", "CLOSE", "CLOSE_SEQ", "CLOSE_SEQ_ARMS", "WAVE"}:
                raise RuntimeError(f"Invalid finger action: {action}")
            if side not in {"LEFT", "RIGHT", "BOTH"}:
                raise RuntimeError(f"Invalid finger side: {side}")

            line = f"FINGER:{action}:{side}"
            if self._serial is None:
                print(f"[GESTURE-MOCK] {line}")
                return
            self._serial.write((line + "\n").encode("utf-8"))
            
            # For CLOSE_SEQ_ARMS, wait for animation to actually complete
            if action == "CLOSE_SEQ_ARMS":
                self._wait_for_animation_complete()
            return

        if name != "arm_calibration_step":
            self._send({"type": "command", "name": name, "params": params})
            return

        if not self._enable_main_arms:
            raise RuntimeError("Safety block: main arm servo command is disabled")

        side = str(params.get("side", "")).upper()
        joint = str(params.get("joint", "")).upper()
        direction = str(params.get("direction", "")).upper()
        amount = int(params.get("amount", 10))

        if side not in {"LEFT", "RIGHT"}:
            raise RuntimeError(f"Invalid arm side: {side}")
        if joint not in {"ELBOW", "SHOULDER1", "SHOULDER2"}:
            raise RuntimeError(f"Invalid arm joint: {joint}")
        if direction not in {"UP", "DOWN", "LEFT", "RIGHT"}:
            raise RuntimeError(f"Invalid arm direction: {direction}")

        amount = max(1, min(100, amount))
        line = f"ARM_CAL:{side}:{joint}:{direction}:{amount}"

        if self._serial is None:
            print(f"[GESTURE-MOCK] {line}")
            return
        self._serial.write((line + "\n").encode("utf-8"))
