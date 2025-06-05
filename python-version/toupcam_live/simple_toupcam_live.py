"""
Simple ToupCam Live Stream
This script provides a basic live stream from a ToupCam camera using the same default exposure parameters
as the full toupcam_live_control.py implementation.
"""

import sys
import os
import ctypes
import time
import threading
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import messagebox
from skimage import filters, morphology, measure, segmentation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
    print(f"Check if the path is correct: {sdk_path}")
    sys.exit(1)

class SimpleToupCamLive:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple ToupCam Live Stream")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Camera variables
        self.hcam = None
        self.cam_buffer = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.running = False
        
        # Default exposure parameters (same as in toupcam_live_control.py)
        self.exposure_time = 8333  # 8.333ms in microseconds
        
        # UI update variables
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.new_frame_available = False
        self.frame_lock = threading.Lock()
        self.render_running = False
        
        # AOI (Area of Interest) variables
        self.aoi_active = False  # Flag to enable/disable AOI drawing
        self.aoi_rect = None     # Canvas rectangle object
        self.aoi_overlay = None  # Canvas overlay object
        self.aoi_coords = [0, 0, 0, 0]  # [start_x, start_y, end_x, end_y]
        self.aoi_drawing = False  # Flag to indicate active drawing
        self.aoi_adjusting = False  # Flag to indicate border adjustment
        self.aoi_adjust_handle = None  # Which handle is being adjusted
        self.aoi_handle_size = 8  # Size of adjustment handles
        self.aoi_handles = []  # List of handle objects on canvas
        self.aoi_handle_coords = {}  # Coordinates of handles
        
        # Cell detection variables
        self.cell_detector = CellDetector()
        self.cell_detection_active = False
        self.cell_detection_thread = None
        self.cell_detection_interval = 0.05  # 10 FPS for cell detection
        self.last_detection_time = 0
        self.detected_cells = []
        self.detection_result_image = None
        self.detection_result_photo = None
        self.detection_canvas = None
        
        # Create UI
        self.create_ui()
        
        # Start camera
        self.start_camera()
        
        # Start rendering thread
        self.start_render_thread()
        
        # Make sure the window is visible
        self.root.update()
    
    def create_ui(self):
        """Create a user interface with canvas for video display and control panel"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for video display
        video_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Video canvas - use a light gray background to better see the video boundaries
        self.canvas = tk.Canvas(
            video_frame, 
            bg="#f0f0f0",  # Light gray background
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for AOI drawing
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # FPS counter
        self.fps_label = ttk.Label(video_frame, text="FPS: 0")
        self.fps_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # Right panel for controls
        control_frame = ttk.Frame(main_frame, width=250, borderwidth=2, relief="groove")
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)  # Prevent shrinking
        
        # Title for control panel
        ttk.Label(control_frame, text="Controls", font=("Arial", 12, "bold")).pack(pady=10)
        
        # AOI controls
        aoi_frame = ttk.LabelFrame(control_frame, text="Area of Interest")
        aoi_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Draw AOI button
        self.draw_aoi_var = tk.BooleanVar(value=False)
        self.draw_aoi_button = ttk.Checkbutton(
            aoi_frame,
            text="Draw AOI",
            variable=self.draw_aoi_var,
            command=self.toggle_aoi_drawing
        )
        self.draw_aoi_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Clear AOI button
        self.clear_aoi_button = ttk.Button(
            aoi_frame,
            text="Clear AOI",
            command=self.clear_aoi
        )
        self.clear_aoi_button.pack(fill=tk.X, padx=5, pady=5)
        
        # AOI Opacity slider
        ttk.Label(aoi_frame, text="Overlay Opacity:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.opacity_var = tk.DoubleVar(value=0.5)
        opacity_scale = ttk.Scale(
            aoi_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.opacity_var,
            command=self.update_aoi_overlay
        )
        opacity_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        
        # Cell Detection controls
        cell_frame = ttk.LabelFrame(control_frame, text="Cell Detection")
        cell_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start/Stop Cell Detection buttons
        button_frame = ttk.Frame(cell_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_detection_button = ttk.Button(
            button_frame,
            text="Start Detection",
            command=self.start_cell_detection
        )
        self.start_detection_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        
        self.stop_detection_button = ttk.Button(
            button_frame,
            text="Stop Detection",
            command=self.stop_cell_detection,
            state=tk.DISABLED
        )
        self.stop_detection_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2,0))
        
        # Cell count display
        self.cell_count_var = tk.StringVar(value="Cells: 0")
        ttk.Label(cell_frame, textvariable=self.cell_count_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Detection results frame
        results_frame = ttk.LabelFrame(control_frame, text="Detection Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for detection results
        self.detection_canvas = tk.Canvas(
            results_frame,
            bg="#f0f0f0",
            width=230,
            height=200
        )
        self.detection_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def start_camera(self):
        """Initialize and start the camera with default exposure parameters"""
        devices = toupcam.Toupcam.EnumV2()
        if not devices:
            self.status_var.set("No camera found")
            messagebox.showerror(
                "Camera Error", 
                "No ToupCam cameras found. Please connect a camera and restart the application."
            )
            return
        
        device = devices[0]  # Use the first camera
        
        try:
            # Open the camera
            self.hcam = toupcam.Toupcam.Open(None)
            if not self.hcam:
                self.status_var.set("Failed to open camera")
                return
            
            # Get camera properties
            self.frame_width, self.frame_height = self.hcam.get_Size()
            print(f"Camera resolution: {self.frame_width}x{self.frame_height}")
            
            # Set camera properties for optimal performance
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BYTEORDER, 0)  # RGB
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_UPSIDE_DOWN, 0)  # Normal orientation
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimize frame queue
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_CALLBACK_THREAD, 1)  # Enable dedicated callback thread
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_THREAD_PRIORITY, 2)  # Set high thread priority
            
            # Disable auto exposure
            self.hcam.put_AutoExpoEnable(False)
            
            # Set anti-flicker to 60Hz (for 16.67ms exposure)
            self.hcam.put_HZ(2)  # 2 = 60Hz
            
            # Set exposure time (in microseconds)
            self.hcam.put_ExpoTime(self.exposure_time)  # 8.333ms
            
            # Set other camera options
            self.hcam.put_Brightness(0)
            self.hcam.put_Contrast(0)
            self.hcam.put_Gamma(100)  # 1.0
            
            # Set white balance
            self.hcam.put_TempTint(4796, 1153)  # Temperature 4796, Tint 1153
            
            # Allocate buffer for image data
            buffer_size = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(buffer_size)
            
            # Pre-allocate numpy array for frame buffer to avoid memory allocations
            self.frame_buffer_shape = (self.frame_height, toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3, 3)
            
            # Register callback
            self.hcam.StartPullModeWithCallback(self.on_frame, self)
            
            # Set running flag to True to enable image processing
            self.running = True
            
            self.status_var.set(f"Camera started: {device.displayname}")
            
        except Exception as e:
            self.status_var.set(f"Error starting camera: {str(e)}")
            messagebox.showerror("Camera Error", f"Error starting camera: {str(e)}")
    
    def on_frame(self, nEvent, ctx):
        """Camera event callback function"""
        try:
            if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
                ctx.process_image()
            elif nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
                ctx.status_var.set("Camera disconnected")
        except Exception as e:
            print(f"[ERROR] Exception in on_frame: {e}")
    
    def process_image(self):
        """Process the image from the camera"""
        if not self.running or not self.hcam:
            return
            
        # Track frame timing for FPS calculation
        current_time = time.time()
            
        try:
            # Pull the image from the camera
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Convert the raw buffer to a numpy array
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8).reshape(self.frame_buffer_shape)
            frame = frame[:, :self.frame_width, :]
            
            # Store the frame
            with self.frame_lock:
                self.frame_buffer = frame
                self.new_frame_available = True
            
            # Count frames for FPS calculation
            self.frame_count += 1
            if current_time - self.last_fps_time >= 1.0:
                self.fps = self.frame_count / (current_time - self.last_fps_time)
                self.fps_label.configure(text=f"FPS: {self.fps:.1f}")
                self.status_var.set(f"Camera running: {self.fps:.1f} FPS")
                self.frame_count = 0
                self.last_fps_time = current_time
                
        except toupcam.HRESULTException as ex:
            print(f"[ERROR] Error pulling image: 0x{ex.hr & 0xffffffff:x}")
        except Exception as e:
            print(f"[ERROR] process_image exception: {e}")
    
    def update_frame(self):
        """Update the UI with the latest frame"""
        if not self.running or self.frame_buffer is None:
            return
            
        # Get the current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Calculate the display size while maintaining aspect ratio
            camera_aspect_ratio = self.frame_width / self.frame_height
            canvas_aspect_ratio = canvas_width / canvas_height
            
            if canvas_aspect_ratio > camera_aspect_ratio:
                # Canvas is wider than needed - height will be the constraint
                display_height = canvas_height
                display_width = int(display_height * camera_aspect_ratio)
                # Center horizontally
                self.display_offset_x = (canvas_width - display_width) // 2
                self.display_offset_y = 0
            else:
                # Canvas is taller than needed - width will be the constraint
                display_width = canvas_width
                display_height = int(display_width / camera_aspect_ratio)
                # Center vertically
                self.display_offset_x = 0
                self.display_offset_y = (canvas_height - display_height) // 2
            
            # Store display dimensions for coordinate mapping
            self.display_width = display_width
            self.display_height = display_height
            
            # Convert BGR to RGB for display
            rgb_frame = cv2.cvtColor(self.frame_buffer, cv2.COLOR_BGR2RGB)
            
            # Resize the frame to fill the entire canvas
            display_frame = cv2.resize(rgb_frame, (display_width, display_height), 
                                      interpolation=cv2.INTER_LINEAR)
            
            # Apply AOI overlay if active
            if hasattr(self, 'aoi_coords') and all(coord != 0 for coord in self.aoi_coords):
                # Create a copy of the frame for overlay
                overlay = display_frame.copy()
                
                # Create a mask for the AOI (white inside AOI, black outside)
                mask = np.zeros((display_height, display_width), dtype=np.uint8)
                x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
                
                # Convert canvas coordinates to image coordinates
                mask_x1 = max(0, x1 - self.display_offset_x)
                mask_y1 = max(0, y1 - self.display_offset_y)
                mask_x2 = min(display_width, x2 - self.display_offset_x)
                mask_y2 = min(display_height, y2 - self.display_offset_y)
                
                # Only draw if we have valid coordinates
                if mask_x1 < mask_x2 and mask_y1 < mask_y2:
                    cv2.rectangle(mask, (mask_x1, mask_y1), (mask_x2, mask_y2), 255, -1)  # Fill rectangle with white
                
                # Darken areas outside AOI
                alpha = self.opacity_var.get()  # Get opacity from slider
                overlay_dark = cv2.addWeighted(overlay, 1-alpha, np.zeros_like(overlay), alpha, 0)
                
                # Apply mask: keep original inside AOI, darkened outside
                mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
                display_frame = np.where(mask_3ch > 0, display_frame, overlay_dark)
                
                # Draw detected cells on the main display if cell detection is active
                if self.cell_detection_active and hasattr(self, 'detected_cells') and self.detected_cells:
                    # Draw bounding boxes for detected cells
                    for cell in self.detected_cells:
                        bbox = cell['bbox']
                        y1_cell, x1_cell, y2_cell, x2_cell = bbox
                        
                        # Draw rectangle
                        cv2.rectangle(display_frame, (x1_cell, y1_cell), (x2_cell, y2_cell), (255, 0, 0), 2)
                        
                        # Add text with cell properties (simplified for main display)
                        text = f"A:{cell['area']:.0f}"
                        centroid = cell['centroid']
                        
                        # Place text at the centroid
                        cv2.putText(display_frame, text, (int(centroid[1]), int(centroid[0])), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Convert to PhotoImage
            img = Image.fromarray(display_frame)
            self.photo_image = ImageTk.PhotoImage(image=img)
            
            # If this is the first frame, create the image on the canvas
            if not self.canvas.find_withtag("video"):
                self.canvas.create_image(
                    self.display_offset_x, self.display_offset_y,  # Position with calculated offsets
                    anchor=tk.NW,  # Northwest anchor (top-left)
                    image=self.photo_image,
                    tags=("video",)
                )
            else:
                # Update the existing image and position
                self.canvas.itemconfig("video", image=self.photo_image)
                self.canvas.coords("video", self.display_offset_x, self.display_offset_y)
                
            # Update AOI rectangle if it exists
            if self.aoi_rect:
                # Use the original AOI coordinates for the rectangle on canvas
                # since the canvas already has the image positioned with offsets
                x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
                self.canvas.coords(self.aoi_rect, x1, y1, x2, y2)
                
                # Update handle positions
                self.update_handle_positions()
    
    def start_render_thread(self):
        """Start a dedicated thread for rendering frames"""
        self.render_running = True
        self.render_thread = threading.Thread(target=self.render_loop)
        self.render_thread.daemon = True
        self.render_thread.start()
        print("Render thread started")
    
    def render_loop(self):
        """Continuously render frames at a high rate"""
        try:
            while self.render_running:
                if self.running and self.frame_buffer is not None:
                    # Use tkinter's thread-safe after method to update UI
                    self.root.after_idle(self.update_frame)
                    
                # Sleep briefly to avoid excessive CPU usage
                time.sleep(0.01)  # 10ms = potential for 100fps
        except Exception as e:
            print(f"Error in render loop: {str(e)}")
        
        print("Render thread exiting")
    
    def on_closing(self):
        """Clean up resources when closing the application"""
        print("Closing application and cleaning up resources...")
        
        # Stop cell detection if active
        if self.cell_detection_active:
            self.cell_detection_active = False
            if hasattr(self, 'cell_detection_thread') and self.cell_detection_thread and self.cell_detection_thread.is_alive():
                self.cell_detection_thread.join(timeout=1.0)
                print("Cell detection thread stopped")
        
        # Stop render thread
        self.render_running = False
        if hasattr(self, 'render_thread') and self.render_thread.is_alive():
            self.render_thread.join(timeout=1.0)
        
        # Stop camera
        self.cleanup_camera()
        
        # Force quit the application after a short delay
        self.root.after(100, self._force_quit)
    
    def _force_quit(self):
        """Force quit the application"""
        try:
            self.root.quit()
            print("Application quit successfully")
        except Exception as e:
            print(f"Error during quit: {e}")
            # As a last resort
            try:
                self.root.destroy()
                print("Application destroyed")
            except Exception as e:
                print(f"Error during destroy: {e}")
    
    def cleanup_camera(self):
        """Clean up camera resources with timeout protection"""
        if self.hcam:
            print("Starting camera cleanup...")
            camera_ref = self.hcam
            self.hcam = None  # Immediately set to None to prevent further access
            self.running = False  # Stop any ongoing camera operations
            
            try:
                # Create a thread to handle camera cleanup with timeout
                def cleanup_camera_thread():
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
                        print(f"Error in camera cleanup thread: {e}")
                
                # Start and wait for cleanup thread with timeout
                cleanup_thread = threading.Thread(target=cleanup_camera_thread, daemon=True)
                cleanup_thread.start()
                
                # Only wait a short time - don't let it block the application exit
                print("Waiting for camera cleanup...")
                cleanup_thread.join(timeout=1.0)  # Wait up to 1 second for cleanup
                
                if cleanup_thread.is_alive():
                    print("WARNING: Camera cleanup timed out, abandoning camera resources")
                else:
                    print("Camera cleanup completed")
                    
            except Exception as e:
                print(f"Error during camera cleanup: {e}")
    
    def toggle_aoi_drawing(self):
        """Toggle AOI drawing mode"""
        self.aoi_active = self.draw_aoi_var.get()
        if self.aoi_active:
            self.status_var.set("Click and drag to draw Area of Interest")
        else:
            self.status_var.set("AOI drawing disabled")
    
    def clear_aoi(self):
        """Clear the AOI rectangle"""
        if self.aoi_rect:
            self.canvas.delete(self.aoi_rect)
            self.aoi_rect = None
        
        # Clear handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
        
        # Reset AOI coordinates
        self.aoi_coords = [0, 0, 0, 0]
        self.status_var.set("AOI cleared")
    
    def get_adjusted_aoi_coords(self):
        """Return AOI coordinates adjusted to ensure x1<x2 and y1<y2 and account for display offsets"""
        x1, y1, x2, y2 = self.aoi_coords
        
        # Ensure x1 < x2 and y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        # Clamp coordinates to the visible display area
        # This ensures the AOI is within the visible image area
        x1 = max(self.display_offset_x, min(x1, self.display_offset_x + self.display_width))
        x2 = max(self.display_offset_x, min(x2, self.display_offset_x + self.display_width))
        y1 = max(self.display_offset_y, min(y1, self.display_offset_y + self.display_height))
        y2 = max(self.display_offset_y, min(y2, self.display_offset_y + self.display_height))
        
        return [x1, y1, x2, y2]
    
    def update_aoi_overlay(self, *args):
        """Update the AOI overlay based on opacity slider"""
        # Force a frame update to refresh the overlay
        if hasattr(self, 'aoi_coords') and all(coord != 0 for coord in self.aoi_coords):
            self.update_frame()
    
    def start_cell_detection(self):
        """Start the cell detection process"""
        # Check if AOI is defined
        if not all(coord != 0 for coord in self.aoi_coords):
            messagebox.showwarning("No AOI", "Please draw an Area of Interest before starting cell detection.")
            return
        
        # Check if camera is running
        if not self.running or self.frame_buffer is None:
            messagebox.showwarning("Camera Not Running", "Camera must be running to detect cells.")
            return
        
        # Update UI
        self.start_detection_button.config(state=tk.DISABLED)
        self.stop_detection_button.config(state=tk.NORMAL)
        self.draw_aoi_button.config(state=tk.DISABLED)
        self.clear_aoi_button.config(state=tk.DISABLED)
        
        # Set detection active
        self.cell_detection_active = True
        self.status_var.set("Cell detection active in AOI")
        
        # Start detection thread
        self.cell_detection_thread = threading.Thread(target=self.cell_detection_loop)
        self.cell_detection_thread.daemon = True
        self.cell_detection_thread.start()
    
    def stop_cell_detection(self):
        """Stop the cell detection process"""
        # Update UI
        self.start_detection_button.config(state=tk.NORMAL)
        self.stop_detection_button.config(state=tk.DISABLED)
        self.draw_aoi_button.config(state=tk.NORMAL)
        self.clear_aoi_button.config(state=tk.NORMAL)
        
        # Set detection inactive
        self.cell_detection_active = False
        self.status_var.set("Cell detection stopped")
    
    def display_to_camera_coords(self, display_coords):
        """Convert display coordinates to camera coordinates"""
        x1, y1, x2, y2 = display_coords
        
        # Adjust for display offsets
        x1 = max(0, x1 - self.display_offset_x)
        x2 = max(0, x2 - self.display_offset_x)
        y1 = max(0, y1 - self.display_offset_y)
        y2 = max(0, y2 - self.display_offset_y)
        
        # Scale to camera resolution
        scale_x = self.frame_width / self.display_width
        scale_y = self.frame_height / self.display_height
        
        cam_x1 = int(x1 * scale_x)
        cam_x2 = int(x2 * scale_x)
        cam_y1 = int(y1 * scale_y)
        cam_y2 = int(y2 * scale_y)
        
        # Ensure coordinates are within camera bounds
        cam_x1 = max(0, min(cam_x1, self.frame_width - 1))
        cam_x2 = max(0, min(cam_x2, self.frame_width - 1))
        cam_y1 = max(0, min(cam_y1, self.frame_height - 1))
        cam_y2 = max(0, min(cam_y2, self.frame_height - 1))
        
        return [cam_x1, cam_y1, cam_x2, cam_y2]
    
    def cell_detection_loop(self):
        """Background thread for cell detection"""
        try:
            while self.cell_detection_active and self.running:
                current_time = time.time()
                
                # Process at the specified interval (10 FPS)
                if current_time - self.last_detection_time >= self.cell_detection_interval:
                    self.last_detection_time = current_time
                    
                    # Get the current frame
                    with self.frame_lock:
                        if self.frame_buffer is not None:
                            frame = self.frame_buffer.copy()
                        else:
                            continue
                    
                    # Get the adjusted AOI coordinates in display space
                    display_aoi_coords = self.get_adjusted_aoi_coords()
                    
                    # Convert to camera coordinates
                    camera_aoi_coords = self.display_to_camera_coords(display_aoi_coords)
                    
                    # Detect cells in the AOI using camera coordinates
                    self.detected_cells, result_image = self.cell_detector.detect_cells(frame, camera_aoi_coords)
                    
                    # Update the cell count display
                    self.cell_count_var.set(f"Cells: {len(self.detected_cells)}")
                    
                    # Update the detection result display
                    self.update_detection_display(result_image)
                
                # Sleep briefly to avoid excessive CPU usage
                time.sleep(0.01)
        except Exception as e:
            print(f"Error in cell detection loop: {str(e)}")
            self.status_var.set(f"Detection error: {str(e)}")
            # Reset UI
            self.root.after_idle(self.stop_cell_detection)
    
    def update_detection_display(self, result_image):
        """Update the detection result display"""
        if result_image is None or self.detection_canvas is None:
            return
        
        # Get the canvas size
        canvas_width = self.detection_canvas.winfo_width()
        canvas_height = self.detection_canvas.winfo_height()
        
        # Skip if canvas is not yet properly sized
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Resize the result image to fit the canvas
        aspect_ratio = result_image.shape[1] / result_image.shape[0]
        
        if canvas_width / canvas_height > aspect_ratio:
            display_height = canvas_height
            display_width = int(display_height * aspect_ratio)
        else:
            display_width = canvas_width
            display_height = int(display_width / aspect_ratio)
        
        # Resize the image
        display_image = cv2.resize(result_image, (display_width, display_height))
        
        # Convert to PhotoImage
        img = Image.fromarray(display_image)
        self.detection_result_photo = ImageTk.PhotoImage(image=img)
        
        # Update the canvas
        self.root.after_idle(self._update_detection_canvas)
    
    def _update_detection_canvas(self):
        """Update the detection canvas (called on the main thread)"""
        if self.detection_result_photo is None:
            return
        
        canvas_width = self.detection_canvas.winfo_width()
        canvas_height = self.detection_canvas.winfo_height()
        
        # If this is the first image, create the image on the canvas
        if not self.detection_canvas.find_withtag("result"):
            self.detection_canvas.create_image(
                canvas_width//2, 
                canvas_height//2, 
                anchor=tk.CENTER, 
                image=self.detection_result_photo,
                tags=("result",)
            )
        else:
            # Update the existing image
            self.detection_canvas.itemconfig("result", image=self.detection_result_photo)
    
    def on_canvas_click(self, event):
        """Handle mouse click on canvas"""
        x, y = event.x, event.y
        
        # Check if we're in AOI drawing mode
        if not self.aoi_active:
            return
        
        # Check if we're clicking on a handle
        for handle_id, handle_pos in self.aoi_handle_coords.items():
            hx, hy = handle_pos
            if abs(x - hx) <= self.aoi_handle_size and abs(y - hy) <= self.aoi_handle_size:
                self.aoi_adjusting = True
                self.aoi_adjust_handle = handle_id
                return
        
        # Start drawing new AOI
        self.aoi_drawing = True
        self.aoi_coords = [x, y, x, y]  # Initialize with click position
        
        # Create or update rectangle
        if self.aoi_rect:
            self.canvas.coords(self.aoi_rect, x, y, x, y)
        else:
            self.aoi_rect = self.canvas.create_rectangle(
                x, y, x, y,
                outline="yellow",
                width=2,
                tags=("aoi",)
            )
        
        # Clear existing handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
    
    def on_canvas_release(self, event):
        """Handle mouse release on canvas"""
        if self.aoi_drawing or self.aoi_adjusting:
            # Finalize the AOI
            x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
            
            # Ensure minimum size
            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                self.status_var.set("AOI too small, try again")
                self.clear_aoi()
            else:
                self.status_var.set(f"AOI set: ({x1},{y1}) to ({x2},{y2})")
                # Create handles for the AOI
                self.create_aoi_handles()
            
            self.aoi_drawing = False
            self.aoi_adjusting = False
            self.aoi_adjust_handle = None
        
    def on_canvas_drag(self, event):
        """Handle mouse drag on canvas"""
        x, y = event.x, event.y
        
        # Constrain to canvas bounds
        x = max(0, min(x, self.canvas.winfo_width()))
        y = max(0, min(y, self.canvas.winfo_height()))
        
        if self.aoi_drawing:
            # Update end coordinates while drawing
            self.aoi_coords[2] = x
            self.aoi_coords[3] = y
            
            # Update rectangle
            x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
            self.canvas.coords(self.aoi_rect, x1, y1, x2, y2)
            
        elif self.aoi_adjusting and self.aoi_adjust_handle:
            # Adjust the appropriate corner or edge
            x1, y1, x2, y2 = self.aoi_coords
            
            if self.aoi_adjust_handle == "nw":
                self.aoi_coords[0] = x
                self.aoi_coords[1] = y
            elif self.aoi_adjust_handle == "ne":
                self.aoi_coords[2] = x
                self.aoi_coords[1] = y
            elif self.aoi_adjust_handle == "se":
                self.aoi_coords[2] = x
                self.aoi_coords[3] = y
            elif self.aoi_adjust_handle == "sw":
                self.aoi_coords[0] = x
                self.aoi_coords[3] = y
            elif self.aoi_adjust_handle == "n":
                self.aoi_coords[1] = y
            elif self.aoi_adjust_handle == "e":
                self.aoi_coords[2] = x
            elif self.aoi_adjust_handle == "s":
                self.aoi_coords[3] = y
            elif self.aoi_adjust_handle == "w":
                self.aoi_coords[0] = x
            
            # Update rectangle
            x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
            self.canvas.coords(self.aoi_rect, x1, y1, x2, y2)
            
            # Update handles
            self.update_handle_positions()
    
    def create_aoi_handles(self):
        """Create handles for adjusting the AOI"""
        # Clear existing handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
        
        x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
        
        # Create corner handles
        handle_positions = {
            "nw": (x1, y1),
            "ne": (x2, y1),
            "se": (x2, y2),
            "sw": (x1, y2),
            "n": ((x1 + x2) // 2, y1),
            "e": (x2, (y1 + y2) // 2),
            "s": ((x1 + x2) // 2, y2),
            "w": (x1, (y1 + y2) // 2)
        }
        
        # Create handle rectangles
        for handle_id, (hx, hy) in handle_positions.items():
            size = self.aoi_handle_size
            handle = self.canvas.create_rectangle(
                hx - size//2, hy - size//2,
                hx + size//2, hy + size//2,
                fill="white", outline="black",
                tags=("handle", handle_id)
            )
            self.aoi_handles.append(handle)
            self.aoi_handle_coords[handle_id] = (hx, hy)
    
    def update_handle_positions(self):
        """Update the positions of AOI adjustment handles"""
        if not self.aoi_handles:
            return
            
        x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
        
        # Update handle positions
        handle_positions = {
            "nw": (x1, y1),
            "ne": (x2, y1),
            "se": (x2, y2),
            "sw": (x1, y2),
            "n": ((x1 + x2) // 2, y1),
            "e": (x2, (y1 + y2) // 2),
            "s": ((x1 + x2) // 2, y2),
            "w": (x1, (y1 + y2) // 2)
        }
        
        # Update handle rectangles
        for i, handle_id in enumerate(["nw", "ne", "se", "sw", "n", "e", "s", "w"]):
            if i < len(self.aoi_handles):
                hx, hy = handle_positions[handle_id]
                size = self.aoi_handle_size
                self.canvas.coords(
                    self.aoi_handles[i],
                    hx - size//2, hy - size//2,
                    hx + size//2, hy + size//2
                )
                self.aoi_handle_coords[handle_id] = (hx, hy)

class CellDetector:
    """Cell detection class for processing images and detecting cells"""
    def __init__(self):
        # Parameters for cell detection
        self.clahe_clip_limit = 2.5
        self.clahe_tile_size = 10
        self.detected_cells = []
        self.processing = False
    
    def detect_cells(self, image, aoi_coords=None):
        """Process image and detect cells, optionally within an AOI"""
        # Make a copy of the image to avoid modifying the original
        org = image.copy()
        
        # If AOI is provided, crop the image to the AOI
        if aoi_coords and all(coord != 0 for coord in aoi_coords):
            x1, y1, x2, y2 = aoi_coords
            # Ensure x1 < x2 and y1 < y2
            if x1 > x2: x1, x2 = x2, x1
            if y1 > y2: y1, y2 = y2, y1
            
            # Crop the image to the AOI
            org = org[y1:y2, x1:x2]
            
            # If the cropped image is too small, return empty results
            if org.shape[0] < 10 or org.shape[1] < 10:
                return [], org
        
        # Convert BGR to RGB for display
        org_rgb = cv2.cvtColor(org, cv2.COLOR_BGR2RGB)
        
        # Convert to grayscale
        gray_image = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, 
                              tileGridSize=(self.clahe_tile_size, self.clahe_tile_size))
        enhanced_image = clahe.apply(gray_image)
        
        # Convert to float and denoise
        double_image = enhanced_image.astype(np.float32) / 255.0
        denoised_image = cv2.GaussianBlur(double_image, (3, 3), 2)
        
        # Binary image
        try:
            binary_image1 = cv2.adaptiveThreshold(org[:,:,2], 255, 
                                              cv2.ADAPTIVE_THRESH_MEAN_C,
                                              cv2.THRESH_BINARY, 11, 2)
            binary_image2 = cv2.adaptiveThreshold(org[:,:,2], 255, 
                                              cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                              cv2.THRESH_BINARY, 11, 2)
            binary_image = binary_image1 | binary_image2
            binary_image = ~binary_image
        except:
            # Fallback if the above fails
            _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        
        # Edge detection
        img_8bit = (denoised_image * 255).astype(np.uint8)
        edge_canny = cv2.Canny(img_8bit, 30, 150)
        
        # Prewitt edge detection
        kernelx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
        kernely = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
        img_prewittx = cv2.filter2D(img_8bit, -1, kernelx)
        img_prewitty = cv2.filter2D(img_8bit, -1, kernely)
        edge_prewitt = np.sqrt(img_prewittx**2 + img_prewitty**2)
        edge_prewitt = edge_prewitt > 30
        
        # Roberts edge detection
        roberts_x = np.array([[1, 0], [0, -1]])
        roberts_y = np.array([[0, 1], [-1, 0]])
        img_robertsx = cv2.filter2D(img_8bit, -1, roberts_x)
        img_robertsy = cv2.filter2D(img_8bit, -1, roberts_y)
        edge_roberts = np.sqrt(img_robertsx**2 + img_robertsy**2)
        edge_roberts = edge_roberts > 30
        
        # Sobel edge detection
        sobelx = cv2.Sobel(img_8bit, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(img_8bit, cv2.CV_64F, 0, 1, ksize=3)
        edge_sobel = np.sqrt(sobelx**2 + sobely**2)
        edge_sobel = edge_sobel > 30
        
        # Edge combination
        roi_edge = edge_canny.astype(bool) | edge_prewitt | edge_roberts | edge_sobel
        
        # Combine segmentations
        roi_seg = roi_edge | binary_image.astype(bool)
        
        # Pre-processing to reduce noise
        roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=15)
        small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        roi_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_OPEN, small_kernel)
        
        # Final processing
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=2)
        final_seg = morphology.remove_small_objects(final_seg.astype(bool), min_size=20)
        final_seg = morphology.remove_small_holes(final_seg)
        final_seg = morphology.remove_small_objects(final_seg, min_size=100)
        
        # Label connected components
        labeled_image = measure.label(final_seg)
        props = measure.regionprops(labeled_image)
        
        # Filter cells based on properties
        detected_cells = []
        for prop in props:
            area = prop.area
            perimeter = prop.perimeter
            circularity = (perimeter * perimeter) / (4 * np.pi * area)
            
            # Cell filtering criteria (adjusted for live detection)
            if (100 < area < 8000 and 
                30 < perimeter < 800 and 
                0.8 < circularity < 12):
                
                bbox = prop.bbox
                height = bbox[2] - bbox[0]
                width = bbox[3] - bbox[1]
                
                # Check aspect ratio
                if ((height > width and 1.5 * width > height) or 
                    (width > height and 1.5 * height > width) or 
                    (height == width)):
                    
                    # If using AOI, adjust the coordinates back to the original image
                    if aoi_coords and all(coord != 0 for coord in aoi_coords):
                        x1_aoi, y1_aoi = aoi_coords[0], aoi_coords[1]
                        adjusted_bbox = (
                            bbox[0] + y1_aoi,  # y1
                            bbox[1] + x1_aoi,  # x1
                            bbox[2] + y1_aoi,  # y2
                            bbox[3] + x1_aoi   # x2
                        )
                        detected_cells.append({
                            'bbox': adjusted_bbox,
                            'area': area,
                            'perimeter': perimeter,
                            'circularity': circularity,
                            'centroid': (prop.centroid[0] + y1_aoi, prop.centroid[1] + x1_aoi)
                        })
                    else:
                        detected_cells.append({
                            'bbox': bbox,
                            'area': area,
                            'perimeter': perimeter,
                            'circularity': circularity,
                            'centroid': prop.centroid
                        })
        
        # Create a visualization of the detected cells
        result_image = self.visualize_cells(org_rgb, detected_cells, aoi_coords)
        
        return detected_cells, result_image
    
    def visualize_cells(self, image, cells, aoi_coords=None):
        """Create a visualization of the detected cells"""
        # Make a copy of the image for drawing
        result_image = image.copy()
        
        # Draw bounding boxes for detected cells
        for cell in cells:
            bbox = cell['bbox']
            
            # If using AOI, adjust the coordinates for the visualization
            if aoi_coords and all(coord != 0 for coord in aoi_coords):
                y1, x1, y2, x2 = bbox
                y1_aoi, x1_aoi = aoi_coords[1], aoi_coords[0]
                y1 -= y1_aoi
                x1 -= x1_aoi
                y2 -= y1_aoi
                x2 -= x1_aoi
                bbox = (y1, x1, y2, x2)
            else:
                y1, x1, y2, x2 = bbox
            
            # Draw rectangle
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Add text with cell properties
            text = f"A:{cell['area']:.0f}\nP:{cell['perimeter']:.0f}\nC:{cell['circularity']:.2f}"
            centroid = cell['centroid']
            if aoi_coords and all(coord != 0 for coord in aoi_coords):
                centroid = (centroid[0] - aoi_coords[1], centroid[1] - aoi_coords[0])
            
            # Place text at the centroid
            cv2.putText(result_image, text, (int(centroid[1]), int(centroid[0])), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        return result_image

def main():
    root = tk.Tk()
    app = SimpleToupCamLive(root)
    root.mainloop()

if __name__ == "__main__":
    main()
