"""
MP4 Video File Live Stream
This script provides a basic live stream from an MP4 video file on loop using OpenCV,
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
import scipy.ndimage as ndi

# Import for multi-monitor support
try:
    import win32api
    HAS_WIN32API = True
except ImportError:
    HAS_WIN32API = False
    print("win32api not available. Multi-monitor support will be limited.")
    # You may need to install pywin32: pip install pywin32

class MP4VideoLive:
    def __init__(self, root):
        self.root = root
        self.root.title("MP4 Video Live Stream")
        # Initialize in fullscreen mode
        self.root.attributes('-fullscreen', True)
        # Add key binding to exit fullscreen with Escape key
        self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())
        self.fullscreen = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Video variables
        self.cap = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.running = False
        
        # Video file settings
        self.video_path = ""  # Path to the MP4 file
        self.frame_position = 0  # Current frame position
        
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
        self.aoi_overlay_mode = "darken"  # Default overlay mode ("darken" or "brighten")
        
        # Cell detection variables
        self.cell_detector = CellDetector()
        self.cell_detection_active = False
        self.cell_detection_thread = None
        self.cell_detection_interval = 0.05  # 20 FPS for cell detection
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
        
        # Video control panel
        video_control_frame = ttk.LabelFrame(control_frame, text="Video Controls")
        video_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a frame for the buttons
        button_frame = ttk.Frame(video_control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Load video button
        load_button = ttk.Button(button_frame, text="Load Video", command=self.start_camera)
        load_button.pack(side=tk.LEFT, padx=2, pady=5, fill=tk.X, expand=True)
        
        # Stop video button
        stop_button = ttk.Button(button_frame, text="Stop Video", command=self.stop_camera)
        stop_button.pack(side=tk.LEFT, padx=2, pady=5, fill=tk.X, expand=True)
        
        # Change video button
        change_button = ttk.Button(button_frame, text="Change Video", command=self.change_video)
        change_button.pack(side=tk.LEFT, padx=2, pady=5, fill=tk.X, expand=True)
        
        # Create a second row for additional controls
        control_row2 = ttk.Frame(video_control_frame)
        control_row2.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Toggle fullscreen button
        fullscreen_button = ttk.Button(control_row2, text="Toggle Fullscreen (Esc)", command=self.toggle_fullscreen)
        fullscreen_button.pack(side=tk.LEFT, padx=2, pady=5, fill=tk.X, expand=True)
        
        # Exit button - styled to be noticeable
        exit_button = ttk.Button(control_row2, text="Exit Application", command=self.on_closing, style="Exit.TButton")
        exit_button.pack(side=tk.LEFT, padx=2, pady=5, fill=tk.X, expand=True)
        
        # Create a custom style for the exit button
        style = ttk.Style()
        style.configure("Exit.TButton", foreground="red", font=("Arial", 9, "bold"))
        
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
        
        # Segmentation parameters tab
        seg_frame = ttk.Frame(param_notebook)
        param_notebook.add(seg_frame, text="Segmentation")
        
        # Min Object Size
        ttk.Label(seg_frame, text="Min Object Size:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.min_object_size_var = tk.IntVar(value=15)
        min_object_size_scale = ttk.Scale(
            seg_frame,
            from_=5,
            to=50,
            orient=tk.HORIZONTAL,
            variable=self.min_object_size_var,
            command=self.update_min_object_size
        )
        min_object_size_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.min_object_size_value_label = ttk.Label(seg_frame, text="15")
        self.min_object_size_value_label.pack(anchor=tk.E, padx=5)
        
        # Eccentricity Threshold
        ttk.Label(seg_frame, text="Eccentricity Threshold:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.eccentricity_var = tk.DoubleVar(value=0.98)
        eccentricity_scale = ttk.Scale(
            seg_frame,
            from_=0.5,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.eccentricity_var,
            command=self.update_eccentricity
        )
        eccentricity_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.eccentricity_value_label = ttk.Label(seg_frame, text="0.98")
        self.eccentricity_value_label.pack(anchor=tk.E, padx=5)
        
        # Area Threshold Small
        ttk.Label(seg_frame, text="Area Threshold Small:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.area_small_var = tk.IntVar(value=200)
        area_small_scale = ttk.Scale(
            seg_frame,
            from_=50,
            to=500,
            orient=tk.HORIZONTAL,
            variable=self.area_small_var,
            command=self.update_area_small
        )
        area_small_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.area_small_value_label = ttk.Label(seg_frame, text="200")
        self.area_small_value_label.pack(anchor=tk.E, padx=5)
        
        # Area Threshold Large
        ttk.Label(seg_frame, text="Area Threshold Large:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.area_large_var = tk.IntVar(value=400)
        area_large_scale = ttk.Scale(
            seg_frame,
            from_=200,
            to=1000,
            orient=tk.HORIZONTAL,
            variable=self.area_large_var,
            command=self.update_area_large
        )
        area_large_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.area_large_value_label = ttk.Label(seg_frame, text="400")
        self.area_large_value_label.pack(anchor=tk.E, padx=5)
        
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
        
        # Aspect Ratio Threshold
        ttk.Label(filter_frame, text="Aspect Ratio Threshold:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.aspect_ratio_var = tk.DoubleVar(value=1.5)
        aspect_ratio_scale = ttk.Scale(
            filter_frame,
            from_=1.0,
            to=3.0,
            orient=tk.HORIZONTAL,
            variable=self.aspect_ratio_var,
            command=self.update_aspect_ratio
        )
        aspect_ratio_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.aspect_ratio_value_label = ttk.Label(filter_frame, text="1.5")
        self.aspect_ratio_value_label.pack(anchor=tk.E, padx=5)
        
        # Watershed segmentation parameters tab
        watershed_frame = ttk.Frame(param_notebook)
        param_notebook.add(watershed_frame, text="Watershed")
        
        # Enable/Disable Watershed
        watershed_enable_frame = ttk.Frame(watershed_frame)
        watershed_enable_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(watershed_enable_frame, text="Use Watershed:").pack(side=tk.LEFT)
        self.use_watershed_var = tk.BooleanVar(value=True)
        self.use_watershed_checkbox = ttk.Checkbutton(
            watershed_enable_frame, 
            variable=self.use_watershed_var,
            command=self.update_use_watershed
        )
        self.use_watershed_checkbox.pack(side=tk.RIGHT)
        
        # Watershed Distance Threshold
        ttk.Label(watershed_frame, text="Distance Threshold:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.watershed_distance_var = tk.IntVar(value=10)
        watershed_distance_scale = ttk.Scale(
            watershed_frame,
            from_=1,
            to=50,
            orient=tk.HORIZONTAL,
            variable=self.watershed_distance_var,
            command=self.update_watershed_distance
        )
        watershed_distance_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.watershed_distance_value_label = ttk.Label(watershed_frame, text="10")
        self.watershed_distance_value_label.pack(anchor=tk.E, padx=5)
        
        # Watershed Compactness
        ttk.Label(watershed_frame, text="Compactness:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.watershed_compactness_var = tk.DoubleVar(value=0.5)
        watershed_compactness_scale = ttk.Scale(
            watershed_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.watershed_compactness_var,
            command=self.update_watershed_compactness
        )
        watershed_compactness_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.watershed_compactness_value_label = ttk.Label(watershed_frame, text="0.5")
        self.watershed_compactness_value_label.pack(anchor=tk.E, padx=5)
        
        # Watershed Minimum Area
        ttk.Label(watershed_frame, text="Min Area for Watershed:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.watershed_min_area_var = tk.IntVar(value=500)
        watershed_min_area_scale = ttk.Scale(
            watershed_frame,
            from_=100,
            to=1000,
            orient=tk.HORIZONTAL,
            variable=self.watershed_min_area_var,
            command=self.update_watershed_min_area
        )
        watershed_min_area_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.watershed_min_area_value_label = ttk.Label(watershed_frame, text="500")
        self.watershed_min_area_value_label.pack(anchor=tk.E, padx=5)
        
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
        """Load and start playing an MP4 video file on loop"""
        try:
            # If no video path is set, open a file dialog to select an MP4 file
            if not self.video_path:
                # Set default video directory to E:\Videos\ToupCamRecordings
                videos_dir = r"E:\Videos\ToupCamRecordings"
                
                # If the specified directory doesn't exist, fall back to parent directory
                if not os.path.exists(videos_dir):
                    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    videos_dir = os.path.join(parent_dir, "videos")
                    
                    # If videos directory doesn't exist, use the current directory
                    if not os.path.exists(videos_dir):
                        videos_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Update status before opening dialog
                self.status_var.set("Opening file dialog...")
                
                # Process all pending events to ensure UI is updated
                self.root.update_idletasks()
                self.root.update()
                
                # Open file dialog to select MP4 file
                self.video_path = filedialog.askopenfilename(
                    title="Select MP4 Video File",
                    initialdir=videos_dir,
                    filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
                    parent=self.root
                )
                
                if not self.video_path:
                    self.status_var.set("No video file selected")
                    return
            
            # Try to open the video file
            self.cap = cv2.VideoCapture(self.video_path)
            
            # Check if video opened successfully
            if not self.cap.isOpened():
                self.status_var.set("Failed to open video file")
                messagebox.showerror(
                    "Video Error", 
                    f"Could not open video file: {self.video_path}"
                )
                return
            
            # Get video properties
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps_source = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"Video resolution: {self.frame_width}x{self.frame_height}")
            print(f"Total frames: {self.total_frames}, Source FPS: {self.fps_source}")
            
            # In fullscreen mode, we don't need to set window size
            # Just print the screen dimensions for reference
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            print(f"Screen dimensions: {screen_width}x{screen_height}")
            print(f"Video resolution: {self.frame_width}x{self.frame_height}")
            
            # If not in fullscreen mode, calculate and set window size
            if not self.fullscreen:
                # Calculate window size to maintain aspect ratio but limit to screen size
                available_width = screen_width - 100  # Leave some margin
                available_height = screen_height - 100  # Leave some margin
                
                # Calculate scaling factor to fit within screen
                width_scale = available_width / self.frame_width
                height_scale = available_height / self.frame_height
                scale = min(width_scale, height_scale, 1.0)  # Don't scale up if video is smaller than screen
                
                # Calculate window dimensions
                window_width = int(self.frame_width * scale)
                window_height = int(self.frame_height * scale)
                
                # Add extra space for controls (approximately 250px for right panel)
                window_width += 250
                
                # Set window size
                self.root.geometry(f"{window_width}x{window_height}+{(screen_width-window_width)//2}+{(screen_height-window_height)//2}")
                print(f"Window size set to: {window_width}x{window_height}")
            
            # Update canvas size to match video dimensions
            # We need to wait for the window to be updated before setting canvas dimensions
            self.root.update_idletasks()
            
            # Get the available space for the canvas (video frame size)
            video_frame = self.canvas.master
            video_frame_width = video_frame.winfo_width()
            video_frame_height = video_frame.winfo_height()
            
            # Calculate canvas size to maintain aspect ratio within the video frame
            canvas_aspect_ratio = self.frame_width / self.frame_height
            frame_aspect_ratio = video_frame_width / video_frame_height
            
            if frame_aspect_ratio > canvas_aspect_ratio:
                # Frame is wider than needed
                canvas_height = video_frame_height
                canvas_width = int(canvas_height * canvas_aspect_ratio)
            else:
                # Frame is taller than needed
                canvas_width = video_frame_width
                canvas_height = int(canvas_width / canvas_aspect_ratio)
            
            # Set initial display dimensions and offsets
            self.display_width = canvas_width
            self.display_height = canvas_height
            self.display_offset_x = (video_frame_width - canvas_width) // 2
            self.display_offset_y = (video_frame_height - canvas_height) // 2
            
            print(f"Canvas size set to: {canvas_width}x{canvas_height}")
            print(f"Display offsets: x={self.display_offset_x}, y={self.display_offset_y}")
            
            # Set running flag to True to enable image processing
            self.running = True
            
            # Start the frame capture thread
            self.capture_thread = threading.Thread(target=self.capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            self.status_var.set(f"Video loaded: {os.path.basename(self.video_path)} ({self.frame_width}x{self.frame_height})")
        except Exception as e:
            self.status_var.set(f"Error loading video: {str(e)}")
            messagebox.showerror("Video Error", f"Error loading video: {str(e)}")
    
    def capture_frames(self):
        """Continuously capture frames from the MP4 file in a separate thread, looping when reaching the end"""
        target_fps = self.fps_source if self.fps_source > 0 else 30  # Default to 30 FPS if source FPS is not available
        frame_delay = 1.0 / target_fps  # Time to wait between frames to maintain source FPS
        
        while self.running:
            try:
                # Read a frame from the video file
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
                        self.status_var.set(f"Video playing: {os.path.basename(self.video_path)} - {self.fps:.1f} FPS")
                        self.frame_count = 0
                        self.last_fps_time = current_time
                    
                    # Update frame position
                    self.frame_position = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                    
                    # Control playback speed to match target FPS
                    time.sleep(frame_delay)
                else:
                    # Reached the end of the video, loop back to the beginning
                    print("Reached end of video, looping back to beginning")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.frame_position = 0
                    
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
            # Calculate aspect ratio of the video
            video_aspect_ratio = self.frame_width / self.frame_height  # 2688/1520 = 1.77
            canvas_aspect_ratio = canvas_width / canvas_height
            
            # Maintain aspect ratio while fitting in the canvas
            if canvas_aspect_ratio > video_aspect_ratio:
                # Canvas is wider than video aspect ratio
                display_height = canvas_height
                display_width = int(display_height * video_aspect_ratio)
                self.display_offset_x = (canvas_width - display_width) // 2
                self.display_offset_y = 0
            else:
                # Canvas is taller than video aspect ratio
                display_width = canvas_width
                display_height = int(display_width / video_aspect_ratio)
                self.display_offset_x = 0
                self.display_offset_y = (canvas_height - display_height) // 2
            
            # Store display dimensions for coordinate mapping
            self.display_width = display_width
            self.display_height = display_height
            
            # Convert BGR to RGB for display
            rgb_frame = cv2.cvtColor(self.frame_buffer, cv2.COLOR_BGR2RGB)
            
            # Apply AOI overlay if active
            if hasattr(self, 'aoi_coords') and all(coord != 0 for coord in self.aoi_coords):
                # Get AOI coordinates scaled to original image size
                aoi_coords = self.scale_aoi_to_original(self.get_adjusted_aoi_coords())
                
                # Only apply mask if AOI has a valid area
                if all(coord != 0 for coord in aoi_coords) and \
                   abs(aoi_coords[2]-aoi_coords[0]) > 10 and abs(aoi_coords[3]-aoi_coords[1]) > 10:
                    # Create a copy of the frame for overlay
                    overlay = rgb_frame.copy()
                    
                    # Create a mask for the AOI (white inside AOI, black outside)
                    mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
                    x1, y1, x2, y2 = aoi_coords
                    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)  # Fill rectangle with white
                    
                    # Darken areas outside AOI while keeping AOI at normal brightness
                    alpha = self.opacity_var.get()  # Get opacity from slider
                    
                    # Create a darkened version of the entire frame
                    overlay_dark = cv2.addWeighted(overlay, 1-alpha, np.zeros_like(overlay), alpha, 0)
                    
                    # Convert mask to 3-channel for boolean operations
                    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
                    
                    # Apply the mask: keep original frame inside AOI, darkened outside
                    rgb_frame = np.where(mask_3ch > 0, rgb_frame, overlay_dark)
            
            # Resize the frame to fit the display dimensions
            display_frame = cv2.resize(rgb_frame, (self.display_width, self.display_height))
            
            # Draw detected cells on the display if cell detection is active
            if self.cell_detection_active and hasattr(self, 'detected_cells') and self.detected_cells:
                # Get the current AOI coordinates for filtering
                if hasattr(self, 'aoi_coords') and all(coord != 0 for coord in self.aoi_coords):
                    # Get AOI coordinates in original image space
                    x1_aoi, y1_aoi, x2_aoi, y2_aoi = self.aoi_coords
                    # Ensure x1 < x2 and y1 < y2
                    if x1_aoi > x2_aoi:
                        x1_aoi, x2_aoi = x2_aoi, x1_aoi
                    if y1_aoi > y2_aoi:
                        y1_aoi, y2_aoi = y2_aoi, y1_aoi
                else:
                    # No AOI defined, use full frame
                    x1_aoi, y1_aoi, x2_aoi, y2_aoi = 0, 0, self.frame_width, self.frame_height
                
                # Draw bounding boxes for detected cells
                for cell in self.detected_cells:
                    # Get the original coordinates
                    bbox = cell['bbox']
                    y1_cell, x1_cell, y2_cell, x2_cell = bbox
                    
                    # Check if cell is within AOI
                    if x1_aoi <= x1_cell and x2_aoi >= x2_cell and y1_aoi <= y1_cell and y2_aoi >= y2_cell:
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
                    self.display_offset_x, self.display_offset_y,  # Position with offsets for centering
                    anchor=tk.NW,  # Northwest anchor (top-left)
                    image=self.photo_image,
                    tags=("video",)
                )
            else:
                # Update the existing image
                self.canvas.itemconfig("video", image=self.photo_image)
                self.canvas.coords("video", self.display_offset_x, self.display_offset_y)
                
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

    def stop_camera(self):
        """Stop the video playback and release resources"""
        # Stop the rendering thread
        self.render_running = False
        
        # Stop the cell detection if it's running
        if self.cell_detection_active:
            self.stop_cell_detection()
        
        # Set running flag to False to stop frame capture
        self.running = False
        
        # Wait for threads to finish
        if hasattr(self, 'capture_thread') and self.capture_thread is not None:
            self.capture_thread.join(timeout=1.0)
            
        # Release video resources
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        # Clear the frame buffer
        with self.frame_lock:
            self.frame_buffer = None
        
        # Update UI
        self.canvas.delete("all")
        self.status_var.set("Video stopped")
    
    def change_video(self):
        """Change the current video file"""
        # Stop current video if running
        if self.running:
            self.stop_camera()
        
        # Reset video path to force file selection dialog
        self.video_path = ""
        
        # Start with new video
        self.start_camera()

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
                
    def toggle_fullscreen(self, event=None):
        """Toggle between fullscreen and windowed mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        
        if not self.fullscreen:
            # If exiting fullscreen, set a reasonable window size
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            window_width = min(int(screen_width * 0.8), 1600)
            window_height = min(int(screen_height * 0.8), 900)
            self.root.geometry(f"{window_width}x{window_height}+{(screen_width-window_width)//2}+{(screen_height-window_height)//2}")
            
        # Force a redraw to update the display
        self.root.update_idletasks()
        self.new_frame_available = True
        
        return "break"  # Prevent the event from propagating
    
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
        """Clear the AOI rectangle and associated mask"""
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
        
        # Force a frame update to clear the grey mask overlay
        self.new_frame_available = True
        
        self.status_var.set("AOI cleared")
    
    def update_aoi_overlay(self, value=None):
        """Update the AOI overlay opacity"""
        # This function is called when the opacity slider is changed
        # We don't need to do anything here except force a redraw
        # The actual opacity is applied during the render process
        # Just set a flag to indicate the frame needs to be updated
        self.new_frame_available = True
    
    def scale_aoi_to_original(self, aoi_coords):
        """Scale AOI coordinates from display size to original image size"""
        x1, y1, x2, y2 = aoi_coords
        
        # Remove display offsets
        x1 -= self.display_offset_x
        y1 -= self.display_offset_y
        x2 -= self.display_offset_x
        y2 -= self.display_offset_y
        
        # Scale coordinates from display size to original image size
        x1_orig = int(x1 * (self.frame_width / self.display_width))
        y1_orig = int(y1 * (self.frame_height / self.display_height))
        x2_orig = int(x2 * (self.frame_width / self.display_width))
        y2_orig = int(y2 * (self.frame_height / self.display_height))
        
        # Ensure coordinates are within image bounds
        x1_orig = max(0, min(x1_orig, self.frame_width - 1))
        y1_orig = max(0, min(y1_orig, self.frame_height - 1))
        x2_orig = max(0, min(x2_orig, self.frame_width - 1))
        y2_orig = max(0, min(y2_orig, self.frame_height - 1))
        
        return [x1_orig, y1_orig, x2_orig, y2_orig]
    
    def scale_coords_to_display(self, coords):
        """Scale coordinates from original image size to display size"""
        # Input can be [x, y] or [x1, y1, x2, y2]
        if len(coords) == 2:
            x, y = coords
            
            # Scale coordinates from original image size to display size
            x_display = int(x * (self.display_width / self.frame_width))
            y_display = int(y * (self.display_height / self.frame_height))
            
            # Apply display offsets
            x_display += self.display_offset_x
            y_display += self.display_offset_y
            
            return [x_display, y_display]
        else:
            x1, y1, x2, y2 = coords
            
            # Scale coordinates from original image size to display size
            x1_display = int(x1 * (self.display_width / self.frame_width))
            y1_display = int(y1 * (self.display_height / self.frame_height))
            x2_display = int(x2 * (self.display_width / self.frame_width))
            y2_display = int(y2 * (self.display_height / self.frame_height))
            
            # Apply display offsets
            x1_display += self.display_offset_x
            y1_display += self.display_offset_y
            x2_display += self.display_offset_x
            y2_display += self.display_offset_y
            
            return [x1_display, y1_display, x2_display, y2_display]
        self.new_frame_available = True
    
    def get_adjusted_aoi_coords(self):
        """Return AOI coordinates adjusted to ensure x1<x2 and y1<y2 and with display offsets applied"""
        x1, y1, x2, y2 = self.aoi_coords
        
        # Ensure x1 < x2 and y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        # Apply display offsets to coordinates
        x1 += self.display_offset_x
        y1 += self.display_offset_y
        x2 += self.display_offset_x
        y2 += self.display_offset_y
            
        return [x1, y1, x2, y2]
    
    def scale_aoi_to_original(self, aoi_coords):
        """Scale AOI coordinates from display size to original image size"""
        x1, y1, x2, y2 = aoi_coords
        
        # Remove display offsets
        x1 -= self.display_offset_x
        y1 -= self.display_offset_y
        x2 -= self.display_offset_x
        y2 -= self.display_offset_y
        
        # Get original frame dimensions
        orig_width = self.frame_width
        orig_height = self.frame_height
        
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
        orig_width = self.frame_width
        orig_height = self.frame_height
        
        # Get display dimensions
        display_width = self.display_width
        display_height = self.display_height
        
        # Calculate scale factors
        scale_x = display_width / orig_width
        scale_y = display_height / orig_height
        
        # Handle different input formats
        if len(coords) == 2:
            # Handle [x, y] format
            x, y = coords
            x_display = int(x * scale_x)
            y_display = int(y * scale_y)
            
            # Apply display offsets
            x_display += self.display_offset_x
            y_display += self.display_offset_y
            
            return [x_display, y_display]
        elif len(coords) == 4:
            # Handle [x1, y1, x2, y2] format
            x1, y1, x2, y2 = coords
            x1_display = int(x1 * scale_x)
            y1_display = int(y1 * scale_y)
            x2_display = int(x2 * scale_x)
            y2_display = int(y2 * scale_y)
            
            # Apply display offsets
            x1_display += self.display_offset_x
            y1_display += self.display_offset_y
            x2_display += self.display_offset_x
            y2_display += self.display_offset_y
            
            return [x1_display, y1_display, x2_display, y2_display]
        else:
            # Handle arbitrary coordinate list [x1, y1, x2, y2, ...]
            scaled_coords = []
            for i in range(0, len(coords), 2):
                if i+1 < len(coords):
                    x = int(coords[i] * scale_x) + self.display_offset_x
                    y = int(coords[i+1] * scale_y) + self.display_offset_y
                    scaled_coords.extend([x, y])
            
            return scaled_coords
    
    def update_aoi_overlay(self, *args):
        """Update the AOI overlay based on opacity slider"""
        # Force a redraw of the frame to update the overlay with new opacity
        self.new_frame_available = True
        
        # If AOI is active, force an immediate frame update
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
        """Update the maximum circularity value"""
        value = float(value)
        self.max_circularity_value_label.config(text=f"{value:.1f}")
        # We'll apply the parameters when the user clicks the Apply Button
        
    def update_aspect_ratio(self, value):
        """Update the aspect ratio threshold"""
        value = float(value)
        self.aspect_ratio_value_label.config(text=f"{value:.1f}")
        # We'll apply the parameters when the user clicks the Apply Button
        
    def update_min_object_size(self, value):
        """Update the minimum object size"""
        value = int(float(value))
        self.min_object_size_value_label.config(text=f"{value}")
        # We'll apply the parameters when the user clicks the Apply Button
        
    def update_eccentricity(self, value):
        """Update the eccentricity threshold"""
        value = float(value)
        self.eccentricity_value_label.config(text=f"{value:.2f}")
        # We'll apply the parameters when the user clicks the Apply Button
        
    def update_area_small(self, value):
        """Update the area threshold small"""
        value = int(float(value))
        self.area_small_value_label.config(text=f"{value}")
        # We'll apply the parameters when the user clicks the Apply Button
        
    def update_area_large(self, value):
        """Update the area threshold large"""
        value = int(float(value))
        self.area_large_value_label.config(text=f"{value}")
        # We'll apply the parameters when the user clicks the Apply Button
    
    def update_use_watershed(self, value=None):
        """Update the use watershed flag"""
        # If value is provided (from parameter loading), use it to set the checkbox
        if value is not None:
            self.use_watershed_var.set(bool(value))
        # We'll apply the parameters when the user clicks the Apply Button
    
    def update_watershed_distance(self, value):
        """Update the watershed distance threshold"""
        value = int(float(value))
        self.watershed_distance_value_label.config(text=f"{value}")
        # We'll apply the parameters when the user clicks the Apply Button
    
    def update_watershed_compactness(self, value):
        """Update the watershed compactness value"""
        value = float(value)
        self.watershed_compactness_value_label.config(text=f"{value:.1f}")
        # We'll apply the parameters when the user clicks the Apply Button
    
    def update_watershed_min_area(self, value):
        """Update the minimum area for watershed segmentation"""
        value = int(float(value))
        self.watershed_min_area_value_label.config(text=f"{value}")
        # We'll apply the parameters when the user clicks the Apply Button
    
    def show_file_dialog(self, dialog_type='open', **kwargs):
        """Show a file dialog, temporarily exiting fullscreen mode if needed
        
        Args:
            dialog_type: 'open' for open dialog, 'save' for save dialog
            **kwargs: Arguments to pass to the file dialog function
            
        Returns:
            Selected file path or None if canceled
        """
        # Store current fullscreen state
        was_fullscreen = self.fullscreen
        
        # Temporarily exit fullscreen mode to ensure dialog appears properly
        if was_fullscreen:
            self.root.attributes('-fullscreen', False)
            self.root.update()
        
        try:
            # Show the appropriate dialog
            if dialog_type == 'open':
                file_path = filedialog.askopenfilename(parent=self.root, **kwargs)
            else:  # save dialog
                file_path = filedialog.asksaveasfilename(parent=self.root, **kwargs)
        finally:
            # Restore fullscreen mode if it was active
            if was_fullscreen:
                self.root.attributes('-fullscreen', True)
                self.fullscreen = True
                self.root.update()
        
        return file_path
    
    def load_parameters(self):
        """Load parameters from a JSON file"""
        # Look for parameters directory in the parent directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        params_dir = os.path.join(parent_dir, "parameters")
        
        # If parameters directory doesn't exist, use the current directory
        if not os.path.exists(params_dir):
            params_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Update status before opening dialog
        self.status_var.set("Opening file dialog...")
        self.root.update_idletasks()
        
        # Show file dialog to select parameter file
        file_path = self.show_file_dialog(
            dialog_type='open',
            title="Load Parameters",
            initialdir=params_dir,
            filetypes=[("JSON files", "*.json")]
        )
        
        if not file_path:
            self.status_var.set("Parameter loading canceled")
            return
        
        # Continue with parameter loading
        self._load_parameters_from_file(file_path)
    
    def _load_parameters_from_file(self, file_path):
        """Load parameters from the specified file and apply them"""
        # Temporarily pause the camera processing to prevent freezing
        was_detection_active = self.cell_detection_active
        if was_detection_active:
            self.stop_cell_detection()
            
        # Store the current state of the render thread, but don't stop it
        # This prevents the video from stopping during parameter loading
        was_rendering = self.render_running
        
        try:
            # Update status
            self.status_var.set(f"Loading parameters from {os.path.basename(file_path)}...")
            self.root.update_idletasks()
            
            # Load parameters from file
            with open(file_path, 'r') as f:
                params = json.load(f)
            
            # Filter out Edge tab parameters that no longer exist in the UI
            # This ensures backward compatibility with older parameter files
            filtered_params = {}
            for key, value in params.items():
                # Skip Edge tab parameters that no longer exist
                if key in ['canny_low', 'canny_high', 'edge_threshold']:
                    continue
                filtered_params[key] = value
                
            # Update UI controls with loaded parameters
            self.update_ui_from_params(filtered_params)
            
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
            'min_object_size': (self.min_object_size_var, self.update_min_object_size),
            'eccentricity_threshold': (self.eccentricity_var, self.update_eccentricity),
            'area_threshold_small': (self.area_small_var, self.update_area_small),
            'area_threshold_large': (self.area_large_var, self.update_area_large),
            'area_min': (self.min_area_var, self.update_min_area),
            'area_max': (self.max_area_var, self.update_max_area),
            'perimeter_min': (self.min_perimeter_var, self.update_min_perimeter),
            'perimeter_max': (self.max_perimeter_var, self.update_max_perimeter),
            'circularity_min': (self.min_circularity_var, self.update_min_circularity),
            'circularity_max': (self.max_circularity_var, self.update_max_circularity),
            'aspect_ratio_threshold': (self.aspect_ratio_var, self.update_aspect_ratio),
            'use_watershed': (self.use_watershed_var, self.update_use_watershed),
            'watershed_distance_threshold': (self.watershed_distance_var, self.update_watershed_distance),
            'watershed_compactness': (self.watershed_compactness_var, self.update_watershed_compactness),
            'watershed_min_area': (self.watershed_min_area_var, self.update_watershed_min_area)
        }
        
        # Additional mappings for parameters with different names
        additional_mappings = {
            # Handle legacy parameter names for backward compatibility
            'min_area': (self.min_area_var, self.update_min_area),
            'max_area': (self.max_area_var, self.update_max_area),
            'min_perimeter': (self.min_perimeter_var, self.update_min_perimeter),
            'max_perimeter': (self.max_perimeter_var, self.update_max_perimeter),
            'min_circularity': (self.min_circularity_var, self.update_min_circularity),
            'max_circularity': (self.max_circularity_var, self.update_max_circularity)
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
            
        # Ensure area_min/max and min_area/max_area are synchronized
        if 'area_min' in params and 'min_area' not in params:
            self.cell_detector.min_area = params['area_min']
        if 'area_max' in params and 'max_area' not in params:
            self.cell_detector.max_area = params['area_max']
        if 'min_area' in params and 'area_min' not in params:
            self.cell_detector.area_min = params['min_area']
        if 'max_area' in params and 'area_max' not in params:
            self.cell_detector.area_max = params['max_area']
    
    def apply_detection_parameters(self):
        """Apply all detection parameters to the cell detector"""
        # Update CLAHE parameters
        self.cell_detector.clahe_clip_limit = self.clahe_clip_var.get()
        self.cell_detector.clahe_tile_size = self.clahe_tile_var.get()
        
        # Update segmentation parameters (replacing edge detection parameters)
        self.cell_detector.min_object_size = self.min_object_size_var.get()
        self.cell_detector.eccentricity_threshold = self.eccentricity_var.get()
        self.cell_detector.area_threshold_small = self.area_small_var.get()
        self.cell_detector.area_threshold_large = self.area_large_var.get()
        
        # Update cell filtering parameters
        # Set both area_min/max and min_area/max_area for compatibility
        self.cell_detector.area_min = self.min_area_var.get()
        self.cell_detector.area_max = self.max_area_var.get()
        self.cell_detector.min_area = self.min_area_var.get()  # For backward compatibility
        self.cell_detector.max_area = self.max_area_var.get()  # For backward compatibility
        
        # Update perimeter and circularity parameters
        self.cell_detector.min_perimeter = self.min_perimeter_var.get()
        self.cell_detector.max_perimeter = self.max_perimeter_var.get()
        self.cell_detector.min_circularity = self.min_circularity_var.get()
        self.cell_detector.max_circularity = self.max_circularity_var.get()
        
        # Update aspect ratio threshold
        self.cell_detector.aspect_ratio_threshold = self.aspect_ratio_var.get()
        
        # Update watershed segmentation parameters
        self.cell_detector.use_watershed = self.use_watershed_var.get()
        self.cell_detector.watershed_distance_threshold = self.watershed_distance_var.get()
        self.cell_detector.watershed_compactness = self.watershed_compactness_var.get()
        self.cell_detector.watershed_min_area = self.watershed_min_area_var.get()
        
        # Force a frame update to refresh the display
        self.new_frame_available = True
        
        # Update status
        self.status_var.set("Detection parameters applied")
    
    def start_cell_detection(self):
        """Start the cell detection process"""
        # Check if AOI is defined
        if not all(coord != 0 for coord in self.aoi_coords):
            messagebox.showwarning("No AOI", "Please draw an Area of Interest before starting cell detection.")
            return
        
        # Check if video is playing
        if not self.running or self.frame_buffer is None:
            messagebox.showwarning("Video Not Playing", "Video must be playing to detect cells.")
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
        
        # Cell detection variables
        self.cell_detection_active = False
        self.detected_cells = []
        self.cell_detector = CellDetector()
        self.cell_detector.min_object_size = 0
        self.cell_detector.eccentricity_threshold = 0
        self.cell_detector.area_threshold_small = 0
        self.cell_detector.area_threshold_large = 0
        self.cell_detector.area_min = 0
        self.cell_detector.area_max = 0
        self.cell_detector.min_perimeter = 0
        self.cell_detector.max_perimeter = 0
        self.cell_detector.min_circularity = 0
        self.cell_detector.max_circularity = 0
        self.cell_detector.aspect_ratio_threshold = 0
        self.cell_detector.use_watershed = False
        self.cell_detector.watershed_distance_threshold = 0
        self.cell_detector.watershed_compactness = 0
        self.cell_detector.watershed_min_area = 0
        self.status_var.set("Cell detection stopped")
    
    def cell_detection_loop(self):
        """Background thread for cell detection"""
        try:
            while self.cell_detection_active and self.running:
                current_time = time.time()
                
                # Process at the specified interval
                if current_time - self.last_detection_time >= self.cell_detection_interval:
                    self.last_detection_time = current_time
                    
                    # Start timing the detection cycle
                    detection_start_time = time.time()
                    
                    # Get the current frame
                    with self.frame_lock:
                        if self.frame_buffer is not None:
                            frame = self.frame_buffer.copy()
                        else:
                            continue
                    
                    # Get the AOI coordinates from the canvas display
                    # First, get the display coordinates with offsets
                    display_coords = self.get_adjusted_aoi_coords()
                    
                    # Now scale these to the original image dimensions
                    # This will remove the display offsets and apply proper scaling
                    scaled_aoi_coords = self.scale_aoi_to_original(display_coords)
                    
                    # Detect cells in the AOI
                    self.detected_cells, result_image = self.cell_detector.detect_cells(frame, scaled_aoi_coords)
                    
                    # Calculate detection time
                    detection_end_time = time.time()
                    detection_time_ms = (detection_end_time - detection_start_time) * 1000  # Convert to milliseconds
                    
                    # Log the coordinates and timing information
                    print(f"Cell detection using AOI: {scaled_aoi_coords} - Time: {detection_time_ms:.2f} ms")
                    
                    # Update the cell count display with timing information
                    self.cell_count_var.set(f"Cells: {len(self.detected_cells)} - Time: {detection_time_ms:.2f} ms")
                    
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
        
        # Store the result image for processing on the main thread
        # This reduces thread contention and makes updates smoother
        self.detection_result_image = result_image.copy()
        
        # Schedule the update on the main thread with a slight delay to reduce flashing
        # Use after instead of after_idle to better control the update rate
        self.root.after(50, self._update_detection_canvas)
    
    def _update_detection_canvas(self):
        """Update the detection canvas (called on the main thread)"""
        if self.detection_result_image is None or self.detection_canvas is None:
            return
        
        canvas_width = self.detection_canvas.winfo_width()
        canvas_height = self.detection_canvas.winfo_height()
        
        # Skip if canvas is not yet properly sized
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        # Resize the result image to fit the canvas
        aspect_ratio = self.detection_result_image.shape[1] / self.detection_result_image.shape[0]
        
        if canvas_width / canvas_height > aspect_ratio:
            display_height = canvas_height
            display_width = int(display_height * aspect_ratio)
        else:
            display_width = canvas_width
            display_height = int(display_width / aspect_ratio)
        
        # Resize the image
        try:
            display_image = cv2.resize(self.detection_result_image, (display_width, display_height))
            
            # Convert to PhotoImage
            img = Image.fromarray(display_image)
            self.detection_result_photo = ImageTk.PhotoImage(image=img)
            
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
        except Exception as e:
            print(f"Error updating detection canvas: {str(e)}")
            # Don't attempt to update again immediately if there was an error
    
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
        
        # Start drawing new AOI - remove display offsets to store raw coordinates
        self.aoi_drawing = True
        # Adjust for display offsets when storing the coordinates
        adjusted_x = x - self.display_offset_x
        adjusted_y = y - self.display_offset_y
        self.aoi_coords = [adjusted_x, adjusted_y, adjusted_x, adjusted_y]  # Initialize with adjusted click position
        
        # Create or update rectangle - use display coordinates for canvas drawing
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
                # Force a frame update to create the grey mask
                self.new_frame_available = True
            
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
            # Update end coordinates while drawing - adjust for display offsets
            adjusted_x = x - self.display_offset_x
            adjusted_y = y - self.display_offset_y
            self.aoi_coords[2] = adjusted_x
            self.aoi_coords[3] = adjusted_y
            
            # For display, we need to use canvas coordinates with display offsets
            display_x1 = self.aoi_coords[0] + self.display_offset_x
            display_y1 = self.aoi_coords[1] + self.display_offset_y
            display_x2 = self.aoi_coords[2] + self.display_offset_x
            display_y2 = self.aoi_coords[3] + self.display_offset_y
            
            # Update rectangle with display coordinates
            self.canvas.coords(self.aoi_rect, display_x1, display_y1, display_x2, display_y2)
            
            # Force a frame update to update the grey mask
            self.new_frame_available = True
            
        elif self.aoi_adjusting and self.aoi_adjust_handle:
            # Adjust the appropriate corner or edge - remove display offsets
            adjusted_x = x - self.display_offset_x
            adjusted_y = y - self.display_offset_y
            
            if self.aoi_adjust_handle == "nw":
                self.aoi_coords[0] = adjusted_x
                self.aoi_coords[1] = adjusted_y
            elif self.aoi_adjust_handle == "ne":
                self.aoi_coords[2] = adjusted_x
                self.aoi_coords[1] = adjusted_y
            elif self.aoi_adjust_handle == "se":
                self.aoi_coords[2] = adjusted_x
                self.aoi_coords[3] = adjusted_y
            elif self.aoi_adjust_handle == "sw":
                self.aoi_coords[0] = adjusted_x
                self.aoi_coords[3] = adjusted_y
            elif self.aoi_adjust_handle == "n":
                self.aoi_coords[1] = adjusted_y
            elif self.aoi_adjust_handle == "e":
                self.aoi_coords[2] = adjusted_x
            elif self.aoi_adjust_handle == "s":
                self.aoi_coords[3] = adjusted_y
            elif self.aoi_adjust_handle == "w":
                self.aoi_coords[0] = adjusted_x
            
            # For display, we need to use canvas coordinates with display offsets
            display_x1 = self.aoi_coords[0] + self.display_offset_x
            display_y1 = self.aoi_coords[1] + self.display_offset_y
            display_x2 = self.aoi_coords[2] + self.display_offset_x
            display_y2 = self.aoi_coords[3] + self.display_offset_y
            
            # Update rectangle with display coordinates
            self.canvas.coords(self.aoi_rect, display_x1, display_y1, display_x2, display_y2)
            
            # Update handles
            self.update_handle_positions()
            
            # Force a frame update to update the grey mask
            self.new_frame_available = True
    
    def create_aoi_handles(self):
        """Create handles for adjusting the AOI"""
        # Clear existing handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
        
        # Get display coordinates with offsets applied
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
        # Parameters for cell detection (exactly matched with parameter_visualization_ui.py)
        self.clahe_clip_limit = 2.5
        self.clahe_tile_size = 10
        self.min_object_size = 15
        self.eccentricity_threshold = 0.98
        self.area_threshold_small = 200
        self.area_threshold_large = 400
        self.area_min = 50  # Updated to match parameter_visualization_ui.py
        self.area_max = 300  # Updated to match parameter_visualization_ui.py
        self.min_perimeter = 100  # Updated to match parameter_visualization_ui.py
        self.max_perimeter = 300  # Updated to match parameter_visualization_ui.py
        self.min_circularity = 0.8
        self.max_circularity = 12.0
        self.aspect_ratio_threshold = 1.5
        
        # Edge detection parameters
        self.canny_low = 30
        self.canny_high = 150
        self.edge_threshold = 30
        
        # Morphology parameters
        self.final_min_size = 100
        
        # Watershed segmentation parameters (synced from parameter_visualization_ui.py)
        self.use_watershed = True
        self.watershed_distance_threshold = 10
        self.watershed_footprint_size = 3
        self.watershed_compactness = 0.5
        self.watershed_min_area = 500
        
        # For backward compatibility
        self.min_area = self.area_min
        self.max_area = self.area_max
        
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
        
        # Kirsch operators (added to match parameter_visualization_ui.py)
        kirsch_kernels = [
            np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float32),
            np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float32),
            np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float32),
            np.array([[-3, -3, -3], [5, 0, -3], [5, 5, -3]], dtype=np.float32),
            np.array([[-3, -3, -3], [-3, 0, -3], [5, 5, 5]], dtype=np.float32),
            np.array([[-3, -3, -3], [-3, 0, 5], [-3, 5, 5]], dtype=np.float32),
            np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float32),
            np.array([[-3, 5, 5], [-3, 0, 5], [-3, -3, -3]], dtype=np.float32)
        ]
        
        kirsch_outputs = []
        for kernel in kirsch_kernels:
            # Apply Kirsch filter (keeping float32)
            filtered = cv2.filter2D(denoised_image.astype(np.float32), -1, kernel)
            
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
        
        i9 = np.zeros_like(kirsch_outputs[0], dtype=bool)
        for output in kirsch_outputs:
            i9 = i9 | output
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        i9 = cv2.erode(i9.astype(np.uint8), kernel, iterations=1)
        i9 = cv2.morphologyEx(i9, cv2.MORPH_CLOSE, kernel)
        
        # Combine segmentations
        roi_seg = roi_edge | i9.astype(bool) | binary_image.astype(bool)
        
        # Pre-processing to reduce noise
        roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=self.min_object_size)
        small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        roi_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_OPEN, small_kernel)
        
        # Final processing (matched with parameter_visualization_ui.py)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=2)
        final_seg = morphology.remove_small_objects(final_seg.astype(bool), min_size=self.min_object_size)
        
        # Fill holes
        final_seg = morphology.remove_small_holes(final_seg)
        
        # Remove small areas
        final_seg = morphology.remove_small_objects(final_seg, min_size=100)
        
        # Clean up
        final_seg = morphology.thin(final_seg, max_num_iter=1)
        
        # Additional cleaning steps
        final_seg = morphology.remove_small_objects(final_seg, min_size=self.min_object_size)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        final_seg = cv2.morphologyEx(final_seg.astype(np.uint8), cv2.MORPH_OPEN, kernel)
        
        # Label connected components
        labeled_image = measure.label(final_seg)
        props = measure.regionprops(labeled_image)
        
        # First filtering step - create a mask based on eccentricity and area thresholds
        # This exactly matches the approach in parameter_visualization_ui.py
        mask = np.zeros_like(final_seg, dtype=bool)
        for prop in props:
            if ((prop.eccentricity < self.eccentricity_threshold and prop.area > self.area_threshold_small) or 
                (prop.area > self.area_threshold_large)):
                mask[labeled_image == prop.label] = True
        
        # Update final segmentation with the mask
        final_seg = mask
        
        # Apply watershed segmentation to separate touching cells if enabled
        if self.use_watershed:
            # First, get the original labeled image and region properties
            original_labeled = measure.label(final_seg)
            original_props = measure.regionprops(original_labeled)
            
            # Create a mask for large objects that need watershed segmentation
            large_objects_mask = np.zeros_like(final_seg, dtype=bool)
            for prop in original_props:
                if prop.area > self.watershed_min_area:
                    large_objects_mask[original_labeled == prop.label] = True
            
            # Create a mask for small objects that don't need watershed segmentation
            small_objects_mask = final_seg & ~large_objects_mask
            
            # Only apply watershed to large objects
            if np.any(large_objects_mask):
                # Distance transform on large objects only
                distance = ndi.distance_transform_edt(large_objects_mask)
                
                # Apply threshold to distance map to find markers
                # This helps identify separate cells even when they're touching
                distance_peaks = distance > self.watershed_distance_threshold
                
                # Clean up the peaks to get better markers
                distance_peaks = morphology.remove_small_objects(distance_peaks, min_size=2)
                
                # Label the peaks as markers
                markers = measure.label(distance_peaks)
                
                # Apply watershed segmentation to large objects only
                # Use the negative distance as the input for watershed
                watershed_labels = segmentation.watershed(-distance, markers, mask=large_objects_mask, 
                                                        compactness=self.watershed_compactness)
                
                # Combine the watershed segmentation of large objects with the small objects
                # First, get the maximum label from watershed_labels
                max_watershed_label = np.max(watershed_labels) if np.any(watershed_labels) else 0
                
                # Label the small objects starting from max_watershed_label + 1
                small_objects_labeled = measure.label(small_objects_mask)
                small_objects_labeled[small_objects_labeled > 0] += max_watershed_label
                
                # Combine the two labeled images
                combined_labels = watershed_labels.copy()
                combined_labels[small_objects_mask] = small_objects_labeled[small_objects_mask]
                
                # Final labeled image
                labeled_image = combined_labels
            else:
                # If no large objects, just use the original labeling
                labeled_image = original_labeled
        else:
            # Re-label after filtering without watershed
            labeled_image = measure.label(final_seg)
        
        # Get updated region properties after watershed segmentation
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
            
            # Second filtering step - check area, perimeter, circularity and aspect ratio
            if (self.area_min < area < self.area_max and 
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

def get_monitor_info():
    """Get information about available monitors
    
    Returns:
        list: List of monitor information dictionaries with keys:
            - left, top, right, bottom: Monitor boundaries
            - width, height: Monitor dimensions
            - is_primary: Boolean indicating if this is the primary monitor
    """
    monitors = []
    
    if HAS_WIN32API:
        try:
            # Get information for all monitors
            monitor_info = win32api.EnumDisplayMonitors()
            
            # Get detailed information for each monitor
            for i, monitor in enumerate(monitor_info):
                monitor_rect = win32api.GetMonitorInfo(monitor[0])
                work_area = monitor_rect['Work']
                monitor_area = monitor_rect['Monitor']
                is_primary = (monitor_rect['Flags'] == 1)  # Primary monitor has flag value 1
                
                monitors.append({
                    'left': monitor_area[0],
                    'top': monitor_area[1],
                    'right': monitor_area[2],
                    'bottom': monitor_area[3],
                    'width': monitor_area[2] - monitor_area[0],
                    'height': monitor_area[3] - monitor_area[1],
                    'work_left': work_area[0],
                    'work_top': work_area[1],
                    'work_right': work_area[2],
                    'work_bottom': work_area[3],
                    'work_width': work_area[2] - work_area[0],
                    'work_height': work_area[3] - work_area[1],
                    'is_primary': is_primary
                })
        except Exception as e:
            print(f"Error getting monitor information: {e}")
    
    # If no monitors detected or win32api not available, create a fallback entry
    if not monitors:
        # Get screen dimensions from tkinter as fallback
        temp_root = tk.Tk()
        screen_width = temp_root.winfo_screenwidth()
        screen_height = temp_root.winfo_screenheight()
        temp_root.destroy()
        
        monitors.append({
            'left': 0,
            'top': 0,
            'right': screen_width,
            'bottom': screen_height,
            'width': screen_width,
            'height': screen_height,
            'work_left': 0,
            'work_top': 0,
            'work_right': screen_width,
            'work_bottom': screen_height,
            'work_width': screen_width,
            'work_height': screen_height,
            'is_primary': True
        })
    
    return monitors

def main():
    # Get monitor information
    monitors = get_monitor_info()
    
    # Create the root window
    root = tk.Tk()
    
    # Position the window on the secondary monitor if available, otherwise on the primary
    if len(monitors) > 1:
        # Find the secondary monitor (first non-primary monitor)
        secondary_monitor = None
        for monitor in monitors:
            if not monitor['is_primary']:
                secondary_monitor = monitor
                break
        
        if secondary_monitor:
            print("Positioning application on secondary monitor")
            # Position the window on the secondary monitor
            x = secondary_monitor['work_left']
            y = secondary_monitor['work_top']
            root.geometry(f"+{x}+{y}")
    else:
        print("Only one monitor detected, using primary monitor")
    
    # Create and run the application
    app = MP4VideoLive(root)
    root.mainloop()

if __name__ == "__main__":
    main()
