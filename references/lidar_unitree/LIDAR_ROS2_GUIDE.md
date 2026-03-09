# LiDAR and ROS2 Integration (Future)

This document describes the planned integration of Unitree LiDAR for autonomous navigation and perception.

## Overview

LiDAR provides 3D point cloud data for:
- SLAM (Simultaneous Localization and Mapping)
- Obstacle avoidance
- Autonomous navigation
- Environmental mapping

**Status:** Currently in planning phase - not yet integrated

## Hardware Specifications

### Unitree LiDAR

**Model:** Unitree M1 (typical specification)

| Specification | Value |
|---|---|
| Wavelength | 905nm |
| Range | 0.15m - 25m |
| Resolution | 0.2° |
| Point cloud rate | 10 Hz (100,000 points/sec) |
| FOV | 360° horizontal, ±25° vertical |
| Baud Rate | 2,000,000 bps |
| Interface | Serial (RS-422) |
| Power | 5V @ 500mA |

## Connection Setup

### Serial Interface

**Port:** `/dev/ttyUSB1` (or first available USB serial)  
**Baud Rate:** 2,000,000 (very high speed!)  
**Protocol:** Binary packet format

### Wiring

```
LiDAR → Arduino/USB
TX → RX (inverted logic may be needed)
RX → TX
GND → GND
5V → 5V
```

### Cable Configuration

```bash
# Identify LiDAR USB device
lsusb | grep -i "unitree\|lidar"

# Check serial port assignment
ls -l /dev/ttyUSB*

# Test connection (careful - high baud rate!)
# Use screen with caution
```

## ROS2 Integration

### Installation

ROS2 Humble (Ubuntu 22.04 compatible):

```bash
# Install ROS2
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | \
  sudo apt-key add -

sudo apt update
sudo apt install ros-humble-desktop

# Source ROS2
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Workspace Setup

```bash
# Create ROS2 workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws

# Clone Unitree LiDAR driver
git clone https://github.com/unitreerobotics/lidar_driver.git src/lidar_driver

# Build
colcon build --symlink-install

# Source workspace
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/ros2_ws/install/setup.bash
```

## LiDAR Point Cloud Streaming

### Standard ROS2 Topics

**Point Cloud Topic:** `/lidar/points`

```python
import rclpy
from sensor_msgs.msg import PointCloud2

def callback(msg):
    # Process point cloud
    # msg.data contains point coordinates
    # msg.height, msg.width = point dimensions
    print(f"Received {len(msg.data)} points")

node = rclpy.create_node('lidar_listener')
sub = node.create_subscription(PointCloud2, '/lidar/points', callback, 10)
rclpy.spin(node)
```

### Point Cloud Format

Each point contains:
- X, Y, Z coordinates (meters)
- Intensity (return strength)
- Timestamp

Typical point cloud:
- 100,000 points per cycle
- 10 Hz refresh = 1,000,000 pts/sec
- Data rate: ~40 MB/sec (raw format)

## SLAM Implementation

### ORB-SLAM3 (Recommended)

For robust visual+LiDAR SLAM:

```bash
# Install ORB-SLAM3
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
cd ORB_SLAM3
chmod +x build.sh
./build.sh

# ROS2 wrapper
git clone https://github.com/thien94/orb_slam3_ros2_wrapper.git
```

### LeGO-LOAM (Lighter)

For LiDAR-only SLAM:

```bash
git clone https://github.com/RoboSense-LiDAR/lego_loam_ros2.git
colcon build
```

## Obstacle Avoidance

### Basic Implementation

```python
import numpy as np
from sensor_msgs.msg import PointCloud2

class ObstacleDetector:
    def __init__(self):
        self.cloud = None
        self.obstacle_distance = 1.0  # meters
    
    def process_cloud(self, cloud_msg):
        # Convert point cloud to numpy array
        points = self.cloud_to_array(cloud_msg)
        
        # Find closest obstacles
        distances = np.linalg.norm(points, axis=1)
        min_distance = np.min(distances[distances > 0])
        
        if min_distance < self.obstacle_distance:
            # Stop forward motion
            self.stop_motion()
    
    def cloud_to_array(self, msg):
        # Extract X, Y, Z from point cloud
        # Return numpy array [N, 3]
        pass
```

## Mapping

### Map Visualization

```bash
# Terminal 1: Start ROS2 nodes
ros2 launch lego_loam lego_loam.launch.py

# Terminal 2: Open RViz for visualization
rviz2

# Add displays:
# - PointCloud2 topic: /lidar/points
# - Map topic: /map (if using SLAM)
```

### Map Storage

Saved maps are typically `.pcd` (Point Cloud Data) format:

```bash
# Save map
ros2 service call /save_map std_srvs/srv/Empty

# Load map
ros2 service call /load_map std_srvs/srv/Empty
```

## Integration with Humanoid Gestures

Synchronize LiDAR perception with humanoid responses:

```python
class PerceptionGestureSync:
    def __init__(self, llm, gesture_controller):
        self.llm = llm
        self.gestures = gesture_controller
        self.cloud = None
    
    def on_obstacle_detected(self, obstacle_location):
        # Analyze obstacle with LLM
        response = self.llm.process("Object detected at " + obstacle_location)
        
        # Gesture based on response
        if "avoid" in response.lower():
            self.gestures.execute("point", hand="right")
        elif "confirm" in response.lower():
            self.gestures.execute("thumbs_up", hand="right")
```

## Performance Optimization

### Point Cloud Downsampling

Reduce data size by 50-75%:

```python
import open3d as o3d

def downsample_cloud(points, voxel_size=0.05):
    """Reduce point density"""
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    return pcd.voxel_down_sample(voxel_size)
```

### CPU Usage

- Full point cloud (100k pts): ~30-40% CPU on Xavier
- Downsampled: ~10-15% CPU
- Recommend max 50k points/cycle for real-time

### Latency

- LiDAR capture: ~100ms (at 10 Hz)
- SLAM processing: ~200-300ms
- Gesture execution: ~500-1000ms
- **Total end-to-end latency:** ~1-2 seconds

## Troubleshooting

| Problem | Solution |
|---------|----------|
| High baud rate errors | Check USB cable quality, try lower baud if available |
| ROS2 not detecting device | Verify `/dev/ttyUSB1` exists, check udev rules |
| Point cloud has gaps | Normal - LiDAR has blind spots, use filtering |
| SLAM diverging | Reduce movement speed, use feature-rich environment |
| High CPU usage | Downsample points, reduce SLAM frequency |

### Debug Commands

```bash
# List active ROS2 nodes
ros2 node list

# Check topics
ros2 topic list
ros2 topic echo /lidar/points

# Monitor CPU usage
top -p $(pgrep -f "ros2 launch")
```

## Future Enhancements

- [ ] SLAM-based autonomous navigation
- [ ] Dynamic obstacle tracking
- [ ] Multi-LiDAR fusion (depth camera)
- [ ] Loop closure detection
- [ ] Uncertainty-aware path planning

## References

- Unitree LiDAR: https://www.unitree.com/
- ROS2 Documentation: https://docs.ros.org/en/humble/
- ORB-SLAM3: https://github.com/UZ-SLAMLab/ORB_SLAM3
- LeGO-LOAM: https://github.com/RoboSense-LiDAR/lego_loam_ros2
- Open3D: http://www.open3d.org/

See Also:
- [Voice System](../chatbot_robot/VOICE_SETUP.md)
- [Hardware Setup](../robot_arm_servos/HARDWARE_SETUP.md)
- [Configuration](../../examples/configurations/CONFIGURATIONS.md)
