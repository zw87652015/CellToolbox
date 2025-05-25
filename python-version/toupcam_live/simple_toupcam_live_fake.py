"""
OBS Virtual Camera Live Stream
This script provides a basic live stream from an OBS virtual camera using OpenCV,
while maintaining the same cell detection functionality as the ToupCam implementation.
"""

import sys
import os
import time
import threading
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from skimage import filters, morphology, measure, segmentation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json

class VirtualCameraLive:
    def __init__(self, root):
        self.root = root
        self.root.title("OBS Virtual Camera Live Stream")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Camera variables
        self.cap = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.running = False
        
        # Camera settings
        self.camera_index = 0  # Default camera index (usually 0 for first camera)
        
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
        
        # Parameter controls
        param_notebook = ttk.Notebook(cell_frame)
        param_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CLAHE parameters tab
        clahe_frame = ttk.Frame(param_notebook)
        param_notebook.add(clahe_frame, text="CLAHE")
        
        # CLAHE Clip Limit
        ttk.Label(clahe_frame, text="Clip Limit:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.clahe_clip_var = tk.DoubleVar(value=2.5)
        clahe_clip_scale = ttk.Scale(
            clahe_frame,
            from_=1.0,
            to=5.0,
            orient=tk.HORIZONTAL,
            variable=self.clahe_clip_var,
            command=self.update_clahe_clip
        )
        clahe_clip_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.clahe_clip_value_label = ttk.Label(clahe_frame, text="2.5")
        self.clahe_clip_value_label.pack(anchor=tk.E, padx=5)
        
        # CLAHE Tile Size
        ttk.Label(clahe_frame, text="Tile Size:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.clahe_tile_var = tk.IntVar(value=10)
        clahe_tile_scale = ttk.Scale(
            clahe_frame,
            from_=2,
            to=20,
            orient=tk.HORIZONTAL,
            variable=self.clahe_tile_var,
            command=self.update_clahe_tile
        )
        clahe_tile_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.clahe_tile_value_label = ttk.Label(clahe_frame, text="10")
        self.clahe_tile_value_label.pack(anchor=tk.E, padx=5)
        
        # Edge detection parameters tab
        edge_frame = ttk.Frame(param_notebook)
        param_notebook.add(edge_frame, text="Edge")
        
        # Canny Low Threshold
        ttk.Label(edge_frame, text="Canny Low:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.canny_low_var = tk.IntVar(value=30)
        canny_low_scale = ttk.Scale(
            edge_frame,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.canny_low_var,
            command=self.update_canny_low
        )
        canny_low_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.canny_low_value_label = ttk.Label(edge_frame, text="30")
        self.canny_low_value_label.pack(anchor=tk.E, padx=5)
        
        # Canny High Threshold
        ttk.Label(edge_frame, text="Canny High:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.canny_high_var = tk.IntVar(value=150)
        canny_high_scale = ttk.Scale(
            edge_frame,
            from_=50,
            to=300,
            orient=tk.HORIZONTAL,
            variable=self.canny_high_var,
            command=self.update_canny_high
        )
        canny_high_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.canny_high_value_label = ttk.Label(edge_frame, text="150")
        self.canny_high_value_label.pack(anchor=tk.E, padx=5)
        
        # Edge Threshold
        ttk.Label(edge_frame, text="Edge Threshold:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.edge_threshold_var = tk.IntVar(value=30)
        edge_threshold_scale = ttk.Scale(
            edge_frame,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.edge_threshold_var,
            command=self.update_edge_threshold
        )
        edge_threshold_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.edge_threshold_value_label = ttk.Label(edge_frame, text="30")
        self.edge_threshold_value_label.pack(anchor=tk.E, padx=5)
        
        # Cell filtering parameters tab
        filter_frame = ttk.Frame(param_notebook)
        param_notebook.add(filter_frame, text="Filter")
        
        # Area Range
        ttk.Label(filter_frame, text="Area Range:").pack(anchor=tk.W, padx=5, pady=(5,0))
        area_frame = ttk.Frame(filter_frame)
        area_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        
        self.min_area_var = tk.IntVar(value=100)
        min_area_scale = ttk.Scale(
            area_frame,
            from_=50,
            to=500,
            orient=tk.HORIZONTAL,
            variable=self.min_area_var,
            command=self.update_min_area
        )
        min_area_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        
        self.max_area_var = tk.IntVar(value=8000)
        max_area_scale = ttk.Scale(
            area_frame,
            from_=1000,
            to=15000,
            orient=tk.HORIZONTAL,
            variable=self.max_area_var,
            command=self.update_max_area
        )
        max_area_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2,0))
        
        area_value_frame = ttk.Frame(filter_frame)
        area_value_frame.pack(fill=tk.X, padx=5)
        self.min_area_value_label = ttk.Label(area_value_frame, text="100")
        self.min_area_value_label.pack(side=tk.LEFT)
        self.max_area_value_label = ttk.Label(area_value_frame, text="8000")
        self.max_area_value_label.pack(side=tk.RIGHT)
        
        # Perimeter Range
        ttk.Label(filter_frame, text="Perimeter Range:").pack(anchor=tk.W, padx=5, pady=(5,0))
        perimeter_frame = ttk.Frame(filter_frame)
        perimeter_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        
        self.min_perimeter_var = tk.IntVar(value=30)
        min_perimeter_scale = ttk.Scale(
            perimeter_frame,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.min_perimeter_var,
            command=self.update_min_perimeter
        )
        min_perimeter_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        
        self.max_perimeter_var = tk.IntVar(value=800)
        max_perimeter_scale = ttk.Scale(
            perimeter_frame,
            from_=200,
            to=1500,
            orient=tk.HORIZONTAL,
            variable=self.max_perimeter_var,
            command=self.update_max_perimeter
        )
        max_perimeter_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2,0))
        
        perimeter_value_frame = ttk.Frame(filter_frame)
        perimeter_value_frame.pack(fill=tk.X, padx=5)
        self.min_perimeter_value_label = ttk.Label(perimeter_value_frame, text="30")
        self.min_perimeter_value_label.pack(side=tk.LEFT)
        self.max_perimeter_value_label = ttk.Label(perimeter_value_frame, text="800")
        self.max_perimeter_value_label.pack(side=tk.RIGHT)
        
        # Circularity Range
        ttk.Label(filter_frame, text="Circularity Range:").pack(anchor=tk.W, padx=5, pady=(5,0))
        circularity_frame = ttk.Frame(filter_frame)
        circularity_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        
        self.min_circularity_var = tk.DoubleVar(value=0.8)
        min_circularity_scale = ttk.Scale(
            circularity_frame,
            from_=0.5,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.min_circularity_var,
            command=self.update_min_circularity
        )
        min_circularity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        
        self.max_circularity_var = tk.DoubleVar(value=12.0)
        max_circularity_scale = ttk.Scale(
            circularity_frame,
            from_=5.0,
            to=20.0,
            orient=tk.HORIZONTAL,
            variable=self.max_circularity_var,
            command=self.update_max_circularity
        )
        max_circularity_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2,0))
        
        circularity_value_frame = ttk.Frame(filter_frame)
        circularity_value_frame.pack(fill=tk.X, padx=5)
        self.min_circularity_value_label = ttk.Label(circularity_value_frame, text="0.8")
        self.min_circularity_value_label.pack(side=tk.LEFT)
        self.max_circularity_value_label = ttk.Label(circularity_value_frame, text="12.0")
        self.max_circularity_value_label.pack(side=tk.RIGHT)
        
        # Parameter load/save buttons
        param_buttons_frame = ttk.Frame(cell_frame)
        param_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Apply button for all parameters
        self.apply_params_button = ttk.Button(
            param_buttons_frame,
            text="Apply Parameters",
            command=self.apply_detection_parameters
        )
        self.apply_params_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        
        # Load parameters button
        self.load_params_button = ttk.Button(
            param_buttons_frame,
            text="Load Parameters",
            command=self.load_parameters
        )
        self.load_params_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2,0))
        
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
        """Initialize and start the OBS virtual camera using OpenCV"""
        try:
            # Try to open the camera (usually 0 for default camera)
            # For OBS virtual camera, this should be one of the available camera indices
            self.cap = cv2.VideoCapture(self.camera_index)
            
            # Check if camera opened successfully
            if not self.cap.isOpened():
                # Try a few more indices if the first one fails
                for i in range(1, 5):
                    self.cap = cv2.VideoCapture(i)
                    if self.cap.isOpened():
                        self.camera_index = i
                        break
                
                if not self.cap.isOpened():
                    self.status_var.set("Failed to open camera")
                    messagebox.showerror(
                        "Camera Error", 
                        "No camera found. Please start OBS Virtual Camera and restart the application."
                    )
                    return
            
            # Get camera properties
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Camera resolution: {self.frame_width}x{self.frame_height}")
            
            # Set running flag to True to enable image processing
            self.running = True
            
            # Start the frame capture thread
            self.capture_thread = threading.Thread(target=self.capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            self.status_var.set(f"Camera started: OBS Virtual Camera ({self.frame_width}x{self.frame_height})")
        except Exception as e:
            self.status_var.set(f"Error starting camera: {str(e)}")
            messagebox.showerror("Camera Error", f"Error starting camera: {str(e)}")
    
    def capture_frames(self):
        """Continuously capture frames from the camera in a separate thread"""
        while self.running:
            try:
                # Read a frame from the camera
                ret, frame = self.cap.read()
                
                if ret:
                    # Store the frame
                    with self.frame_lock:
                        self.frame_buffer = frame
                        self.new_frame_available = True
                    
                    # Track frame timing for FPS calculation
                    current_time = time.time()
                    self.frame_count += 1
                    if current_time - self.last_fps_time >= 1.0:
                        self.fps = self.frame_count / (current_time - self.last_fps_time)
                        self.fps_label.configure(text=f"FPS: {self.fps:.1f}")
                        self.status_var.set(f"Camera running: {self.fps:.1f} FPS")
                        self.frame_count = 0
                        self.last_fps_time = current_time
                else:
                    print("[ERROR] Failed to read frame from camera")
                    time.sleep(0.01)  # Short sleep to prevent CPU overload
                    
            except Exception as e:
                print(f"[ERROR] Exception in capture_frames: {e}")
                time.sleep(0.1)  # Sleep on error to prevent rapid error loops
    
    # The process_image method is no longer needed as we're handling frames in capture_frames
    
    def update_frame(self):
        """Update the UI with the latest frame"""
        if not self.running or self.frame_buffer is None:
            return
            
        # Get the current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Use the full canvas size for display, stretching if needed
            display_width = canvas_width
            display_height = canvas_height
            
            # Store display dimensions for coordinate mapping
            self.display_width = display_width
            self.display_height = display_height
            self.display_offset_x = 0  # No offset
            self.display_offset_y = 0  # No offset
            
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
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)  # Fill rectangle with white
                
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
                        # Get the original coordinates
                        bbox = cell['bbox']
                        y1_cell, x1_cell, y2_cell, x2_cell = bbox
                        
                        # Scale coordinates to display size
                        # Convert [y1, x1, y2, x2] to [x1, y1, x2, y2] for scaling
                        orig_coords = [x1_cell, y1_cell, x2_cell, y2_cell]
                        scaled_coords = self.scale_coords_to_display(orig_coords)
                        
                        # Extract scaled coordinates
                        display_x1, display_y1, display_x2, display_y2 = scaled_coords
                        
                        # Draw rectangle with scaled coordinates
                        cv2.rectangle(display_frame, 
                                     (display_x1, display_y1), 
                                     (display_x2, display_y2), 
                                     (255, 0, 0), 2)
                        
                        # Scale centroid coordinates
                        centroid = cell['centroid']
                        # Centroid is (y, x) format, convert to (x, y) for scaling
                        centroid_coords = [centroid[1], centroid[0]]
                        scaled_centroid = self.scale_coords_to_display(centroid_coords)
                        
                        # Add text with cell properties (simplified for main display)
                        text = f"A:{cell['area']:.0f}"
                        
                        # Place text at the scaled centroid
                        cv2.putText(display_frame, text, 
                                   (scaled_centroid[0], scaled_centroid[1]), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Convert to PhotoImage
            img = Image.fromarray(display_frame)
            self.photo_image = ImageTk.PhotoImage(image=img)
            
            # If this is the first frame, create the image on the canvas
            if not self.canvas.find_withtag("video"):
                self.canvas.create_image(
                    0, 0,  # Position at top-left corner
                    anchor=tk.NW,  # Northwest anchor (top-left)
                    image=self.photo_image,
                    tags=("video",)
                )
            else:
                # Update the existing image
                self.canvas.itemconfig("video", image=self.photo_image)
                
            # Update AOI rectangle if it exists
            if self.aoi_rect:
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
            print(f"[ERROR] Exception in capture_frames: {e}")
            time.sleep(0.1)  # Sleep on error to prevent rapid error loops

    def on_closing(self):
        """Clean up resources when the application is closed"""
        self.running = False
        
        # Stop cell detection if active
        if self.cell_detection_active:
            self.stop_cell_detection()
        
        # Stop rendering
        self.render_running = False
        
        # Close the camera
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            print("Camera released successfully")
        
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
    
    def start_cell_detection(self):
        """Start cell detection processing"""
        if not self.cell_detection_active:
            self.cell_detection_active = True
            self.start_detection_button.config(state=tk.DISABLED)
            self.stop_detection_button.config(state=tk.NORMAL)
            self.status_var.set("Cell detection started")
    
    def stop_cell_detection(self):
        """Stop cell detection processing"""
        if self.cell_detection_active:
            self.cell_detection_active = False
            self.start_detection_button.config(state=tk.NORMAL)
            self.stop_detection_button.config(state=tk.DISABLED)
            self.status_var.set("Cell detection stopped")
    
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
    
    def update_aoi_overlay(self, value=None):
        """Update the AOI overlay opacity"""
        # This function is called when the opacity slider is changed
        # We don't need to do anything here except force a redraw
        # The actual opacity is applied during the render process
        # Just set a flag to indicate the frame needs to be updated
        self.new_frame_available = True
    
    def get_adjusted_aoi_coords(self):
        """Return AOI coordinates adjusted to ensure x1<x2 and y1<y2"""
        x1, y1, x2, y2 = self.aoi_coords
        
        # Ensure x1 < x2 and y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        return [x1, y1, x2, y2]
    
    def scale_aoi_to_original(self, aoi_coords):
        """Scale AOI coordinates from display size to original image size"""
        x1, y1, x2, y2 = aoi_coords
        
        # Get original frame dimensions
        if self.frame_buffer is not None:
            orig_height, orig_width = self.frame_buffer.shape[:2]
        else:
            # Default to camera resolution if frame buffer is not available
            orig_width, orig_height = 640, 480  # Default camera resolution
        
        # Get display dimensions
        display_width = self.display_width
        display_height = self.display_height
        
        # Calculate scale factors
        scale_x = orig_width / display_width
        scale_y = orig_height / display_height
        
        # Scale coordinates
        scaled_x1 = int(x1 * scale_x)
        scaled_y1 = int(y1 * scale_y)
        scaled_x2 = int(x2 * scale_x)
        scaled_y2 = int(y2 * scale_y)
        
        # Ensure coordinates are within bounds
        scaled_x1 = max(0, min(scaled_x1, orig_width - 1))
        scaled_y1 = max(0, min(scaled_y1, orig_height - 1))
        scaled_x2 = max(0, min(scaled_x2, orig_width - 1))
        scaled_y2 = max(0, min(scaled_y2, orig_height - 1))
        
        return [scaled_x1, scaled_y1, scaled_x2, scaled_y2]
    
    def scale_coords_to_display(self, coords):
        """Scale coordinates from original image size to display size"""
        # Get original frame dimensions
        if self.frame_buffer is not None:
            orig_height, orig_width = self.frame_buffer.shape[:2]
        else:
            # Default to camera resolution if frame buffer is not available
            orig_width, orig_height = 640, 480  # Default camera resolution
        
        # Get display dimensions
        display_width = self.display_width
        display_height = self.display_height
        
        # Calculate scale factors
        scale_x = display_width / orig_width
        scale_y = display_height / orig_height
        
        # Scale the coordinates
        scaled_coords = []
        for i in range(0, len(coords), 2):
            if i+1 < len(coords):
                x = int(coords[i] * scale_x)
                y = int(coords[i+1] * scale_y)
                scaled_coords.extend([x, y])
        
        return scaled_coords
    
    def update_aoi_overlay(self, *args):
        """Update the AOI overlay based on opacity slider"""
        # Force a frame update to refresh the overlay
        if hasattr(self, 'aoi_coords') and all(coord != 0 for coord in self.aoi_coords):
            self.update_frame()
    
    def update_clahe_clip(self, value):
        """Update CLAHE clip limit value"""
        value = float(value)
        self.clahe_clip_value_label.config(text=f"{value:.1f}")
    
    def update_clahe_tile(self, value):
        """Update CLAHE tile size value"""
        value = int(float(value))
        self.clahe_tile_value_label.config(text=str(value))
    
    def update_canny_low(self, value):
        """Update Canny low threshold value"""
        value = int(float(value))
        self.canny_low_value_label.config(text=str(value))
    
    def update_canny_high(self, value):
        """Update Canny high threshold value"""
        value = int(float(value))
        self.canny_high_value_label.config(text=str(value))
    
    def update_edge_threshold(self, value):
        """Update edge threshold value"""
        value = int(float(value))
        self.edge_threshold_value_label.config(text=str(value))
    
    def update_min_area(self, value):
        """Update minimum area value"""
        value = int(float(value))
        self.min_area_value_label.config(text=str(value))
    
    def update_max_area(self, value):
        """Update maximum area value"""
        value = int(float(value))
        self.max_area_value_label.config(text=str(value))
    
    def update_min_perimeter(self, value):
        """Update minimum perimeter value"""
        value = int(float(value))
        self.min_perimeter_value_label.config(text=str(value))
    
    def update_max_perimeter(self, value):
        """Update maximum perimeter value"""
        value = int(float(value))
        self.max_perimeter_value_label.config(text=str(value))
    
    def update_min_circularity(self, value):
        """Update minimum circularity value"""
        value = float(value)
        self.min_circularity_value_label.config(text=f"{value:.1f}")
    
    def update_max_circularity(self, value):
        """Update maximum circularity value"""
        value = float(value)
        self.max_circularity_value_label.config(text=f"{value:.1f}")
    
    def load_parameters(self):
        """Load parameters from a JSON file"""
        # Schedule this function to run after a short delay to ensure UI is responsive
        self.root.after(10, self._load_parameters_impl)
    
    def _load_parameters_impl(self):
        """Implementation of parameter loading with proper thread handling"""
        # Temporarily pause the camera processing to prevent freezing
        was_detection_active = self.cell_detection_active
        if was_detection_active:
            self.stop_cell_detection()
        
        # Temporarily stop the render thread to free up resources
        was_rendering = self.render_running
        if was_rendering:
            self.render_running = False
            time.sleep(0.1)  # Give the render thread time to stop
        
        try:
            # Look for parameters directory in the parent directory
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            params_dir = os.path.join(parent_dir, "parameters")
            
            # If parameters directory doesn't exist, use the current directory
            if not os.path.exists(params_dir):
                params_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Update status before opening dialog
            self.status_var.set("Opening file dialog...")
            
            # Process all pending events to ensure UI is updated
            self.root.update_idletasks()
            self.root.update()
            
            # Open file dialog to select parameter file
            file_path = filedialog.askopenfilename(
                title="Load Parameters",
                initialdir=params_dir,
                filetypes=[("JSON files", "*.json")],
                parent=self.root
            )
            
            if not file_path:
                self.status_var.set("Parameter loading canceled")
                # Restart render thread if it was active
                if was_rendering:
                    self.render_running = True
                # Resume cell detection if it was active before
                if was_detection_active:
                    self.start_cell_detection()
                return
                
            # Load parameters from file
            with open(file_path, 'r') as f:
                params = json.load(f)
                
            # Update UI controls with loaded parameters
            self.update_ui_from_params(params)
            
            # Apply the loaded parameters
            self.apply_detection_parameters()
            
            # Update status
            self.status_var.set(f"Parameters loaded from {os.path.basename(file_path)}")
            
            # Restart render thread if it was active
            if was_rendering:
                self.render_running = True
            
            # Resume cell detection if it was active before
            if was_detection_active:
                self.start_cell_detection()
            
        except Exception as e:
            self.status_var.set(f"Error loading parameters: {str(e)}")
            messagebox.showerror("Error", f"Failed to load parameters: {str(e)}")
            
            # Restart render thread if it was active
            if was_rendering:
                self.render_running = True
                
            # Resume cell detection if it was active before
            if was_detection_active:
                self.start_cell_detection()
    
    def update_ui_from_params(self, params):
        """Update UI controls based on loaded parameters"""
        # Map parameter names to UI variables and update functions
        param_mapping = {
            'clahe_clip_limit': (self.clahe_clip_var, self.update_clahe_clip),
            'clahe_tile_size': (self.clahe_tile_var, self.update_clahe_tile),
            'min_object_size': None,  # Not directly exposed in UI
            'eccentricity_threshold': None,  # Not directly exposed in UI
            'area_threshold_small': None,  # Not directly exposed in UI
            'area_threshold_large': None,  # Not directly exposed in UI
            'area_min': (self.min_area_var, self.update_min_area),
            'area_max': (self.max_area_var, self.update_max_area),
            'perimeter_min': (self.min_perimeter_var, self.update_min_perimeter),
            'perimeter_max': (self.max_perimeter_var, self.update_max_perimeter),
            'circularity_min': (self.min_circularity_var, self.update_min_circularity),
            'circularity_max': (self.max_circularity_var, self.update_max_circularity),
            'aspect_ratio_threshold': None  # Not directly exposed in UI
        }
        
        # Additional mappings for parameters with different names
        additional_mappings = {
            'canny_low': (self.canny_low_var, self.update_canny_low),
            'canny_high': (self.canny_high_var, self.update_canny_high),
            'edge_threshold': (self.edge_threshold_var, self.update_edge_threshold)
        }
        
        # Update UI controls based on loaded parameters
        for param_name, value in params.items():
            # Check if parameter exists in main mapping
            if param_name in param_mapping and param_mapping[param_name] is not None:
                var, update_func = param_mapping[param_name]
                var.set(value)
                update_func(value)
            # Check additional mappings
            elif param_name in additional_mappings:
                var, update_func = additional_mappings[param_name]
                var.set(value)
                update_func(value)
            
        # Update cell detector parameters that are not directly exposed in UI
        # These parameters will be used in the cell detection process
        if 'min_object_size' in params:
            self.cell_detector.min_object_size = params['min_object_size']
        if 'eccentricity_threshold' in params:
            self.cell_detector.eccentricity_threshold = params['eccentricity_threshold']
        if 'area_threshold_small' in params:
            self.cell_detector.area_threshold_small = params['area_threshold_small']
        if 'area_threshold_large' in params:
            self.cell_detector.area_threshold_large = params['area_threshold_large']
        if 'aspect_ratio_threshold' in params:
            self.cell_detector.aspect_ratio_threshold = params['aspect_ratio_threshold']
    
    def apply_detection_parameters(self):
        """Apply all detection parameters to the cell detector"""
        # Update CLAHE parameters
        self.cell_detector.clahe_clip_limit = self.clahe_clip_var.get()
        self.cell_detector.clahe_tile_size = self.clahe_tile_var.get()
        
        # Update edge detection parameters
        self.cell_detector.canny_low = self.canny_low_var.get()
        self.cell_detector.canny_high = self.canny_high_var.get()
        self.cell_detector.edge_threshold = self.edge_threshold_var.get()
        
        # Update cell filtering parameters
        self.cell_detector.min_area = self.min_area_var.get()
        self.cell_detector.max_area = self.max_area_var.get()
        self.cell_detector.min_perimeter = self.min_perimeter_var.get()
        self.cell_detector.max_perimeter = self.max_perimeter_var.get()
        self.cell_detector.min_circularity = self.min_circularity_var.get()
        self.cell_detector.max_circularity = self.max_circularity_var.get()
        
        # Update morphology parameters
        self.cell_detector.min_object_size = 15  # Default value from parameter_visualization_ui.py
        
        # Update additional parameters from parameter_visualization_ui.py
        # These values will be overridden if they are in the loaded parameter file
        self.cell_detector.eccentricity_threshold = 0.98
        self.cell_detector.area_threshold_small = 200
        self.cell_detector.area_threshold_large = 400
        self.cell_detector.aspect_ratio_threshold = 1.5
        
        # Update status
        self.status_var.set("Detection parameters applied")
    
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
        
        # Apply current parameters to the cell detector
        self.apply_detection_parameters()
        
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
                    
                    # Get the adjusted AOI coordinates
                    display_aoi_coords = self.get_adjusted_aoi_coords()
                    
                    # Scale AOI coordinates to match the original image resolution
                    scaled_aoi_coords = self.scale_aoi_to_original(display_aoi_coords)
                    
                    # Detect cells in the AOI
                    self.detected_cells, result_image = self.cell_detector.detect_cells(frame, scaled_aoi_coords)
                    
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
        # Parameters for cell detection (aligned with parameter_visualization_ui.py)
        self.clahe_clip_limit = 2.5
        self.clahe_tile_size = 10
        
        # Edge detection parameters
        self.canny_low = 30
        self.canny_high = 150
        self.edge_threshold = 30
        
        # Cell filtering parameters (aligned with parameter_visualization_ui.py)
        self.min_area = 200  # Updated from 100 to 200
        self.max_area = 3000  # Updated from 8000 to 3000
        self.min_perimeter = 300
        self.max_perimeter = 800
        self.min_circularity = 0.8
        self.max_circularity = 12.0
        
        # Additional parameters from parameter_visualization_ui.py
        self.min_object_size = 15
        self.eccentricity_threshold = 0.98
        self.area_threshold_small = 200
        self.area_threshold_large = 400
        self.aspect_ratio_threshold = 1.5
        
        # Morphology parameters
        self.final_min_size = 100
        
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
        edge_canny = cv2.Canny(img_8bit, self.canny_low, self.canny_high)
        
        # Prewitt edge detection
        kernelx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
        kernely = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
        img_prewittx = cv2.filter2D(img_8bit, -1, kernelx)
        img_prewitty = cv2.filter2D(img_8bit, -1, kernely)
        edge_prewitt = np.sqrt(img_prewittx**2 + img_prewitty**2)
        edge_prewitt = edge_prewitt > self.edge_threshold
        
        # Roberts edge detection
        roberts_x = np.array([[1, 0], [0, -1]])
        roberts_y = np.array([[0, 1], [-1, 0]])
        img_robertsx = cv2.filter2D(img_8bit, -1, roberts_x)
        img_robertsy = cv2.filter2D(img_8bit, -1, roberts_y)
        edge_roberts = np.sqrt(img_robertsx**2 + img_robertsy**2)
        edge_roberts = edge_roberts > self.edge_threshold
        
        # Sobel edge detection
        sobelx = cv2.Sobel(img_8bit, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(img_8bit, cv2.CV_64F, 0, 1, ksize=3)
        edge_sobel = np.sqrt(sobelx**2 + sobely**2)
        edge_sobel = edge_sobel > self.edge_threshold
        
        # Edge combination
        roi_edge = edge_canny.astype(bool) | edge_prewitt | edge_roberts | edge_sobel
        
        # Combine segmentations
        roi_seg = roi_edge | binary_image.astype(bool)
        
        # Pre-processing to reduce noise
        roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=self.min_object_size)
        small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        roi_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_OPEN, small_kernel)
        
        # Final processing
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=2)
        final_seg = morphology.remove_small_objects(final_seg.astype(bool), min_size=20)
        final_seg = morphology.remove_small_holes(final_seg)
        final_seg = morphology.remove_small_objects(final_seg, min_size=self.final_min_size)
        
        # Label connected components
        labeled_image = measure.label(final_seg)
        props = measure.regionprops(labeled_image)
        
        # Filter cells based on properties
        detected_cells = []
        for prop in props:
            area = prop.area
            perimeter = prop.perimeter
            circularity = (perimeter * perimeter) / (4 * np.pi * area)
            eccentricity = prop.eccentricity
            
            # Get bounding box for aspect ratio calculation
            bbox = prop.bbox
            height = bbox[2] - bbox[0]
            width = bbox[3] - bbox[1]
            
            # Calculate aspect ratio condition using parameter from visualization UI
            aspect_ratio_condition = (
                (height > width and self.aspect_ratio_threshold * width > height) or
                (width > height and self.aspect_ratio_threshold * height > width) or
                (height == width)
            )
            
            # Cell filtering criteria (aligned with parameter_visualization_ui.py)
            # First check eccentricity and area thresholds
            if ((eccentricity < self.eccentricity_threshold and area > self.area_threshold_small) or 
                (area > self.area_threshold_large)):
                # Then check area, perimeter, circularity and aspect ratio
                if (self.min_area < area < self.max_area and 
                    self.min_perimeter < perimeter < self.max_perimeter and 
                    self.min_circularity < circularity < self.max_circularity and
                    aspect_ratio_condition):
                    
                    # Calculate centroid
                    y, x = prop.centroid
                    
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
                            'eccentricity': eccentricity,
                            'centroid': (y + y1_aoi, x + x1_aoi)
                        })
                    else:
                        # Add cell to the list
                        detected_cells.append({
                            'bbox': bbox,
                            'centroid': (y, x),
                            'area': area,
                            'perimeter': perimeter,
                            'circularity': circularity,
                            'eccentricity': eccentricity
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
    app = VirtualCameraLive(root)
    root.mainloop()

if __name__ == "__main__":
    main()
