import argparse

from robot_sync_app.bootstrap.container import build_orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Robot speech+gesture+face orchestrator")
    parser.add_argument("--config", default="config/config.yaml", help="Path to YAML config")
    parser.add_argument("--text", required=True, help="Text to speak")
    parser.add_argument("--intent", default="chat", help="Intent label (chat|quiz)")
    args = parser.parse_args()

    orchestrator = build_orchestrator(args.config)
    orchestrator.run_once(text=args.text, intent=args.intent)


if __name__ == "__main__":
    main()
