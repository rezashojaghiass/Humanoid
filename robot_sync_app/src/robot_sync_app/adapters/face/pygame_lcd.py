import os
import glob
import time
import multiprocessing
from pathlib import Path
from PIL import Image
from robot_sync_app.ports.face_port import FacePort


def animation_process(queue, assets_path, width, height):
    """Separate process that handles all pygame display and animation."""
    try:
        import pygame
        
        # Configure SDL to use the HDMI display, not VNC
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        os.environ['DISPLAY'] = ':0'
        
        # Initialize pygame in THIS process (with its own GL context)
        pygame.init()
        pygame.mixer.quit()
        
        # Create display
        flags = pygame.FULLSCREEN | pygame.HWSURFACE
        screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Robot Face - Buzz Lightyear")
        pygame.mouse.set_visible(False)
        screen.fill((0, 0, 0))
        pygame.display.flip()
        
        # Load animations
        expressions = {}
        if os.path.exists(assets_path):
            for expr_dir in os.listdir(assets_path):
                expr_path = os.path.join(assets_path, expr_dir)
                if not os.path.isdir(expr_path):
                    continue
                
                frames = []
                frame_files = sorted(glob.glob(os.path.join(expr_path, "frame_*.png")))
                for frame_file in frame_files:
                    try:
                        img = Image.open(frame_file)
                        img = img.resize((width, height), Image.LANCZOS)
                        frames.append(img)
                    except:
                        pass
                
                if frames:
                    expressions[expr_dir] = frames
        
        print(f"[FACE_PROCESS] Loaded expressions: {list(expressions.keys())}", flush=True)
        
        # Animation loop
        running = True
        current_expr = None
        current_duration = 0.0
        
        while running:
            # Check for commands from main process
            try:
                cmd = queue.get(timeout=0.05)
                if cmd is None:  # Shutdown signal
                    running = False
                    break
                
                expr_name, duration = cmd
                current_expr = expr_name
                current_duration = duration
                
                if expr_name not in expressions:
                    print(f"[FACE_PROCESS] Expression '{expr_name}' not found", flush=True)
                    continue
                
                frames = expressions[expr_name]
                if duration <= 0:
                    duration = len(frames) * 0.05
                
                frame_delay = duration / len(frames)
                frame_delay = max(frame_delay, 0.01)
                
                print(f"[FACE_PROCESS] Animating: {expr_name} for {duration:.2f}s ({frame_delay*1000:.1f}ms per frame)", flush=True)
                
                # Play animation
                elapsed = 0.0
                frame_idx = 0
                
                while elapsed < duration and running:
                    # Check for new commands (non-blocking)
                    try:
                        new_cmd = queue.get_nowait()
                        if new_cmd is None:
                            running = False
                            break
                        expr_name, duration = new_cmd
                        break  # Start new animation
                    except:
                        pass  # No new command
                    
                    img = frames[frame_idx % len(frames)]
                    
                    try:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        surf = pygame.image.fromstring(img.tobytes(), img.size, "RGB")
                        screen.blit(surf, (0, 0))
                        pygame.display.flip()
                        
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                running = False
                    except:
                        pass
                    
                    time.sleep(frame_delay)
                    elapsed += frame_delay
                    frame_idx += 1
            except:
                pass
        
        pygame.quit()
        print("[FACE_PROCESS] Shutting down", flush=True)
    except Exception as e:
        print(f"[FACE_PROCESS] Error: {e}", flush=True)


class PyGameLCDFaceAdapter(FacePort):
    """Renders facial expressions using separate animation process.
    
    Uses multiprocessing so animation runs on separate CPU core in parallel with audio.
    """

    def __init__(self, width: int = 1280, height: int = 800, fullscreen: bool = True, 
                 assets_path: str = "/home/reza/cropped_animation_frames"):
        try:
            self.width = width
            self.height = height
            self.fullscreen = fullscreen
            self.assets_path = assets_path
            
            # Create queue for animation commands (main process -> animation process)
            self.animation_queue = multiprocessing.Queue()
            
            # Start animation process
            self.animation_proc = multiprocessing.Process(
                target=animation_process,
                args=(self.animation_queue, assets_path, width, height),
                daemon=True
            )
            self.animation_proc.start()
            
            print(f"[FACE] HDMI Display initialized: {width}x{height} (separate process)", flush=True)
            time.sleep(0.5)  # Give animation process time to initialize
        except Exception as e:
            print(f"[FACE] Failed to initialize: {e}")
            self.animation_proc = None
            self.animation_queue = None

    def set_expression(self, expression: str, audio_duration: float = 0.0) -> None:
        """Send animation command to animation process (non-blocking).
        
        Args:
            expression: Expression name
            audio_duration: Duration in seconds
        """
        print(f"[FACE] expression={expression}, looping for {audio_duration:.2f}s", flush=True)
        
        if not self.animation_queue:
            return
        
        # Map expression names
        expr_map = {
            "happy": "Smile",
            "smile": "Smile",
            "sad": "Sad",
            "surprise": "Surprise",
            "neutral": "Smile",
            "aa": "AA",
            "ee": "EE",
            "oo": "OO",
        }
        
        target_expr = expr_map.get(expression.lower(), expression)
        
        # Send command to animation process (non-blocking)
        try:
            self.animation_queue.put((target_expr, audio_duration), block=False)
        except:
            pass

    def cleanup(self):
        """Stop animation process."""
        if self.animation_queue:
            try:
                self.animation_queue.put(None)  # Shutdown signal
            except:
                pass
        
        if self.animation_proc and self.animation_proc.is_alive():
            self.animation_proc.join(timeout=2.0)
            self.animation_proc.terminate()
