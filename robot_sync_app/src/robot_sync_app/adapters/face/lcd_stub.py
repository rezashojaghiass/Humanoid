from robot_sync_app.ports.face_port import FacePort


class LCDStubFaceAdapter(FacePort):
    """Stub face adapter for testing without physical display."""

    def set_expression(self, expression: str, audio_duration: float = 0.0) -> None:
        print(f"[FACE_STUB] expression={expression}, duration={audio_duration:.2f}s")

    def cleanup(self) -> None:
        print("[FACE_STUB] Cleaned up")
