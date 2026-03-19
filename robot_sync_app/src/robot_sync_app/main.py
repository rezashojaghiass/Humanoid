import argparse
import logging
import multiprocessing
import sys
from pathlib import Path

import yaml

from robot_sync_app.bootstrap.container import build_orchestrator, build_voice_session
from robot_sync_app.startup.riva_manager import ensure_riva_ready


# Set multiprocessing to use 'fork' on systems that support it
# This prevents module re-execution on ARM/Jetson
if multiprocessing.get_start_method(allow_none=True) != 'fork':
    try:
        multiprocessing.set_start_method('fork', force=True)
    except RuntimeError:
        # Already set, or system doesn't support fork
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except:
            pass  # Use system default


def setup_logging():
    """Configure logging for real-time console output"""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # Simple format - just the message
        stream=sys.stdout,  # Output to stdout (unbuffered with -u flag)
        force=True
    )
    
    # Ensure all loggers use this configuration
    for logger_name in ['robot_sync_app', 'riva_speech', 'riva_mic_asr']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        # Flush after each log
        for handler in logger.handlers:
            handler.flush()


def main() -> None:
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Robot speech+gesture+face orchestrator")
    parser.add_argument("--config", default="config/config.yaml", help="Path to YAML config")
    parser.add_argument("--text", default="", help="Text to speak (text mode)")
    parser.add_argument("--intent", default="chat", help="Intent label (chat|quiz|arm_calibration)")
    parser.add_argument("--voice", action="store_true", help="Run conversation loop (mic->ASR->LLM->TTS)")
    parser.add_argument("--max-turns", type=int, default=0, help="Max turns for voice mode (0=infinite)")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    ensure_riva_ready(cfg)

    if args.voice:
        session = build_voice_session(args.config)
        session.run(intent=args.intent, max_turns=args.max_turns)
        return

    orchestrator = build_orchestrator(args.config)

    if not args.text.strip():
        raise ValueError("In text mode, --text is required. Or run with --voice.")
    
    orchestrator.run_once(text=args.text, intent=args.intent)


if __name__ == "__main__":
    main()
