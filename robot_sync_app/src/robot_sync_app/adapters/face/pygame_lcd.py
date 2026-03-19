import os
import glob
import threading
import time
from pathlib import Path
from PIL import Image
from robot_sync_app.ports.face_port import FacePort


class PyGameLCDFaceAdapter(FacePort):
    """Renders animated facial expressions from Buzz Lightyear animation frames to HDMI display.
    
    Works with:
    - Physical HDMI monitor attached to Xavier
    - Animated frame sequences (30 frames per expression)
    - Independent from VNC/headless connections
    - Background threading for parallel animation during speech
    """

    def __init__(self, width: int = 1280, height: int = 800, fullscreen: bool = True, 
                 assets_path: str = "/home/reza/cropped_animation_frames"):
        """
        Initialize the HDMI face display with animated expressions.
        
        Args:
            width: Display width in pixels (default 1280 for 8" HDMI monitor)
            height: Display height in pixels (default 800 for 8" HDMI monitor)
            fullscreen: Whether to run fullscreen on HDMI display
            assets_path: Path to facial animation assets folder
        """
        try:
            import pygame
            self.pygame = pygame
            
            # Configure SDL to use the HDMI display, not VNC
            os.environ['SDL_VIDEODRIVER'] = 'x11'
            os.environ['DISPLAY'] = ':0'  # Direct X11 display, not VNC
            
            # Initialize pygame without audio mixer to avoid conflicts with PyAudio
            pygame.init()
            pygame.mixer.quit()  # Disable mixer so PyAudio can use the audio device
            
            self.width = width
            self.height = height
            self.fullscreen = fullscreen
            self.assets_path = assets_path
            
            # Create display on HDMI monitor in fullscreen
            # Use FULLSCREEN | pygame.HWSURFACE to bypass window manager
            flags = pygame.FULLSCREEN | pygame.HWSURFACE
            self.screen = pygame.display.set_mode((width, height), flags)
            pygame.display.set_caption("Robot Face - Buzz Lightyear")
            
            # Hide mouse cursor for fullscreen display
            pygame.mouse.set_visible(False)
            
            # Fill with black initially
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
            
            # Load animation frames for each expression
            self.expressions = self._load_animations()
            
            # Animation state and threading
            self.running = True
            self.current_expression = "Smile"
            self.current_frame = 0
            self._animation_thread = None
            self._animation_lock = threading.Lock()
            self._stop_animation = threading.Event()
            self._target_expression = None
            
            print(f"[FACE] HDMI Display initialized: {width}x{height}")
            print(f"[FACE] Loaded expressions: {list(self.expressions.keys())}")
        except ImportError:
            print("[FACE] PyGame not available. Install with: pip install pygame")
            self.pygame = None
            self.screen = None
            self.expressions = {}
        except Exception as e:
            print(f"[FACE] Failed to initialize HDMI display: {e}")
            self.pygame = None
            self.screen = None
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
            
            # Load all frames for this expression
            frames = []
            frame_files = sorted(glob.glob(os.path.join(expr_path, "frame_*.png")))
            
            for frame_file in frame_files:
                try:
                    img = Image.open(frame_file)
                    
                    # Frames are already in correct orientation (cropped)
                    # No rotation needed
                    
                    # Resize to display size if needed
                    img = img.resize((self.width, self.height), Image.LANCZOS)
                    frames.append(img)
                except Exception as e:
                    print(f"[FACE] Failed to load {frame_file}: {e}")
            
            if frames:
                expressions[expr_dir] = frames
                print(f"[FACE] Loaded '{expr_dir}': {len(frames)} frames (no rotation needed)")
        
        return expressions

    def _animate_background(self) -> None:
        """Background thread that continuously loops animation frames."""
        frame_delay = 0.033  # ~30fps (33ms per frame)
        
        while self.running:
            # Wait for target expression to be set
            while self._target_expression is None and self.running:
                time.sleep(0.01)
            
            if not self.running:
                break
            
            with self._animation_lock:
                target = self._target_expression
                if target not in self.expressions:
                    continue
                frames = self.expressions[target]
            
            # Loop animation frames continuously until stopped
            frame_idx = 0
            while not self._stop_animation.is_set() and self.running:
                if self._target_expression != target:
                    # Expression changed, break to get new target
                    break
                
                with self._animation_lock:
                    img = frames[frame_idx % len(frames)]
                
                try:
                    # Ensure image is in RGB mode
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Convert PIL image to pygame surface
                    surf = self.pygame.image.fromstring(img.tobytes(), img.size, "RGB")
                    
                    # Display frame on HDMI monitor
                    self.screen.blit(surf, (0, 0))
                    self.pygame.display.flip()
                    
                    # Handle pygame events (prevent window from freezing)
                    try:
                        for event in self.pygame.event.get():
                            if event.type == self.pygame.QUIT:
                                self.running = False
                    except:
                        pass
                    
                    frame_idx += 1
                    time.sleep(frame_delay)
                except Exception as e:
                    print(f"[FACE] Animation error: {e}")
                    break

    def set_expression(self, expression: str) -> None:
        """Start displaying the specified animated expression on HDMI monitor in background.
        
        Args:
            expression: Expression name (e.g., 'Smile', 'Sad', 'Surprise', 'AA', 'EE', 'OO')
        """
        print(f"[FACE] expression={expression}")
        
        if not self.pygame or not self.screen or not self.expressions:
            return
        
        # Map expression names to available animations
        expr_map = {
            "happy": "Smile",
            "smile": "Smile",
            "sad": "Sad",
            "surprise": "Surprise",
            "neutral": "Smile",  # Default to smile if no match
            "aa": "AA",
            "ee": "EE",
            "oo": "OO",
        }
        
        # Get the correct folder name
        target_expr = expr_map.get(expression.lower(), expression)
        
        # Use target expression if available, otherwise use first available
        if target_expr not in self.expressions:
            available = list(self.expressions.keys())
            if not available:
                print(f"[FACE] No expressions loaded!")
                return
            target_expr = available[0]
            print(f"[FACE] Expression '{expression}' not found, using '{target_expr}'")
        
        # Start background animation thread if not already running
        if self._animation_thread is None or not self._animation_thread.is_alive():
            self._animation_thread = threading.Thread(target=self._animate_background, daemon=True)
            self._animation_thread.start()
        
        # Stop current animation and set new target
        self._stop_animation.set()
        time.sleep(0.05)  # Brief pause to let old animation finish
        self._stop_animation.clear()
        
        with self._animation_lock:
            self._target_expression = target_expr

    def cleanup(self):
        """Clean up pygame resources."""
        self.running = False
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)
        if self.pygame:
            self.pygame.quit()
