from pathlib import Path
from typing import Any, Dict

import yaml

from robot_sync_app.application.behavior_planner import BehaviorPlanner
from robot_sync_app.application.orchestrator_service import OrchestratorService
from robot_sync_app.application.voice_session_service import VoiceSessionService
from robot_sync_app.adapters.asr.riva_mic_asr import RivaMicASRAdapter
from robot_sync_app.adapters.face.lcd_stub import LCDStubFaceAdapter
from robot_sync_app.adapters.face.pygame_lcd import PyGameLCDFaceAdapter
from robot_sync_app.adapters.gesture.arduino_serial import ArduinoSerialGestureAdapter
from robot_sync_app.adapters.llm.bedrock_llm import BedrockLLMAdapter
from robot_sync_app.adapters.llm.simple_llm import SimpleLLMAdapter
from robot_sync_app.adapters.speech.riva_speech import RivaSpeechAdapter
from robot_sync_app.adapters.storage.local_storage import LocalStorageAdapter
from robot_sync_app.adapters.storage.s3_storage import S3StorageAdapter
from robot_sync_app.ports.storage_port import StoragePort


def _load_yaml(path: str) -> Dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _build_storage(cfg: Dict[str, Any]) -> StoragePort:
    if cfg["storage"]["backend"] == "s3":
        return S3StorageAdapter(
            bucket=cfg["storage"]["s3_bucket"],
            prefix=cfg["storage"]["s3_prefix"],
        )
    return LocalStorageAdapter(base_path=cfg["storage"]["local_base_path"])


def build_orchestrator(config_path: str) -> OrchestratorService:
    cfg = _load_yaml(config_path)

    planner = BehaviorPlanner()
    storage = _build_storage(cfg)

    speech = RivaSpeechAdapter(
        server=cfg["speech"]["riva_server"],
        voice_name=cfg["speech"]["voice_name"],
        sample_rate_hz=cfg["speech"]["sample_rate_hz"],
        output_device_index=cfg["speech"]["output_device_index"],
        output_device_name_hint=cfg["speech"].get("output_device_name_hint", "KT USB Audio"),
    )

    gesture = ArduinoSerialGestureAdapter(
        port=cfg["gesture"]["serial_port"],
        baud_rate=cfg["gesture"]["baud_rate"],
        enable_main_arms=cfg["safety"]["enable_main_arms"],
        allowed_finger_gestures=cfg["gesture"]["allowed_finger_gestures"],
    )

    # Initialize face adapter based on config
    face_provider = cfg["face"].get("provider", "lcd_stub")
    if face_provider == "pygame_lcd":
        face = PyGameLCDFaceAdapter(
            width=cfg["face"].get("width", 1024),
            height=cfg["face"].get("height", 768),
            fullscreen=cfg["face"].get("fullscreen", True),
        )
    else:
        face = LCDStubFaceAdapter()

    return OrchestratorService(
        planner=planner,
        speech=speech,
        gesture=gesture,
        face=face,
        storage=storage,
        neutral_expression=cfg["face"]["default_expression"],
    )


def build_voice_session(config_path: str) -> VoiceSessionService:
    cfg = _load_yaml(config_path)
    storage = _build_storage(cfg)
    orchestrator = build_orchestrator(config_path)

    asr = RivaMicASRAdapter(
        server=cfg["asr"]["riva_server"],
        input_device_index=cfg["asr"].get("input_device_index"),
        input_device_name_hint=cfg["asr"].get("input_device_name_hint", "Wireless GO II"),
        max_duration_sec=cfg["asr"].get("max_duration_sec", 20),
        silence_threshold=cfg["asr"].get("silence_threshold", 500),
        silence_duration_sec=cfg["asr"].get("silence_duration_sec", 0.5),
        sample_rate_hz=cfg["asr"].get("sample_rate_hz", 16000),
    )

    if cfg["llm"].get("provider", "bedrock") == "simple":
        llm = SimpleLLMAdapter()
    else:
        llm = BedrockLLMAdapter(
            model_id=cfg["llm"]["aws_model_id"],
            region=cfg["llm"]["aws_region"],
            system_prompt=cfg["llm"].get("system_prompt", "You are a helpful robot assistant."),
            min_cooldown_sec=cfg["llm"].get("min_cooldown_sec", 1.5),
        )

    return VoiceSessionService(
        asr=asr,
        llm=llm,
        orchestrator=orchestrator,
        storage=storage,
    )
