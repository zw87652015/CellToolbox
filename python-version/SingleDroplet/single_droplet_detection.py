"""
Single Droplet Cell Detection
----------------------------
A module for detecting and analyzing cells within a user-selected rectangular area.
Uses USB camera input and implements rectangle selection for cell identification.
"""

import cv2
import numpy as np
import json
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import ctypes
from skimage import filters, morphology, measure, segmentation
import threading
import time
import queue
import pygame
import math
import random

# Add parent directory to path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Win32 constants for window management
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SW_SHOW = 5
SWP_SHOWWINDOW = 0x0040

# Win32 API functions for window management
SetWindowPos = ctypes.windll.user32.SetWindowPos
ShowWindow = ctypes.windll.user32.ShowWindow
BringWindowToTop = ctypes.windll.user32.BringWindowToTop
AttachThreadInput = ctypes.windll.user32.AttachThreadInput
GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
GetCurrentThreadId = ctypes.windll.kernel32.GetCurrentThreadId

# Global variables
CAMERA_INDEX = 0  # Default camera index, can be changed

class DetectedCell:
    """Class to store information about a detected cell"""
    def __init__(self, center, radius, contour=None, bbox=None):
        self.center = center  # (x, y) tuple
        self.radius = radius  # estimated radius
        self.contour = contour  # OpenCV contour points
        self.bbox = bbox  # Bounding box (x, y, w, h)
        
    def __str__(self):
        return f"Cell at ({self.center[0]:.1f}, {self.center[1]:.1f}), radius: {self.radius:.1f}px"
        
    def to_dict(self):
        """Convert to dictionary for saving"""
        return {
            "center_x": float(self.center[0]),
            "center_y": float(self.center[1]),
            "radius": float(self.radius),
            "bbox": self.bbox
        }

def load_calibration_data():
    """Load the latest calibration data"""
    try:
        with open('E:/Documents/Codes/Matlab/CellToolbox/python-version/calibration/latest_calibration.json', 'r') as f:
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

def detect_cells_in_roi(frame, roi_rect, params=None):
    """
    Detect cells within the specified region of interest
    
    Args:
        frame: The input frame (BGR format)
        roi_rect: Rectangle defining the ROI (x, y, width, height)
        params: Optional parameters for cell detection
        
    Returns:
        List of DetectedCell objects
    """
    # Default parameters if none provided
    if params is None:
        params = {
            'area': (100, 5000),
            'perimeter': (30, 1000),
            'circularity': (0.2, 1.0)
        }
    
    # Extract ROI from frame
    x, y, w, h = roi_rect
    roi = frame[y:y+h, x:x+w]
    
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(10, 10))
    enhanced_image = clahe.apply(gray)
    
    # Convert to float and apply Gaussian blur
    float_image = enhanced_image.astype(np.float32) / 255.0
    denoised_image = cv2.GaussianBlur(float_image, (3, 3), 2)
    
    # Kirsch operators for edge detection (4 main directions)
    kirsch_kernels = [
        np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float32),  # Vertical
        np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float32),  # Horizontal
        np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float32),  # Diagonal 1
        np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float32)   # Diagonal 2
    ]

    kirsch_outputs = []
    for kernel in kirsch_kernels:
        # Apply Kirsch filter (keeping float32)
        filtered = cv2.filter2D(denoised_image, -1, kernel)
        
        # Convert to absolute values
        filtered = np.abs(filtered)
        
        # Normalize to 0-1 range
        filtered_min = np.min(filtered)
        filtered_max = np.max(filtered)
        if filtered_max > filtered_min:  # Avoid division by zero
            filtered_norm = (filtered - filtered_min) / (filtered_max - filtered_min)
        else:
            filtered_norm = np.zeros_like(filtered)
        
        # Calculate Otsu threshold
        binary = filtered_norm > filters.threshold_otsu(filtered_norm)
        kirsch_outputs.append(binary)

    # Combine all Kirsch outputs
    binary = np.zeros_like(kirsch_outputs[0], dtype=bool)
    for output in kirsch_outputs:
        binary = binary | output
    
    # Convert to uint8 for contour detection
    binary = binary.astype(np.uint8) * 255

    # Remove small areas
    binary = morphology.remove_small_objects(binary.astype(bool), min_size=100)

    # Clean up - using less aggressive thinning
    binary = morphology.thin(binary, max_num_iter=1)

    # Fill small holes in cells to fix gaps
    binary = morphology.remove_small_holes(binary.astype(bool), area_threshold=100)
    binary = binary.astype(np.uint8) * 255

    # Calculate and filter based on more lenient eccentricity
    labeled = measure.label(binary)
    props = measure.regionprops(labeled)
    mask = np.zeros_like(binary, dtype=bool)
    
    for prop in props:
        # More lenient criteria for eccentricity and area
        if (prop.eccentricity < 0.99 and prop.area > 100) or (prop.area > 300):
            mask[labeled == prop.label] = True
    
    binary = mask.astype(np.uint8) * 255

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Get parameters
    area_min, area_max = params['area']
    perimeter_min, perimeter_max = params['perimeter']
    circularity_min, circularity_max = params['circularity']
    
    # Process each contour and create cell objects
    detected_cells = []
    for contour in contours:
        # Calculate properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Check if the contour meets the criteria
        if (area_min <= area <= area_max and
            perimeter_min <= perimeter <= perimeter_max and
            circularity_min <= circularity <= circularity_max):
            
            # Get bounding box
            bx, by, bw, bh = cv2.boundingRect(contour)
            
            # Calculate center and radius
            moments = cv2.moments(contour)
            if moments["m00"] != 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
            else:
                cx = bx + bw // 2
                cy = by + bh // 2
                
            # Estimate radius as average of half-width and half-height
            radius = (bw + bh) / 4
            
            # Adjust coordinates to original frame
            cx += x
            cy += y
            bx += x
            by += y
            
            # Create cell object
            cell = DetectedCell((cx, cy), radius, contour, (bx, by, bw, bh))
            detected_cells.append(cell)
    
    return detected_cells

def is_cell_in_rectangle(cell, rect):
    """
    Check if a cell is inside or intersects with the rectangle
    
    Args:
        cell: DetectedCell object
        rect: Rectangle (x, y, width, height)
        
    Returns:
        bool: True if cell is inside or intersects with rectangle
    """
    # Rectangle coordinates
    rx, ry, rw, rh = rect
    
    # Cell center
    cx, cy = cell.center
    
    # Cell bounding box
    bx, by, bw, bh = cell.bbox
    
    # Check if cell center is inside rectangle
    center_inside = (rx <= cx <= rx + rw) and (ry <= cy <= ry + rh)
    
    # Check if cell bounding box intersects with rectangle
    intersects = not (bx + bw < rx or bx > rx + rw or by + bh < ry or by > ry + rh)
    
    return center_inside or intersects

class SingleDropletApp:
    """Main application for single droplet cell detection"""
    
    def __init__(self, root=None):
        # Create or use provided root window
        if root is None:
            self.root = tk.Tk()
            self.root.title("Single Droplet Cell Detection")
            self.owns_root = True
        else:
            self.root = root
            self.owns_root = False
        
        # Initialize donut parameters
        self.donut_inner_scale = 1.2  # Inner circle is 1.2x the cell radius
        self.donut_outer_scale = 2.0  # Outer circle is 2x the cell radius
        
        # Initialize camera
        self.camera = cv2.VideoCapture(CAMERA_INDEX)
        if not self.camera.isOpened():
            raise RuntimeError(f"Could not open camera {CAMERA_INDEX}")
        
        # Get camera resolution
        self.cam_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Initialize variables
        self.running = True
        self.detection_active = False
        self.rect = None
        self.rect_start = None
        self.rect_end = None
        self.detected_cells = []
        self.selected_cells = []
        self.show_donuts = False
        self.pygame_running = False
        self.pygame_initialized = False
        self.view_mode_var = tk.StringVar(value="Camera")
        
        # Load calibration data
        self.calibration_data = load_calibration_data()
        
        # Create UI
        self.create_ui()
        
        # Set up protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize pygame directly in the main thread
        self.initialize_pygame()
        
        # Start camera update thread
        self.update_thread = threading.Thread(target=self.update_camera)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Start Pygame update thread
        self.pygame_thread = threading.Thread(target=self.update_pygame)
        self.pygame_thread.daemon = True
        self.pygame_thread.start()
        
        # Start window focus maintenance thread
        self.focus_thread = threading.Thread(target=self.maintain_window_focus)
        self.focus_thread.daemon = True
        self.focus_thread.start()
    
    def create_ui(self):
        """Create the application UI"""
        # Create frames
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        display_frame = ttk.Frame(self.root, padding=10)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create camera canvas
        self.camera_canvas = tk.Canvas(display_frame, width=640, height=480, bg="black")
        self.camera_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.camera_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.camera_canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.camera_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Create control buttons
        ttk.Button(control_frame, text="Detect Cells", command=self.toggle_detection).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Save Selected Cells", command=self.save_selected_cells).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Clear Selection", command=self.clear_selection).pack(fill=tk.X, pady=5)
        
        # Create view mode toggle button
        self.view_toggle_button = ttk.Button(control_frame, text="Switch to Donut View", command=self.toggle_view_mode)
        self.view_toggle_button.pack(fill=tk.X, pady=5)
        
        # Create donut parameter controls
        donut_frame = ttk.LabelFrame(control_frame, text="Donut Parameters", padding=10)
        donut_frame.pack(fill=tk.X, pady=10)
        
        # Inner scale slider
        ttk.Label(donut_frame, text="Inner Scale:").pack(anchor=tk.W)
        inner_scale_var = tk.DoubleVar(value=self.donut_inner_scale)
        inner_scale = ttk.Scale(donut_frame, from_=0.5, to=2.0, variable=inner_scale_var, 
                               command=lambda v: self.update_donut_params('inner', float(v)))
        inner_scale.pack(fill=tk.X)
        
        # Outer scale slider
        ttk.Label(donut_frame, text="Outer Scale:").pack(anchor=tk.W)
        outer_scale_var = tk.DoubleVar(value=self.donut_outer_scale)
        outer_scale = ttk.Scale(donut_frame, from_=1.0, to=4.0, variable=outer_scale_var,
                               command=lambda v: self.update_donut_params('outer', float(v)))
        outer_scale.pack(fill=tk.X)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Cell info text
        self.cell_info_var = tk.StringVar(value="No cells detected")
        cell_info = ttk.Label(control_frame, textvariable=self.cell_info_var, wraplength=200)
        cell_info.pack(fill=tk.X, pady=10)
        
        # Update the UI based on the current view mode
        self.view_mode_var.trace_add("write", lambda *args: self._update_view_button())
    
    def _update_view_button(self):
        """Update the view toggle button text based on the current view mode"""
        current_mode = self.view_mode_var.get()
        if current_mode == "Camera":
            self.view_toggle_button['text'] = "Switch to Donut View"
        else:
            self.view_toggle_button['text'] = "Switch to Camera View"
    
    def initialize_pygame(self):
        """Initialize pygame"""
        print("Initializing pygame...")
        # Initialize pygame
        pygame.init()
        
        # Get projector resolution from calibration data
        try:
            projector_resolution = self.calibration_data.get('projector_resolution', None)
            if projector_resolution and isinstance(projector_resolution, dict):
                projector_width = projector_resolution.get('width', 1024)
                projector_height = projector_resolution.get('height', 768)
            else:
                # Default to 1024x768 if not available or invalid
                projector_width, projector_height = 1024, 768
                print(f"Warning: Using default projector resolution {projector_width}x{projector_height}")
        except Exception as e:
            # Default to 1024x768 if there's an error
            projector_width, projector_height = 1024, 768
            print(f"Warning: Error getting projector resolution, using default {projector_width}x{projector_height}: {str(e)}")
        
        print(f"Creating pygame window with resolution {projector_width}x{projector_height}")
        
        # Create pygame window with projector resolution
        # Use NOFRAME for a simple window
        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
        
        # Create the pygame display
        self.pygame_screen = pygame.display.set_mode((projector_width, projector_height))
        pygame.display.set_caption("Cell Donut Display")
        
        # Fill screen with black to make it visible
        self.pygame_screen.fill((0, 0, 0))
        pygame.display.flip()
        
        # Set window to stay on top
        hwnd = pygame.display.get_wm_info()['window']
        print(f"Window handle: {hwnd}")
        
        # Use multiple Win32 API calls to ensure visibility
        ShowWindow(hwnd, SW_SHOW)
        SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        BringWindowToTop(hwnd)
        
        # Set flag to indicate pygame initialization is complete
        self.pygame_running = True
        self.pygame_initialized = True
        self.show_donuts = True  # Always show donuts
        print("Pygame initialization complete")
    
    def update_pygame(self):
        """Update the Pygame screen"""
        print("Starting pygame update thread")
        
        # Main pygame loop
        while self.pygame_running:
            try:
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.pygame_running = False
                
                # Clear screen with black
                self.pygame_screen.fill((0, 0, 0))
                
                # Draw FOV corners from calibration data
                try:
                    fov_corners = self.calibration_data.get('fov_corners', None)
                    if fov_corners and isinstance(fov_corners, list) and len(fov_corners) >= 4:
                        # Draw FOV outline with thin lines only
                        pygame.draw.lines(self.pygame_screen, (50, 50, 50), True, fov_corners, 1)
                except Exception as e:
                    print(f"Error drawing FOV corners: {str(e)}")
                
                # Draw donuts if enabled
                if self.show_donuts and self.selected_cells:
                    # Get calibration data
                    try:
                        scale = self.calibration_data.get('scale', 1.0)
                        rotation = self.calibration_data.get('rotation', 0.0)
                        offset_x = self.calibration_data.get('offset_x', 0)
                        offset_y = self.calibration_data.get('offset_y', 0)
                        
                        # Get FOV corners for scaling reference
                        fov_corners = self.calibration_data.get('fov_corners', None)
                        
                        # Calculate FOV bounds if available
                        fov_min_x, fov_min_y, fov_max_x, fov_max_y = 0, 0, 0, 0
                        fov_width, fov_height = 0, 0
                        
                        if fov_corners and isinstance(fov_corners, list) and len(fov_corners) >= 4:
                            # Extract x and y coordinates
                            x_coords = [corner[0] for corner in fov_corners]
                            y_coords = [corner[1] for corner in fov_corners]
                            
                            # Calculate bounds
                            fov_min_x = min(x_coords)
                            fov_max_x = max(x_coords)
                            fov_min_y = min(y_coords)
                            fov_max_y = max(y_coords)
                            
                            # Calculate dimensions
                            fov_width = fov_max_x - fov_min_x
                            fov_height = fov_max_y - fov_min_y
                        
                        # Get camera and projector resolutions
                        cam_width = self.calibration_data.get('camera_resolution', {}).get('width', self.cam_width)
                        cam_height = self.calibration_data.get('camera_resolution', {}).get('height', self.cam_height)
                        
                        # Print debug info
                        print(f"Selected cells: {len(self.selected_cells)}")
                        print(f"FOV bounds: ({fov_min_x}, {fov_min_y}) to ({fov_max_x}, {fov_max_y})")
                        print(f"Camera resolution: {cam_width}x{cam_height}")
                        
                        # Draw each cell as a donut
                        for cell in self.selected_cells:
                            try:
                                # Get cell center and radius
                                # Check cell structure - it could be a tuple or an object
                                if hasattr(cell, 'center') and hasattr(cell, 'radius'):
                                    # Cell is an object with center and radius attributes
                                    center = cell.center
                                    radius = cell.radius
                                elif isinstance(cell, tuple) and len(cell) == 2:
                                    # Cell is a tuple of ((x, y), radius)
                                    center, radius = cell
                                else:
                                    # Unknown structure, print and skip
                                    print(f"Unknown cell structure: {cell}")
                                    continue
                                
                                # Extract x, y from center
                                if isinstance(center, tuple) and len(center) == 2:
                                    x, y = center
                                else:
                                    print(f"Invalid center format: {center}")
                                    continue
                                
                                # Map camera coordinates directly to FOV space
                                if fov_width > 0 and fov_height > 0 and cam_width > 0 and cam_height > 0:
                                    # Normalize camera coordinates (0-1)
                                    x_norm = x / cam_width
                                    y_norm = y / cam_height
                                    
                                    # Map to FOV space
                                    x_final = int(fov_min_x + x_norm * fov_width)
                                    y_final = int(fov_min_y + y_norm * fov_height)
                                    
                                    # Ensure coordinates are within FOV bounds
                                    x_final = max(fov_min_x, min(x_final, fov_max_x))
                                    y_final = max(fov_min_y, min(y_final, fov_max_y))
                                    
                                    # Scale radius relative to FOV
                                    radius_scale = min(fov_width, fov_height) / 20  # Adjust this factor as needed
                                    scaled_radius = radius * (radius_scale / 100)
                                else:
                                    # Fallback to original transformation
                                    # Apply calibration transformations
                                    x_rot = x * math.cos(math.radians(rotation)) - y * math.sin(math.radians(rotation))
                                    y_rot = x * math.sin(math.radians(rotation)) + y * math.cos(math.radians(rotation))
                                    
                                    # Scale
                                    x_scaled = x_rot * scale
                                    y_scaled = y_rot * scale
                                    
                                    # Apply offset
                                    x_final = int(x_scaled + offset_x)
                                    y_final = int(y_scaled + offset_y)
                                    scaled_radius = radius * scale
                                
                                # Calculate inner and outer radii
                                inner_radius = int(scaled_radius * self.donut_inner_scale)
                                outer_radius = int(scaled_radius * self.donut_outer_scale)
                                
                                # Ensure radius is reasonable
                                max_radius = min(fov_width, fov_height) // 10
                                outer_radius = min(outer_radius, max_radius)
                                inner_radius = min(inner_radius, outer_radius - 1)
                                
                                # Draw outer circle (filled white)
                                pygame.draw.circle(self.pygame_screen, (255, 255, 255), (x_final, y_final), outer_radius)
                                
                                # Draw inner circle (filled black) to create donut effect
                                pygame.draw.circle(self.pygame_screen, (0, 0, 0), (x_final, y_final), inner_radius)
                                
                                print(f"Drawing donut at ({x_final}, {y_final}) with inner radius {inner_radius} and outer radius {outer_radius}")
                            except Exception as e:
                                print(f"Error drawing individual cell: {str(e)}")
                                import traceback
                                traceback.print_exc()
                    
                    except Exception as e:
                        print(f"Error drawing donuts: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                # Update display
                pygame.display.flip()
                
                # Cap the frame rate
                pygame.time.delay(30)  # ~33 fps
                
            except Exception as e:
                print(f"Error in pygame update: {str(e)}")
                time.sleep(0.1)
        
        print("Pygame update thread exiting")
    
    def maintain_window_focus(self):
        """Maintain window focus for the pygame window"""
        print("Starting window focus maintenance thread")
        
        # Wait for pygame to initialize
        while not self.pygame_initialized and self.running:
            time.sleep(0.1)
        
        # Get window handle
        try:
            hwnd = pygame.display.get_wm_info()['window']
            print(f"Focus thread got window handle: {hwnd}")
            
            # Initial window setup - make it visible once
            ShowWindow(hwnd, SW_SHOW)
            
            # Keep the window visible but not forcefully in foreground
            SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            print("Window visibility set up - not forcing foreground")
            
            # Just keep the thread alive without forcing focus
            while self.pygame_running and self.running:
                time.sleep(1.0)
                
        except Exception as e:
            print(f"Error in window setup: {str(e)}")
        
        print("Window focus maintenance thread exiting")
    
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        # Clear previous rectangle
        self.camera_canvas.delete("rect")
        
        # Get display dimensions
        display_width = self.camera_canvas.winfo_width()
        display_height = self.camera_canvas.winfo_height()
        
        # Convert to camera coordinates
        x = int(event.x * self.cam_width / display_width)
        y = int(event.y * self.cam_height / display_height)
        
        # Store start position
        self.rect_start = (x, y)
        self.rect_end = (x, y)  # Initialize end to start
    
    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if not self.rect_start:
            return
        
        # Get display dimensions
        display_width = self.camera_canvas.winfo_width()
        display_height = self.camera_canvas.winfo_height()
        
        # Convert to camera coordinates
        x = int(event.x * self.cam_width / display_width)
        y = int(event.y * self.cam_height / display_height)
        
        # Update end position
        self.rect_end = (x, y)
        
        # Clear previous rectangle
        self.camera_canvas.delete("rect")
        
        # Draw new rectangle (scaled to display)
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        
        # Scale coordinates to match display size
        x1_scaled = int(x1 * display_width / self.cam_width)
        y1_scaled = int(y1 * display_height / self.cam_height)
        x2_scaled = int(x2 * display_width / self.cam_width)
        y2_scaled = int(y2 * display_height / self.cam_height)
        
        # Draw rectangle on canvas
        self.camera_canvas.create_rectangle(
            x1_scaled, y1_scaled, x2_scaled, y2_scaled,
            outline="red", width=2, tags="rect"
        )
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if not self.rect_start:
            return
        
        # Get display dimensions
        display_width = self.camera_canvas.winfo_width()
        display_height = self.camera_canvas.winfo_height()
        
        # Convert to camera coordinates
        x = int(event.x * self.cam_width / display_width)
        y = int(event.y * self.cam_height / display_height)
        
        # Update end position
        self.rect_end = (x, y)
        
        # Calculate rectangle in (x, y, width, height) format
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        
        # Ensure x1 <= x2 and y1 <= y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Calculate width and height
        w = x2 - x1
        h = y2 - y1
        
        # Store rectangle
        self.rect = (x1, y1, w, h)
        
        # Update status
        self.status_var.set(f"Rectangle selected: ({x1}, {y1}, {w}, {h})")
    
    def update_camera(self):
        """Update camera feed"""
        while self.running:
            try:
                # Read frame from camera
                ret, frame = self.camera.read()
                if not ret:
                    self.status_var.set("Error: Could not read from camera")
                    time.sleep(0.1)
                    continue
                
                # Convert to RGB for tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize for display
                display_width = self.camera_canvas.winfo_width()
                display_height = self.camera_canvas.winfo_height()
                
                # Ensure valid dimensions
                if display_width > 1 and display_height > 1:
                    frame_resized = cv2.resize(frame_rgb, (display_width, display_height))
                    
                    # Convert to PhotoImage
                    img = Image.fromarray(frame_resized)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    # Update canvas
                    self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.camera_canvas.image = imgtk  # Keep reference
                
                # Draw rectangle if being drawn or already drawn
                if self.rect_start and self.rect_end:
                    x1, y1 = self.rect_start
                    x2, y2 = self.rect_end
                    
                    # Scale coordinates to match display size
                    x1_scaled = int(x1 * display_width / self.cam_width)
                    y1_scaled = int(y1 * display_height / self.cam_height)
                    x2_scaled = int(x2 * display_width / self.cam_width)
                    y2_scaled = int(y2 * display_height / self.cam_height)
                    
                    # Draw rectangle on canvas
                    self.camera_canvas.create_rectangle(
                        x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                        outline="red", width=2, tags="rect"
                    )
                
                # Draw detected cells on the camera view
                if hasattr(self, 'detected_cells') and self.detected_cells:
                    # Clear previous cell markers
                    self.camera_canvas.delete("cell")
                    
                    # Draw circles for each detected cell
                    for cell in self.detected_cells:
                        # Scale coordinates to match display size
                        center_x = int(cell.center[0] * display_width / self.cam_width)
                        center_y = int(cell.center[1] * display_height / self.cam_height)
                        radius = int(cell.radius * display_width / self.cam_width)
                        
                        # Draw circle for each cell
                        color = "green" if cell in self.selected_cells else "blue"
                        self.camera_canvas.create_oval(
                            center_x - radius, center_y - radius,
                            center_x + radius, center_y + radius,
                            outline=color, width=2, tags="cell"
                        )
                
                # Store the current frame for use in detect_cells
                self.current_frame = frame
                
                # Sleep to reduce CPU usage
                time.sleep(0.03)  # ~30 fps
                
            except Exception as e:
                print(f"Error in camera update: {str(e)}")
                time.sleep(0.1)
    
    def detect_cells(self):
        """Detect cells in the current frame within the rectangle"""
        if not self.rect:
            self.status_var.set("No rectangle selected")
            return
        
        try:
            # Use the stored current frame
            if not hasattr(self, 'current_frame'):
                self.status_var.set("No frame available")
                return
                
            frame = self.current_frame
            
            # Detect cells in ROI
            self.detected_cells = detect_cells_in_roi(frame, self.rect)
            
            # Filter cells that are inside or intersect with the rectangle
            self.selected_cells = [cell for cell in self.detected_cells 
                                  if is_cell_in_rectangle(cell, self.rect)]
            
            # Update cell info
            self.update_cell_info()
            
            # Update status
            self.status_var.set(f"Detected {len(self.detected_cells)} cells, {len(self.selected_cells)} selected")
            
            # Update pygame display if enabled
            if self.show_donuts:
                print(f"Updating pygame with {len(self.selected_cells)} cells")
        
        except Exception as e:
            self.status_var.set(f"Error detecting cells: {str(e)}")
            print(f"Error in detect_cells: {str(e)}")
    
    def update_cell_info(self):
        """Update the cell information text"""
        self.cell_info_var.set(f"Selected Cells: {len(self.selected_cells)}")
        
        if not self.selected_cells:
            return
        
        cell_info = ""
        for i, cell in enumerate(self.selected_cells):
            cell_info += f"Cell {i+1}:\n"
            cell_info += f"  Center: ({cell.center[0]:.1f}, {cell.center[1]:.1f})\n"
            cell_info += f"  Radius: {cell.radius:.1f} px\n"
            cell_info += f"  Bounding Box: {cell.bbox}\n\n"
        
        self.cell_info_var.set(cell_info)
    
    def toggle_detection(self):
        """Detect cells once when button is clicked"""
        if not self.rect:
            self.status_var.set("Please draw a rectangle first")
            return
            
        # Run cell detection once
        self.detect_cells()
        
        # Update status
        self.status_var.set(f"Detected {len(self.selected_cells)} cells in selection")
    
    def save_selected_cells(self):
        """Save selected cells to a file"""
        if not self.selected_cells:
            messagebox.showinfo("No Cells", "No cells selected to save")
            return
        
        # Create data directory if it doesn't exist
        os.makedirs("../data", exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"../data/cells_{timestamp}.json"
        
        # Convert cells to dictionaries
        cell_data = [cell.to_dict() for cell in self.selected_cells]
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(cell_data, f, indent=2)
        
        self.status_var.set(f"Saved {len(self.selected_cells)} cells to {filename}")
        messagebox.showinfo("Cells Saved", f"Saved {len(self.selected_cells)} cells to {filename}")
    
    def clear_selection(self):
        """Clear the current selection"""
        self.rect = None
        self.rect_start = None
        self.rect_end = None
        self.detected_cells = []
        self.selected_cells = []
        
        # Clear canvas
        self.camera_canvas.delete("rect")
        self.camera_canvas.delete("cell")
        
        # Update cell info
        self.update_cell_info()
        
        # Update status
        self.status_var.set("Selection cleared")
    
    def display_donuts(self):
        """Display white donuts for detected cells on the black background screen"""
        if not self.selected_cells:
            if self.rect is None:
                self.status_var.set("No rectangle selected")
                return
                
            ret, frame = self.camera.read()
            if not ret:
                self.status_var.set("Error: Could not read from camera")
                return
            
            # Detect cells
            self.detected_cells = detect_cells_in_roi(frame, self.rect)
            
            # Filter cells that are inside or intersect with the rectangle
            self.selected_cells = [cell for cell in self.detected_cells 
                                  if is_cell_in_rectangle(cell, self.rect)]
            
            # Update cell information
            self.update_cell_info()
        
        if not self.selected_cells:
            self.status_var.set("No cells detected")
            return
        
        # Get calibration data
        scale = self.calibration_data['scale']
        rotation = self.calibration_data['rotation']
        offset_x = self.calibration_data['offset_x']
        offset_y = self.calibration_data['offset_y']
        
        # Enable donut display in pygame thread
        self.show_donuts = True
        
        # Set status
        self.status_var.set(f"Displaying {len(self.selected_cells)} donuts on black screen")
        
        # Make sure pygame is initialized
        if not self.pygame_initialized:
            self.status_var.set("Waiting for pygame initialization...")
            # Wait for pygame to initialize
            for _ in range(50):  # Wait up to 5 seconds
                if self.pygame_initialized:
                    break
                time.sleep(0.1)
            
            if not self.pygame_initialized:
                self.status_var.set("Error: Pygame initialization timed out")
                return
        
        # Since the window is always visible, just ensure it's in focus
        hwnd = pygame.display.get_wm_info()['window']
        BringWindowToTop(hwnd)
    
    def update_donut_params(self, param_type, value):
        """Update donut parameters"""
        if param_type == 'inner':
            self.donut_inner_scale = value
        elif param_type == 'outer':
            self.donut_outer_scale = value
    
    def toggle_view_mode(self):
        """Toggle between camera and donut view"""
        current_mode = self.view_mode_var.get()
        
        if current_mode == "Camera":
            # Switch to donut view
            self.view_mode_var.set("Donuts")
            self.show_donuts = True
            
            # Make sure pygame window is visible
            if self.pygame_initialized:
                try:
                    hwnd = pygame.display.get_wm_info()['window']
                    ShowWindow(hwnd, SW_SHOW)
                    SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
                    BringWindowToTop(hwnd)
                    print("Showing pygame window")
                except Exception as e:
                    print(f"Error showing pygame window: {str(e)}")
        else:
            # Switch to camera view
            self.view_mode_var.set("Camera")
            
            # Don't hide pygame window, just stop showing donuts
            # This ensures the window remains initialized
            self.show_donuts = False
            print("Hiding donuts")
    
    def on_close(self):
        """Handle window close event"""
        self.running = False
        self.pygame_running = False
        
        # Release camera
        if self.camera is not None:
            self.camera.release()
        
        # Wait for threads to finish
        if hasattr(self, 'update_thread') and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        
        if hasattr(self, 'pygame_thread') and self.pygame_thread.is_alive():
            self.pygame_thread.join(timeout=1.0)
        
        # Quit pygame
        pygame.quit()
        
        # Destroy root window if we own it
        if self.owns_root:
            self.root.destroy()
        
        # Force exit if threads are still running
        import sys
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        if self.owns_root:
            self.root.mainloop()

def main():
    """Main function to start the application"""
    try:
        app = SingleDropletApp()
        app.run()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
