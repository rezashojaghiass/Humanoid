# 🧭 Xavier Component Map (What Lives Where)

This file is the source of truth for your current Xavier paths.

Use this first to avoid re-installing or re-downloading components that already exist.

---

## 1) Core project paths

- Humanoid repo: `/home/reza/RobotArmServos/Humanoid`
- Main app code: `/home/reza/RobotArmServos/Humanoid/robot_sync_app`
- Runtime config: `/home/reza/RobotArmServos/Humanoid/robot_sync_app/config/config.yaml`

---

## 2) Voice/Riva paths (NVMe)

- ChatBotRobot workspace: `/mnt/nvme/adrian/ChatBotRobot`
- Start script used by docs: `/mnt/nvme/adrian/ChatBotRobot/scripts/start_riva.sh`

Riva quickstart base on your Xavier:

- `/mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0`

Riva model repository (already present):

- `/mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0/model_repository`

Riva config file that defines model location:

- `/mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0/config.sh`
  - `riva_model_loc="$(pwd)/model_repository"` on tegra

---

## 3) Docker assets (already cached locally)

Detected local images:

- `nvcr.io/nvidia/riva/riva-speech:2.24.0-l4t-aarch64`
- `nvcr.io/nvidia/riva/riva-speech:2.14.0-l4t-aarch64`

This means you generally **do not need** to pull Riva again unless you intentionally upgrade versions.

---

## 4) Credentials and host-level files

- AWS credentials: `/home/reza/.aws/credentials`

---

## 5) Device endpoints used by app

- Riva gRPC endpoint: `localhost:50051`
- Riva HTTP endpoint: `localhost:50000`
- Finger Arduino (expected): `/dev/ttyACM0`
- Motor Arduino (expected): `/dev/ttyUSB0`

---

## 6) Existence-first checks (run before any install/pull)

```bash
# Paths
for p in \
  /home/reza/RobotArmServos/Humanoid \
  /mnt/nvme/adrian/ChatBotRobot/scripts/start_riva.sh \
  /mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0 \
  /mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0/model_repository \
  /home/reza/.aws/credentials
do
  [ -e "$p" ] && echo "[OK] $p" || echo "[MISSING] $p"
done

# Riva images (skip docker pull if present)
docker images --format '{{.Repository}}:{{.Tag}}' | grep -Ei 'riva-speech|nvidia/riva'

# Riva containers
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'riva|speech' || true
```

---

## 7) Operational rule

- If path/image exists → **reuse it**
- If missing → install/download only that missing component
