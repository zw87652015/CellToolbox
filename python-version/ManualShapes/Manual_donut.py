import pygame
import json
import numpy as np
import sys
import ctypes
import math
import os
import threading
import time
import tkinter as tk
from tkinter import ttk
import multiprocessing
from multiprocessing import Process, Value, Array

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

class Donut:
    def __init__(self, x, y, outer_radius=150, inner_radius=75, visible=True):
        self.center_x = x
        self.center_y = y
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.visible = visible
        self.dragging_center = False
        self.dragging_outer = False
        self.dragging_inner = False
        self.drag_start_pos = (0, 0)
        self.drag_start_radius_outer = outer_radius
        self.drag_start_radius_inner = inner_radius
        
    def is_point_inside(self, x, y):
        """Check if a point is inside the donut"""
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        return self.inner_radius < distance < self.outer_radius
    
    def is_point_inside_inner_circle(self, x, y):
        """Check if a point is inside the inner circle of the donut"""
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < self.inner_radius
    
    def is_point_on_inner_border(self, x, y, tolerance=10):
        """Check if a point is on the inner border of the donut"""
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        return abs(distance - self.inner_radius) < tolerance
    
    def is_point_on_outer_border(self, x, y, tolerance=10):
        """Check if a point is on the outer border of the donut"""
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        return abs(distance - self.outer_radius) < tolerance
    
    def is_point_over_donut(self, x, y, tolerance=10):
        """Check if a point is over any part of the donut (inside or on borders)"""
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        return (distance < self.outer_radius + tolerance)
    
    def scale(self, scale_up, factor, min_inner_radius, min_radius_gap, max_outer_radius):
        """Scale the donut while maintaining thickness"""
        # Calculate current thickness (absolute value)
        thickness = self.outer_radius - self.inner_radius
        
        if scale_up:
            # Increase outer radius
            new_outer = min(self.outer_radius * (1 + factor), max_outer_radius)
            # Maintain absolute thickness
            new_inner = new_outer - thickness
        else:
            # Decrease outer radius
            new_outer = max(self.outer_radius * (1 - factor), thickness + min_inner_radius)
            # Maintain absolute thickness
            new_inner = new_outer - thickness
        
        # Ensure inner radius doesn't go below minimum
        new_inner = max(new_inner, min_inner_radius)
        
        # Update radii
        self.outer_radius = new_outer
        self.inner_radius = new_inner
    
    def move(self, dx, dy):
        """Move the donut by the specified delta"""
        self.center_x += dx
        self.center_y += dy
    
    def resize_outer(self, new_distance, min_radius_gap, max_outer_radius):
        """Resize the outer radius"""
        # Ensure outer radius is at least min_radius_gap larger than inner radius
        # and not larger than max_outer_radius
        self.outer_radius = max(min(new_distance, max_outer_radius), self.inner_radius + min_radius_gap)
    
    def resize_inner(self, new_distance, min_inner_radius, min_radius_gap):
        """Resize the inner radius"""
        # Ensure inner radius is at least min_inner_radius
        # and at most (outer_radius - min_radius_gap)
        self.inner_radius = max(min(new_distance, self.outer_radius - min_radius_gap), min_inner_radius)
    
    def draw(self, screen, WHITE, BLACK, YELLOW, selected):
        """Draw the donut on the screen"""
        if self.visible:
            # Draw the donut (filled white ring)
            pygame.draw.circle(screen, WHITE if selected else WHITE, (int(self.center_x), int(self.center_y)), int(self.outer_radius))  # Outer circle (filled)
            pygame.draw.circle(screen, BLACK, (int(self.center_x), int(self.center_y)), int(self.inner_radius))  # Inner circle (cuts out center)
            
            # Draw the borders of the circles for better visibility during editing
            pygame.draw.circle(screen, YELLOW if selected else WHITE, (int(self.center_x), int(self.center_y)), int(self.outer_radius), 2)  # Outer border
            pygame.draw.circle(screen, YELLOW if selected else WHITE, (int(self.center_x), int(self.center_y)), int(self.inner_radius), 2)  # Inner border
        else:
            # Draw just the outer circle line to show where the hidden donut is
            color = YELLOW if selected else WHITE
            line_thickness = 1  # Thin line
            
            # Draw the outer circle only
            pygame.draw.circle(screen, color, (int(self.center_x), int(self.center_y)), int(self.outer_radius), line_thickness)
    
    def to_dict(self):
        """Convert donut to dictionary for saving"""
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "outer_radius": self.outer_radius,
            "inner_radius": self.inner_radius,
            "visible": self.visible
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create donut from dictionary"""
        return cls(
            data["center_x"],
            data["center_y"],
            data["outer_radius"],
            data["inner_radius"],
            data.get("visible", True)  # Default to visible if not specified
        )

class Rest:
    """Represents a filled disk (no hole) that temporarily replaces a donut"""
    def __init__(self, x, y, radius, visible=True):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.visible = visible
    
    def draw(self, screen, WHITE, BLACK, YELLOW, selected):
        """Draw the rest disk on the screen"""
        if self.visible:
            # Draw a filled circle
            pygame.draw.circle(screen, WHITE if selected else WHITE, (int(self.center_x), int(self.center_y)), int(self.radius))
            # Draw the border for better visibility
            pygame.draw.circle(screen, YELLOW if selected else WHITE, (int(self.center_x), int(self.center_y)), int(self.radius), 2)
    
    def to_dict(self):
        """Convert rest to dictionary for saving"""
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "radius": self.radius,
            "visible": self.visible
        }

class Expect:
    """Represents a small disk that appears at the center of a Rest disk"""
    def __init__(self, x, y, radius, visible=True):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.visible = visible
    
    def draw(self, screen, GREEN, BLACK, YELLOW, selected):
        """Draw the expect disk on the screen"""
        if self.visible:
            # Draw a filled circle with green color
            pygame.draw.circle(screen, GREEN if selected else GREEN, (int(self.center_x), int(self.center_y)), int(self.radius))
            # Draw the border for better visibility
            pygame.draw.circle(screen, YELLOW if selected else GREEN, (int(self.center_x), int(self.center_y)), int(self.radius), 2)
    
    def to_dict(self):
        """Convert expect to dictionary for saving"""
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "radius": self.radius,
            "visible": self.visible
        }

class ParameterControlPanel:
    """Control panel for adjusting parameters of the Expect disks"""
    def __init__(self):
        # Use shared memory for communication between processes
        self._expect_radius = Value('i', 30)  # Default radius for Expect disks
        self._panel_active = Value('i', 0)    # 0 = inactive, 1 = active
        self.process = None
    
    @property
    def expect_radius(self):
        return self._expect_radius.value
    
    @property
    def panel_active(self):
        return self._panel_active.value == 1
    
    def create_panel(self):
        """Create the parameter control panel in a separate process"""
        if self.process is not None and self.process.is_alive():
            return
        
        # Set panel as active
        self._panel_active.value = 1
        
        # Start a new process for the Tkinter UI
        self.process = Process(target=self._run_panel, args=(self._expect_radius, self._panel_active))
        self.process.daemon = True
        self.process.start()
    
    def _run_panel(self, expect_radius, panel_active):
        """Run the parameter control panel in a separate process"""
        root = tk.Tk()
        root.title("Parameter Control Panel")
        root.geometry("400x300")
        
        # Handle window close event
        def on_close():
            panel_active.value = 0
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_close)
        
        # Create a frame for the Expect radius control
        radius_frame = ttk.LabelFrame(root, text="Expect Disk Radius")
        radius_frame.pack(fill="x", padx=10, pady=10)
        
        # Create a scale for adjusting the radius
        radius_var = tk.IntVar(value=expect_radius.value)
        
        def update_radius(value):
            # Update the shared memory value
            try:
                val = int(float(value))
                expect_radius.value = val
                radius_value_label.config(text=f"Radius: {val}")
            except ValueError:
                pass
        
        radius_scale = ttk.Scale(
            radius_frame, 
            from_=5, 
            to=100,
            orient="horizontal",
            length=300,
            value=expect_radius.value,
            command=update_radius
        )
        radius_scale.pack(padx=10, pady=5)
        
        # Create a label to display the current radius value
        radius_value_label = ttk.Label(radius_frame, text=f"Radius: {expect_radius.value}")
        radius_value_label.pack(padx=10, pady=5)
        
        # Create a frame for future parameters (placeholder)
        future_frame = ttk.LabelFrame(root, text="Future Parameters")
        future_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add a placeholder label
        placeholder_label = ttk.Label(future_frame, text="Space for future parameters")
        placeholder_label.pack(padx=10, pady=40)
        
        # Start the Tkinter event loop
        root.mainloop()
        
        # Ensure panel is marked as inactive when the window is closed
        panel_active.value = 0
    
    def on_close(self):
        """Handle closing the panel from the main process"""
        if self.process and self.process.is_alive():
            self._panel_active.value = 0
            self.process.terminate()
            self.process.join()
            self.process = None

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
    
    # Create parameter control panel
    param_panel = ParameterControlPanel()
    
    # Set up display
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    
    # Set environment variable for window position
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
    
    # Create the pygame display - using normal window mode instead of fullscreen
    # This is important for window management
    screen = pygame.display.set_mode((2560, 1600))
    pygame.display.set_caption("Manual Donut Tool")
    
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
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error in window focus maintenance: {str(e)}")
        
        print("Window focus maintenance thread exiting")
    
    # Start the focus thread
    focus_thread = threading.Thread(target=maintain_window_focus)
    focus_thread.daemon = True
    focus_thread.start()
    
    # List to store all donuts
    donuts = []
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    params_file = os.path.join(script_dir, 'donut_params.json')
    
    # Try to load existing donuts
    try:
        with open(params_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                # Multiple donuts format
                for donut_data in data:
                    donuts.append(Donut.from_dict(donut_data))
            elif isinstance(data, dict):
                # Single donut format (legacy)
                donuts.append(Donut(
                    data.get("center_x", screen_width // 2),
                    data.get("center_y", screen_height // 2),
                    data.get("outer_radius", 150),
                    data.get("inner_radius", 75)
                ))
    except (FileNotFoundError, json.JSONDecodeError):
        # Create a default donut if no file exists or it's invalid
        donuts.append(Donut(screen_width // 2, screen_height // 2))
    
    # Currently selected donut (None if no donut is selected)
    selected_donut_index = None if not donuts else 0
    
    # Constants for donut manipulation
    min_radius_gap = 10
    min_inner_radius = 10
    max_outer_radius = 500
    
    # Scaling factor for mouse wheel
    SCALE_FACTOR = 0.05  # 5% change per scroll
    KEYBOARD_SCALE_FACTOR = 0.01  # 1% change per keypress (more precise)
    
    # Scaling delay for keyboard (to slow down continuous scaling)
    scale_delay = 0
    SCALE_DELAY_MAX = 3  # Only apply scaling every 3 frames
    
    # Colors
    BLACK = (60, 60, 60)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)  # For highlighting selected donut
    
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
        pygame.K_RSHIFT: False,
        pygame.K_MINUS: False,  # For shrinking
        pygame.K_EQUALS: False  # For growing
    }
    
    # Font for displaying radius values
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 24)
    small_font = pygame.font.SysFont('Arial', 12)  # Smaller font for instructions
    
    # Function to find donut under mouse pointer
    def find_donut_under_pointer(x, y):
        for i, donut in enumerate(donuts):
            if donut.is_point_over_donut(x, y):
                return i
        return None
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_donut_index = find_donut_under_pointer(mouse_x, mouse_y)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Toggle visibility of donut under pointer with 'h' key
                elif event.key == pygame.K_h:
                    if hover_donut_index is not None:
                        donuts[hover_donut_index].visible = not donuts[hover_donut_index].visible
                # Add new donut at pointer position with 'j' key
                elif event.key == pygame.K_j:
                    donuts.append(Donut(mouse_x, mouse_y))
                    selected_donut_index = len(donuts) - 1
                # Delete donut under pointer with 'k' key
                elif event.key == pygame.K_k:
                    if hover_donut_index is not None:
                        del donuts[hover_donut_index]
                        if selected_donut_index == hover_donut_index:
                            selected_donut_index = None
                        elif selected_donut_index is not None and selected_donut_index > hover_donut_index:
                            selected_donut_index -= 1
                # Fill donuts as disks when G key is pressed
                elif event.key == pygame.K_g:
                    # Create the parameter control panel if it doesn't exist
                    if not param_panel.panel_active:
                        param_panel.create_panel()
                    
                    # Create a list to store the temporary Rest objects
                    rest_disks = []
                    rest_radii = []
                    rest_centers = []
                    
                    # Convert each donut to a Rest disk
                    for i, donut in enumerate(donuts):
                        if donut.visible:
                            # Create a Rest disk with the same outer radius as the donut
                            rest = Rest(donut.center_x, donut.center_y, donut.outer_radius)
                            rest_disks.append(rest)
                            rest_radii.append(donut.outer_radius)
                            rest_centers.append((donut.center_x, donut.center_y))
                    
                    # If there are any disks to display
                    if rest_disks:
                        # Clear the screen
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
                        
                        # Draw all Rest disks
                        for i, rest in enumerate(rest_disks):
                            # Display the Rest_n label
                            text = font.render(f"Rest_{i+1} (r={int(rest_radii[i])})", True, WHITE)
                            text_rect = text.get_rect(center=(rest.center_x, rest.center_y))
                            
                            # Draw the Rest disk
                            rest.draw(screen, WHITE, BLACK, YELLOW, False)
                            
                            # Draw the label
                            screen.blit(text, text_rect)
                        
                        # Update the display
                        pygame.display.flip()
                        
                        # Wait for 1 second
                        time.sleep(1)
                        
                        # Hide Rest_n disks and show Expect_n disks
                        screen.fill(BLACK)
                        
                        # Draw FOV borders again
                        if calibration_data and 'fov_corners' in calibration_data:
                            fov_corners = calibration_data['fov_corners']
                            for i in range(len(fov_corners)):
                                start_point = fov_corners[i]
                                end_point = fov_corners[(i + 1) % len(fov_corners)]
                                pygame.draw.line(screen, WHITE, 
                                               (int(start_point[0]), int(start_point[1])),
                                               (int(end_point[0]), int(end_point[1])), 1)
                        
                        # Create and draw Expect_n disks
                        expect_disks = []
                        for i, center in enumerate(rest_centers):
                            # Create an Expect disk with the radius from the parameter panel
                            expect = Expect(center[0], center[1], param_panel.expect_radius)
                            expect_disks.append(expect)
                            
                            # Display the Expect_n label
                            text = font.render(f"Expect_{i+1} (r={param_panel.expect_radius})", True, GREEN)
                            text_rect = text.get_rect(center=(center[0], center[1] - param_panel.expect_radius - 20))
                            
                            # Draw the Expect disk
                            expect.draw(screen, GREEN, BLACK, YELLOW, False)
                            
                            # Draw the label
                            screen.blit(text, text_rect)
                        
                        # Update the display
                        pygame.display.flip()
                        
                        # Wait for 1 second
                        time.sleep(1)
                # Track key state for continuous movement
                elif event.key in keys_pressed:
                    keys_pressed[event.key] = True
            
            elif event.type == pygame.KEYUP:
                # Update key state when released
                if event.key in keys_pressed:
                    keys_pressed[event.key] = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = event.pos
                    
                    # Find donut under pointer
                    donut_index = find_donut_under_pointer(mouse_x, mouse_y)
                    if donut_index is not None:
                        selected_donut_index = donut_index
                        donut = donuts[selected_donut_index]
                        
                        # Different behavior based on visibility
                        if donut.visible:
                            # Calculate distance from center
                            dx = mouse_x - donut.center_x
                            dy = mouse_y - donut.center_y
                            distance = math.sqrt(dx*dx + dy*dy)
                            
                            # Check if clicking on inner circle border
                            if donut.is_point_on_inner_border(mouse_x, mouse_y):
                                donut.dragging_inner = True
                                donut.drag_start_pos = (mouse_x, mouse_y)
                                donut.drag_start_radius_inner = donut.inner_radius
                            
                            # Check if clicking on outer circle border
                            elif donut.is_point_on_outer_border(mouse_x, mouse_y):
                                donut.dragging_outer = True
                                donut.drag_start_pos = (mouse_x, mouse_y)
                                donut.drag_start_radius_outer = donut.outer_radius
                            
                            # Check if clicking inside the donut or inside inner circle
                            elif donut.is_point_inside(mouse_x, mouse_y) or donut.is_point_inside_inner_circle(mouse_x, mouse_y):
                                donut.dragging_center = True
                                donut.drag_start_pos = (mouse_x, mouse_y)
                        else:
                            # For hidden donuts, only allow dragging (no resizing)
                            donut.dragging_center = True
                            donut.drag_start_pos = (mouse_x, mouse_y)
                
                # Mouse wheel for scaling selected donut (only if visible)
                elif (event.button == 4 or event.button == 5) and selected_donut_index is not None:
                    donut = donuts[selected_donut_index]
                    if hover_donut_index == selected_donut_index and donut.visible:  # Only scale if mouse is over the selected donut and it's visible
                        if event.button == 4:  # Scroll up
                            donut.scale(True, SCALE_FACTOR, min_inner_radius, min_radius_gap, max_outer_radius)
                        elif event.button == 5:  # Scroll down
                            donut.scale(False, SCALE_FACTOR, min_inner_radius, min_radius_gap, max_outer_radius)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    # Reset dragging state for all donuts
                    for donut in donuts:
                        donut.dragging_center = False
                        donut.dragging_outer = False
                        donut.dragging_inner = False
            
            elif event.type == pygame.MOUSEMOTION:
                # Handle dragging for selected donut
                if selected_donut_index is not None:
                    donut = donuts[selected_donut_index]
                    
                    if donut.dragging_center:
                        # Move the entire donut
                        mouse_x, mouse_y = event.pos
                        dx = mouse_x - donut.drag_start_pos[0]
                        dy = mouse_y - donut.drag_start_pos[1]
                        donut.move(dx, dy)
                        donut.drag_start_pos = (mouse_x, mouse_y)
                    
                    # Only allow resizing if the donut is visible
                    elif donut.visible and donut.dragging_outer:
                        # Resize the outer circle
                        mouse_x, mouse_y = event.pos
                        dx = mouse_x - donut.center_x
                        dy = mouse_y - donut.center_y
                        new_distance = math.sqrt(dx*dx + dy*dy)
                        donut.resize_outer(new_distance, min_radius_gap, max_outer_radius)
                    
                    elif donut.visible and donut.dragging_inner:
                        # Resize the inner circle
                        mouse_x, mouse_y = event.pos
                        dx = mouse_x - donut.center_x
                        dy = mouse_y - donut.center_y
                        new_distance = math.sqrt(dx*dx + dy*dy)
                        donut.resize_inner(new_distance, min_inner_radius, min_radius_gap)
        
        # Handle continuous keyboard movement for selected donut
        if selected_donut_index is not None and hover_donut_index == selected_donut_index:
            donut = donuts[selected_donut_index]
            speed = MOVE_SPEED_FAST if keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT] else MOVE_SPEED
            
            if keys_pressed[pygame.K_LEFT]:
                donut.move(-speed, 0)
            if keys_pressed[pygame.K_RIGHT]:
                donut.move(speed, 0)
            if keys_pressed[pygame.K_UP]:
                donut.move(0, -speed)
            if keys_pressed[pygame.K_DOWN]:
                donut.move(0, speed)
                
            # Handle continuous scaling with - and = keys (only if donut is visible)
            if donut.visible and (keys_pressed[pygame.K_EQUALS] or keys_pressed[pygame.K_MINUS]):
                scale_delay += 1
                if scale_delay >= SCALE_DELAY_MAX:
                    scale_delay = 0
                    if keys_pressed[pygame.K_EQUALS]:  # = key for growing
                        donut.scale(True, KEYBOARD_SCALE_FACTOR, min_inner_radius, min_radius_gap, max_outer_radius)
                    if keys_pressed[pygame.K_MINUS]:  # - key for shrinking
                        donut.scale(False, KEYBOARD_SCALE_FACTOR, min_inner_radius, min_radius_gap, max_outer_radius)
        
        # Clear the screen
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
        
        # Draw all donuts
        for i, donut in enumerate(donuts):
            donut.draw(screen, WHITE, BLACK, YELLOW, i == selected_donut_index)
        
        # Draw radius values for selected donut
        if selected_donut_index is not None:
            donut = donuts[selected_donut_index]
            outer_text = font.render(f"Outer: {int(donut.outer_radius)}", True, WHITE)
            inner_text = font.render(f"Inner: {int(donut.inner_radius)}", True, WHITE)
            screen.blit(outer_text, (20, 20))
            screen.blit(inner_text, (20, 50))
        
        # Draw instructions
        instructions = [
            "ESC: Exit",
            "Arrow keys: Move donut (hold Shift for faster movement)",
            "Mouse wheel: Scale donut quickly",
            "-/= keys: Scale donut precisely",
            "Drag center/inside: Move donut",
            "Drag inner circle: Resize inner radius",
            "Drag outer circle: Resize outer radius",
            "H: Toggle donut visibility",
            "J: Add new donut at pointer position",
            "K: Delete donut under pointer",
            "G: Start Rest/Expect disk sequence with parameter control"
        ]
        
        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, GREEN)
            screen.blit(text, (20, 100 + i * 15))  # Reduced vertical spacing
        
        # Update the display
        pygame.display.flip()
        clock.tick(60)
    
    # Save donut parameters before quitting
    if donuts:
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            params_file = os.path.join(script_dir, 'donut_params.json')
            
            with open(params_file, 'w') as f:
                json.dump([donut.to_dict() for donut in donuts], f)
            print(f"Donut parameters saved successfully to {params_file}")
        except Exception as e:
            print(f"Error saving donut parameters: {e}")
    
    # Signal the focus thread to exit
    running = False
    
    # Close the parameter control panel if it's open
    param_panel.on_close()
    
    # Quit Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
