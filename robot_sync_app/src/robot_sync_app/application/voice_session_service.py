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

    def run(self, intent: str = "chat", max_turns: int = 0) -> None:
        if intent == "arm_calibration":
            self._run_arm_calibration(max_turns=max_turns)
            return

        turn = 0
        print("🎙️ Voice session started. Say 'QUIT' to end.")

        greeting = "Hi Adrian, I am ready. What should we do?"
        self._orchestrator.run_once(text=greeting, intent=intent)

        while True:
            if max_turns > 0 and turn >= max_turns:
                print("✓ Reached max turns")
                break

            user_text = self._asr.listen_and_transcribe()
            if not user_text:
                continue

            if user_text.lower().strip() == "quit":
                print("👋 Ending voice session")
                break

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
        elif "shoulder 1" in t or "shoulder1" in t or "s1" in t or "first shoulder" in t:
            joint = "SHOULDER1"
        elif "shoulder 2" in t or "shoulder2" in t or "s2" in t or "second shoulder" in t:
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
        print("🎙️ Arm calibration session started. Say 'QUIT' to end.")
        self._say("Arm calibration mode. Short answers only.")
        self._say("Main menu. Say left, right, or quit.")

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
            if t in {"quit", "stop", "exit"}:
                self._orchestrator.send_command("stop_all", {})
                self._say("Calibration ended.")
                print("👋 Ending arm calibration")
                break

            if "main menu" in t or "menu" in t or "enough" in t:
                last_cmd = None
                side = None
                joint = None
                self._say("Main menu. Say left, right, or quit.")
                continue

            if "some more" in t or t == "more":
                if not last_cmd:
                    self._say("No previous move. Main menu. Say left or right.")
                    continue
                self._orchestrator.send_command("arm_calibration_step", last_cmd)
                self._say("Done. Say some more, reverse, main menu, or quit.")
                turn += 1
                continue

            if "reverse" in t:
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
                if "left" in t:
                    side = "LEFT"
                    self._say("Say elbow, shoulder one, or shoulder two.")
                elif "right" in t:
                    side = "RIGHT"
                    self._say("Say elbow, shoulder one, or shoulder two.")
                else:
                    self._say("Main menu. Say left, right, or quit.")
                continue

            if joint is None:
                if "elbow" in t or "elb" in t:
                    joint = "ELBOW"
                    self._say("Say up or down.")
                elif "shoulder 1" in t or "shoulder1" in t or "first shoulder" in t or t == "s1":
                    joint = "SHOULDER1"
                    self._say("Say up or down.")
                elif "shoulder 2" in t or "shoulder2" in t or "second shoulder" in t or t == "s2":
                    joint = "SHOULDER2"
                    self._say("Say up or down.")
                else:
                    self._say("Say elbow, shoulder one, or shoulder two.")
                continue

            direction = None
            if "up" in t or "raise" in t:
                direction = "UP"
            elif "down" in t or "lower" in t:
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

