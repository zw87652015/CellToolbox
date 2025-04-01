"""
Single Droplet Cell Detection
----------------------------
A module for detecting and analyzing cells within a user-selected rectangular area.
Uses ToupCam camera input and implements rectangle selection for cell identification.
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
import toupcam

# Add parent directory to path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the toupcam SDK path to the Python path
sdk_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'toupcamsdk.20241216', 'python')
sys.path.append(sdk_path)

# Add the DLL directory to the PATH environment variable
dll_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'toupcamsdk.20241216', 'win', 'x64')
os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']

# Explicitly load the DLL using ctypes
toupcam_dll_path = os.path.join(dll_path, 'toupcam.dll')
if os.path.exists(toupcam_dll_path):
    try:
        toupcam_dll = ctypes.WinDLL(toupcam_dll_path)
        print(f"Successfully loaded ToupCam DLL from: {toupcam_dll_path}")
    except Exception as e:
        print(f"Error loading ToupCam DLL: {e}")
else:
    print(f"ToupCam DLL not found at: {toupcam_dll_path}")

try:
    import toupcam
    print(f"Successfully imported toupcam module from: {sdk_path}")
except ImportError as e:
    print(f"Error importing toupcam module: {e}")
    sys.exit(1)

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
            self.root.title("ToupCam Single Droplet Cell Detection")
            self.owns_root = True
        else:
            self.root = root
            self.owns_root = False
        
        # Initialize donut parameters
        self.donut_inner_scale = 1.2  # Inner circle is 1.2x the cell radius
        self.donut_outer_scale = 2.0  # Outer circle is 2x the cell radius
        
        # Initialize camera variables
        self.hcam = None
        self.cam_buffer = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.auto_exposure = True
        self.exposure_time = 16667  # Default to 16.67ms (60Hz anti-flicker)
        self.gain = 100  # Default gain
        self.light_source = 2  # Default to 60Hz (North America)
        
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
        
        # Start camera
        self.start_camera()
        
        # Start Pygame update thread
        self.pygame_thread = threading.Thread(target=self.update_pygame)
        self.pygame_thread.daemon = True
        self.pygame_thread.start()
        
        # Start window focus maintenance thread
        self.focus_thread = threading.Thread(target=self.maintain_window_focus)
        self.focus_thread.daemon = True
        self.focus_thread.start()
    
    def start_camera(self):
        """Initialize and start the ToupCam camera"""
        devices = toupcam.Toupcam.EnumV2()
        if not devices:
            messagebox.showerror("Camera Error", "No ToupCam cameras found")
            self.status_var.set("No ToupCam cameras found")
            return
        
        device = devices[0]  # Use the first camera
        
        # Update camera info
        self.status_var.set(f"Connecting to camera: {device.displayname}")
        
        # Try to open the camera
        try:
            self.hcam = toupcam.Toupcam.Open(device.id)
            if not self.hcam:
                self.status_var.set("Failed to open camera")
                return
            
            # Get camera properties
            self.frame_width, self.frame_height = self.hcam.get_Size()
            
            # Calculate buffer size
            bufsize = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(bufsize)
            
            # Create frame buffer for OpenCV
            self.frame_buffer = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
            
            # Set camera options for low latency
            try:
                # Set low latency mode if available
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_NOPACKET_TIMEOUT, 0)  # Disable packet timeout
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimum frame buffer
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_PROCESSMODE, 0)  # Raw mode for lower latency
                self.hcam.put_RealTime(True)  # Enable real-time mode
                
                # Set 60Hz anti-flicker (common in North America)
                self.hcam.put_HZ(self.light_source)
                
                # Set manual exposure with optimal time for 60Hz (16.67ms)
                self.hcam.put_AutoExpoEnable(False)
                self.hcam.put_ExpoTime(self.exposure_time)
                
            except toupcam.HRESULTException as ex:
                print(f"Could not set camera options: 0x{ex.hr & 0xffffffff:x}")
            
            # Start the camera with callback
            self.running = True
            self.hcam.StartPullModeWithCallback(self.camera_callback, self)
            
            self.status_var.set("Camera started successfully")
            
        except toupcam.HRESULTException as ex:
            self.status_var.set(f"Error initializing camera: 0x{ex.hr & 0xffffffff:x}")
    
    @staticmethod
    def camera_callback(nEvent, ctx):
        """Static callback function for the camera events"""
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            ctx.process_image()
        elif nEvent == toupcam.TOUPCAM_EVENT_EXPOSURE:
            ctx.status_var.set("Auto exposure adjustment in progress")
        elif nEvent == toupcam.TOUPCAM_EVENT_TEMPTINT:
            ctx.status_var.set("White balance adjustment in progress")
        elif nEvent == toupcam.TOUPCAM_EVENT_ERROR:
            ctx.status_var.set("Camera error occurred")
        elif nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
            ctx.status_var.set("Camera disconnected")
    
    def process_image(self):
        """Process the image received from the camera"""
        if not self.running or not self.hcam:
            return
        
        try:
            # Pull the image from the camera with minimal processing
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Convert the raw buffer to a numpy array
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8)
            
            # Reshape the array to an image format
            frame = frame.reshape((self.frame_height, toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3, 3))
            frame = frame[:, :self.frame_width, :]
            
            # Store the frame (no copy to reduce latency)
            self.frame_buffer = frame
            
            # Update UI with the new frame
            self.root.after_idle(self.update_frame)
            
        except toupcam.HRESULTException as ex:
            print(f"Error pulling image: 0x{ex.hr & 0xffffffff:x}")
    
    def update_frame(self):
        """Update the UI with the latest frame"""
        if not self.running or self.frame_buffer is None:
            return
        
        # Make a copy of the frame for processing
        frame = self.frame_buffer.copy()
        
        # Convert BGR to RGB for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Draw rectangle if we're selecting
        if self.rect_start and self.rect_end:
            x1, y1 = self.rect_start
            x2, y2 = self.rect_end
            cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw detected cells if detection is active
        if self.detection_active and self.rect:
            for cell in self.detected_cells:
                # Draw circle at cell center
                cv2.circle(frame_rgb, 
                          (int(cell.center[0]), int(cell.center[1])), 
                          int(cell.radius), 
                          (0, 0, 255), 
                          2)
                
                # Draw bounding box
                if cell.bbox:
                    x, y, w, h = cell.bbox
                    cv2.rectangle(frame_rgb, (x, y), (x+w, y+h), (255, 0, 0), 1)
        
        # Convert to PhotoImage for display
        h, w = frame_rgb.shape[:2]
        img = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image=img)
        
        # Update canvas
        self.canvas.config(width=w, height=h)
        self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        self.canvas.image = photo  # Keep a reference to prevent garbage collection
        
        # Update cell info
        if self.detection_active:
            self.update_cell_info()
        
        # If in camera view mode, schedule next update
        if self.view_mode_var.get() == "Camera":
            self.root.after(10, self.update_frame)
            
    def update_camera(self):
        """Legacy method - no longer needed with ToupCam callback approach"""
        pass
    
    def create_ui(self):
        """Create the application UI"""
        # Create frames
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.Frame(main_frame, width=200)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create camera canvas
        self.canvas = tk.Canvas(display_frame, width=640, height=480, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Create control buttons
        ttk.Button(control_frame, text="Detect Cells", command=self.toggle_detection).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Save Cells", command=self.save_selected_cells).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Clear Selection", command=self.clear_selection).pack(fill=tk.X, pady=5)
        
        # View toggle button
        self.view_toggle_button = ttk.Button(control_frame, text="Switch to Donut View", command=self.toggle_view_mode)
        self.view_toggle_button.pack(fill=tk.X, pady=5)
        
        # Create donut parameter controls
        donut_frame = ttk.LabelFrame(control_frame, text="Donut Parameters")
        donut_frame.pack(fill=tk.X, pady=10)
        
        # Inner radius scale
        inner_frame = ttk.Frame(donut_frame)
        inner_frame.pack(fill=tk.X, pady=5)
        ttk.Label(inner_frame, text="Inner Scale:").pack(side=tk.LEFT)
        inner_scale = ttk.Scale(inner_frame, from_=1.0, to=2.0, orient=tk.HORIZONTAL,
                              command=lambda v: self.update_donut_params('inner', float(v)))
        inner_scale.set(self.donut_inner_scale)
        inner_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Outer radius scale
        outer_frame = ttk.Frame(donut_frame)
        outer_frame.pack(fill=tk.X, pady=5)
        ttk.Label(outer_frame, text="Outer Scale:").pack(side=tk.LEFT)
        outer_scale = ttk.Scale(outer_frame, from_=1.5, to=4.0, orient=tk.HORIZONTAL,
                              command=lambda v: self.update_donut_params('outer', float(v)))
        outer_scale.set(self.donut_outer_scale)
        outer_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Cell information display
        info_frame = ttk.LabelFrame(control_frame, text="Cell Information")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.cell_info_var = tk.StringVar(value="No cells detected")
        cell_info_label = ttk.Label(info_frame, textvariable=self.cell_info_var, justify=tk.LEFT)
        cell_info_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
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
                        cam_width = self.calibration_data.get('camera_resolution', {}).get('width', self.frame_width)
                        cam_height = self.calibration_data.get('camera_resolution', {}).get('height', self.frame_height)
                        
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
        self.canvas.delete("rect")
        
        # Get display dimensions
        display_width = self.canvas.winfo_width()
        display_height = self.canvas.winfo_height()
        
        # Convert to camera coordinates
        x = int(event.x * self.frame_width / display_width)
        y = int(event.y * self.frame_height / display_height)
        
        # Store start position
        self.rect_start = (x, y)
        self.rect_end = (x, y)  # Initialize end to start
    
    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if not self.rect_start:
            return
        
        # Get display dimensions
        display_width = self.canvas.winfo_width()
        display_height = self.canvas.winfo_height()
        
        # Convert to camera coordinates
        x = int(event.x * self.frame_width / display_width)
        y = int(event.y * self.frame_height / display_height)
        
        # Update end position
        self.rect_end = (x, y)
        
        # Clear previous rectangle
        self.canvas.delete("rect")
        
        # Draw new rectangle (scaled to display)
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        
        # Scale coordinates to match display size
        x1_scaled = int(x1 * display_width / self.frame_width)
        y1_scaled = int(y1 * display_height / self.frame_height)
        x2_scaled = int(x2 * display_width / self.frame_width)
        y2_scaled = int(y2 * display_height / self.frame_height)
        
        # Draw rectangle on canvas
        self.canvas.create_rectangle(
            x1_scaled, y1_scaled, x2_scaled, y2_scaled,
            outline="red", width=2, tags="rect"
        )
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if not self.rect_start:
            return
        
        # Get display dimensions
        display_width = self.canvas.winfo_width()
        display_height = self.canvas.winfo_height()
        
        # Convert to camera coordinates
        x = int(event.x * self.frame_width / display_width)
        y = int(event.y * self.frame_height / display_height)
        
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
    
    def detect_cells(self):
        """Detect cells in the current frame within the rectangle"""
        if not self.rect:
            self.status_var.set("No rectangle selected")
            return
        
        try:
            # Use the current frame buffer
            if self.frame_buffer is None:
                self.status_var.set("No frame available")
                return
                
            # Make a copy of the frame for processing
            frame = self.frame_buffer.copy()
            
            # Detect cells in ROI
            self.detected_cells = detect_cells_in_roi(frame, self.rect)
            
            # Update status
            self.status_var.set(f"Detected {len(self.detected_cells)} cells")
            
            # Update cell info
            self.update_cell_info()
            
        except Exception as e:
            self.status_var.set(f"Error detecting cells: {str(e)}")
            import traceback
            traceback.print_exc()

    def display_donuts(self):
        """Display white donuts for detected cells on the black background screen"""
        if not self.pygame_initialized or not self.pygame_running:
            self.status_var.set("Pygame not initialized")
            return
            
        if not self.detected_cells:
            self.status_var.set("No cells detected")
            return
            
        try:
            # Get the current frame for reference
            if self.frame_buffer is None:
                self.status_var.set("No frame available")
                return
                
            # Create a black background
            screen_width, screen_height = pygame.display.get_surface().get_size()
            screen = pygame.display.get_surface()
            screen.fill((0, 0, 0))
            
            # Draw donuts for each cell
            for cell in self.detected_cells:
                # Calculate inner and outer radius
                inner_radius = int(cell.radius * self.donut_inner_scale)
                outer_radius = int(cell.radius * self.donut_outer_scale)
                
                # Draw the outer circle (white)
                pygame.draw.circle(screen, (255, 255, 255), 
                                  (int(cell.center[0]), int(cell.center[1])), 
                                  outer_radius)
                
                # Draw the inner circle (black)
                pygame.draw.circle(screen, (0, 0, 0), 
                                  (int(cell.center[0]), int(cell.center[1])), 
                                  inner_radius)
            
            # Update the display
            pygame.display.flip()
            
            # Update status
            self.status_var.set(f"Displaying {len(self.detected_cells)} donuts")
            
        except Exception as e:
            self.status_var.set(f"Error displaying donuts: {str(e)}")
            import traceback
            traceback.print_exc()

    def update_cell_info(self):
        """Update the cell information text"""
        self.cell_info_var.set(f"Selected Cells: {len(self.detected_cells)}")
        
        if not self.detected_cells:
            return
        
        cell_info = ""
        for i, cell in enumerate(self.detected_cells):
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
        self.status_var.set(f"Detected {len(self.detected_cells)} cells in selection")
    
    def save_selected_cells(self):
        """Save selected cells to a file"""
        if not self.detected_cells:
            messagebox.showinfo("No Cells", "No cells selected to save")
            return
        
        # Create data directory if it doesn't exist
        os.makedirs("../data", exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"../data/cells_{timestamp}.json"
        
        # Convert cells to dictionaries
        cell_data = [cell.to_dict() for cell in self.detected_cells]
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(cell_data, f, indent=2)
        
        self.status_var.set(f"Saved {len(self.detected_cells)} cells to {filename}")
        messagebox.showinfo("Cells Saved", f"Saved {len(self.detected_cells)} cells to {filename}")
    
    def clear_selection(self):
        """Clear the current selection"""
        self.rect = None
        self.rect_start = None
        self.rect_end = None
        self.detected_cells = []
        self.selected_cells = []
        
        # Clear canvas
        self.canvas.delete("rect")
        self.canvas.delete("cell")
        
        # Update cell info
        self.update_cell_info()
        
        # Update status
        self.status_var.set("Selection cleared")
    
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
            # Switch to Donut view
            self.view_mode_var.set("Donut")
            self._update_view_button()
            
            # Make sure we have cells detected
            if not self.detected_cells:
                # Try to detect cells if we have a rectangle
                if self.rect:
                    self.detect_cells()
                
                # If still no cells, show error
                if not self.detected_cells:
                    self.status_var.set("No cells detected. Please detect cells first.")
                    # Switch back to camera view
                    self.view_mode_var.set("Camera")
                    self._update_view_button()
                    return
            
            # Display donuts
            self.display_donuts()
            
            # Update status
            self.status_var.set(f"Displaying {len(self.detected_cells)} donuts")
            
        else:
            # Switch to Camera view
            self.view_mode_var.set("Camera")
            self._update_view_button()
            
            # Resume camera updates
            self.update_frame()
            
            # Update status
            self.status_var.set("Camera view active")
            
    def _update_view_button(self):
        """Update the view toggle button text based on the current view mode"""
        current_mode = self.view_mode_var.get()
        if current_mode == "Camera":
            self.view_toggle_button.config(text="Switch to Donut View")
        else:
            self.view_toggle_button.config(text="Switch to Camera View")
    
    def on_close(self):
        """Handle window close event"""
        print("Closing application...")
        
        # Set running flag to False to stop threads
        self.running = False
        self.pygame_running = False
        
        # Release camera with proper cleanup
        if self.hcam:
            camera_ref = self.hcam
            self.hcam = None  # Immediately set to None so we don't try to access it again
            
            try:
                # Create a thread to handle camera cleanup with timeout
                def cleanup_camera():
                    try:
                        print("Attempting to stop camera...")
                        try:
                            camera_ref.Stop()
                            print("Camera stopped successfully")
                        except Exception as e:
                            print(f"Error stopping camera: {e}")
                        
                        print("Attempting to close camera...")
                        try:
                            camera_ref.Close()
                            print("Camera closed successfully")
                        except Exception as e:
                            print(f"Error closing camera: {e}")
                    except Exception as e:
                        print(f"Fatal error in camera cleanup: {e}")
                
                # Start camera cleanup in a separate thread
                cleanup_thread = threading.Thread(target=cleanup_camera)
                cleanup_thread.daemon = True  # Make thread a daemon so it won't block program exit
                cleanup_thread.start()
                
                # Only wait a very short time - don't let it block the application exit
                print("Waiting briefly for camera cleanup...")
                cleanup_thread.join(timeout=0.5)  # Wait max 0.5 second for entire cleanup
                
                if cleanup_thread.is_alive():
                    print("WARNING: Camera cleanup timed out, abandoning camera resources")
            except Exception as e:
                print(f"Error setting up camera cleanup: {e}")
        
        # Wait for threads to finish
        if hasattr(self, 'pygame_thread') and self.pygame_thread.is_alive():
            self.pygame_thread.join(timeout=1.0)
        
        if hasattr(self, 'focus_thread') and self.focus_thread.is_alive():
            self.focus_thread.join(timeout=1.0)
        
        # Quit pygame
        if self.pygame_initialized:
            try:
                pygame.quit()
            except Exception as e:
                print(f"Error quitting pygame: {e}")
        
        # Destroy the root window if we own it
        if self.owns_root:
            self.root.destroy()
        
        print("Application closed successfully")
    
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
