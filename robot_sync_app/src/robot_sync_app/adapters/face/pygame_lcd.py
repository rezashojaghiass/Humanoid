import os
import glob
import time
import sys
import multiprocessing
from pathlib import Path
from PIL import Image
from robot_sync_app.ports.face_port import FacePort


def animation_process(queue, assets_path, width, height, log_queue):
    """Separate process that handles all pygame display and animation."""
    screen = None
    try:
        import pygame
        
        # Configure SDL to use the HDMI display, not VNC
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        os.environ['DISPLAY'] = ':0'
        
        # Initialize pygame in THIS process (with its own GL context)
        pygame.init()
        pygame.mixer.quit()
        
        # Create display - NOT in fullscreen initially to allow proper cleanup
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Robot Face - Buzz Lightyear")
        pygame.mouse.set_visible(False)
        screen.fill((0, 0, 0))
        pygame.display.flip()
        
        # Try to set fullscreen after creation
        try:
            pygame.display.toggle_fullscreen()
        except:
            pass
        
        log_queue.put("[FACE_PROCESS] PyGame initialized on separate process")
        
        # Pre-load and convert animations to pygame surfaces (more efficient)
        expressions = {}
        if os.path.exists(assets_path):
            for expr_dir in os.listdir(assets_path):
                expr_path = os.path.join(assets_path, expr_dir)
                if not os.path.isdir(expr_path):
                    continue
                
                surfaces = []
                frame_files = sorted(glob.glob(os.path.join(expr_path, "frame_*.png")))
                for frame_file in frame_files:
                    try:
                        # Load PIL image, convert to RGB, resize
                        img = Image.open(frame_file)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img = img.resize((width, height), Image.LANCZOS)
                        
                        # Convert to pygame surface immediately and close PIL image
                        surf = pygame.image.fromstring(img.tobytes(), img.size, "RGB")
                        surfaces.append(surf)
                        img.close()  # Explicitly close PIL image to free memory
                    except Exception as e:
                        pass
                
                if surfaces:
                    expressions[expr_dir] = surfaces
        
        log_queue.put(f"[FACE_PROCESS] Loaded expressions: {list(expressions.keys())}")
        
        # Animation loop
        running = True
        
        while running:
            # Check for commands from main process
            try:
                cmd = queue.get(timeout=0.1)
                if cmd is None:  # Shutdown signal
                    log_queue.put("[FACE_PROCESS] Received shutdown signal")
                    running = False
                    break
                
                expr_name, duration = cmd
                
                if expr_name not in expressions:
                    log_queue.put(f"[FACE_PROCESS] Expression '{expr_name}' not found")
                    continue
                
                surfaces = expressions[expr_name]
                if duration <= 0:
                    duration = len(surfaces) * 0.05
                
                frame_delay = duration / len(surfaces)
                frame_delay = max(frame_delay, 0.01)
                
                log_queue.put(f"[FACE_PROCESS] Animating: {expr_name} for {duration:.2f}s ({frame_delay*1000:.1f}ms per frame)")
                
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
                        log_queue.put(f"[FACE_PROCESS] Interrupted - new animation requested")
                        break  # Start new animation
                    except:
                        pass  # No new command
                    
                    surf = surfaces[frame_idx % len(surfaces)]
                    
                    try:
                        screen.blit(surf, (0, 0))
                        pygame.display.flip()
                        
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                running = False
                    except Exception as e:
                        log_queue.put(f"[FACE_PROCESS] Render error: {e}")
                        pass
                    
                    time.sleep(frame_delay)
                    elapsed += frame_delay
                    frame_idx += 1
            except Exception as e:
                pass
        
        # Cleanup sequence
        log_queue.put("[FACE_PROCESS] Starting cleanup...")
        
        # Step 1: Clear display with black screen
        if screen:
            try:
                screen.fill((0, 0, 0))
                pygame.display.flip()
                time.sleep(0.2)
            except:
                pass
        
        # Step 2: Exit fullscreen mode
        log_queue.put("[FACE_PROCESS] Exiting fullscreen...")
        try:
            pygame.display.toggle_fullscreen()
            time.sleep(0.3)
        except:
            pass
        
        # Step 3: Clear again and flip
        if screen:
            try:
                screen.fill((0, 0, 0))
                pygame.display.flip()
                time.sleep(0.1)
            except:
                pass
        
        # Step 4: Quit pygame
        log_queue.put("[FACE_PROCESS] Quitting pygame...")
        pygame.quit()
        time.sleep(0.2)
        
        log_queue.put("[FACE_PROCESS] PyGame quit - shutting down")
        
    except Exception as e:
        log_queue.put(f"[FACE_PROCESS] Error: {e}")
    finally:
        # Final cleanup
        try:
            if screen:
                screen = None
        except:
            pass
        log_queue.put(None)  # Signal that process is done


class PyGameLCDFaceAdapter(FacePort):
    """Renders facial expressions using separate animation process.
    
    Uses multiprocessing so animation runs on separate CPU core in parallel with audio.
    Logs are piped back to main process. Properly cleans up display and returns to desktop.
    """

    def __init__(self, width: int = 1280, height: int = 800, fullscreen: bool = True, 
                 assets_path: str = "/home/reza/cropped_animation_frames"):
        try:
            self.width = width
            self.height = height
            self.fullscreen = fullscreen
            self.assets_path = assets_path
            
            # Create queues for bidirectional communication
            self.animation_queue = multiprocessing.Queue()
            self.log_queue = multiprocessing.Queue()
            
            # Start animation process
            self.animation_proc = multiprocessing.Process(
                target=animation_process,
                args=(self.animation_queue, assets_path, width, height, self.log_queue),
                daemon=False  # Not daemon so we can properly clean it up
            )
            self.animation_proc.start()
            
            print(f"[FACE] HDMI Display initialized: {width}x{height} (separate process)", flush=True)
            
            # Give animation process time to initialize
            time.sleep(0.5)
            
            # Drain any startup logs
            self._drain_logs()
            
        except Exception as e:
            print(f"[FACE] Failed to initialize: {e}", flush=True)
            self.animation_proc = None
            self.animation_queue = None
            self.log_queue = None

    def _drain_logs(self):
        """Print any pending logs from animation process."""
        if not self.log_queue:
            return
        
        while True:
            try:
                log_msg = self.log_queue.get_nowait()
                if log_msg is None:
                    break
                print(log_msg, flush=True)
            except:
                break

    def set_expression(self, expression: str, audio_duration: float = 0.0) -> None:
        """Send animation command to animation process (non-blocking).
        
        Args:
            expression: Expression name
            audio_duration: Duration in seconds
        """
        print(f"[FACE] expression={expression}, looping for {audio_duration:.2f}s", flush=True)
        
        # Drain pending logs from animation process
        self._drain_logs()
        
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
        """Stop animation process and drain any remaining logs."""
        print("[FACE] Cleaning up...", flush=True)
        
        # Drain remaining logs
        self._drain_logs()
        
        # Send shutdown signal
        if self.animation_queue:
            try:
                self.animation_queue.put(None, block=False)
            except:
                pass
        
        # Wait for process to finish (with time for display cleanup)
        if self.animation_proc and self.animation_proc.is_alive():
            print("[FACE] Waiting for animation process to finish...", flush=True)
            self.animation_proc.join(timeout=3.0)
            
            # Force terminate if still alive
            if self.animation_proc.is_alive():
                print("[FACE] Force terminating animation process", flush=True)
                self.animation_proc.terminate()
                self.animation_proc.join(timeout=1.0)
        
        # Drain final logs
        self._drain_logs()
        
        print("[FACE] Cleanup complete", flush=True)
