from pathlib import Path
from typing import Any, Dict

import yaml

from robot_sync_app.application.behavior_planner import BehaviorPlanner
from robot_sync_app.application.orchestrator_service import OrchestratorService
from robot_sync_app.adapters.face.lcd_stub import LCDStubFaceAdapter
from robot_sync_app.adapters.gesture.arduino_serial import ArduinoSerialGestureAdapter
from robot_sync_app.adapters.speech.riva_speech import RivaSpeechAdapter
from robot_sync_app.adapters.storage.local_storage import LocalStorageAdapter
from robot_sync_app.adapters.storage.s3_storage import S3StorageAdapter


def _load_yaml(path: str) -> Dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def build_orchestrator(config_path: str) -> OrchestratorService:
    cfg = _load_yaml(config_path)

    planner = BehaviorPlanner()

    if cfg["storage"]["backend"] == "s3":
        storage = S3StorageAdapter(
            bucket=cfg["storage"]["s3_bucket"],
            prefix=cfg["storage"]["s3_prefix"],
        )
    else:
        storage = LocalStorageAdapter(base_path=cfg["storage"]["local_base_path"])

    speech = RivaSpeechAdapter(
        server=cfg["speech"]["riva_server"],
        voice_name=cfg["speech"]["voice_name"],
        sample_rate_hz=cfg["speech"]["sample_rate_hz"],
        output_device_index=cfg["speech"]["output_device_index"],
    )

    gesture = ArduinoSerialGestureAdapter(
        port=cfg["gesture"]["serial_port"],
        baud_rate=cfg["gesture"]["baud_rate"],
        enable_main_arms=cfg["safety"]["enable_main_arms"],
        allowed_finger_gestures=cfg["gesture"]["allowed_finger_gestures"],
    )

    face = LCDStubFaceAdapter()

    return OrchestratorService(
        planner=planner,
        speech=speech,
        gesture=gesture,
        face=face,
        storage=storage,
        neutral_expression=cfg["face"]["default_expression"],
    )
