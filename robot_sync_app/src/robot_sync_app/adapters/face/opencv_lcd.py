import os
import glob
import time
import threading
from pathlib import Path
import cv2
import numpy as np
from robot_sync_app.ports.face_port import FacePort


class OpenCVLCDFaceAdapter(FacePort):
    """
    Renders animated facial expressions using OpenCV (CPU-based, thread-safe).
    Works with:
    - Physical HDMI monitor attached to Xavier
    - Animated frame sequences (30 frames per expression)
    - Background animation thread (thread-safe, no GL context issues)
    - Simple and reliable
    """

    def __init__(self, width: int = 1280, height: int = 800,
                 assets_path: str = "/home/reza/cropped_animation_frames"):
        """
        Initialize the HDMI face display with animated expressions using OpenCV.
        
        Args:
            width: Display width in pixels (default 1280 for 8" HDMI monitor)
            height: Display height in pixels (default 800 for 8" HDMI monitor)
            assets_path: Path to facial animation assets folder
        """
        try:
            # Configure display
            os.environ['DISPLAY'] = ':0'  # Direct X11 display, not VNC
            
            self.width = width
            self.height = height
            self.assets_path = assets_path
            
            # Load animation frames for each expression
            self.expressions = self._load_animations()
            
            # Animation state and threading
            self.running = True
            self.current_expression = "Smile"
            self.current_frame = 0
            self._animation_thread = None
            self._animation_lock = threading.Lock()
            self._new_animation_event = threading.Event()
            self._target_expression = None
            self._target_duration = 0.0
            
            # Create OpenCV window (thread-safe)
            cv2.namedWindow('Robot Face', cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty('Robot Face', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
            # Hide mouse cursor when displaying images
            try:
                import subprocess
                subprocess.run(['xdotool', 'mousemove', '640', '400'], check=False, stderr=subprocess.DEVNULL)
            except Exception:
                pass  # xdotool not available, skip
            
            # Display initial black frame
            black_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            cv2.imshow('Robot Face', black_frame)
            cv2.waitKey(1)
            
            # Start background animation thread
            self._animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self._animation_thread.start()
            
            print(f"[FACE] OpenCV HDMI Display initialized: {width}x{height}")
            print(f"[FACE] Loaded expressions: {list(self.expressions.keys())}")
            
        except Exception as e:
            print(f"[FACE] Failed to initialize OpenCV display: {e}")
            self.expressions = {}

    def _load_animations(self) -> dict:
        """Load all animation frame sequences from assets folder."""
        expressions = {}
        
        if not os.path.exists(self.assets_path):
            print(f"[FACE] Assets path not found: {self.assets_path}")
            return expressions
        
        for expr_dir in os.listdir(self.assets_path):
            expr_path = os.path.join(self.assets_path, expr_dir)
            
            if not os.path.isdir(expr_path):
                continue
            
            frames = []
            frame_files = sorted(glob.glob(os.path.join(expr_path, "*.png")))
            
            for frame_file in frame_files:
                try:
                    # Load image with OpenCV (BGR format)
                    frame = cv2.imread(frame_file)
                    if frame is not None:
                        # Resize to display dimensions
                        frame = cv2.resize(frame, (self.width, self.height))
                        frames.append(frame)
                except Exception as e:
                    print(f"[FACE] Error loading frame {frame_file}: {e}")
            
            if frames:
                expressions[expr_dir] = frames
                print(f"[FACE] Loaded '{expr_dir}': {len(frames)} frames")
        
        return expressions

    def set_expression(self, expression: str, duration: float = 0.0) -> None:
        """
        Set facial expression to display (with optional duration for looping).
        
        Args:
            expression: Name of expression (e.g., 'happy', 'sad', 'smile')
            duration: How long to loop the animation (0 = single play)
        """
        with self._animation_lock:
            if expression not in self.expressions:
                print(f"[FACE] Expression '{expression}' not found")
                return
            
            self._target_expression = expression
            self._target_duration = duration
            self.current_frame = 0
            self._new_animation_event.set()

    def _animation_loop(self) -> None:
        """Background thread animation loop - thread-safe OpenCV rendering."""
        while self.running:
            try:
                # Wait for animation request
                self._new_animation_event.wait(timeout=0.1)
                self._new_animation_event.clear()
                
                with self._animation_lock:
                    if not self._target_expression or self._target_expression not in self.expressions:
                        continue
                    
                    expression = self._target_expression
                    duration = self._target_duration
                    frames = self.expressions[expression]
                
                if not frames:
                    continue
                
                # Calculate frame timing
                num_frames = len(frames)
                if duration > 0:
                    frame_time = duration / num_frames
                else:
                    frame_time = 0.033  # ~30fps default
                
                print(f"[FACE] Animation: '{expression}' {num_frames} frames over {duration:.2f}s ({frame_time*1000:.1f}ms per frame)")
                
                # Play animation loop
                frame_index = 0
                loop_start = time.time()
                
                while self.running:
                    with self._animation_lock:
                        # Check if animation changed
                        if self._target_expression != expression:
                            break
                    
                    # Display frame (with graceful fallback if no display)
                    frame = frames[frame_index % num_frames]
                    try:
                        cv2.imshow('Robot Face', frame)
                        cv2.waitKey(max(1, int(frame_time * 1000)))
                    except cv2.error:
                        # No display available, just sleep to maintain timing
                        time.sleep(frame_time)
                    
                    frame_index += 1
                    
                    # Stop looping if duration expired and not repeating
                    if duration > 0:
                        elapsed = time.time() - loop_start
                        if elapsed >= duration:
                            break
            
            except Exception as e:
                print(f"[FACE] Animation error: {e}")
                time.sleep(0.1)

    def send_command(self, name: str, params: dict) -> None:
        """Compatibility method for orchestrator commands."""
        pass

    def cleanup(self) -> None:
        """Cleanup display resources."""
        self.running = False
        if self._animation_thread:
            self._animation_thread.join(timeout=2)
        try:
            cv2.destroyAllWindows()
            print("[FACE] Display cleaned up")
        except Exception as e:
            print(f"[FACE] Cleanup error: {e}")

    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()
