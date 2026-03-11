import shlex
import socket
import subprocess
import time
from typing import Any, Dict, List


def _is_port_open(host: str, port: int, timeout_sec: float = 1.0) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout_sec)
        return sock.connect_ex((host, port)) == 0


def _run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _ensure_docker_running() -> None:
    status = subprocess.run(["systemctl", "is-active", "--quiet", "docker"], check=False)
    if status.returncode == 0:
        return

    # Try non-interactive sudo first.
    started = subprocess.run(["sudo", "-n", "systemctl", "start", "docker"], check=False)
    if started.returncode != 0:
        raise RuntimeError(
            "Docker daemon is not running and auto-start failed. "
            "Run 'sudo systemctl start docker' once, then re-run the app."
        )


def ensure_riva_ready(cfg: Dict[str, Any]) -> None:
    riva_cfg = cfg.get("riva_startup", {})
    if not riva_cfg.get("enabled", True):
        return

    host = riva_cfg.get("host", "localhost")
    port = int(riva_cfg.get("port", 50051))
    timeout_sec = int(riva_cfg.get("ready_timeout_sec", 300))

    if _is_port_open(host, port):
        print(f"✓ Riva already reachable at {host}:{port}")
        return

    _ensure_docker_running()

    # Fast path: if containers exist but are stopped, start by name.
    container_names = riva_cfg.get("container_names", ["riva-speech", "riva-models-download", "riva-models-extract"])
    _run(["docker", "start", *container_names], check=False)

    start = time.time()
    while time.time() - start < 15:
        if _is_port_open(host, port):
            print(f"✓ Riva is up at {host}:{port}")
            return
        time.sleep(1)

    # Full startup via configured command.
    start_command = riva_cfg.get(
        "start_command",
        "cd /mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0 && bash riva_start.sh config.sh -s",
    )
    print("⏳ Starting Riva, please wait...")
    proc = subprocess.run(["bash", "-lc", start_command], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Failed to start Riva automatically.\n"
            f"Command: {start_command}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )

    start = time.time()
    while time.time() - start < timeout_sec:
        if _is_port_open(host, port):
            print(f"✓ Riva is ready at {host}:{port}")
            return
        time.sleep(2)

    raise TimeoutError(f"Riva did not become ready on {host}:{port} within {timeout_sec}s")
