from robot_sync_app.ports.face_port import FacePort


class LCDStubFaceAdapter(FacePort):
    def set_expression(self, expression: str) -> None:
        # Replace with real LCD drawing code on Jetson
        print(f"[FACE] expression={expression}")
