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
BLACK = (30, 30, 30)  # Using dark gray instead of pure black
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

class UShape:
    """U-Shape class that can be added, hidden, deleted, and selected"""
    def __init__(self, x, y, width=200, height=200, thickness=20, visible=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.thickness = thickness  # Thickness of the borders
        self.visible = visible
        self.dragging = False
        self.resizing = False
        self.thickness_adjusting = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
    def is_point_inside(self, x, y):
        """Check if a point is inside the U-shape"""
        # Check if point is in the outer rectangle
        if not self.rect.collidepoint(x, y):
            return False
            
        # Check if point is in the inner area (which is not part of the U-shape)
        inner_rect = pygame.Rect(
            self.rect.left + self.thickness,
            self.rect.top,
            self.rect.width - 2 * self.thickness,
            self.rect.height - self.thickness
        )
        
        # If point is in the inner rectangle, it's not in the U-shape
        if inner_rect.collidepoint(x, y):
            return False
            
        return True
    
    def is_point_on_resize_corner(self, x, y, tolerance=10):
        """Check if a point is on the bottom-right corner for resizing"""
        return (abs(x - self.rect.right) < tolerance and 
                abs(y - self.rect.bottom) < tolerance)
    
    def is_point_on_thickness_control(self, x, y, tolerance=10):
        """Check if a point is on the thickness control point (top-right corner)"""
        return (abs(x - self.rect.right) < tolerance and 
                abs(y - self.rect.top) < tolerance)
    
    def move(self, dx, dy):
        """Move the U-shape by the specified delta"""
        self.rect.x += dx
        self.rect.y += dy
    
    def resize(self, new_width, new_height):
        """Resize the U-shape with minimum size check"""
        # Minimum size should be at least twice the thickness
        min_size = max(20, self.thickness * 2 + 10)
        self.rect.width = max(min_size, new_width)
        self.rect.height = max(min_size, new_height)
    
    def adjust_thickness(self, new_thickness):
        """Adjust the thickness of the U-shape borders"""
        # Ensure thickness is at least 5 pixels and not more than half the width/height
        max_thickness = min(self.rect.width // 2 - 5, self.rect.height // 2 - 5)
        self.thickness = max(5, min(max_thickness, new_thickness))
    
    def draw(self, screen, WHITE, BLACK, YELLOW, selected):
        """Draw the U-shape on the screen"""
        if self.visible:
            # Define the outer and inner rectangles
            outer_rect = self.rect
            inner_rect = pygame.Rect(
                self.rect.left + self.thickness,
                self.rect.top,
                self.rect.width - 2 * self.thickness,
                self.rect.height - self.thickness
            )
            
            # Draw the U-shape by drawing the outer rectangle and then "erasing" the inner part
            color = WHITE
            pygame.draw.rect(screen, color, outer_rect)
            pygame.draw.rect(screen, BLACK, inner_rect)
            
            # Draw border if selected
            if selected:
                pygame.draw.rect(screen, YELLOW, outer_rect, 2)
                pygame.draw.rect(screen, YELLOW, inner_rect, 2)
            
            # Draw thickness control point at top-right corner
            pygame.draw.circle(screen, RED, (self.rect.right, self.rect.top), 5)
            
            # Display dimensions and thickness in yellow text
            font = pygame.font.SysFont('Arial', 16)
            # Width text - placed below the rectangle
            width_text = font.render(f"W: {self.rect.width}", True, YELLOW)
            screen.blit(width_text, (self.rect.x + 5, self.rect.bottom + 2))
            # Height text - placed to the right of the rectangle
            height_text = font.render(f"H: {self.rect.height}", True, YELLOW)
            screen.blit(height_text, (self.rect.right + 2, self.rect.y + 5))
            # Thickness text - placed at the top-right corner
            thickness_text = font.render(f"T: {self.thickness}", True, RED)
            screen.blit(thickness_text, (self.rect.right + 2, self.rect.top - 20))
        else:
            # Draw just the outline for hidden U-shapes
            color = YELLOW if selected else WHITE
            line_thickness = 1  # Thin line
            
            # Draw the outer rectangle outline
            pygame.draw.rect(screen, color, self.rect, line_thickness)
            
            # Draw the inner rectangle outline
            inner_rect = pygame.Rect(
                self.rect.left + self.thickness,
                self.rect.top,
                self.rect.width - 2 * self.thickness,
                self.rect.height - self.thickness
            )
            pygame.draw.rect(screen, color, inner_rect, line_thickness)
            
            # Display dimensions and thickness for hidden U-shapes too
            font = pygame.font.SysFont('Arial', 16)
            width_text = font.render(f"W: {self.rect.width}", True, YELLOW)
            screen.blit(width_text, (self.rect.x + 5, self.rect.bottom + 2))
            height_text = font.render(f"H: {self.rect.height}", True, YELLOW)
            screen.blit(height_text, (self.rect.right + 2, self.rect.y + 5))
            thickness_text = font.render(f"T: {self.thickness}", True, RED)
            screen.blit(thickness_text, (self.rect.right + 2, self.rect.top - 20))
    
    def to_dict(self):
        """Convert U-shape to dictionary for saving"""
        return {
            "x": self.rect.x,
            "y": self.rect.y,
            "width": self.rect.width,
            "height": self.rect.height,
            "thickness": self.thickness,
            "visible": self.visible
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create U-shape from dictionary"""
        return cls(
            data["x"],
            data["y"],
            data["width"],
            data["height"],
            data.get("thickness", 20),  # Default thickness if not specified
            data.get("visible", True)   # Default to visible if not specified
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
    pygame.display.set_caption("Manual U-Shape Tool")
    
    # Fill screen with black to make it visible
    screen.fill(BLACK)
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
    
    # List to store all U-shapes
    ushapes = []
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    params_file = os.path.join(script_dir, 'ushape_params.json')
    
    # Try to load existing U-shapes
    try:
        with open(params_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                # Multiple U-shapes format
                for shape_data in data:
                    ushapes.append(UShape.from_dict(shape_data))
            elif isinstance(data, dict):
                # Single U-shape format (legacy)
                ushapes.append(UShape(
                    data.get("x", screen_width // 4),
                    data.get("y", screen_height // 4),
                    data.get("width", 200),
                    data.get("height", 200),
                    data.get("thickness", 20)
                ))
    except (FileNotFoundError, json.JSONDecodeError):
        # Create a default U-shape if no file exists or it's invalid
        ushapes.append(UShape(screen_width // 4, screen_height // 4))
    
    # Currently selected U-shape(s)
    selected_shape_indices = set()
    if ushapes:
        selected_shape_indices.add(0)
    
    # Constants
    resize_margin = 10  # Pixels from edge where resizing is activated
    
    # Movement speed for keyboard controls (pixels per frame)
    MOVE_SPEED = 1  # More precise movement
    MOVE_SPEED_FAST = 5  # Faster movement with shift key
    
    # Thickness adjustment speed
    THICKNESS_SPEED = 1
    THICKNESS_SPEED_FAST = 5
    
    # Key state tracking for continuous movement
    keys_pressed = {
        pygame.K_LEFT: False,
        pygame.K_RIGHT: False,
        pygame.K_UP: False,
        pygame.K_DOWN: False,
        pygame.K_LSHIFT: False,
        pygame.K_RSHIFT: False,
        pygame.K_PLUS: False,
        pygame.K_EQUALS: False,  # For + without shift
        pygame.K_MINUS: False,
        pygame.K_KP_PLUS: False,  # Numpad +
        pygame.K_KP_MINUS: False  # Numpad -
    }
    
    # Font for displaying info
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 24)
    small_font = pygame.font.SysFont('Arial', 12)  # Smaller font for instructions
    
    # Function to find U-shape under mouse pointer
    def find_shape_under_pointer(x, y):
        for i in range(len(ushapes) - 1, -1, -1):  # Check from top to bottom (last added first)
            shape = ushapes[i]
            if shape.is_point_inside(x, y):
                return i
        return None
    
    # Function to find U-shape with resize corner under pointer
    def find_resize_corner_under_pointer(x, y):
        for i in range(len(ushapes) - 1, -1, -1):
            shape = ushapes[i]
            if shape.is_point_on_resize_corner(x, y, resize_margin):
                return i
        return None
    
    # Function to find U-shape with thickness control under pointer
    def find_thickness_control_under_pointer(x, y):
        for i in range(len(ushapes) - 1, -1, -1):
            shape = ushapes[i]
            if shape.is_point_on_thickness_control(x, y, resize_margin):
                return i
        return None
    
    # Function to save U-shapes to file
    def save_shapes():
        try:
            with open(params_file, 'w') as f:
                json.dump([shape.to_dict() for shape in ushapes], f)
                print(f"Saved {len(ushapes)} U-shapes to {params_file}")
        except Exception as e:
            print(f"Error saving U-shapes: {str(e)}")
    
    # Clipboard for copying U-shapes
    clipboard_shapes = []
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_shape_index = find_shape_under_pointer(mouse_x, mouse_y)
        hover_resize_index = find_resize_corner_under_pointer(mouse_x, mouse_y)
        hover_thickness_index = find_thickness_control_under_pointer(mouse_x, mouse_y)
        
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
                
                # Copy the selected U-shape(s) with Ctrl+C
                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    if selected_shape_indices:
                        # Copy the selected U-shape(s) to clipboard
                        clipboard_shapes = []
                        for idx in selected_shape_indices:
                            source_shape = ushapes[idx]
                            clipboard_shapes.append(UShape(
                                source_shape.rect.x,
                                source_shape.rect.y,
                                source_shape.rect.width,
                                source_shape.rect.height,
                                source_shape.thickness,
                                source_shape.visible
                            ))
                        print(f"{len(clipboard_shapes)} U-shape(s) copied to clipboard")
                
                # Paste the copied U-shape(s) with Ctrl+V
                elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    if clipboard_shapes:
                        # Create new U-shapes at a slightly offset position
                        new_indices = set()
                        for clipboard_shape in clipboard_shapes:
                            new_shape = UShape(
                                clipboard_shape.rect.x + 20,
                                clipboard_shape.rect.y + 20,
                                clipboard_shape.rect.width,
                                clipboard_shape.rect.height,
                                clipboard_shape.thickness,
                                clipboard_shape.visible
                            )
                            ushapes.append(new_shape)
                            new_indices.add(len(ushapes) - 1)
                        # Update selection to the newly pasted U-shapes
                        selected_shape_indices = new_indices
                        print(f"{len(clipboard_shapes)} U-shape(s) pasted from clipboard")
                
                # Toggle visibility of U-shape under pointer with 'h' key
                elif event.key == pygame.K_h:
                    if hover_shape_index is not None:
                        ushapes[hover_shape_index].visible = not ushapes[hover_shape_index].visible
                
                # Add new U-shape at pointer position with 'j' key
                elif event.key == pygame.K_j:
                    ushapes.append(UShape(mouse_x, mouse_y))
                    selected_shape_indices = {len(ushapes) - 1}
                
                # Delete U-shape under pointer with 'k' key
                elif event.key == pygame.K_k:
                    if hover_shape_index is not None:
                        # Remove the deleted index from selected indices
                        if hover_shape_index in selected_shape_indices:
                            selected_shape_indices.remove(hover_shape_index)
                        
                        # Adjust indices of selected U-shapes after the deleted one
                        adjusted_indices = set()
                        for idx in selected_shape_indices:
                            if idx > hover_shape_index:
                                adjusted_indices.add(idx - 1)
                            else:
                                adjusted_indices.add(idx)
                        selected_shape_indices = adjusted_indices
                        
                        # Delete the U-shape
                        del ushapes[hover_shape_index]
                
                # Save U-shapes when 's' is pressed
                elif event.key == pygame.K_s:
                    save_shapes()
            
            elif event.type == pygame.KEYUP:
                # Key state tracking for continuous movement
                if event.key in keys_pressed:
                    keys_pressed[event.key] = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if clicking on a thickness control
                thickness_index = find_thickness_control_under_pointer(mouse_x, mouse_y)
                if thickness_index is not None:
                    # Select only this U-shape for thickness adjustment if Shift is not held
                    if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        selected_shape_indices = {thickness_index}
                    else:
                        selected_shape_indices.add(thickness_index)
                    ushapes[thickness_index].thickness_adjusting = True
                
                # Check if clicking on a resize corner
                elif hover_resize_index is not None:
                    # Select only this U-shape for resizing if Shift is not held
                    if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        selected_shape_indices = {hover_resize_index}
                    else:
                        selected_shape_indices.add(hover_resize_index)
                    ushapes[hover_resize_index].resizing = True
                
                # Check if clicking inside a U-shape
                elif hover_shape_index is not None:
                    # If Shift is held, toggle selection of this U-shape
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if hover_shape_index in selected_shape_indices:
                            selected_shape_indices.remove(hover_shape_index)
                        else:
                            selected_shape_indices.add(hover_shape_index)
                    else:
                        # Without Shift, select only this U-shape
                        selected_shape_indices = {hover_shape_index}
                    
                    # Start dragging all selected U-shapes
                    for idx in selected_shape_indices:
                        shape = ushapes[idx]
                        shape.dragging = True
                        shape.drag_offset_x = shape.rect.x - mouse_x
                        shape.drag_offset_y = shape.rect.y - mouse_y
                else:
                    # Deselect if clicking on empty space and Shift is not held
                    if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        selected_shape_indices = set()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                # Stop dragging, resizing, and thickness adjusting for all U-shapes
                for shape in ushapes:
                    shape.dragging = False
                    shape.resizing = False
                    shape.thickness_adjusting = False
            
            elif event.type == pygame.MOUSEMOTION:
                # Handle dragging, resizing, and thickness adjusting
                for i, shape in enumerate(ushapes):
                    if i in selected_shape_indices:
                        if shape.dragging:
                            shape.rect.x = mouse_x + shape.drag_offset_x
                            shape.rect.y = mouse_y + shape.drag_offset_y
                        elif shape.resizing:
                            new_width = mouse_x - shape.rect.left
                            new_height = mouse_y - shape.rect.top
                            shape.resize(new_width, new_height)
                        elif shape.thickness_adjusting:
                            # Adjust thickness based on distance from top-left corner
                            dx = mouse_x - shape.rect.left
                            dy = mouse_y - shape.rect.top
                            new_thickness = min(dx, shape.rect.height - dy)
                            shape.adjust_thickness(new_thickness)
        
        # Handle continuous keyboard movement for selected U-shapes
        if selected_shape_indices:
            speed = MOVE_SPEED_FAST if keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT] else MOVE_SPEED
            thickness_speed = THICKNESS_SPEED_FAST if keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT] else THICKNESS_SPEED
            
            for idx in selected_shape_indices:
                shape = ushapes[idx]
                
                # Movement controls
                if keys_pressed[pygame.K_LEFT]:
                    shape.move(-speed, 0)
                if keys_pressed[pygame.K_RIGHT]:
                    shape.move(speed, 0)
                if keys_pressed[pygame.K_UP]:
                    shape.move(0, -speed)
                if keys_pressed[pygame.K_DOWN]:
                    shape.move(0, speed)
                
                # Thickness controls
                if (keys_pressed[pygame.K_PLUS] or keys_pressed[pygame.K_EQUALS] or 
                    keys_pressed[pygame.K_KP_PLUS]):
                    shape.adjust_thickness(shape.thickness + thickness_speed)
                if keys_pressed[pygame.K_MINUS] or keys_pressed[pygame.K_KP_MINUS]:
                    shape.adjust_thickness(shape.thickness - thickness_speed)
        
        # Draw all U-shapes
        for i, shape in enumerate(ushapes):
            is_selected = (i in selected_shape_indices)
            shape.draw(screen, WHITE, BLACK, YELLOW, is_selected)
        
        # Display instructions
        instructions = [
            "Controls:",
            "J: Add new U-shape at cursor",
            "H: Hide/Show U-shape under cursor",
            "K: Delete U-shape under cursor",
            "Click: Select U-shape",
            "Shift+Click: Multi-select U-shapes",
            "Click+Drag: Move U-shape(s)",
            "Click on bottom-right corner: Resize U-shape",
            "Click on top-right corner: Adjust thickness",
            "+/-: Increase/decrease thickness",
            "Arrow keys: Move selected U-shape(s)",
            "Shift+Arrows: Move faster",
            "Ctrl+C: Copy selected U-shape(s)",
            "Ctrl+V: Paste copied U-shape(s)",
            "S: Save U-shapes",
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
    
    # Save U-shapes before exiting
    save_shapes()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
