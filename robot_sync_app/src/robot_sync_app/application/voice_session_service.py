from datetime import datetime, timezone
from typing import Any, Dict, Optional

from robot_sync_app.application.orchestrator_service import OrchestratorService
from robot_sync_app.ports.asr_port import ASRPort
from robot_sync_app.ports.llm_port import LLMPort
from robot_sync_app.ports.storage_port import StoragePort


class VoiceSessionService:
    def __init__(
        self,
        asr: ASRPort,
        llm: LLMPort,
        orchestrator: OrchestratorService,
        storage: StoragePort,
    ) -> None:
        self._asr = asr
        self._llm = llm
        self._orchestrator = orchestrator
        self._storage = storage
        self._chat_move_side: Optional[str] = None
        self._chat_move_joint: Optional[str] = None
        self._chat_last_cmd: Optional[Dict[str, Any]] = None

    def run(self, intent: str = "chat", max_turns: int = 0) -> None:
        if intent == "arm_calibration":
            self._run_arm_calibration(max_turns=max_turns)
            return

        turn = 0
        print("🎙️ Voice session started. Say 'QUIT' to end.")

        greeting = "Hi Reza, I am ready. What should we do?"
        self._orchestrator.run_once(text=greeting, intent=intent)

        while True:
            if max_turns > 0 and turn >= max_turns:
                print("✓ Reached max turns")
                break

            user_text = self._asr.listen_and_transcribe()
            if not user_text:
                continue

            user_text_lower = user_text.lower().strip()
            if "quit" in user_text_lower or "exit" in user_text_lower or "stop" in user_text_lower:
                print("👋 Ending voice session")
                break

            if self._is_movement_intent(user_text):
                # Hybrid behavior: once movement intent is detected in chat,
                # hand off to the exact calibration-style short-answer loop.
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

            reply = self._llm.generate_reply(user_text=user_text, intent=intent)
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

    def _is_movement_intent(self, text: str) -> bool:
        # Conservative detector: explicit movement phrases, structured arm/finger
        # commands, or movement keywords trigger calibration-style mode.
        t = " ".join(text.lower().strip().replace(".", " ").replace(",", " ").split())

        if t in {"movement mode", "move mode", "control mode", "arm calibration", "calibration mode"}:
            return True

        if self._parse_arm_command(text) is not None:
            return True

        if self._parse_finger_command(text) is not None:
            return True

        movement_words = {"move", "movement", "arm", "elbow", "shoulder", "fingers", "finger", "hand", "hands", "reverse", "some more", "more", "main menu"}
        return any(w in t for w in movement_words)

    def _parse_finger_command(self, text: str) -> Optional[Dict[str, Any]]:
        t = text.lower().strip()
        
        # Check for wave command first (can work standalone)
        if "wave" in t:
            action = "WAVE"
        # Then check for finger/hand commands
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

        # Shortcut: "left arm up/down" maps to SHOULDER2.
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

        if t_clean in {"movement mode", "move mode", "control mode"}:
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
                self._orchestrator.send_command("arm_calibration_step", self._chat_last_cmd)
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

        # Fixed step amount. Duration safety is enforced on Arduino side (0.5s per move).
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
        print("🎙️ Arm calibration session started. Say 'QUIT' to return to chat.")
        self._say("Arm calibration mode. Short answers only.")
        self._say("Available commands: wave, fingers open or close, left or right arm moves, stop motion, some more, reverse, main menu, or quit to return to chat.")

        turn = 0
        last_cmd: Optional[Dict[str, Any]] = None
        side: Optional[str] = None
        joint: Optional[str] = None

        while True:
            if max_turns > 0 and turn >= max_turns:
                print("✓ Reached max turns")
                break

            user_text = self._asr.listen_and_transcribe()
            if not user_text:
                continue

            t = user_text.lower().strip()
            t_clean = " ".join(t.replace(".", " ").replace(",", " ").split())
            if t_clean in {"quit", "stop", "exit", "chat mode", "conversation mode", "normal mode"}:
                self._orchestrator.send_command("stop_all", {})
                self._say("Calibration ended. Returning to chat mode.")
                print("👋 Ending arm calibration")
                break

            finger = self._parse_finger_command(user_text)
            if finger:
                self._orchestrator.send_command("finger_command", finger)
                self._say("Done. Say left, right, main menu, or quit.")
                turn += 1
                continue

            if "main menu" in t_clean or "menu" in t_clean or "enough" in t_clean:
                last_cmd = None
                side = None
                joint = None
                self._say("Main menu. Say left, right, or quit.")
                continue

            if "some more" in t_clean or t_clean == "more":
                if not last_cmd:
                    self._say("No previous move. Main menu. Say left or right.")
                    continue
                self._orchestrator.send_command("arm_calibration_step", last_cmd)
                self._say("Done. Say some more, reverse, main menu, or quit.")
                turn += 1
                continue

            if "reverse" in t_clean:
                if not last_cmd:
                    self._say("No previous move. Main menu. Say left or right.")
                    continue
                rev = dict(last_cmd)
                rev["direction"] = "DOWN" if str(rev.get("direction")) == "UP" else "UP"
                self._orchestrator.send_command("arm_calibration_step", rev)
                last_cmd = rev
                self._say("Reversed. Say some more, reverse, main menu, or quit.")
                turn += 1
                continue

            # Full command still accepted (e.g. "left elbow up")
            cmd = self._parse_arm_command(user_text)
            if cmd:
                self._orchestrator.send_command("arm_calibration_step", cmd)
                last_cmd = cmd
                side = str(cmd["side"])
                joint = str(cmd["joint"])
                self._say("Done. Say some more, reverse, main menu, or quit.")
                turn += 1
                continue

            # Guided short-answer flow
            if side is None:
                if "left" in t_clean:
                    side = "LEFT"
                    self._say("Say elbow, shoulder one, or shoulder two.")
                elif "right" in t_clean:
                    side = "RIGHT"
                    self._say("Say elbow, shoulder one, or shoulder two.")
                else:
                    self._say("Main menu. Say left, right, or quit.")
                continue

            if joint is None:
                if "elbow" in t_clean or "elb" in t_clean:
                    joint = "ELBOW"
                    self._say("Say up or down.")
                elif "shoulder 1" in t_clean or "shoulder1" in t_clean or "shoulder one" in t_clean or "first shoulder" in t_clean or t_clean in {"s1", "one", "1"}:
                    joint = "SHOULDER1"
                    self._say("Say up or down.")
                elif "shoulder 2" in t_clean or "shoulder2" in t_clean or "shoulder two" in t_clean or "second shoulder" in t_clean or t_clean in {"s2", "two", "2", "to"}:
                    joint = "SHOULDER2"
                    self._say("Say up or down.")
                else:
                    self._say("Say elbow, shoulder one, or shoulder two.")
                continue

            direction = None
            if "up" in t_clean or "raise" in t_clean:
                direction = "UP"
            elif "down" in t_clean or "lower" in t_clean:
                direction = "DOWN"

            if not direction:
                self._say("Say up or down.")
                continue

            cmd = {
                "side": side,
                "joint": joint,
                "direction": direction,
                "amount": 15,
            }
            self._orchestrator.send_command("arm_calibration_step", cmd)
            last_cmd = cmd
            self._say("Done. Say some more, reverse, main menu, or quit.")
            turn += 1

