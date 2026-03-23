import time
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from robot_sync_app.application.orchestrator_service import OrchestratorService
from robot_sync_app.ports.asr_port import ASRPort
from robot_sync_app.ports.llm_port import LLMPort
from robot_sync_app.ports.storage_port import StoragePort
from robot_sync_app.ports.gesture_port import GesturePort


class VoiceSessionService:
    """
    Voice session with threading architecture:
    - Main thread: Available for animation/display updates (pygame safe)
    - Background thread: Handles RIVA operations (ASR, LLM, TTS)
    """

    def __init__(
        self,
        asr: ASRPort,
        llm: LLMPort,
        orchestrator: OrchestratorService,
        storage: StoragePort,
        gesture_adapters: Optional[Dict[str, GesturePort]] = None,
    ) -> None:
        self._asr = asr
        self._llm = llm
        self._orchestrator = orchestrator
        self._storage = storage
        self._gesture_adapters = gesture_adapters or {}  # {'stub': ..., 'arduino_serial': ...}
        self._chat_move_side: Optional[str] = None
        self._chat_move_joint: Optional[str] = None
        self._chat_last_cmd: Optional[Dict[str, Any]] = None

    def _enable_servos(self) -> None:
        """Switch to arduino_serial gesture adapter to enable servo movements"""
        if "arduino_serial" in self._gesture_adapters:
            self._orchestrator.set_gesture_adapter(self._gesture_adapters["arduino_serial"])
            print("✓ Servos enabled")

    def _disable_servos(self) -> None:
        """Switch to stub gesture adapter to disable servo movements"""
        if "stub" in self._gesture_adapters:
            self._orchestrator.set_gesture_adapter(self._gesture_adapters["stub"])
            print("✓ Servos disabled")

    def run(self, intent: str = "chat", max_turns: int = 0) -> None:
        """Main thread handles orchestration, background thread handles RIVA I/O"""
        if intent == "arm_calibration":
            self._run_arm_calibration(max_turns=max_turns)
            return

        turn = 0
        print("🎙️ Voice session started. Say 'QUIT' to end.")

        # Greeting: main thread, blocking is OK for initialization
        greeting = "Hi Reza, I am ready. What should we do?"
        print(f"🤖 Speaking greeting: {greeting}")
        self._orchestrator.run_once(text=greeting, intent=intent)
        print("✓ Greeting completed")
        
        print("⏳ Waiting for speaker to settle before listening...")
        time.sleep(0.5)
        print("✓ Ready to listen")

        # Thread synchronization
        should_exit = threading.Event()
        
        def riva_worker() -> None:
            """Background thread: ASR, LLM, TTS - all RIVA I/O operations"""
            nonlocal turn
            
            while not should_exit.is_set():
                try:
                    # ASR: listen (blocking, OK in background thread)
                    user_text = self._asr.listen_and_transcribe()
                    if not user_text or should_exit.is_set():
                        continue

                    user_text_lower = user_text.lower().strip()
                    if any(word in user_text_lower for word in ["quit", "exit", "stop"]):
                        print("👋 Ending voice session")
                        should_exit.set()
                        break

                    if self._is_movement_intent(user_text):
                        self._orchestrator.run_once(
                            text="Switching to movement mode.",
                            intent="arm_calibration",
                        )
                        self._run_arm_calibration(max_turns=0)
                        self._orchestrator.run_once(
                            text="Back to chat mode.",
                            intent="arm_calibration",
                        )
                        continue

                    # LLM: generate reply (blocking, OK in background thread)
                    reply = self._llm.generate_reply(user_text=user_text, intent=intent)
                    
                    # TTS: speak reply with animation sync
                    self._orchestrator.run_once(text=reply, intent=intent)

                    turn += 1
                    self._storage.put_json(
                        "sessions/latest_turn.json",
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "turn": turn,
                            "intent": intent,
                            "user_text": user_text,
                            "assistant_reply": reply,
                        },
                    )

                    if max_turns > 0 and turn >= max_turns:
                        print("✓ Reached max turns")
                        should_exit.set()
                        break
                        
                except Exception as e:
                    print(f"❌ Error in background RIVA thread: {e}")
                    should_exit.set()
                    break
        
        # Start background thread for RIVA operations
        riva_thread = threading.Thread(target=riva_worker, daemon=True)
        riva_thread.start()
        
        # Main thread: wait for exit signal
        # In future, main thread could handle animation updates here
        while not should_exit.is_set():
            time.sleep(0.1)  # Small sleep to prevent busy-wait
        
        # Wait for background thread to finish
        riva_thread.join(timeout=5)

    def _is_movement_intent(self, text: str) -> bool:
        t = " ".join(text.lower().strip().replace(".", " ").replace(",", " ").split())
        if t in {"movement mode", "move mode", "motion mode", "control mode", "arm calibration", "calibration mode"}:
            return True

        if self._parse_arm_command(text) is not None:
            return True

        if self._parse_finger_command(text) is not None:
            return True

        movement_words = {"move", "movement", "arm", "elbow", "shoulder", "fingers", "finger", "hand", "hands", "reverse", "some more", "more", "main menu"}
        return any(w in t for w in movement_words)

    def _parse_finger_command(self, text: str) -> Optional[Dict[str, Any]]:
        t = text.lower().strip()
        
        if "wave" in t:
            action = "WAVE"
        elif "finger" in t or "fingers" in t or "hand" in t or "hands" in t:
            action = None
            if "open" in t:
                action = "OPEN"
            elif "close" in t:
                action = "CLOSE"
            
            if not action:
                return None
        else:
            return None

        side = "BOTH"
        if "left" in t:
            side = "LEFT"
        elif "right" in t:
            side = "RIGHT"

        return {"action": action, "side": side}

    def _parse_chat_arm_command(self, text: str) -> Optional[Dict[str, Any]]:
        cmd = self._parse_arm_command(text)
        if cmd:
            return cmd

        t = text.lower().strip()
        side = None
        if "left" in t:
            side = "LEFT"
        elif "right" in t:
            side = "RIGHT"

        direction = None
        if "up" in t or "raise" in t:
            direction = "UP"
        elif "down" in t or "lower" in t:
            direction = "DOWN"

        if side and direction and (" arm" in f" {t}" or t.startswith("arm ")):
            return {
                "side": side,
                "joint": "SHOULDER2",
                "direction": direction,
                "amount": 15,
            }

        return None

    def _handle_chat_movement(self, user_text: str) -> Optional[str]:
        t = user_text.lower().strip()
        t_clean = " ".join(t.replace(".", " ").replace(",", " ").split())
        
        if t_clean in {"movement mode", "move mode", "motion mode", "control mode"}:
            self._chat_move_side = None
            self._chat_move_joint = None
            self._chat_last_cmd = None
            return "Entering movement mode. You can say: wave, fingers open or close, left or right arm, stop motion, or chat mode to exit."
        
        if t_clean in {"chat mode", "normal mode", "conversation mode"}:
            self._chat_move_side = None
            self._chat_move_joint = None
            self._chat_last_cmd = None
            return "Back to normal chat mode."

        if t_clean in {"main menu", "menu", "reset"}:
            self._chat_move_side = None
            self._chat_move_joint = None
            return "Movement menu. Available: wave, fingers open or close, left or right arm moves, stop motion, or chat mode to exit."
        
        if t_clean in {"stop motion", "stop all", "freeze"}:
            self._orchestrator.send_command("stop_all", {})
            return "Stopped all movement."

        finger = self._parse_finger_command(user_text)
        if finger:
            self._orchestrator.send_command("finger_command", finger)
            action = str(finger["action"]).lower()
            side = str(finger["side"]).lower()
            return f"Done. Fingers {action} on {side}."

        cmd = self._parse_chat_arm_command(user_text)
        if cmd:
            self._orchestrator.send_command("arm_calibration_step", cmd)
            self._chat_move_side = str(cmd["side"])
            self._chat_move_joint = str(cmd["joint"])
            self._chat_last_cmd = dict(cmd)
            return "Done. Say some more, reverse, main menu, or chat mode."
        
        if t_clean in {"some more", "more"}:
            if self._chat_last_cmd:
                cmd_amplified = dict(self._chat_last_cmd)
                cmd_amplified["amount"] = max(1, min(100, cmd_amplified.get("amount", 15) * 5))
                self._orchestrator.send_command("arm_calibration_step", cmd_amplified)
                return "Done."
            return "No previous arm move. Say left or right."

        if t_clean == "reverse":
            if not self._chat_last_cmd:
                return "No previous arm move."
            rev = dict(self._chat_last_cmd)
            rev["direction"] = "DOWN" if str(rev.get("direction")) == "UP" else "UP"
            self._orchestrator.send_command("arm_calibration_step", rev)
            self._chat_last_cmd = rev
            return "Reversed."

        if self._chat_move_side is None and t_clean in {"left", "right"}:
            self._chat_move_side = "LEFT" if t_clean == "left" else "RIGHT"
            return "Say elbow, shoulder one, or shoulder two."

        if self._chat_move_side and self._chat_move_joint is None:
            if "elbow" in t_clean or "elb" in t_clean:
                self._chat_move_joint = "ELBOW"
                return "Say up or down."
            if "shoulder 1" in t_clean or "shoulder1" in t_clean or "shoulder one" in t_clean or t_clean in {"s1", "one", "1"}:
                self._chat_move_joint = "SHOULDER1"
                return "Say up or down."
            if "shoulder 2" in t_clean or "shoulder2" in t_clean or "shoulder two" in t_clean or t_clean in {"s2", "two", "2", "to"}:
                self._chat_move_joint = "SHOULDER2"
                return "Say up or down."

        if self._chat_move_side and self._chat_move_joint:
            direction = None
            if "up" in t_clean or "raise" in t_clean:
                direction = "UP"
            elif "down" in t_clean or "lower" in t_clean:
                direction = "DOWN"

            if direction:
                cmd2 = {
                    "side": self._chat_move_side,
                    "joint": self._chat_move_joint,
                    "direction": direction,
                    "amount": 15,
                }
                self._orchestrator.send_command("arm_calibration_step", cmd2)
                self._chat_last_cmd = dict(cmd2)
                return "Done. Say some more, reverse, main menu, or chat mode."
        
        if "move" in t_clean or "fingers" in t_clean or "shoulder" in t_clean or "elbow" in t_clean or "arm" in t_clean:
            return "Movement command not clear. Try: left shoulder two down, or fingers open."
        
        return None

    def _say(self, text: str) -> None:
        self._orchestrator.run_once(text=text, intent="arm_calibration")
        
    def _parse_arm_command(self, text: str) -> Optional[Dict[str, Any]]:
        t = text.lower().strip()

        side = None
        if "left" in t:
            side = "LEFT"
        elif "right" in t:
            side = "RIGHT"

        joint = None
        if "elbow" in t or "elb" in t:
            joint = "ELBOW"
        elif "shoulder 1" in t or "shoulder1" in t or "shoulder one" in t or "s1" in t or "first shoulder" in t:
            joint = "SHOULDER1"
        elif "shoulder 2" in t or "shoulder2" in t or "shoulder two" in t or "s2" in t or "second shoulder" in t:
            joint = "SHOULDER2"

        direction = None
        if "up" in t or "raise" in t:
            direction = "UP"
        elif "down" in t or "lower" in t:
            direction = "DOWN"

        amount = 15

        if not side or not joint or not direction:
            return None

        return {
            "side": side,
            "joint": joint,
            "direction": direction,
            "amount": max(1, min(100, amount)),
        }

    def _run_arm_calibration(self, max_turns: int = 0) -> None:
        # Enable servos when entering movement mode
        self._enable_servos()
        
        print("🎙️ Arm calibration session started. Say 'QUIT' to return to chat.")
        self._say("Arm calibration mode. Short answers only.")
        time.sleep(0.5)

        turn = 0
        last_cmd: Optional[Dict[str, Any]] = None
        body_part: Optional[str] = None  # "shoulder", "elbow", or "fingers"
        side: Optional[str] = None       # "LEFT" or "RIGHT"
        joint: Optional[str] = None      # "SHOULDER1", "SHOULDER2", or "ELBOW"
        direction: Optional[str] = None  # "UP", "DOWN", "LEFT", "RIGHT", "OPEN", "CLOSE"

        while True:
            if max_turns > 0 and turn >= max_turns:
                print("✓ Reached max turns")
                break

            user_text = self._asr.listen_and_transcribe()
            if not user_text:
                continue

            t = user_text.lower().strip()
            t_clean = " ".join(t.replace(".", " ").replace(",", " ").split())
            
            # Exit conditions
            if t_clean in {"quit", "stop", "exit", "chat mode", "conversation mode", "normal mode"}:
                self._orchestrator.send_command("stop_all", {})
                self._say("Calibration ended. Returning to chat mode.")
                # Disable servos when exiting movement mode
                self._disable_servos()
                print("👋 Ending arm calibration")
                break

            # Main menu reset
            if "main menu" in t_clean or "menu" in t_clean or "enough" in t_clean:
                last_cmd = None
                body_part = None
                side = None
                joint = None
                direction = None
                self._say("What do you want me to do?")
                continue

            # Handle "some more" - amplify last command
            if "some more" in t_clean or t_clean == "more":
                if not last_cmd:
                    self._say("No previous move. What do you want me to do?")
                    continue
                cmd_amplified = dict(last_cmd)
                cmd_amplified["amount"] = max(1, min(100, cmd_amplified.get("amount", 15) * 5))
                self._orchestrator.send_command("arm_calibration_step", cmd_amplified)
                self._say("Done. Say some more, reverse, main menu, or quit.")
                turn += 1
                continue

            # Handle "reverse" - reverse direction
            if "reverse" in t_clean:
                if not last_cmd:
                    self._say("No previous move. What do you want me to do?")
                    continue
                rev = dict(last_cmd)
                rev_direction = str(rev.get("direction"))
                if rev_direction == "UP":
                    rev["direction"] = "DOWN"
                elif rev_direction == "DOWN":
                    rev["direction"] = "UP"
                elif rev_direction == "LEFT":
                    rev["direction"] = "RIGHT"
                elif rev_direction == "RIGHT":
                    rev["direction"] = "LEFT"
                elif rev_direction == "OPEN":
                    rev["direction"] = "CLOSE"
                elif rev_direction == "CLOSE":
                    rev["direction"] = "OPEN"
                self._orchestrator.send_command("arm_calibration_step", rev)
                last_cmd = rev
                self._say("Reversed. Say some more, reverse, main menu, or quit.")
                turn += 1
                continue

            # ========== STEP 1: Ask "What do you want me to do?" ==========
            if body_part is None:
                # Parse body part from user input
                if "finger" in t_clean or "hand" in t_clean:
                    body_part = "fingers"
                    side = None  # Fingers don't need a side
                    self._say("Do you want me to open or close?")
                    continue
                elif "shoulder" in t_clean:
                    body_part = "shoulder"
                    # Now parse which side
                    if "left" in t_clean:
                        side = "LEFT"
                        self._say("Main servo, shoulder one, or second servo, shoulder two?")
                    elif "right" in t_clean:
                        side = "RIGHT"
                        self._say("Main servo, shoulder one, or second servo, shoulder two?")
                    else:
                        self._say("Left shoulder or right shoulder?")
                    continue
                elif "elbow" in t_clean or "elb" in t_clean:
                    body_part = "elbow"
                    # Parse which side
                    if "left" in t_clean:
                        side = "LEFT"
                        self._say("Do you want me to open or close?")
                    elif "right" in t_clean:
                        side = "RIGHT"
                        self._say("Do you want me to open or close?")
                    else:
                        self._say("Left elbow or right elbow?")
                    continue
                else:
                    self._say("What do you want me to do?")
                    continue

            # ========== STEP 2: For shoulders, ask "Shoulder 1 or Shoulder 2?" ==========
            if body_part == "shoulder" and joint is None:
                if "shoulder 1" in t_clean or "shoulder1" in t_clean or "shoulder one" in t_clean or "main servo" in t_clean or t_clean in {"s1", "one", "1", "main"}:
                    joint = "SHOULDER1"
                    self._say("Do you want me to move up or down?")
                    continue
                elif "shoulder 2" in t_clean or "shoulder2" in t_clean or "shoulder two" in t_clean or "second servo" in t_clean or t_clean in {"s2", "two", "2", "second"}:
                    joint = "SHOULDER2"
                    self._say("Do you want me to move left or right?")
                    continue
                elif "left" in t_clean and side is None:
                    side = "LEFT"
                    self._say("Main servo, shoulder one, or second servo, shoulder two?")
                    continue
                elif "right" in t_clean and side is None:
                    side = "RIGHT"
                    self._say("Main servo, shoulder one, or second servo, shoulder two?")
                    continue
                else:
                    self._say("Main servo, shoulder one, or second servo, shoulder two?")
                    continue

            # ========== STEP 3: For elbow, ask "Open or close?" ==========
            if body_part == "elbow" and joint is None:
                if "left" in t_clean and side is None:
                    side = "LEFT"
                    self._say("Do you want me to open or close?")
                    continue
                elif "right" in t_clean and side is None:
                    side = "RIGHT"
                    self._say("Do you want me to open or close?")
                    continue
                else:
                    joint = "ELBOW"  # Default, will ask for action next
                    self._say("Do you want me to open or close?")
                    continue

            # ========== STEP 4: Get direction/action ==========
            if direction is None:
                if body_part == "shoulder" and joint == "SHOULDER1":
                    # Shoulder 1: up or down
                    if "up" in t_clean or "raise" in t_clean:
                        direction = "UP"
                    elif "down" in t_clean or "lower" in t_clean:
                        direction = "DOWN"
                    else:
                        self._say("Do you want me to move up or down?")
                        continue
                elif body_part == "shoulder" and joint == "SHOULDER2":
                    # Shoulder 2: left or right
                    if "left" in t_clean:
                        direction = "LEFT"
                    elif "right" in t_clean:
                        direction = "RIGHT"
                    else:
                        self._say("Do you want me to move left or right?")
                        continue
                elif body_part == "elbow":
                    # Elbow: open or close
                    if "open" in t_clean:
                        direction = "OPEN"
                    elif "close" in t_clean:
                        direction = "CLOSE"
                    else:
                        self._say("Do you want me to open or close?")
                        continue
                elif body_part == "fingers":
                    # Fingers: open or close
                    if "open" in t_clean:
                        direction = "OPEN"
                    elif "close" in t_clean:
                        direction = "CLOSE"
                    else:
                        self._say("Do you want me to open or close?")
                        continue

            # ========== EXECUTE COMMAND ==========
            if body_part == "fingers":
                # Handle finger commands
                action = "OPEN" if direction == "OPEN" else "CLOSE"
                finger_cmd = {"action": action, "side": "BOTH"}
                self._orchestrator.send_command("finger_command", finger_cmd)
                last_cmd = {"action": action, "side": "BOTH"}
                self._say("Done. Say some more, reverse, main menu, or quit.")
                # Reset state for next command
                body_part = None
                side = None
                joint = None
                direction = None
                turn += 1
                continue
            elif body_part in {"shoulder", "elbow"} and side and joint and direction:
                # Handle arm commands
                arm_cmd = {
                    "side": side,
                    "joint": joint,
                    "direction": direction,
                    "amount": 15,
                }
                self._orchestrator.send_command("arm_calibration_step", arm_cmd)
                last_cmd = dict(arm_cmd)
                self._say("Done. Say some more, reverse, main menu, or quit.")
                # Reset state for next command
                body_part = None
                side = None
                joint = None
                direction = None
                turn += 1
                continue

            # Fallback if something goes wrong
            self._say("What do you want me to do?")
