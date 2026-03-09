# VNC Remote Display Setup

This document consolidates the VNC (Virtual Network Computing) setup for remote access and display configuration from the VNC_Setup repository.

## Overview

VNC allows headless operation of the Jetson Xavier with remote desktop access for debugging, monitoring, and development.

## Installation

### Server Setup (Jetson Xavier)

```bash
# Install VNC server (TigerVNC recommended for performance)
sudo apt-get update
sudo apt-get install tigervnc-server tigervnc-common

# Or alternative: TightVNC
sudo apt-get install tightvncserver

# Or alternative: x11vnc (simpler, uses existing X session)
sudo apt-get install x11vnc
```

### Create VNC User

```bash
# Create dedicated VNC user (optional)
sudo useradd -m -s /bin/bash vnc
sudo passwd vnc
```

### Initial VNC Setup

```bash
# Start VNC server (first time - creates config)
vncserver :1 -geometry 1280x720 -depth 24

# If prompted, set VNC password
# It will create ~/.vnc/xstartup and config files
```

### VNC Startup Configuration

Edit `~/.vnc/xstartup`:

```bash
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
```

Make executable:
```bash
chmod +x ~/.vnc/xstartup
```

### Start VNC Server on Boot

Create systemd service: `sudo nano /etc/systemd/system/vncserver@.service`

```ini
[Unit]
Description=Remote desktop service (VNC)
After=syslog.target network-online.target remote-fs.target nss-lookup.target
Wants=network-online.target

[Service]
Type=forking
User=%i
PAMName=login
PIDFile=/home/%i/.vnc/pid
ExecStartPre=/bin/sh -c '/usr/bin/vncserver -kill :%i > /dev/null 2>&1 || true'
ExecStart=/usr/bin/vncserver :%i -geometry 1280x720 -depth 24 -alwaysshared -localhost no
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vncserver@1.service
sudo systemctl start vncserver@1.service
```

Check status:
```bash
sudo systemctl status vncserver@1.service
```

## Client Setup (Windows/Mac/Linux)

### Option 1: VNC Viewer

Download from https://www.realvnc.com/en/connect/download/viewer/

**Quick Start:**
1. Open VNC Viewer
2. Enter: `jetson_ip:5901` (where :1 = port 5901)
3. Enter VNC password
4. Connect

### Option 2: TigerVNC Viewer

```bash
# Linux
sudo apt-get install tigervnc-viewer
vncviewer jetson_ip:5901

# macOS
brew install tigervnc-viewer
vncviewer jetson_ip:5901

# Windows
# Download from https://github.com/TigerVNC/tigervnc/releases
```

### Option 3: SSH Tunnel (Secure)

Forward VNC through SSH:

```bash
# On client machine
ssh -L 5901:localhost:5901 user@jetson_ip

# Then connect VNC to localhost:5901
vncviewer localhost:5901
```

## Network Configuration

### Find Jetson IP Address

```bash
# On Jetson
hostname -I
# or
ip addr | grep "inet " | grep -v "127.0.0.1"
```

### Firewall Rules (Linux)

```bash
# Allow VNC port
sudo ufw allow 5901/tcp

# Check rules
sudo ufw status
```

### Port Forwarding (If behind NAT)

For external access, configure port forwarding on router:
- External port: 5901 → Internal IP (Jetson):5901
- Protocol: TCP

### Security Recommendations

1. **Always use SSH tunnel for internet access**
2. **Set strong VNC password** (min 8 characters)
3. **Disable remote clipboard** if sensitive
4. **Use firewall** to restrict access by IP

## Display Configuration

### Desktop Environment Options

#### XFCE4 (Lightweight, Recommended)

```bash
sudo apt-get install xfce4 xfce4-goodies

# Configure in ~/.vnc/xstartup
startxfce4 &
```

#### LXDE (Even Lighter)

```bash
sudo apt-get install lxde

# Configure in ~/.vnc/xstartup
startlxde &
```

#### GNOME (Feature-rich, heavier)

```bash
sudo apt-get install gnome-desktop-environment

# Configure in ~/.vnc/xstartup
startgnome &
```

### Screen Resolution

Modify `vncserver` command:

```bash
# 1280×720 (recommended for 1Gbps)
vncserver :1 -geometry 1280x720 -depth 24

# 1920×1080 (higher bandwidth)
vncserver :1 -geometry 1920x1080 -depth 24

# 800×600 (low bandwidth)
vncserver :1 -geometry 800x600 -depth 24
```

### Color Depth

- `-depth 8`: 256 colors (fastest, 5MB/min at 1280×720)
- `-depth 16`: 65536 colors (medium, 10MB/min)
- `-depth 24`: 16M colors (best quality, 15MB/min)

## Optimization for Limited Bandwidth

### Connection Settings

VNC Viewer:
- Compression: 9 (max)
- Quality: Low or Medium
- Encoding: Tight or ZLib

### Jetson Configuration

```bash
# Reduce color depth for remote sessions
vncserver :1 -geometry 1024x768 -depth 8

# Or adjust on-the-fly with vncconfig
vncconfig -display :1 &
```

### Network Optimization

```bash
# Increase TCP buffer sizes
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
```

## Monitoring VNC

### Check Active Sessions

```bash
vncserver -list
# Output:
# TigerVNC server sessions:
# :1		Xvnc process ID: 1234
```

### Kill VNC Session

```bash
vncserver -kill :1
```

### View Logs

```bash
tail -f ~/.vnc/$(hostname):1.log
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Cannot connect | Check firewall, verify port 5901, restart vncserver |
| Slow performance | Reduce resolution/color depth, increase compression |
| Black screen | Check desktop environment, try `startx &` |
| Mouse/keyboard not responding | Update VNC viewer, check xstartup script |
| Out of memory | XFCE uses less RAM than GNOME |

### Test Connection

```bash
# From client, test connectivity
nc -zv jetson_ip 5901
# Output: succeeded if connection works
```

### Reset VNC Password

```bash
vncpasswd ~/.vnc/passwd

# Then restart server
vncserver -kill :1
vncserver :1 -geometry 1280x720 -depth 24
```

## Performance Benchmarks

(On Jetson Xavier with 1Gbps LAN)

| Resolution | Color Depth | Bandwidth | FPS |
|------------|-------------|-----------|-----|
| 800×600    | 8-bit       | 2-3 MB/s  | 30  |
| 1024×768   | 16-bit      | 5-8 MB/s  | 25  |
| 1280×720   | 24-bit      | 8-12 MB/s | 20  |
| 1920×1080  | 24-bit      | 15-20 MB/s | 15 |

## Advanced Configuration

### Multiple Displays

```bash
# Display :1 (port 5901)
vncserver :1 -geometry 1280x720

# Display :2 (port 5902)
vncserver :2 -geometry 1280x720
```

### Persistent Sessions

Use `screen` to maintain sessions:

```bash
# Create detachable screen session
screen -S humanoid

# Run application
python src/robot_sync_app/main.py --voice

# Detach: Ctrl+A then D
# Reattach: screen -r humanoid
```

## Integration with Humanoid System

### Monitor Voice Pipeline

```bash
# SSH to Jetson
ssh user@jetson_ip

# Open VNC viewer
# In remote desktop, open terminal
python examples/test_scripts/test_audio_devices.py
```

### Troubleshoot Hardware

VNC allows real-time observation of:
- Serial communication (via terminal)
- Audio levels
- Gesture execution
- LCD display output
- System resource usage

## References

- TigerVNC: https://tigervnc.org/
- RealVNC: https://www.realvnc.com/
- x11vnc: http://www.karlrunge.com/x11vnc/

See Also:
- [Hardware Setup](../robot_arm_servos/HARDWARE_SETUP.md)
- [Voice System](../chatbot_robot/VOICE_SETUP.md)
