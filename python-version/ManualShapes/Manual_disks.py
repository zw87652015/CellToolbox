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

class Disk:
    """Disk class that can be added, hidden, deleted, and selected"""
    def __init__(self, x, y, radius=100, visible=True):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.visible = visible
        self.dragging = False
        self.resizing = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
    def is_point_inside(self, x, y):
        """Check if a point is inside the disk"""
        distance = ((x - self.center_x) ** 2 + (y - self.center_y) ** 2) ** 0.5
        return distance <= self.radius
    
    def is_point_on_border(self, x, y, tolerance=10):
        """Check if a point is on the border of the disk for resizing"""
        distance = ((x - self.center_x) ** 2 + (y - self.center_y) ** 2) ** 0.5
        return abs(distance - self.radius) <= tolerance
    
    def move(self, dx, dy):
        """Move the disk by the specified delta"""
        self.center_x += dx
        self.center_y += dy
    
    def resize(self, new_radius):
        """Resize the disk with minimum size check"""
        self.radius = max(5, new_radius)  # Minimum radius of 5
    
    def draw(self, screen, WHITE, BLACK, RED, selected):
        """Draw the disk on the screen"""
        if self.visible:
            # Draw filled white circle with border
            pygame.draw.circle(screen, WHITE, (int(self.center_x), int(self.center_y)), int(self.radius))
            pygame.draw.circle(screen, RED if selected else WHITE, (int(self.center_x), int(self.center_y)), int(self.radius), 2)
            
            # Display radius in red text
            font = pygame.font.SysFont('Arial', 16)
            # Radius text - placed below the disk
            radius_text = font.render(f"R: {int(self.radius)}", True, RED)
            screen.blit(radius_text, (int(self.center_x - 20), int(self.center_y + self.radius + 5)))
        else:
            # Draw just the outline for hidden disks
            color = RED if selected else WHITE
            line_thickness = 1  # Thin line
            pygame.draw.circle(screen, color, (int(self.center_x), int(self.center_y)), int(self.radius), line_thickness)
            
            # Display radius for hidden disks too
            font = pygame.font.SysFont('Arial', 16)
            radius_text = font.render(f"R: {int(self.radius)}", True, RED)
            screen.blit(radius_text, (int(self.center_x - 20), int(self.center_y + self.radius + 5)))
    
    def to_dict(self):
        """Convert disk to dictionary for saving"""
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "radius": self.radius,
            "visible": self.visible
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create disk from dictionary"""
        # Handle both old rectangle format and new disk format
        if "center_x" in data and "center_y" in data and "radius" in data:
            # New disk format
            return cls(
                data["center_x"],
                data["center_y"],
                data["radius"],
                data.get("visible", True)
            )
        elif "x" in data and "y" in data and "width" in data and "height" in data:
            # Old rectangle format - convert to disk
            center_x = data["x"] + data["width"] // 2
            center_y = data["y"] + data["height"] // 2
            radius = min(data["width"], data["height"]) // 2
            return cls(
                center_x,
                center_y,
                radius,
                data.get("visible", True)
            )
        else:
            # Unknown format - create default disk
            return cls(400, 400, 100, data.get("visible", True))

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
    pygame.display.set_caption("Manual Disk Tool")
    
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
    
    # List to store all disks
    disks = []
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    params_file = os.path.join(script_dir, 'disk_params.json')
    
    # Try to load existing disks
    try:
        with open(params_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                # Multiple disks format
                for disk_data in data:
                    disks.append(Disk.from_dict(disk_data))
            elif isinstance(data, dict):
                # Single disk format (legacy)
                disks.append(Disk.from_dict(data))
    except (FileNotFoundError, json.JSONDecodeError):
        # Create a default disk if no file exists or it's invalid
        disks.append(Disk(screen_width // 4, screen_height // 4))
    
    # Currently selected disk(s)
    selected_disk_indices = set()
    if disks:
        selected_disk_indices.add(0)
    
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
    
    # Function to find disk under mouse pointer
    def find_disk_under_pointer(x, y):
        for i in range(len(disks) - 1, -1, -1):  # Check from top to bottom (last added first)
            disk = disks[i]
            if disk.is_point_inside(x, y):
                return i
        return None
    
    # Function to find disk with border under pointer for resizing
    def find_disk_border_under_pointer(x, y):
        for i in range(len(disks) - 1, -1, -1):
            disk = disks[i]
            if disk.is_point_on_border(x, y, resize_margin):
                return i
        return None
    
    # Function to save disks to file
    def save_disks():
        try:
            with open(params_file, 'w') as f:
                json.dump([disk.to_dict() for disk in disks], f)
                print(f"Saved {len(disks)} disks to {params_file}")
        except Exception as e:
            print(f"Error saving disks: {str(e)}")
    
    # Clipboard for copying disks
    clipboard_disks = []
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_disk_index = find_disk_under_pointer(mouse_x, mouse_y)
        hover_resize_index = find_disk_border_under_pointer(mouse_x, mouse_y)
        
        # Fill screen with black
        screen.fill(BLACK)
        
        # Draw FOV borders using calibration data if available
        if calibration_data and 'fov_corners' in calibration_data:
            fov_corners = calibration_data['fov_corners']
            for i in range(len(fov_corners)):
                start_point = fov_corners[i]
                end_point = fov_corners[(i + 1) % len(fov_corners)]
                pygame.draw.line(screen, RED, 
                               (int(start_point[0]), int(start_point[1])),
                               (int(end_point[0]), int(end_point[1])), 2)
        
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
                
                # Copy the selected disk(s) with Ctrl+C
                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    if selected_disk_indices:
                        # Copy the selected disk(s) to clipboard
                        clipboard_disks = []
                        for idx in selected_disk_indices:
                            source_disk = disks[idx]
                            clipboard_disks.append(Disk(
                                source_disk.center_x,
                                source_disk.center_y,
                                source_disk.radius,
                                source_disk.visible
                            ))
                        print(f"{len(clipboard_disks)} disk(s) copied to clipboard")
                
                # Paste the copied disk(s) with Ctrl+V
                elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    if clipboard_disks:
                        # Create new disks at a slightly offset position
                        new_indices = set()
                        for clipboard_disk in clipboard_disks:
                            new_disk = Disk(
                                clipboard_disk.center_x + 20,
                                clipboard_disk.center_y + 20,
                                clipboard_disk.radius,
                                clipboard_disk.visible
                            )
                            disks.append(new_disk)
                            new_indices.add(len(disks) - 1)
                        # Update selection to the newly pasted disks
                        selected_disk_indices = new_indices
                        print(f"{len(clipboard_disks)} disk(s) pasted from clipboard")
                
                # Toggle visibility of disk under pointer with 'h' key
                elif event.key == pygame.K_h:
                    if hover_disk_index is not None:
                        disks[hover_disk_index].visible = not disks[hover_disk_index].visible
                
                # Add new disk at pointer position with 'j' key
                elif event.key == pygame.K_j:
                    disks.append(Disk(mouse_x, mouse_y))
                    selected_disk_indices = {len(disks) - 1}
                
                # Delete disk under pointer with 'k' key
                elif event.key == pygame.K_k:
                    if hover_disk_index is not None:
                        # Remove the deleted index from selected indices
                        if hover_disk_index in selected_disk_indices:
                            selected_disk_indices.remove(hover_disk_index)
                        
                        # Adjust indices of selected disks after the deleted one
                        adjusted_indices = set()
                        for idx in selected_disk_indices:
                            if idx > hover_disk_index:
                                adjusted_indices.add(idx - 1)
                            else:
                                adjusted_indices.add(idx)
                        selected_disk_indices = adjusted_indices
                        
                        # Delete the disk
                        del disks[hover_disk_index]
                
                # Save disks when 's' is pressed
                elif event.key == pygame.K_s:
                    save_disks()
            
            elif event.type == pygame.KEYUP:
                # Key state tracking for continuous movement
                if event.key in keys_pressed:
                    keys_pressed[event.key] = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if clicking on a disk border for resizing
                resize_index = find_disk_border_under_pointer(mouse_x, mouse_y)
                if resize_index is not None:
                    # Select only this disk for resizing if Shift is not held
                    if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        selected_disk_indices = {resize_index}
                    else:
                        selected_disk_indices.add(resize_index)
                    disks[resize_index].resizing = True
                
                # Check if clicking inside a disk
                elif hover_disk_index is not None:
                    # If Shift is held, toggle selection of this disk
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if hover_disk_index in selected_disk_indices:
                            selected_disk_indices.remove(hover_disk_index)
                        else:
                            selected_disk_indices.add(hover_disk_index)
                    else:
                        # Without Shift, select only this disk
                        selected_disk_indices = {hover_disk_index}
                    
                    # Start dragging all selected disks
                    for idx in selected_disk_indices:
                        disk = disks[idx]
                        disk.dragging = True
                        disk.drag_offset_x = disk.center_x - mouse_x
                        disk.drag_offset_y = disk.center_y - mouse_y
                else:
                    # Deselect if clicking on empty space and Shift is not held
                    if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        selected_disk_indices = set()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                # Stop dragging and resizing for all disks
                for disk in disks:
                    disk.dragging = False
                    disk.resizing = False
            
            elif event.type == pygame.MOUSEMOTION:
                # Handle dragging and resizing
                for i, disk in enumerate(disks):
                    if i in selected_disk_indices:
                        if disk.dragging:
                            disk.center_x = mouse_x + disk.drag_offset_x
                            disk.center_y = mouse_y + disk.drag_offset_y
                        elif disk.resizing:
                            # Calculate new radius based on distance from center to mouse
                            new_radius = ((mouse_x - disk.center_x) ** 2 + (mouse_y - disk.center_y) ** 2) ** 0.5
                            disk.resize(new_radius)
        
        # Handle continuous keyboard movement for selected disks
        if selected_disk_indices:
            speed = MOVE_SPEED_FAST if keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT] else MOVE_SPEED
            for idx in selected_disk_indices:
                disk = disks[idx]
                
                if keys_pressed[pygame.K_LEFT]:
                    disk.move(-speed, 0)
                if keys_pressed[pygame.K_RIGHT]:
                    disk.move(speed, 0)
                if keys_pressed[pygame.K_UP]:
                    disk.move(0, -speed)
                if keys_pressed[pygame.K_DOWN]:
                    disk.move(0, speed)
        
        # Draw all disks
        for i, disk in enumerate(disks):
            is_selected = (i in selected_disk_indices)
            disk.draw(screen, WHITE, BLACK, RED, is_selected)
        
        # Display instructions
        instructions = [
            "Controls:",
            "J: Add new disk at cursor",
            "H: Hide/Show disk under cursor",
            "K: Delete disk under cursor",
            "Click: Select disk",
            "Shift+Click: Multi-select disks",
            "Click+Drag: Move disk(s)",
            "Click on border: Resize disk",
            "Arrow keys: Move selected disk(s)",
            "Shift+Arrows: Move faster",
            "Ctrl+C: Copy selected disk(s)",
            "Ctrl+V: Paste copied disk(s)",
            "S: Save disks",
            "ESC: Exit"
        ]
        
        y_offset = 10
        for instruction in instructions:
            text_surface = small_font.render(instruction, True, RED)
            screen.blit(text_surface, (10, y_offset))
            y_offset += 20
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Save disks before exiting
    save_disks()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()