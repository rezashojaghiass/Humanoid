import os
from PIL import Image, ImageDraw
from robot_sync_app.ports.face_port import FacePort


class PyGameLCDFaceAdapter(FacePort):
    """Renders facial expressions to HDMI display on Jetson Xavier.
    
    Works with:
    - Physical HDMI monitor attached to Xavier
    - Independent from VNC/headless connections
    """

    def __init__(self, width: int = 1024, height: int = 768, fullscreen: bool = True):
        """
        Initialize the HDMI face display.
        
        Args:
            width: Display width in pixels (default 1024 for typical small HDMI monitors)
            height: Display height in pixels (default 768)
            fullscreen: Whether to run fullscreen on HDMI display
        """
        try:
            import pygame
            self.pygame = pygame
            
            # Configure SDL to use the HDMI display, not VNC
            os.environ['SDL_VIDEODRIVER'] = 'x11'
            os.environ['DISPLAY'] = ':0'  # Direct X11 display, not VNC
            
            pygame.init()
            
            self.width = width
            self.height = height
            self.fullscreen = fullscreen
            
            # Create display on HDMI monitor
            flags = pygame.FULLSCREEN if fullscreen else 0
            self.screen = pygame.display.set_mode((width, height), flags)
            pygame.display.set_caption("Robot Face")
            
            # Fill with black initially
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
            
            self.running = True
            self.current_expression = "neutral"
            print(f"[FACE] HDMI Display initialized: {width}x{height} (fullscreen={fullscreen})")
        except ImportError:
            print("[FACE] PyGame not available. Install with: pip install pygame")
            self.pygame = None
            self.screen = None
        except Exception as e:
            print(f"[FACE] Failed to initialize HDMI display: {e}")
            self.pygame = None
            self.screen = None

    def set_expression(self, expression: str) -> None:
        """Display the specified expression on HDMI monitor.
        
        Args:
            expression: Expression name (e.g., 'happy', 'neutral', 'sad')
        """
        print(f"[FACE] expression={expression}")
        
        if not self.pygame or not self.screen:
            return
            
        self.current_expression = expression.lower()
        
        # Create image with black background
        img = Image.new('RGB', (self.width, self.height), color='black')
        draw = ImageDraw.Draw(img)
        
        # Draw expression based on type
        if self.current_expression == "happy":
            self._draw_happy_face(draw)
        elif self.current_expression == "sad":
            self._draw_sad_face(draw)
        elif self.current_expression == "neutral":
            self._draw_neutral_face(draw)
        else:
            self._draw_neutral_face(draw)
        
        # Convert PIL image to pygame surface
        data = img.tobytes()
        size = img.size
        surf = self.pygame.image.fromstring(data, size, "RGB")
        
        # Display on HDMI monitor
        self.screen.blit(surf, (0, 0))
        self.pygame.display.flip()
        
        # Handle pygame events (prevent window from freezing)
        try:
            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    self.running = False
        except:
            pass  # Ignore event errors

    def _draw_happy_face(self, draw):
        """Draw a happy face expression on HDMI display."""
        cx, cy = self.width // 2, self.height // 2
        face_radius = min(self.width, self.height) // 3
        
        # Face circle (yellow)
        draw.ellipse(
            [cx - face_radius, cy - face_radius, cx + face_radius, cy + face_radius],
            outline='yellow', width=5, fill='yellow'
        )
        
        # Left eye
        eye_y = cy - face_radius // 3
        draw.ellipse([cx - face_radius // 2 - 40, eye_y - 20, cx - face_radius // 2 - 10, eye_y + 20], fill='black')
        
        # Right eye
        draw.ellipse([cx + face_radius // 2 + 10, eye_y - 20, cx + face_radius // 2 + 40, eye_y + 20], fill='black')
        
        # Happy mouth (arc)
        mouth_y = cy + face_radius // 4
        draw.arc(
            [cx - face_radius // 3, mouth_y, cx + face_radius // 3, mouth_y + face_radius // 2],
            0, 180, fill='black', width=5
        )

    def _draw_sad_face(self, draw):
        """Draw a sad face expression on HDMI display."""
        cx, cy = self.width // 2, self.height // 2
        face_radius = min(self.width, self.height) // 3
        
        # Face circle (blue)
        draw.ellipse(
            [cx - face_radius, cy - face_radius, cx + face_radius, cy + face_radius],
            outline='blue', width=5, fill='blue'
        )
        
        # Left eye
        eye_y = cy - face_radius // 3
        draw.ellipse([cx - face_radius // 2 - 40, eye_y - 20, cx - face_radius // 2 - 10, eye_y + 20], fill='white')
        
        # Right eye
        draw.ellipse([cx + face_radius // 2 + 10, eye_y - 20, cx + face_radius // 2 + 40, eye_y + 20], fill='white')
        
        # Sad mouth (upside down arc)
        mouth_y = cy + face_radius // 4
        draw.arc(
            [cx - face_radius // 3, mouth_y - face_radius // 2, cx + face_radius // 3, mouth_y],
            0, 180, fill='white', width=5
        )

    def _draw_neutral_face(self, draw):
        """Draw a neutral face expression on HDMI display."""
        cx, cy = self.width // 2, self.height // 2
        face_radius = min(self.width, self.height) // 3
        
        # Face circle (white)
        draw.ellipse(
            [cx - face_radius, cy - face_radius, cx + face_radius, cy + face_radius],
            outline='white', width=5, fill='white'
        )
        
        # Left eye
        eye_y = cy - face_radius // 3
        draw.ellipse([cx - face_radius // 2 - 40, eye_y - 20, cx - face_radius // 2 - 10, eye_y + 20], fill='black')
        
        # Right eye
        draw.ellipse([cx + face_radius // 2 + 10, eye_y - 20, cx + face_radius // 2 + 40, eye_y + 20], fill='black')
        
        # Neutral mouth (straight line)
        mouth_y = cy + face_radius // 4
        draw.line([cx - face_radius // 3, mouth_y, cx + face_radius // 3, mouth_y], fill='black', width=5)

    def cleanup(self):
        """Clean up pygame resources."""
        if self.pygame:
            self.pygame.quit()

