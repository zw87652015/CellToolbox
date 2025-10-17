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
from datetime import datetime, timezone, timedelta

# Import exposure control panel
from exposure_control_panel import ExposureControlPanel

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
        # Use relative path from the current script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        calibration_path = os.path.join(os.path.dirname(script_dir), 'calibration', 'latest_calibration.json')
        with open(calibration_path, 'r') as f:
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
    # Check for empty ROI
    if roi_rect is None or roi_rect[2] <= 0 or roi_rect[3] <= 0:
        return []
    
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
    
    # Validate ROI is not empty
    if roi.size == 0 or roi.shape[0] == 0 or roi.shape[1] == 0:
        print(f"Warning: Empty ROI detected - roi_rect: {roi_rect}, roi.shape: {roi.shape}")
        return []
    
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
        
        # Pattern/Cell Size Ratio parameter
        self.pattern_cell_size_ratio = 1.0  # Default 1:1 ratio between disk and cell size
        
        # Initialize camera variables
        self.hcam = None
        self.cam_buffer = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.auto_exposure = True
        self.exposure_time = 8333   # Default to 8.333ms for higher FPS
        self.gain = 100  # Default gain
        self.light_source = 2  # Default to 60Hz (North America)
        
        # Threading and performance optimization
        self.frame_lock = threading.Lock()
        self.render_running = False
        self.render_thread = None
        self.detection_thread = None
        self.detection_queue = queue.Queue(maxsize=2)  # Small queue to avoid memory buildup
        self.detection_results = []
        self.detection_lock = threading.Lock()
        self.raw_mode = False  # Track RAW mode state
        
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
        
        # Debug mode
        self.debug_mode = False
        self.debug_dot_camera = None  # Store debug dot position in camera coordinates
        self.debug_dot_screen = None  # Store debug dot position in screen coordinates
        self.debug_camera_corners = None  # Store mapped camera corners
        self.debug_fov_corners = None  # Store FOV corners
        
        # Load calibration data
        self.calibration_data = load_calibration_data()
        
        # Initialize exposure control panel
        self.exposure_control_panel = None
        
        # Create UI
        self.create_ui()
        
        # Set up protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize pygame directly in the main thread
        self.initialize_pygame()
        
        # Start camera
        self.start_camera()
        
        # Start render thread for high-performance UI updates
        self.start_render_thread()
        
        # Start cell detection thread
        self.start_detection_thread()
        
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
            
            # Set camera options for low latency and manual exposure
            try:
                # First, disable auto exposure
                print("Disabling auto exposure...")
                self.hcam.put_AutoExpoEnable(False)
                self.auto_exposure = False
                print("Auto exposure disabled")
                
                # Set manual exposure time (8.333ms)
                print(f"Setting exposure time to {self.exposure_time} microseconds...")
                self.hcam.put_ExpoTime(self.exposure_time)
                print(f"Exposure time set to {self.exposure_time} microseconds")
                
            except toupcam.HRESULTException as ex:
                print(f"Error setting exposure: 0x{ex.hr & 0xffffffff:x}")
                
            # Set other camera options separately
            try:
                # Set 60Hz anti-flicker (common in North America)
                self.hcam.put_HZ(self.light_source)
                print(f"Anti-flicker set to {self.light_source} (60Hz)")
            except toupcam.HRESULTException as ex:
                print(f"Could not set anti-flicker: 0x{ex.hr & 0xffffffff:x}")
                
            try:
                # Set low latency options
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimum frame buffer
                self.hcam.put_RealTime(True)  # Enable real-time mode
                print("Low latency options set")
            except toupcam.HRESULTException as ex:
                print(f"Could not set low latency options: 0x{ex.hr & 0xffffffff:x}")
                
            # Set white balance settings
            try:
                # Set white balance temperature and tint
                print("Setting white balance...")
                self.hcam.put_TempTint(5335, 1177)  # Temp=5335, Tint=1177
                print("White balance set to Temp=5335, Tint=1177")
            except toupcam.HRESULTException as ex:
                print(f"Could not set white balance: 0x{ex.hr & 0xffffffff:x}")
            
            # Start the camera with callback
            self.running = True
            self.hcam.StartPullModeWithCallback(self.camera_callback, self)
            
            self.status_var.set("Camera started successfully")
            
        except toupcam.HRESULTException as ex:
            self.status_var.set(f"Error initializing camera: 0x{ex.hr & 0xffffffff:x}")
    
    @staticmethod
    def camera_callback(nEvent, ctx):
        """Static callback function for the camera events - optimized for minimal latency"""
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            ctx.process_image()
        elif nEvent == toupcam.TOUPCAM_EVENT_EXPOSURE:
            pass  # Minimize callback processing for performance
        elif nEvent == toupcam.TOUPCAM_EVENT_TEMPTINT:
            pass  # Minimize callback processing for performance
        elif nEvent == toupcam.TOUPCAM_EVENT_ERROR:
            ctx.status_var.set("Camera error occurred")
        elif nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
            ctx.status_var.set("Camera disconnected")
    
    def process_image(self):
        """Process the image received from the camera - optimized for zero-copy performance"""
        if not self.running or not self.hcam:
            return
    
        try:
            # Always pull as RGB24 for live view (regardless of RAW mode setting)
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Calculate buffer size and stride
            buffer_size = len(self.cam_buffer)
            expected_rgb_size = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            stride = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3
            
            # Debug info
            if buffer_size != expected_rgb_size:
                print(f"Buffer size mismatch: got {buffer_size}, expected {expected_rgb_size}")
                print(f"Frame dimensions: {self.frame_width}x{self.frame_height}")
                print(f"Stride: {stride}")
                
                # Try to use the actual buffer size to determine correct dimensions
                actual_stride = buffer_size // self.frame_height // 3
                if actual_stride > 0:
                    stride = actual_stride
                    print(f"Using calculated stride: {stride}")
            
            # Reshape with error handling
            try:
                frame = np.frombuffer(self.cam_buffer, dtype=np.uint8).reshape(
                    (self.frame_height, stride, 3))[:, :self.frame_width, :]
            except ValueError as e:
                print(f"Reshape error: {e}")
                print(f"Buffer size: {buffer_size}, trying to reshape to ({self.frame_height}, {stride}, 3)")
                # Fall back to a safe reshape
                total_pixels = buffer_size // 3
                if total_pixels == self.frame_width * self.frame_height:
                    frame = np.frombuffer(self.cam_buffer, dtype=np.uint8).reshape(
                        (self.frame_height, self.frame_width, 3))
                else:
                    print("Cannot safely reshape buffer, skipping frame")
                    return
            
            if self.raw_mode:
                # Convert to grayscale for RAW-like visualization
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Convert back to BGR for consistent display
                frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
            
            # Apply the same 180-degree rotation
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            # Thread-safe frame buffer update
            with self.frame_lock:
                self.frame_buffer = frame
            
            # Note: Frame queuing removed - using single-shot detection instead
            
        except toupcam.HRESULTException as ex:
            print(f"Error pulling image: 0x{ex.hr & 0xffffffff:x}")
    
    def start_render_thread(self):
        """Start a dedicated thread for rendering frames at high FPS"""
        self.render_running = True
        self.render_thread = threading.Thread(target=self.render_loop)
        self.render_thread.daemon = True
        self.render_thread.start()
        print("Render thread started")
    
    def render_loop(self):
        """Continuously render frames at a high rate for smooth display"""
        try:
            while self.render_running:
                if self.running and self.frame_buffer is not None:
                    # Use tkinter's thread-safe after_idle method to update UI
                    self.root.after_idle(self.update_frame)
                    
                # Sleep briefly to avoid excessive CPU usage while maintaining high FPS
                time.sleep(0.01)  # 10ms = potential for 100fps
        except Exception as e:
            print(f"Error in render loop: {str(e)}")
        
        print("Render thread exiting")
    
    def start_detection_thread(self):
        """Start a dedicated thread for cell detection processing"""
        self.detection_thread = threading.Thread(target=self.detection_loop)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        print("Detection thread started")
    
    def detection_loop(self):
        """Detection loop disabled - using single-shot detection instead"""
        print("Detection thread started (single-shot mode - no continuous processing)")
        try:
            # Just wait for the application to close
            while self.running:
                time.sleep(1.0)  # Sleep longer since we're not doing continuous detection
                    
        except Exception as e:
            print(f"Error in detection loop: {str(e)}")
        
        print("Detection thread exiting")
    
    def update_frame(self):
        """Update the UI with the latest frame - called from render thread"""
        if not self.running:
            return
            
        # Thread-safe frame access
        with self.frame_lock:
            if self.frame_buffer is None:
                return
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
            with self.detection_lock:
                detected_cells = self.detected_cells.copy()
            
            for cell in detected_cells:
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
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Use default canvas size if not yet rendered
        if canvas_width <= 1:
            canvas_width = 640
        if canvas_height <= 1:
            canvas_height = 480
        
        # Calculate scaling to fit canvas while maintaining aspect ratio
        h, w = frame_rgb.shape[:2]
        scale_x = canvas_width / w
        scale_y = canvas_height / h
        scale = min(scale_x, scale_y)  # Use smaller scale to fit entirely
        
        # Calculate new dimensions
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Resize frame to fit canvas
        frame_resized = cv2.resize(frame_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # Convert to PhotoImage for display
        img = Image.fromarray(frame_resized)
        photo = ImageTk.PhotoImage(image=img)
        
        # Clear canvas and center the image
        self.canvas.delete("all")
        x_offset = (canvas_width - new_width) // 2
        y_offset = (canvas_height - new_height) // 2
        self.canvas.create_image(x_offset, y_offset, image=photo, anchor=tk.NW)
        self.canvas.image = photo  # Keep a reference to prevent garbage collection
        
        # Store scaling factors for coordinate conversion
        self.display_scale = scale
        self.display_offset_x = x_offset
        self.display_offset_y = y_offset
        
        # Draw detected cell outlines on camera view
        self.draw_cell_outlines_on_camera()
        
        # Draw ROI rectangle if set
        self.draw_persistent_roi()
        
        # Update cell info less frequently to reduce UI overhead
        if self.detection_active:
            self.root.after_idle(self.update_cell_info)
            
    def update_camera(self):
        """Legacy method - no longer needed with ToupCam callback approach"""
        pass
    
    def draw_cell_outlines_on_camera(self):
        """Draw outline boxes for detected cells on the camera view"""
        if not hasattr(self, 'detected_cells') or not self.detected_cells:
            return
            
        try:
            # Get current display scaling factors
            if not hasattr(self, 'display_scale') or not hasattr(self, 'display_offset_x'):
                return
                
            scale = self.display_scale
            x_offset = self.display_offset_x
            y_offset = self.display_offset_y
            
            # Draw outline boxes for each detected cell
            for i, cell in enumerate(self.detected_cells):
                center = cell.center
                radius = cell.radius
                
                # Convert cell coordinates to display coordinates
                # Scale the coordinates to match the displayed image size
                display_x = int(center[0] * scale) + x_offset
                display_y = int(center[1] * scale) + y_offset
                display_radius = int(radius * scale)
                
                # Create bounding box coordinates
                x1 = display_x - display_radius
                y1 = display_y - display_radius
                x2 = display_x + display_radius
                y2 = display_y + display_radius
                
                # Draw outline rectangle (green for detected cells)
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='lime',
                    width=2,
                    tags="cell_outline"
                )
                
                # Draw center point
                center_size = 3
                self.canvas.create_oval(
                    display_x - center_size, display_y - center_size,
                    display_x + center_size, display_y + center_size,
                    fill='red',
                    outline='red',
                    tags="cell_center"
                )
                
                # Draw cell ID label
                self.canvas.create_text(
                    display_x, y1 - 10,
                    text=f"Cell {i+1}",
                    fill='yellow',
                    font=('Arial', 8, 'bold'),
                    tags="cell_label"
                )
                
        except Exception as e:
            print(f"Error drawing cell outlines: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def draw_persistent_roi(self):
        """Draw persistent ROI rectangle on camera view"""
        if not self.rect:
            return
            
        try:
            # Get current display scaling factors
            if not hasattr(self, 'display_scale') or not hasattr(self, 'display_offset_x'):
                return
                
            scale = self.display_scale
            x_offset = self.display_offset_x
            y_offset = self.display_offset_y
            
            # Convert ROI from camera coordinates to display coordinates
            roi_x, roi_y, roi_width, roi_height = self.rect
            
            # Scale and offset the ROI coordinates
            display_x = int(roi_x * scale) + x_offset
            display_y = int(roi_y * scale) + y_offset
            display_width = int(roi_width * scale)
            display_height = int(roi_height * scale)
            
            # Draw ROI rectangle outline
            self.canvas.create_rectangle(
                display_x, display_y,
                display_x + display_width, display_y + display_height,
                outline='red',
                width=2,
                tags="persistent_roi"
            )
            
            # Add ROI label
            self.canvas.create_text(
                display_x + 5, display_y - 15,
                text=f"ROI: {roi_width}x{roi_height}",
                fill='red',
                font=('Arial', 8, 'bold'),
                tags="persistent_roi"
            )
            
        except Exception as e:
            print(f"Error drawing persistent ROI: {str(e)}")
            import traceback
            traceback.print_exc()
    
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
        ttk.Button(control_frame, text="Clear ROI", command=self.clear_roi).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Exposure Control", command=self.open_exposure_control).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Capture Photo", command=self.capture_photo).pack(fill=tk.X, pady=5)
        
        # Camera format controls
        format_frame = ttk.LabelFrame(control_frame, text="Camera Format Settings")
        format_frame.pack(fill=tk.X, pady=10)
        
        # RAW format buttons
        raw_button_frame = ttk.Frame(format_frame)
        raw_button_frame.pack(fill=tk.X, pady=2)
        ttk.Button(raw_button_frame, text="Enable RAW", command=lambda: self.set_raw_format(True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(raw_button_frame, text="Enable RGB", command=lambda: self.set_raw_format(False)).pack(side=tk.LEFT, padx=2)
        
        # Bit depth buttons
        depth_button_frame = ttk.Frame(format_frame)
        depth_button_frame.pack(fill=tk.X, pady=2)
        ttk.Button(depth_button_frame, text="Max Bit Depth", command=lambda: self.set_bit_depth(True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(depth_button_frame, text="8-bit Depth", command=lambda: self.set_bit_depth(False)).pack(side=tk.LEFT, padx=2)
        
        # RGB format dropdown
        rgb_format_frame = ttk.Frame(format_frame)
        rgb_format_frame.pack(fill=tk.X, pady=2)
        ttk.Label(rgb_format_frame, text="RGB Format:").pack(side=tk.LEFT)
        self.rgb_format_var = tk.StringVar(value="RGB24")
        rgb_formats = ["RGB24", "RGB48", "RGB32", "8-bit Grey", "16-bit Grey", "RGB64"]
        rgb_combo = ttk.Combobox(rgb_format_frame, textvariable=self.rgb_format_var, values=rgb_formats, state="readonly", width=12)
        rgb_combo.pack(side=tk.RIGHT, padx=2)
        rgb_combo.bind('<<ComboboxSelected>>', self.on_rgb_format_changed)
        
        # Debug mode button
        self.debug_button = ttk.Button(control_frame, text="Enable Debug Mode", command=self.toggle_debug_mode)
        self.debug_button.pack(fill=tk.X, pady=5)
        
        # View toggle button
        self.view_toggle_button = ttk.Button(control_frame, text="Switch to Donut View", command=self.toggle_view_mode)
        self.view_toggle_button.pack(fill=tk.X, pady=5)
        
        # Create pattern parameter controls
        pattern_frame = ttk.LabelFrame(control_frame, text="Pattern Parameters")
        pattern_frame.pack(fill=tk.X, pady=10)
        
        # Pattern/Cell Size Ratio
        ratio_frame = ttk.Frame(pattern_frame)
        ratio_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ratio_frame, text="Pattern/Cell Size Ratio:").pack(side=tk.LEFT)
        
        # Create StringVar for the ratio input
        self.ratio_var = tk.StringVar(value=str(self.pattern_cell_size_ratio))
        ratio_entry = ttk.Entry(ratio_frame, textvariable=self.ratio_var, width=8)
        ratio_entry.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Bind validation to the entry
        ratio_entry.bind('<Return>', self.on_ratio_enter)
        ratio_entry.bind('<FocusOut>', self.on_ratio_focus_out)
        
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
        # Initialize pygame directly in the main thread
        pygame.init()
        pygame.font.init()  # Initialize font system
        print("Initializing pygame...")
        
        # Initialize font for text rendering
        try:
            self.debug_font = pygame.font.Font(None, 16)  # Default font, size 16
            print("Font initialized successfully")
        except Exception as e:
            print(f"Font initialization failed: {e}")
            self.debug_font = None
        
        # Get projector resolution (assuming it's the main display)
        projector_width = self.root.winfo_screenwidth()
        projector_height = self.root.winfo_screenheight()
        print(f"Creating pygame window with resolution {projector_width}x{projector_height}")
        
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
                    if self.calibration_data is not None:
                        fov_corners = self.calibration_data.get('fov_corners', None)
                        if fov_corners and isinstance(fov_corners, list) and len(fov_corners) >= 4:
                            # Draw FOV outline with thin lines only
                            pygame.draw.lines(self.pygame_screen, (50, 50, 50), True, fov_corners, 1)
                except Exception as e:
                    print(f"Error drawing FOV corners: {str(e)}")
                
                # Draw detected cells as boxes if enabled
                if self.show_donuts and self.detected_cells:
                    self.draw_cell_boxes()
                
                # Draw debug elements if available
                if self.debug_mode:
                    # Draw debug dot if available
                    if self.debug_dot_screen:
                        self.draw_debug_dot_pygame()
                    
                    # Draw camera corners and FOV corners
                    self.draw_debug_corners_pygame()
                
                
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
        
        # Convert display coordinates to camera coordinates using scaling factors
        if hasattr(self, 'display_scale') and hasattr(self, 'display_offset_x'):
            # Account for offset and scaling
            x_display = event.x - self.display_offset_x
            y_display = event.y - self.display_offset_y
            
            # Convert to camera coordinates
            x = int(x_display / self.display_scale)
            y = int(y_display / self.display_scale)
            
            # Clamp to frame bounds
            x = max(0, min(x, self.frame_width - 1))
            y = max(0, min(y, self.frame_height - 1))
        else:
            # Fallback to old method if scaling not available
            display_width = self.canvas.winfo_width()
            display_height = self.canvas.winfo_height()
            x = int(event.x * self.frame_width / display_width)
            y = int(event.y * self.frame_height / display_height)
        
        # Store start position
        self.rect_start = (x, y)
        self.rect_end = (x, y)  # Initialize end to start
    
    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if not self.rect_start:
            return
        
        # Convert display coordinates to camera coordinates using scaling factors
        if hasattr(self, 'display_scale') and hasattr(self, 'display_offset_x'):
            # Account for offset and scaling
            x_display = event.x - self.display_offset_x
            y_display = event.y - self.display_offset_y
            
            # Convert to camera coordinates
            x = int(x_display / self.display_scale)
            y = int(y_display / self.display_scale)
            
            # Clamp to frame bounds
            x = max(0, min(x, self.frame_width - 1))
            y = max(0, min(y, self.frame_height - 1))
        else:
            # Fallback to old method if scaling not available
            display_width = self.canvas.winfo_width()
            display_height = self.canvas.winfo_height()
            x = int(event.x * self.frame_width / display_width)
            y = int(event.y * self.frame_height / display_height)
        
        # Update end position
        self.rect_end = (x, y)
        
        # Clear previous rectangle
        self.canvas.delete("rect")
        
        # Draw new rectangle (convert camera coordinates back to display coordinates)
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        
        if hasattr(self, 'display_scale') and hasattr(self, 'display_offset_x'):
            # Scale coordinates to match display size
            x1_scaled = int(x1 * self.display_scale + self.display_offset_x)
            y1_scaled = int(y1 * self.display_scale + self.display_offset_y)
            x2_scaled = int(x2 * self.display_scale + self.display_offset_x)
            y2_scaled = int(y2 * self.display_scale + self.display_offset_y)
        else:
            # Fallback to old method
            display_width = self.canvas.winfo_width()
            display_height = self.canvas.winfo_height()
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
        
        # Convert display coordinates to camera coordinates using scaling factors
        if hasattr(self, 'display_scale') and hasattr(self, 'display_offset_x'):
            # Account for offset and scaling
            x_display = event.x - self.display_offset_x
            y_display = event.y - self.display_offset_y
            
            # Convert to camera coordinates
            x = int(x_display / self.display_scale)
            y = int(y_display / self.display_scale)
            
            # Clamp to frame bounds
            x = max(0, min(x, self.frame_width - 1))
            y = max(0, min(y, self.frame_height - 1))
        else:
            # Fallback to old method if scaling not available
            display_width = self.canvas.winfo_width()
            display_height = self.canvas.winfo_height()
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
    
    def draw_cell_boxes(self):
        """Draw filled circular disks for detected cells at their corresponding positions"""
        try:
            # Check if calibration data is available
            if self.calibration_data is None:
                return
                
            # Get calibration data for coordinate transformation
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
                
                fov_width = fov_max_x - fov_min_x
                fov_height = fov_max_y - fov_min_y
            
            # Get screen dimensions
            screen_width, screen_height = self.pygame_screen.get_size()
            
            # Thread-safe access to detected cells
            with self.detection_lock:
                detected_cells = self.detected_cells.copy() if self.detected_cells else []
            
            # print(f"Drawing {len(detected_cells)} cell circles")  # Commented out to reduce log spam
            
            # Draw each detected cell as a filled circular disk
            for cell in detected_cells:
                try:
                    # Get cell center and radius
                    if hasattr(cell, 'center') and hasattr(cell, 'radius'):
                        center = cell.center
                        radius = cell.radius
                    elif isinstance(cell, tuple) and len(cell) == 2:
                        center, radius = cell
                    else:
                        print(f"Unknown cell structure: {cell}")
                        continue
                    
                    # Use detection results directly since they're already in the rotated coordinate system
                    # The camera view is rotated 180° to appear normal, and detection happens on this rotated view
                    # The calibration should have been done on the same rotated view, so coordinates should match
                    
                    # print(f"Using cell coordinates directly: {center}")  # Commented out to reduce log spam
                    
                    # Map camera coordinates using vector-based transformation
                    result = self.map_camera_to_screen(center[0], center[1])
                    if result:
                        x_final, y_final = result
                        
                        # Calculate radius scaling based on FOV dimensions
                        fov_corners = self.calibration_data.get('fov_corners', None)
                        if fov_corners and len(fov_corners) >= 4:
                            # Get camera resolution
                            cam_width = self.calibration_data.get('camera_resolution', {}).get('width', self.frame_width)
                            cam_height = self.calibration_data.get('camera_resolution', {}).get('height', self.frame_height)
                            
                            # Estimate FOV scale from corner distances
                            TL = fov_corners[0]
                            TR = fov_corners[1]
                            BL = fov_corners[3]
                            
                            # Calculate average scale factor from both vectors
                            vec_x_len = ((TR[0] - TL[0])**2 + (TR[1] - TL[1])**2)**0.5
                            vec_y_len = ((BL[0] - TL[0])**2 + (BL[1] - TL[1])**2)**0.5
                            avg_scale = (vec_x_len + vec_y_len) / (cam_width + cam_height)
                            
                            scaled_radius = int(radius * avg_scale)
                        else:
                            scaled_radius = int(radius * 0.5)  # Default scaling
                        
                        # print(f"Vector mapping: Camera({center[0]}, {center[1]}) -> Screen({x_final}, {y_final})")  # Commented out to reduce log spam
                    else:
                        # print(f"Failed to map cell coordinates: ({center[0]}, {center[1]})")  # Commented out to reduce log spam
                        continue
                    
                    # Apply Pattern/Cell Size Ratio and calculate circle radius (ensure minimum visibility)
                    adjusted_radius = int(scaled_radius * self.pattern_cell_size_ratio)
                    circle_radius = max(5, adjusted_radius)  # Minimum 5 pixels radius
                    
                    # Ensure circle stays within screen bounds
                    circle_x = max(circle_radius, min(screen_width - circle_radius, x_final))
                    circle_y = max(circle_radius, min(screen_height - circle_radius, y_final))
                    
                    # Draw filled white circle
                    pygame.draw.circle(self.pygame_screen, (255, 255, 255), (circle_x, circle_y), circle_radius)
                    
                    # Draw a small black center dot for precise positioning (visible on white background)
                    pygame.draw.circle(self.pygame_screen, (0, 0, 255), (circle_x, circle_y), 1)
                    
                    # print(f"Drew cell circle at screen ({circle_x}, {circle_y}) with radius {circle_radius} (ratio: {self.pattern_cell_size_ratio:.2f})")  # Commented out to reduce log spam
                    
                except Exception as e:
                    print(f"Error drawing individual cell circle: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"Error in draw_cell_boxes: {str(e)}")
            import traceback
            traceback.print_exc()

    def display_donuts(self):
        """Display white donuts for detected cells on the black background screen"""
        print("Entering display_donuts method")  # DEBUG
        if not self.pygame_initialized or not self.pygame_running:
            self.status_var.set("Pygame not initialized")
            print("Pygame not initialized or not running")  # DEBUG
            return
            
        try:
            print("Starting donut display")  # DEBUG
            # Create a black background
            screen = pygame.display.get_surface()
            print(f"Got pygame screen: {screen}")  # DEBUG
            screen.fill((0, 0, 0))
            
            # Get screen dimensions
            screen_width, screen_height = screen.get_size()
            
            # Draw debug box at center
            center_x = screen_width // 2
            center_y = screen_height // 2
            box_size = 50
            box_x = center_x - box_size // 2
            box_y = center_y - box_size // 2
            pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_size, box_size))
            
            print(f"DEBUG: Drew white box at ({box_x}, {box_y}) with size {box_size}x{box_size} on Pygame screen ({screen_width}x{screen_height})")
            print(f"Screen dimensions: {screen_width}x{screen_height}")  # DEBUG
            
            # DEBUG: Draw a white 50x50 pixel box at the center of the screen
            center_x = screen_width // 2
            center_y = screen_height // 2
            box_size = 50
            
            # Calculate box coordinates (top-left corner)
            box_x = center_x - box_size // 2
            box_y = center_y - box_size // 2
            
            # Draw white box
            print(f"Drawing white box at ({box_x}, {box_y}) with size {box_size}x{box_size}")  # DEBUG
            pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_size, box_size))
            
            # Update the display
            pygame.display.flip()
            print("Display flipped")  # DEBUG
            
            # Update status
            self.status_var.set(f"Debug: Displaying white box at center ({center_x}, {center_y})")
            print(f"Drew white 50x50 box at center ({center_x}, {center_y}) on pygame screen ({screen_width}x{screen_height})")
            
        except Exception as e:
            self.status_var.set(f"Error displaying donuts: {str(e)}")
            print(f"Error in display_donuts: {e}")
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
        """Run cell detection once when button is pressed"""
        if not self.rect:
            self.status_var.set("Please draw a rectangle first")
            return
            
        # Get current frame for detection
        with self.frame_lock:
            if self.frame_buffer is None:
                self.status_var.set("No frame available")
                return
                
            # Make a copy of the frame for processing
            frame = self.frame_buffer.copy()
        
        try:
            # Run cell detection once
            self.status_var.set("Detecting cells...")
            detected_cells = detect_cells_in_roi(frame, self.rect)
            
            # Update detected cells
            with self.detection_lock:
                self.detected_cells = detected_cells
            
            # Update cell info
            self.update_cell_info()
            
            # Update status
            self.status_var.set(f"Detected {len(detected_cells)} cells")
            
        except Exception as e:
            self.status_var.set(f"Error detecting cells: {str(e)}")
            print(f"Error in cell detection: {e}")
    
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
        
        self.cell_info_var.set("Selection cleared")
        
    def open_exposure_control(self):
        """Open the exposure control panel"""
        if self.exposure_control_panel is None:
            self.exposure_control_panel = ExposureControlPanel(self)
        self.exposure_control_panel.open_panel()
        
        # Update cell info
        self.update_cell_info()
        
        # Update status
        self.status_var.set("Selection cleared")
    
    def capture_photo(self):
        """Capture a photo with current exposure parameters and save to Captures folder"""
        try:
            # Create Beijing/Shanghai timezone (UTC+8)
            beijing_tz = timezone(timedelta(hours=8))
            
            # Get current time in Beijing/Shanghai timezone
            now = datetime.now(beijing_tz)
            
            # Create date folder name (YYYY-MM-DD)
            date_folder = now.strftime("%Y-%m-%d")
            
            # Create full directory path
            captures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Captures", date_folder)
            os.makedirs(captures_dir, exist_ok=True)
            
            if self.raw_mode:
                # For RAW capture, we capture the Bayer pattern components separately
                bayer_channels = self.capture_raw_frame()
                if bayer_channels is None:
                    self.status_var.set("Failed to capture RAW Bayer data")
                    messagebox.showerror("Capture Error", "Failed to capture RAW Bayer data")
                    return
                
                # Create base filename with time (HH-MM-SS)
                base_filename = now.strftime("%H-%M-%S")
                
                # Save each Bayer channel separately
                channel_names = ["R", "G", "B"]
                saved_files = []
                
                for i, (channel_data, channel_name) in enumerate(zip(bayer_channels, channel_names)):
                    filename = f"{base_filename}_Bayer_{channel_name}.tif"
                    file_path = os.path.join(captures_dir, filename)
                    
                    success = cv2.imwrite(file_path, channel_data)
                    if success:
                        saved_files.append(filename)
                        print(f"RAW Bayer {channel_name} channel saved to: {file_path}")
                    else:
                        print(f"Failed to save Bayer {channel_name} channel")
                
                if saved_files:
                    self.status_var.set(f"RAW Bayer channels captured: {len(saved_files)} files")
                    files_list = "\n".join([os.path.join(captures_dir, f) for f in saved_files])
                    messagebox.showinfo("RAW Capture Success", f"RAW Bayer channels saved:\n{files_list}")
                    print(f"RAW Bayer capture complete: {len(saved_files)} channels saved")
                else:
                    raise Exception("Failed to save any Bayer channel files")
                    
            else:
                # Get current RGB frame
                with self.frame_lock:
                    if self.frame_buffer is None:
                        self.status_var.set("No frame available for capture")
                        messagebox.showerror("Capture Error", "No frame available for capture")
                        return
                    
                    # Make a copy of the current frame
                    frame = self.frame_buffer.copy()
                
                # Create filename with time (HH-MM-SS) - using TIFF format for better quality
                filename = now.strftime("%H-%M-%S.tif")
                
                # Full file path
                file_path = os.path.join(captures_dir, filename)
                
                # Save the image directly as TIFF (no color conversion needed for TIFF)
                # TIFF format preserves the original color depth and quality
                success = cv2.imwrite(file_path, frame)
                
                if success:
                    # Update status and show success message
                    self.status_var.set(f"RGB photo captured: {filename}")
                    messagebox.showinfo("Capture Success", f"RGB photo saved to:\n{file_path}")
                    print(f"RGB photo captured and saved to: {file_path}")
                else:
                    raise Exception("Failed to save image file")
            
        except Exception as e:
            error_msg = f"Error capturing photo: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Capture Error", error_msg)
            print(f"Capture error: {e}")
            import traceback
            traceback.print_exc()
    
    def capture_raw_frame(self):
        """Simulate RAW Bayer pattern capture by processing the current RGB frame"""
        try:
            print("Capturing RAW Bayer pattern data...")
            
            # Get the current RGB frame from the live view
            with self.frame_lock:
                if self.frame_buffer is None:
                    print("No frame buffer available for RAW capture")
                    return None
                
                # Make a copy of the current frame
                rgb_frame = self.frame_buffer.copy()
            
            # Convert BGR to RGB for proper channel extraction
            rgb_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2RGB)
            
            # Extract individual color channels
            r_channel = rgb_frame[:, :, 0]  # Red channel
            g_channel = rgb_frame[:, :, 1]  # Green channel
            b_channel = rgb_frame[:, :, 2]  # Blue channel
            
            # Apply rotation to match the expected orientation
            r_channel = cv2.rotate(r_channel, cv2.ROTATE_180)
            g_channel = cv2.rotate(g_channel, cv2.ROTATE_180)
            b_channel = cv2.rotate(b_channel, cv2.ROTATE_180)
            
            # Simulate Bayer pattern by creating a checkerboard pattern for each channel
            # This creates the "raw-like" effect you were seeing
            height, width = r_channel.shape
            
            # Create Bayer pattern masks
            r_mask = np.zeros((height, width), dtype=np.uint8)
            g_mask = np.zeros((height, width), dtype=np.uint8)
            b_mask = np.zeros((height, width), dtype=np.uint8)
            
            # RGGB Bayer pattern
            r_mask[0::2, 0::2] = 255  # Red at even rows, even columns
            g_mask[0::2, 1::2] = 255  # Green at even rows, odd columns
            g_mask[1::2, 0::2] = 255  # Green at odd rows, even columns
            b_mask[1::2, 1::2] = 255  # Blue at odd rows, odd columns
            
            # Apply Bayer pattern masks to simulate raw sensor data
            r_bayer = cv2.bitwise_and(r_channel, r_mask)
            g_bayer = cv2.bitwise_and(g_channel, g_mask)
            b_bayer = cv2.bitwise_and(b_channel, b_mask)
            
            # Create the three separate channel images
            # Each channel shows only the pixels that would be captured by that color filter
            r_image = np.zeros((height, width, 3), dtype=np.uint8)
            g_image = np.zeros((height, width, 3), dtype=np.uint8)
            b_image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Fill the appropriate channel in each image
            r_image[:, :, 2] = r_bayer  # Red channel in BGR format
            g_image[:, :, 1] = g_bayer  # Green channel in BGR format
            b_image[:, :, 0] = b_bayer  # Blue channel in BGR format
            
            # Detect and extract single subimage from each channel
            # Based on your description: 3 subimages, each 896 pixels wide
            subimage_width = 896
            expected_subimage_width = width // 3  # Should be around 896 (2688/3)
            
            print(f"Image dimensions: {width}x{height}")
            print(f"Expected subimage width: {expected_subimage_width}")
            
            # Extract the first (leftmost) subimage from each channel
            if width >= subimage_width * 3:
                # Use specific crop dimensions: 896x507
                crop_width = 896
                crop_height = 507
                
                print(f"Cropping subimages to: {crop_width}x{crop_height}")
                
                # Ensure we don't exceed image boundaries
                crop_width = min(crop_width, width // 3)
                crop_height = min(crop_height, height)
                
                # Extract and crop the first subimage (leftmost) from each channel
                r_subimage = r_image[:crop_height, :crop_width, :]
                g_subimage = g_image[:crop_height, :crop_width, :]
                b_subimage = b_image[:crop_height, :crop_width, :]
                
                print(f"Subimage extraction complete: {crop_width}x{crop_height}")
                return [r_subimage, g_subimage, b_subimage]
            else:
                print("Image width too small for subimage extraction, returning full images")
                return [r_image, g_image, b_image]
            
        except Exception as e:
            print(f"Error in RAW capture: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def stop_camera_for_settings(self):
        """Stop the camera safely for settings changes"""
        if not self.hcam:
            return False
            
        try:
            print("Stopping camera for settings change...")
            self.running = False  # Stop frame processing
            self.hcam.Stop()
            print("Camera stopped successfully")
            return True
        except Exception as e:
            print(f"Error stopping camera: {e}")
            return False
    
    def restart_camera_after_settings(self):
        """Restart the camera after settings changes"""
        if not self.hcam:
            return False
            
        try:
            print("Restarting camera after settings change...")
            
            # Always allocate buffer for RGB24 since we always pull RGB for live view
            # RAW capture will use separate buffers in the capture_raw_frame method
            bufsize = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(bufsize)
            print(f"Buffer allocated for RGB live view: {bufsize} bytes (RAW mode: {'ON' if self.raw_mode else 'OFF'})")
            
            self.running = True
            self.hcam.StartPullModeWithCallback(self.camera_callback, self)
            print("Camera restarted successfully")
            return True
        except Exception as e:
            print(f"Error restarting camera: {e}")
            return False
    
    def set_raw_format(self, enable_raw=True):
        """Set camera to RAW format (requires camera to be stopped)"""
        if not self.hcam:
            messagebox.showerror("Camera Error", "No camera connected")
            return False
            
        # Stop camera first
        if not self.stop_camera_for_settings():
            messagebox.showerror("Settings Error", "Failed to stop camera for settings change")
            return False
        
        try:
            # Set RAW format
            raw_value = 1 if enable_raw else 0
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_RAW, raw_value)
            self.raw_mode = enable_raw
            print(f"RAW format {'enabled' if enable_raw else 'disabled'}")
            
            # Restart camera
            if self.restart_camera_after_settings():
                mode_text = "RAW" if enable_raw else "RGB"
                self.status_var.set(f"Camera format changed to {mode_text}")
                messagebox.showinfo("Settings Changed", f"Camera format changed to {mode_text}")
                return True
            else:
                messagebox.showerror("Settings Error", "Failed to restart camera after settings change")
                return False
                
        except toupcam.HRESULTException as ex:
            error_msg = f"Failed to set RAW format: 0x{ex.hr & 0xffffffff:x}"
            print(error_msg)
            messagebox.showerror("Settings Error", error_msg)
            # Try to restart camera anyway
            self.restart_camera_after_settings()
            return False
    
    def set_bit_depth(self, use_max_depth=True):
        """Set camera bit depth (requires camera to be stopped)"""
        if not self.hcam:
            messagebox.showerror("Camera Error", "No camera connected")
            return False
            
        # Stop camera first
        if not self.stop_camera_for_settings():
            messagebox.showerror("Settings Error", "Failed to stop camera for settings change")
            return False
        
        try:
            # Set bit depth
            depth_value = 1 if use_max_depth else 0
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BITDEPTH, depth_value)
            print(f"Bit depth set to {'maximum' if use_max_depth else '8-bit'}")
            
            # Restart camera
            if self.restart_camera_after_settings():
                depth_text = "Maximum" if use_max_depth else "8-bit"
                self.status_var.set(f"Camera bit depth changed to {depth_text}")
                messagebox.showinfo("Settings Changed", f"Camera bit depth changed to {depth_text}")
                return True
            else:
                messagebox.showerror("Settings Error", "Failed to restart camera after settings change")
                return False
                
        except toupcam.HRESULTException as ex:
            error_msg = f"Failed to set bit depth: 0x{ex.hr & 0xffffffff:x}"
            print(error_msg)
            messagebox.showerror("Settings Error", error_msg)
            # Try to restart camera anyway
            self.restart_camera_after_settings()
            return False
    
    def set_rgb_format(self, rgb_format=0):
        """Set RGB format (requires camera to be stopped)
        0 = RGB24, 1 = RGB48, 2 = RGB32, 3 = 8-bit grey, 4 = 16-bit grey, 5 = RGB64
        """
        if not self.hcam:
            messagebox.showerror("Camera Error", "No camera connected")
            return False
            
        # Stop camera first
        if not self.stop_camera_for_settings():
            messagebox.showerror("Settings Error", "Failed to stop camera for settings change")
            return False
        
        try:
            # Set RGB format
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_RGB, rgb_format)
            format_names = {0: "RGB24", 1: "RGB48", 2: "RGB32", 3: "8-bit Grey", 4: "16-bit Grey", 5: "RGB64"}
            format_name = format_names.get(rgb_format, f"Format {rgb_format}")
            print(f"RGB format set to {format_name}")
            
            # Restart camera
            if self.restart_camera_after_settings():
                self.status_var.set(f"Camera RGB format changed to {format_name}")
                messagebox.showinfo("Settings Changed", f"Camera RGB format changed to {format_name}")
                return True
            else:
                messagebox.showerror("Settings Error", "Failed to restart camera after settings change")
                return False
                
        except toupcam.HRESULTException as ex:
            error_msg = f"Failed to set RGB format: 0x{ex.hr & 0xffffffff:x}"
            print(error_msg)
            messagebox.showerror("Settings Error", error_msg)
            # Try to restart camera anyway
            self.restart_camera_after_settings()
            return False

    def on_rgb_format_changed(self, event):
        """Handle RGB format combobox selection"""
        format_map = {
            "RGB24": 0,
            "RGB48": 1, 
            "RGB32": 2,
            "8-bit Grey": 3,
            "16-bit Grey": 4,
            "RGB64": 5
        }
        
        selected_format = self.rgb_format_var.get()
        format_value = format_map.get(selected_format, 0)
        self.set_rgb_format(format_value)

    def update_pattern_size_ratio(self, value):
        """Update the Pattern/Cell Size Ratio parameter"""
        self.pattern_cell_size_ratio = value
        # print(f"Pattern/Cell Size Ratio updated to: {value:.2f}")  # Commented out to reduce log spam
    
    def on_ratio_enter(self, event):
        """Handle Enter key press in ratio input box"""
        self.validate_and_update_ratio()
    
    def on_ratio_focus_out(self, event):
        """Handle focus out event in ratio input box"""
        self.validate_and_update_ratio()
    
    def validate_and_update_ratio(self):
        """Validate and update the pattern size ratio from input box"""
        try:
            value = float(self.ratio_var.get())
            # Clamp value to reasonable range
            if value < 0.1:
                value = 0.1
            elif value > 5.0:
                value = 5.0
            
            # Update the parameter and UI
            self.pattern_cell_size_ratio = value
            self.ratio_var.set(f"{value:.2f}")
            # print(f"Pattern/Cell Size Ratio updated to: {value:.2f}")  # Commented out to reduce log spam
            
        except ValueError:
            # Reset to current value if invalid input
            self.ratio_var.set(f"{self.pattern_cell_size_ratio:.2f}")
            # print(f"Invalid ratio input, reset to: {self.pattern_cell_size_ratio:.2f}")  # Commented out to reduce log spam
    
    def toggle_view_mode(self):
        """Toggle between camera and donut view modes"""
        current_mode = self.view_mode_var.get()
        if current_mode == "Camera":
            self.view_mode_var.set("Donut")
            self.show_donut_view()
            
            # Update status
            self.status_var.set("Switched to donut view")
            
        else:
            # Switch to Camera view
            self.view_mode_var.set("Camera")
            self._update_view_button()
            
            # Disable donut display
            self.show_donuts = False
            
            # Update status
            self.status_var.set("Switched to camera view")
            
    def _update_view_button(self):
        """Update the view toggle button text based on the current view mode"""
        current_mode = self.view_mode_var.get()
        if current_mode == "Camera":
            self.view_toggle_button.config(text="Switch to Donut View")
        else:
            self.view_toggle_button.config(text="Switch to Camera View")
    
    def toggle_debug_mode(self):
        """Toggle debug mode for coordinate mapping testing"""
        self.debug_mode = not self.debug_mode
        
        if self.debug_mode:
            self.debug_button.config(text="Disable Debug Mode")
            self.status_var.set("Debug mode enabled - Click on camera view to test coordinate mapping")
            print("Debug mode enabled - Click on camera view to see mapped position in donut view")
            
            # Calculate and store camera corners and FOV corners
            self.calculate_debug_corners()
        else:
            self.debug_button.config(text="Enable Debug Mode")
            self.status_var.set("Debug mode disabled")
            print("Debug mode disabled")
            
            # Clear debug dots
            self.clear_debug_dots()
    
    def clear_debug_dots(self):
        """Clear all debug dots from both camera and pygame views"""
        # Clear debug dots from camera view
        self.canvas.delete("debug_dot")
        
        # Clear debug dot positions
        self.debug_dot_camera = None
        self.debug_dot_screen = None
        self.debug_camera_corners = None
        self.debug_fov_corners = None
    
    def calculate_debug_corners(self):
        """Calculate camera corners and FOV corners for debug visualization"""
        try:
            # Check if calibration data is available
            if self.calibration_data is None:
                print("No calibration data available for debug corners")
                return
                
            # Define camera corners (four corners of the camera view)
            camera_corners = [
                (0, 0),  # Top-left
                (self.frame_width, 0),  # Top-right
                (self.frame_width, self.frame_height),  # Bottom-right
                (0, self.frame_height)  # Bottom-left
            ]
            
            # Map camera corners to screen coordinates
            mapped_corners = []
            for corner in camera_corners:
                screen_pos = self.map_camera_to_screen(corner[0], corner[1])
                if screen_pos:
                    mapped_corners.append({
                        'camera': corner,
                        'screen': screen_pos,
                        'label': f"Cam({screen_pos[0]},{screen_pos[1]})"
                    })
            
            self.debug_camera_corners = mapped_corners
            
            # Get FOV corners from calibration data
            fov_corners = self.calibration_data.get('fov_corners', None)
            if fov_corners and isinstance(fov_corners, list) and len(fov_corners) >= 4:
                # Filter FOV corners that are within monitor bounds
                screen_width = self.pygame_screen.get_width() if hasattr(self, 'pygame_screen') else 2560
                screen_height = self.pygame_screen.get_height() if hasattr(self, 'pygame_screen') else 1600
                
                valid_fov_corners = []
                for i, corner in enumerate(fov_corners):
                    x, y = corner[0], corner[1]
                    if 0 <= x <= screen_width and 0 <= y <= screen_height:
                        valid_fov_corners.append({
                            'screen': (int(x), int(y)),
                            'label': f"FOV{i+1}({int(x)},{int(y)})"
                        })
                
                self.debug_fov_corners = valid_fov_corners
            
            print(f"Debug corners calculated: {len(mapped_corners)} camera corners, {len(self.debug_fov_corners) if self.debug_fov_corners else 0} FOV corners")
            
        except Exception as e:
            print(f"Error calculating debug corners: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def map_camera_to_screen(self, camera_x, camera_y):
        """Map camera coordinates to screen coordinates using vector-based linear transformation"""
        try:
            # Check if calibration data is available
            if self.calibration_data is None:
                return None
                
            # Get FOV corners from calibration data
            fov_corners = self.calibration_data.get('fov_corners', None)
            if not fov_corners or len(fov_corners) < 4:
                print("FOV corners not available for mapping")
                return None
            
            # Get camera resolution
            cam_width = self.calibration_data.get('camera_resolution', {}).get('width', self.frame_width)
            cam_height = self.calibration_data.get('camera_resolution', {}).get('height', self.frame_height)
            
            if cam_width <= 0 or cam_height <= 0:
                print("Invalid camera resolution for mapping")
                return None
            
            # Normalize camera coordinates to [0,1]
            x_norm = camera_x / cam_width
            y_norm = camera_y / cam_height
            
            # Clamp normalized coordinates to [0,1]
            x_norm = max(0, min(1, x_norm))
            y_norm = max(0, min(1, y_norm))
            
            # Extract FOV corners: [TL, TR, BR, BL]
            TL = fov_corners[0]  # top-left
            TR = fov_corners[1]  # top-right
            BL = fov_corners[3]  # bottom-left
            
            # Calculate two basis vectors in FOV space
            vec_x = [TR[0] - TL[0], TR[1] - TL[1]]  # TL -> TR vector
            vec_y = [BL[0] - TL[0], BL[1] - TL[1]]  # TL -> BL vector
            
            # Apply vector-based linear transformation
            x_final = int(TL[0] + x_norm * vec_x[0] + y_norm * vec_y[0])
            y_final = int(TL[1] + x_norm * vec_x[1] + y_norm * vec_y[1])
            
            return x_final, y_final
            
        except Exception as e:
            print(f"Error mapping camera to screen: {str(e)}")
            return None
    
    def on_mouse_down(self, event):
        """Handle mouse button press on camera canvas"""
        if self.debug_mode:
            # Debug mode: handle coordinate mapping test
            self.handle_debug_click(event)
        else:
            # Normal mode: start ROI drawing
            self.rect_start = (event.x, event.y)
            self.rect_end = None
            self.rect = None
    
    def on_mouse_move(self, event):
        """Handle mouse movement on camera canvas"""
        if not self.debug_mode and self.rect_start:
            # Update ROI rectangle during dragging
            self.rect_end = (event.x, event.y)
            self.draw_roi_rectangle()
    
    def on_mouse_up(self, event):
        """Handle mouse button release on camera canvas"""
        if not self.debug_mode and self.rect_start:
            # Finalize ROI rectangle
            self.rect_end = (event.x, event.y)
            self.finalize_roi_rectangle()
    
    def draw_roi_rectangle(self):
        """Draw ROI rectangle on canvas during mouse drag"""
        if not self.rect_start or not self.rect_end:
            return
            
        # Clear previous rectangle
        self.canvas.delete("roi_rect")
        
        # Draw new rectangle
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        
        # Ensure proper rectangle coordinates
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # Draw rectangle outline
        self.canvas.create_rectangle(
            left, top, right, bottom,
            outline='red',
            width=2,
            tags="roi_rect"
        )
    
    def finalize_roi_rectangle(self):
        """Finalize ROI rectangle and convert to camera coordinates"""
        if not self.rect_start or not self.rect_end:
            return
            
        # Get canvas coordinates
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        
        # Ensure proper rectangle coordinates
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # Convert to camera coordinates if display scaling is available
        if hasattr(self, 'display_scale') and hasattr(self, 'display_offset_x'):
            # Convert from display coordinates to camera coordinates
            cam_left = (left - self.display_offset_x) / self.display_scale
            cam_top = (top - self.display_offset_y) / self.display_scale
            cam_right = (right - self.display_offset_x) / self.display_scale
            cam_bottom = (bottom - self.display_offset_y) / self.display_scale
            
            # Ensure coordinates are within camera bounds
            cam_left = max(0, min(cam_left, self.frame_width))
            cam_top = max(0, min(cam_top, self.frame_height))
            cam_right = max(0, min(cam_right, self.frame_width))
            cam_bottom = max(0, min(cam_bottom, self.frame_height))
            
            # Calculate width and height
            width = int(cam_right - cam_left)
            height = int(cam_bottom - cam_top)
            
            # Store ROI rectangle in camera coordinates
            if width > 10 and height > 10:  # Minimum size check
                self.rect = (int(cam_left), int(cam_top), width, height)
                print(f"ROI set: x={int(cam_left)}, y={int(cam_top)}, w={width}, h={height}")
                self.status_var.set(f"ROI set: {width}x{height} at ({int(cam_left)}, {int(cam_top)})")
            else:
                print("ROI too small, ignored")
                self.status_var.set("ROI too small, please draw a larger area")
                self.canvas.delete("roi_rect")
        else:
            print("Display scaling not available for ROI conversion")
    
    def clear_roi(self):
        """Clear the current ROI"""
        self.rect = None
        self.rect_start = None
        self.rect_end = None
        self.canvas.delete("roi_rect")
        self.status_var.set("ROI cleared")
    
    def handle_debug_click(self, event):
        """Handle debug mode click to show coordinate mapping"""
        try:
            # Get click coordinates relative to canvas
            canvas_x = event.x
            canvas_y = event.y
            
            # Convert canvas coordinates to camera coordinates
            if not hasattr(self, 'display_scale') or not hasattr(self, 'display_offset_x'):
                print("Display scaling not available yet")
                return
            
            # Convert from display coordinates to camera coordinates
            camera_x = (canvas_x - self.display_offset_x) / self.display_scale
            camera_y = (canvas_y - self.display_offset_y) / self.display_scale
            
            # Ensure coordinates are within camera bounds
            camera_x = max(0, min(camera_x, self.frame_width))
            camera_y = max(0, min(camera_y, self.frame_height))
            
            print(f"Debug click: Canvas({canvas_x}, {canvas_y}) -> Camera({camera_x:.1f}, {camera_y:.1f})")
            
            # Clear previous debug dots
            self.clear_debug_dots()
            
            # Store camera coordinates for mapping
            self.debug_dot_camera = (camera_x, camera_y)
            
            # Draw debug dot on camera view
            self.draw_debug_dot_camera(canvas_x, canvas_y)
            
            # Map to pygame coordinates and draw there
            self.map_and_draw_debug_dot_pygame(camera_x, camera_y)
            
        except Exception as e:
            print(f"Error in debug click handler: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def draw_debug_dot_camera(self, canvas_x, canvas_y):
        """Draw debug dot on camera view"""
        dot_size = 8
        self.canvas.create_oval(
            canvas_x - dot_size, canvas_y - dot_size,
            canvas_x + dot_size, canvas_y + dot_size,
            fill='white',
            outline='black',
            width=2,
            tags="debug_dot"
        )
        
        # Add label
        self.canvas.create_text(
            canvas_x, canvas_y - 15,
            text="DEBUG",
            fill='white',
            font=('Arial', 8, 'bold'),
            tags="debug_dot"
        )
    
    def map_and_draw_debug_dot_pygame(self, camera_x, camera_y):
        """Map camera coordinates to pygame and draw debug dot using vector transformation"""
        try:
            # Use the same vector-based mapping as the main coordinate transformation
            result = self.map_camera_to_screen(camera_x, camera_y)
            if result:
                x_final, y_final = result
                
                # Store screen coordinates for pygame drawing
                self.debug_dot_screen = (x_final, y_final)
                
                # print(f"Debug mapping: Camera({camera_x:.1f}, {camera_y:.1f}) -> Screen({x_final}, {y_final})")  # Commented out to reduce log spam
            else:
                # print(f"Failed to map camera coordinates: ({camera_x:.1f}, {camera_y:.1f})")  # Commented out to reduce log spam
                pass
        except Exception as e:
            print(f"Error mapping debug dot: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def draw_debug_dot_pygame(self):
        """Draw debug dot on pygame screen"""
        if not self.debug_dot_screen:
            return
            
        try:
            x, y = self.debug_dot_screen
            
            # Draw large white circle with black border for high visibility
            dot_radius = 15
            pygame.draw.circle(self.pygame_screen, (255, 255, 255), (x, y), dot_radius)
            pygame.draw.circle(self.pygame_screen, (0, 0, 0), (x, y), dot_radius, 3)
            
            # Draw center cross for precise positioning
            cross_size = 8
            pygame.draw.line(self.pygame_screen, (255, 0, 0), 
                           (x - cross_size, y), (x + cross_size, y), 2)
            pygame.draw.line(self.pygame_screen, (255, 0, 0), 
                           (x, y - cross_size), (x, y + cross_size), 2)
            
            # Draw coordinate text
            if hasattr(self, 'debug_dot_camera') and self.debug_dot_camera:
                cam_x, cam_y = self.debug_dot_camera
                coord_text = f"Cam({cam_x:.0f},{cam_y:.0f})->Scr({x},{y})"
                
                # Initialize font if not already done
                if not hasattr(self, 'debug_font'):
                    pygame.font.init()
                    self.debug_font = pygame.font.Font(None, 24)
                
                # Render text
                text_surface = self.debug_font.render(coord_text, True, (255, 255, 255))
                text_rect = text_surface.get_rect()
                text_rect.centerx = x
                text_rect.bottom = y - 20
                
                # Draw background rectangle for text visibility
                bg_rect = text_rect.copy()
                bg_rect.inflate(10, 4)
                pygame.draw.rect(self.pygame_screen, (0, 0, 0), bg_rect)
                pygame.draw.rect(self.pygame_screen, (255, 255, 255), bg_rect, 1)
                
                # Draw the text
                self.pygame_screen.blit(text_surface, text_rect)
                
                # print(f"Debug dot drawn at pygame coordinates: ({x}, {y})")  # Commented out to reduce log spam
                
        except Exception as e:
            print(f"Error drawing debug dot on pygame: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def draw_debug_corners_pygame(self):
        """Draw camera corners and FOV corners on pygame screen"""
        try:
            # Draw camera corners (yellow dots)
            if self.debug_camera_corners:
                for corner in self.debug_camera_corners:
                    x, y = corner['screen']
                    label = corner['label']
                    
                    # Check if corner is within screen bounds
                    if hasattr(self, 'pygame_screen'):
                        screen_width = self.pygame_screen.get_width()
                        screen_height = self.pygame_screen.get_height()
                        
                        if 0 <= x <= screen_width and 0 <= y <= screen_height:
                            # Draw yellow circle for camera corners
                            corner_radius = 12
                            pygame.draw.circle(self.pygame_screen, (255, 255, 0), (x, y), corner_radius)
                            pygame.draw.circle(self.pygame_screen, (0, 0, 0), (x, y), corner_radius, 2)
                            
                            # Draw center dot
                            pygame.draw.circle(self.pygame_screen, (0, 0, 0), (x, y), 3)
                            
                            # Draw text label with coordinates
                            if hasattr(self, 'debug_font') and self.debug_font:
                                # Create text surface
                                text_surface = self.debug_font.render(label, True, (255, 255, 255))  # White text
                                text_rect = text_surface.get_rect()
                                
                                # Position text above the corner
                                text_x = x - text_rect.width // 2
                                text_y = y - corner_radius - text_rect.height - 5
                                
                                # Ensure text is within screen bounds
                                text_x = max(5, min(text_x, screen_width - text_rect.width - 5))
                                text_y = max(5, text_y)
                                
                                # Draw background rectangle for better visibility
                                bg_rect = pygame.Rect(text_x - 2, text_y - 2, text_rect.width + 4, text_rect.height + 4)
                                pygame.draw.rect(self.pygame_screen, (0, 0, 0), bg_rect)  # Black background
                                pygame.draw.rect(self.pygame_screen, (255, 255, 0), bg_rect, 1)  # Yellow border
                                
                                # Draw the text
                                self.pygame_screen.blit(text_surface, (text_x, text_y))
                            
                            print(f"Camera corner drawn: {label} at ({x}, {y})")
            
            # Draw FOV corners (cyan dots)
            if self.debug_fov_corners:
                for corner in self.debug_fov_corners:
                    x, y = corner['screen']
                    label = corner['label']
                    
                    # Draw cyan circle for FOV corners
                    corner_radius = 10
                    pygame.draw.circle(self.pygame_screen, (0, 255, 255), (x, y), corner_radius)
                    pygame.draw.circle(self.pygame_screen, (0, 0, 0), (x, y), corner_radius, 2)
                    
                    # Draw center dot
                    pygame.draw.circle(self.pygame_screen, (0, 0, 0), (x, y), 2)
                    
                    # Draw text label with coordinates
                    if hasattr(self, 'debug_font') and self.debug_font:
                        # Create text surface
                        text_surface = self.debug_font.render(label, True, (255, 255, 255))  # White text
                        text_rect = text_surface.get_rect()
                        
                        # Position text below the corner
                        text_x = x - text_rect.width // 2
                        text_y = y + corner_radius + 5
                        
                        # Ensure text is within screen bounds
                        if hasattr(self, 'pygame_screen'):
                            screen_width = self.pygame_screen.get_width()
                            screen_height = self.pygame_screen.get_height()
                            
                            text_x = max(5, min(text_x, screen_width - text_rect.width - 5))
                            text_y = min(text_y, screen_height - text_rect.height - 5)
                        
                        # Draw background rectangle for better visibility
                        bg_rect = pygame.Rect(text_x - 2, text_y - 2, text_rect.width + 4, text_rect.height + 4)
                        pygame.draw.rect(self.pygame_screen, (0, 0, 0), bg_rect)  # Black background
                        pygame.draw.rect(self.pygame_screen, (0, 255, 255), bg_rect, 1)  # Cyan border
                        
                        # Draw the text
                        self.pygame_screen.blit(text_surface, (text_x, text_y))
                    
                    print(f"FOV corner drawn: {label} at ({x}, {y})")
                    
        except Exception as e:
            print(f"Error drawing debug corners on pygame: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_close(self):
        """Handle window close event"""
        print("Closing application...")
        
        # Set running flag to False to stop threads
        self.running = False
        self.render_running = False
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
        if hasattr(self, 'render_thread') and self.render_thread and self.render_thread.is_alive():
            self.render_thread.join(timeout=1.0)
            print("Render thread stopped")
        
        if hasattr(self, 'detection_thread') and self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
            print("Detection thread stopped")
        
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
