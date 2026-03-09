from datetime import datetime, timezone

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
        turn = 0
        print("🎙️ Voice session started. Say 'QUIT' to end.")

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
