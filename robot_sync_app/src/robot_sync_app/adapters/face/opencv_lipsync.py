import os
import glob
import time
import threading
import re
from pathlib import Path
import cv2
import numpy as np
from robot_sync_app.ports.face_port import FacePort


class OpenCVLipSyncFaceAdapter(FacePort):
    """
    Lip-sync animated face using vowel detection from speech text.
    Maps vowel sounds to mouth shapes for realistic lip-syncing.
    """

    def __init__(self, width: int = 1280, height: int = 800,
                 assets_path: str = "/home/reza/cropped_animation_frames_lipsync_3frames"):
        """
        Initialize lip-sync face display.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            assets_path: Path to lip-sync animation frames
        """
        try:
            os.environ['DISPLAY'] = ':0'
            self.width = width
            self.height = height
            self.assets_path = assets_path
            
            # Load all frames
            self.expressions = self._load_animations()
            self.neutral_frame = self._load_neutral_frame()
            
            # Vowel to expression mapping
            self.vowel_map = {
                'a': 'AA',
                'e': 'EE',
                'i': 'EE',
                'o': 'OO',
                'u': 'OO',
            }
            
            # Animation state and threading
            self.running = True
            self.current_frame = None
            self._animation_thread = None
            self._animation_lock = threading.Lock()
            self._pause_animation = False  # Pause flag for expression playback
            self._frame_queue = []  # Queue of frames to display
            self._speaking = False
            self._speech_text = ""
            
            # Create OpenCV window
            cv2.namedWindow('Robot Face', cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty('Robot Face', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
            # Register mouse callback to ignore mouse (prevents cursor visibility)
            cv2.setMouseCallback('Robot Face', lambda *args: None)
            
            # Hide mouse cursor (call multiple times to ensure it works)
            self._hide_cursor()
            time.sleep(0.2)
            self._hide_cursor()
            
            # Display initial neutral frame
            if self.neutral_frame is not None:
                cv2.imshow('Robot Face', self.neutral_frame)
                cv2.waitKey(1)
            
            # Hide cursor again after displaying window
            time.sleep(0.1)
            self._hide_cursor()
            
            # Start background animation thread
            self._animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self._animation_thread.start()
            
            print(f"[FACE] OpenCV Lip-Sync Display initialized: {width}x{height}")
            print(f"[FACE] Loaded expressions: {list(self.expressions.keys())}")
            
        except Exception as e:
            print(f"[FACE] Failed to initialize lip-sync display: {e}")
            self.expressions = {}
            self.neutral_frame = None

    def _hide_cursor(self) -> None:
        """Hide mouse cursor completely using display/X11 methods."""
        import subprocess
        import os
        
        # Method 1: Set blank cursor using X11 via xsetroot
        methods = [
            # xsetroot with /dev/null cursor
            lambda: subprocess.run(['xsetroot', '-cursor', '/dev/null', '/dev/null'],
                                 stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=1),
            # Move cursor far off-screen using xdotool
            lambda: subprocess.run(['xdotool', 'mousemove', '10000', '10000'],
                                 stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=1),
            # Use wmctrl to hide cursor decorations
            lambda: subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,above'],
                                 stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=1),
            # Try creating invisible cursor with ImageMagick if available
            lambda: self._create_invisible_cursor_image(),
        ]
        
        for method in methods:
            try:
                method()
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                continue
        
        # Also disable mouse in the display manager
        try:
            display = os.environ.get('DISPLAY', ':0')
            subprocess.run(f"DISPLAY={display} xset m 0 0", shell=True,
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=1)
        except Exception:
            pass
    
    def _create_invisible_cursor_image(self) -> None:
        """Create an invisible cursor image."""
        try:
            import subprocess
            # Create 1x1 transparent PNG cursor
            subprocess.run(['convert', '-size', '1x1', 'xc:transparent', 
                          '/tmp/invisible_cursor.png'],
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=2)
            # Set it as cursor
            subprocess.run(['xsetroot', '-cursor_name', 'none'],
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=1)
        except Exception:
            pass

    def _load_animations(self) -> dict:
        """Load all animation frame sequences."""
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
                    frame = cv2.imread(frame_file)
                    if frame is not None:
                        # Resize if needed
                        if frame.shape != (self.height, self.width, 3):
                            frame = cv2.resize(frame, (self.width, self.height))
                        frames.append(frame)
                except Exception as e:
                    print(f"[FACE] Error loading frame {frame_file}: {e}")
            
            if frames:
                expressions[expr_dir] = frames
                print(f"[FACE] Loaded '{expr_dir}': {len(frames)} frames")
        
        return expressions

    def _load_neutral_frame(self):
        """Load the neutral/smile frame."""
        neutral_path = os.path.join(self.assets_path, "neutral.png")
        if os.path.exists(neutral_path):
            frame = cv2.imread(neutral_path)
            if frame is not None:
                if frame.shape != (self.height, self.width, 3):
                    frame = cv2.resize(frame, (self.width, self.height))
                print("[FACE] Loaded neutral frame")
                return frame
        return None

    def _detect_vowels(self, text: str) -> list:
        """Detect vowels in text and return frame sequence."""
        vowels = []
        vowel_pattern = r'[aeiouAEIOU]'
        
        for char in text.lower():
            if char in self.vowel_map:
                expr = self.vowel_map[char]
                if expr in self.expressions and self.expressions[expr]:
                    # Get a random frame from the vowel expression for variety
                    frames = self.expressions[expr]
                    # Use frames 1-5 (skip first neutral frame)
                    frame_idx = min(2, len(frames) - 1)
                    vowels.append(frames[frame_idx])
            else:
                # Consonant or non-speech: show neutral
                if self.neutral_frame is not None:
                    vowels.append(self.neutral_frame)
        
        return vowels

    def set_expression(self, expression: str, duration: float = 0.0) -> None:
        """
        Set facial expression (compatibility method).
        In lip-sync mode, this is overridden by speech-based animation.
        """
        # In lip-sync mode, expressions are set by speech content
        pass

    def speak(self, text: str, duration: float = 0.0) -> None:
        """
        Start lip-sync animation based on speech text.
        
        Args:
            text: The text being spoken
            duration: Duration of speech in seconds
        """
        with self._animation_lock:
            self._speech_text = text
            self._speaking = True
        
        # Generate frame sequence from text
        frame_sequence = self._detect_vowels(text)
        
        if not frame_sequence:
            frame_sequence = [self.neutral_frame] if self.neutral_frame is not None else []
        
        # Calculate frame timing based on speech duration
        if duration > 0 and frame_sequence:
            frame_time = duration / len(frame_sequence)
        else:
            frame_time = 0.05  # 50ms per frame default
        
        # Add frames to queue with timing
        with self._animation_lock:
            self._frame_queue = [(frame, frame_time) for frame in frame_sequence]

    def speak_done(self) -> None:
        """Called when speaking is finished - return to neutral."""
        with self._animation_lock:
            self._speaking = False
            self._frame_queue = []

    def _animation_loop(self) -> None:
        """Background thread animation loop."""
        while self.running:
            try:
                # Skip if paused for expression playback
                if self._pause_animation:
                    time.sleep(0.01)
                    continue
                
                with self._animation_lock:
                    if self._frame_queue:
                        frame, frame_time = self._frame_queue.pop(0)
                        self.current_frame = frame
                    else:
                        # Return to neutral when no more frames
                        if not self._speaking and self.neutral_frame is not None:
                            self.current_frame = self.neutral_frame
                        frame = self.current_frame
                        frame_time = 0.033  # 30fps
                
                if frame is not None:
                    try:
                        cv2.imshow('Robot Face', frame)
                        cv2.waitKey(max(1, int(frame_time * 1000)))
                    except cv2.error:
                        time.sleep(frame_time)
                else:
                    time.sleep(0.033)
            
            except Exception as e:
                print(f"[FACE] Animation error: {e}")
                time.sleep(0.1)

    def send_command(self, name: str, params: dict) -> None:
        """Compatibility method for orchestrator commands."""
        if name == "speak":
            text = params.get("text", "")
            duration = params.get("duration", 0.0)
            self.speak(text, duration)
        elif name == "speak_done":
            self.speak_done()

    def cleanup(self) -> None:
        """Cleanup display resources."""
        self.running = False
        if self._animation_thread:
            self._animation_thread.join(timeout=2)
        try:
            cv2.destroyAllWindows()
            print("[FACE] Lip-sync display cleaned up")
        except Exception as e:
            print(f"[FACE] Cleanup error: {e}")

    def play_expression_sequence(self, expression_name: str, frame_indices: list, duration: float = 2.0) -> None:
        """
        Play a sequence of frames from an expression.
        Used for facial expression mode animations.
        
        Args:
            expression_name: Name of expression (e.g., "Smile", "Sad")
            frame_indices: List of frame numbers to play (1-based)
            duration: Total time in seconds to play the sequence
        """
        # Load from the FULL frame set (30 frames per expression)
        full_assets_path = "/home/reza/cropped_animation_frames"
        expr_path = Path(full_assets_path) / expression_name
        
        if not expr_path.exists():
            print(f"[FACE] Expression not found: {expr_path}")
            return
        
        # Get all PNG files sorted numerically by frame number
        all_files = glob.glob(os.path.join(str(expr_path), "*.png"))
        
        # Sort by frame number extracted from filename (e.g., frame_0001.png)
        def get_frame_number(filepath):
            try:
                filename = os.path.basename(filepath)
                # Extract number from frame_XXXX.png format
                import re
                match = re.search(r'frame_(\d+)', filename)
                if match:
                    return int(match.group(1))
            except:
                pass
            return 0
        
        all_files = sorted(all_files, key=get_frame_number)
        
        if not all_files:
            print(f"[FACE] No frames found in {expr_path}")
            return
        
        # Load and prepare frames
        sequence = []
        for frame_idx in frame_indices:
            # Frame indices are 1-based, convert to 0-based file index
            file_idx = frame_idx - 1
            if 0 <= file_idx < len(all_files):
                try:
                    frame = cv2.imread(all_files[file_idx])
                    if frame is not None:
                        frame = cv2.resize(frame, (self.width, self.height))
                        sequence.append(frame)
                        print(f"[FACE] Loaded {expression_name} frame {frame_idx}")
                except Exception as e:
                    print(f"[FACE] Error loading frame {frame_idx}: {e}")
            else:
                print(f"[FACE] Frame index {frame_idx} out of range (max: {len(all_files)})")
        
        if not sequence:
            print(f"[FACE] No valid frames loaded for {expression_name}")
            return
        
        print(f"[FACE] Playing {expression_name} sequence ({len(sequence)} frames, {duration:.1f}s)")
        
        # Pause background animation thread - take ownership of window
        self._pause_animation = True
        time.sleep(0.1)  # Let animation loop pause
        
        # Display frames directly on main window with timing
        frame_duration = duration / len(sequence) if sequence else 0.1
        for i, frame in enumerate(sequence):
            try:
                # Display frame on existing 'Robot Face' window
                cv2.imshow('Robot Face', frame)
                cv2.waitKey(int(frame_duration * 1000))  # Display for frame_duration milliseconds
                print(f"[FACE] Displayed {expression_name} frame {i+1}/{len(sequence)}")
            except Exception as e:
                print(f"[FACE] Error displaying frame: {e}")
        
        # Return to neutral after sequence
        try:
            cv2.imshow('Robot Face', self.neutral_frame)
            cv2.waitKey(100)
        except Exception as e:
            print(f"[FACE] Error displaying neutral frame: {e}")
        
        # Resume background animation thread
        self._pause_animation = False
        
        print(f"[FACE] {expression_name} sequence complete")



