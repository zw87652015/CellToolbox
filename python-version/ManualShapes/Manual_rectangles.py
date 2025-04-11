import pygame
import json
import numpy as np
import sys
import ctypes
import os
import time
import threading

# Win32 constants
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SW_SHOW = 5
SWP_SHOWWINDOW = 0x0040

# Win32 API functions
SetWindowPos = ctypes.windll.user32.SetWindowPos
ShowWindow = ctypes.windll.user32.ShowWindow
BringWindowToTop = ctypes.windll.user32.BringWindowToTop
AttachThreadInput = ctypes.windll.user32.AttachThreadInput
GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
GetCurrentThreadId = ctypes.windll.kernel32.GetCurrentThreadId

# Color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

class Rectangle:
    """Rectangle class that can be added, hidden, deleted, and selected"""
    def __init__(self, x, y, width=200, height=200, visible=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = visible
        self.dragging = False
        self.resizing = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
    def is_point_inside(self, x, y):
        """Check if a point is inside the rectangle"""
        return self.rect.collidepoint(x, y)
    
    def is_point_on_resize_corner(self, x, y, tolerance=10):
        """Check if a point is on the bottom-right corner for resizing"""
        return (abs(x - self.rect.right) < tolerance and 
                abs(y - self.rect.bottom) < tolerance)
    
    def move(self, dx, dy):
        """Move the rectangle by the specified delta"""
        self.rect.x += dx
        self.rect.y += dy
    
    def resize(self, new_width, new_height):
        """Resize the rectangle with minimum size check"""
        self.rect.width = max(10, new_width)  # Minimum size of 10x10
        self.rect.height = max(10, new_height)
    
    def draw(self, screen, WHITE, BLACK, YELLOW, selected):
        """Draw the rectangle on the screen"""
        if self.visible:
            # Draw filled rectangle with border
            pygame.draw.rect(screen, WHITE, self.rect)
            pygame.draw.rect(screen, YELLOW if selected else WHITE, self.rect, 2)
        else:
            # Draw just the outline for hidden rectangles
            color = YELLOW if selected else WHITE
            line_thickness = 1  # Thin line
            pygame.draw.rect(screen, color, self.rect, line_thickness)
    
    def to_dict(self):
        """Convert rectangle to dictionary for saving"""
        return {
            "x": self.rect.x,
            "y": self.rect.y,
            "width": self.rect.width,
            "height": self.rect.height,
            "visible": self.visible
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create rectangle from dictionary"""
        return cls(
            data["x"],
            data["y"],
            data["width"],
            data["height"],
            data.get("visible", True)  # Default to visible if not specified
        )

def load_calibration_data():
    """Load the latest calibration data"""
    try:
        with open('calibration/latest_calibration.json', 'r') as f:
            data = json.load(f)
            required_fields = ['scale', 'rotation', 'offset_x', 'offset_y', 
                             'camera_resolution', 'projector_resolution', 'fov_corners']
            if all(field in data for field in required_fields):
                return data
            else:
                print("Error: Calibration data is missing required fields")
                return None
    except FileNotFoundError:
        print("Error: No calibration data found. Please run calibration first.")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid calibration data format")
        return None

def main():
    # Initialize Pygame
    pygame.init()
    
    # Load calibration data
    calibration_data = load_calibration_data()
    if calibration_data is None:
        print("Failed to load calibration data")
        sys.exit(1)
    
    # Set up display
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    
    # Set environment variable for window position
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
    
    # Create the pygame display - using normal window mode instead of fullscreen
    screen = pygame.display.set_mode((2560, 1600))
    pygame.display.set_caption("Manual Rectangle Tool")
    
    # Fill screen with black to make it visible
    screen.fill((0, 0, 0))
    pygame.display.flip()
    
    # Get window handle
    hwnd = pygame.display.get_wm_info()['window']
    print(f"Window handle: {hwnd}")
    
    # Use multiple Win32 API calls to ensure visibility
    ShowWindow(hwnd, SW_SHOW)
    SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
    BringWindowToTop(hwnd)
    
    # Flag for controlling the window focus thread
    running = True
    pygame_initialized = True
    
    # Start window focus maintenance thread
    def maintain_window_focus():
        """Maintain window focus for the pygame window"""
        print("Starting window focus maintenance thread")
        
        # Wait for pygame to initialize
        while not pygame_initialized and running:
            time.sleep(0.1)
        
        # Get window handle
        try:
            hwnd = pygame.display.get_wm_info()['window']
            print(f"Focus thread got window handle: {hwnd}")
            
            # Initial window setup - make it visible once
            ShowWindow(hwnd, SW_SHOW)
            
            # Important: Set window to NOTOPMOST instead of TOPMOST
            # This allows it to stay visible without forcing it to the foreground
            SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            print("Window visibility set up - not forcing foreground")
            
            # Periodically check and restore window if needed
            while running:
                # Ensure window is visible but not forcefully in foreground
                ShowWindow(hwnd, SW_SHOW)
                time.sleep(0.5)  # Check every half second
        except Exception as e:
            print(f"Error in window focus maintenance: {str(e)}")
        
        print("Window focus maintenance thread exiting")
    
    # Start the focus thread
    focus_thread = threading.Thread(target=maintain_window_focus)
    focus_thread.daemon = True
    focus_thread.start()
    
    # List to store all rectangles
    rectangles = []
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    params_file = os.path.join(script_dir, 'rectangle_params.json')
    
    # Try to load existing rectangles
    try:
        with open(params_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                # Multiple rectangles format
                for rect_data in data:
                    rectangles.append(Rectangle.from_dict(rect_data))
            elif isinstance(data, dict):
                # Single rectangle format (legacy)
                rectangles.append(Rectangle(
                    data.get("x", screen_width // 4),
                    data.get("y", screen_height // 4),
                    data.get("width", 200),
                    data.get("height", 200)
                ))
    except (FileNotFoundError, json.JSONDecodeError):
        # Create a default rectangle if no file exists or it's invalid
        rectangles.append(Rectangle(screen_width // 4, screen_height // 4))
    
    # Currently selected rectangle (None if no rectangle is selected)
    selected_rect_index = None if not rectangles else 0
    
    # Constants
    resize_margin = 10  # Pixels from edge where resizing is activated
    
    # Movement speed for keyboard controls (pixels per frame)
    MOVE_SPEED = 1  # More precise movement
    MOVE_SPEED_FAST = 5  # Faster movement with shift key
    
    # Key state tracking for continuous movement
    keys_pressed = {
        pygame.K_LEFT: False,
        pygame.K_RIGHT: False,
        pygame.K_UP: False,
        pygame.K_DOWN: False,
        pygame.K_LSHIFT: False,
        pygame.K_RSHIFT: False
    }
    
    # Font for displaying info
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 24)
    small_font = pygame.font.SysFont('Arial', 12)  # Smaller font for instructions
    
    # Function to find rectangle under mouse pointer
    def find_rect_under_pointer(x, y):
        for i in range(len(rectangles) - 1, -1, -1):  # Check from top to bottom (last added first)
            rect = rectangles[i]
            if rect.is_point_inside(x, y):
                return i
        return None
    
    # Function to find rectangle with resize corner under pointer
    def find_resize_corner_under_pointer(x, y):
        for i in range(len(rectangles) - 1, -1, -1):
            rect = rectangles[i]
            if rect.is_point_on_resize_corner(x, y, resize_margin):
                return i
        return None
    
    # Function to save rectangles to file
    def save_rectangles():
        try:
            with open(params_file, 'w') as f:
                json.dump([rect.to_dict() for rect in rectangles], f)
                print(f"Saved {len(rectangles)} rectangles to {params_file}")
        except Exception as e:
            print(f"Error saving rectangles: {str(e)}")
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_rect_index = find_rect_under_pointer(mouse_x, mouse_y)
        hover_resize_index = find_resize_corner_under_pointer(mouse_x, mouse_y)
        
        # Fill screen with black
        screen.fill(BLACK)
        
        # Draw FOV borders using calibration data if available
        if calibration_data and 'fov_corners' in calibration_data:
            fov_corners = calibration_data['fov_corners']
            for i in range(len(fov_corners)):
                start_point = fov_corners[i]
                end_point = fov_corners[(i + 1) % len(fov_corners)]
                pygame.draw.line(screen, WHITE, 
                               (int(start_point[0]), int(start_point[1])),
                               (int(end_point[0]), int(end_point[1])), 1)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Key state tracking for continuous movement
                elif event.key in keys_pressed:
                    keys_pressed[event.key] = True
                
                # Toggle visibility of rectangle under pointer with 'h' key
                elif event.key == pygame.K_h:
                    if hover_rect_index is not None:
                        rectangles[hover_rect_index].visible = not rectangles[hover_rect_index].visible
                
                # Add new rectangle at pointer position with 'j' key
                elif event.key == pygame.K_j:
                    rectangles.append(Rectangle(mouse_x, mouse_y))
                    selected_rect_index = len(rectangles) - 1
                
                # Delete rectangle under pointer with 'k' key
                elif event.key == pygame.K_k:
                    if hover_rect_index is not None:
                        del rectangles[hover_rect_index]
                        if selected_rect_index == hover_rect_index:
                            selected_rect_index = None
                        elif selected_rect_index is not None and selected_rect_index > hover_rect_index:
                            selected_rect_index -= 1
                
                # Save rectangles when 's' is pressed
                elif event.key == pygame.K_s:
                    save_rectangles()
            
            elif event.type == pygame.KEYUP:
                # Key state tracking for continuous movement
                if event.key in keys_pressed:
                    keys_pressed[event.key] = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if clicking on a resize corner
                resize_index = find_resize_corner_under_pointer(mouse_x, mouse_y)
                if resize_index is not None:
                    selected_rect_index = resize_index
                    rectangles[selected_rect_index].resizing = True
                
                # Check if clicking inside a rectangle
                elif hover_rect_index is not None:
                    selected_rect_index = hover_rect_index
                    rect = rectangles[selected_rect_index]
                    rect.dragging = True
                    rect.drag_offset_x = rect.rect.x - mouse_x
                    rect.drag_offset_y = rect.rect.y - mouse_y
                else:
                    # Deselect if clicking on empty space
                    selected_rect_index = None
            
            elif event.type == pygame.MOUSEBUTTONUP:
                # Stop dragging and resizing for all rectangles
                for rect in rectangles:
                    rect.dragging = False
                    rect.resizing = False
            
            elif event.type == pygame.MOUSEMOTION:
                # Handle dragging and resizing
                for i, rect in enumerate(rectangles):
                    if i == selected_rect_index:
                        if rect.dragging:
                            rect.rect.x = mouse_x + rect.drag_offset_x
                            rect.rect.y = mouse_y + rect.drag_offset_y
                        elif rect.resizing:
                            new_width = mouse_x - rect.rect.left
                            new_height = mouse_y - rect.rect.top
                            rect.resize(new_width, new_height)
        
        # Handle continuous keyboard movement for selected rectangle
        if selected_rect_index is not None:
            speed = MOVE_SPEED_FAST if keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT] else MOVE_SPEED
            rect = rectangles[selected_rect_index]
            
            if keys_pressed[pygame.K_LEFT]:
                rect.move(-speed, 0)
            if keys_pressed[pygame.K_RIGHT]:
                rect.move(speed, 0)
            if keys_pressed[pygame.K_UP]:
                rect.move(0, -speed)
            if keys_pressed[pygame.K_DOWN]:
                rect.move(0, speed)
        
        # Draw all rectangles
        for i, rect in enumerate(rectangles):
            is_selected = (i == selected_rect_index)
            rect.draw(screen, WHITE, BLACK, YELLOW, is_selected)
        
        # Display instructions
        instructions = [
            "Controls:",
            "J: Add new rectangle at cursor",
            "H: Hide/Show rectangle under cursor",
            "K: Delete rectangle under cursor",
            "Click: Select rectangle",
            "Click+Drag: Move rectangle",
            "Click on corner: Resize rectangle",
            "Arrow keys: Move selected rectangle",
            "Shift+Arrows: Move faster",
            "S: Save rectangles",
            "ESC: Exit"
        ]
        
        y_offset = 10
        for instruction in instructions:
            text_surface = small_font.render(instruction, True, WHITE)
            screen.blit(text_surface, (10, y_offset))
            y_offset += 20
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Save rectangles before exiting
    save_rectangles()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()