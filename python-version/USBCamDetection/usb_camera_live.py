"""
USB Camera Live Stream - Main Application Class
This module contains the main USBCameraLive class that orchestrates the entire application.
"""

import sys
import os
import time
import threading
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from camera_manager import CameraManager
from cell_detector import CellDetector
from aoi_manager import AOIManager

class USBCameraLive:
    """Main application class for USB camera live stream with cell detection"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("USB Camera Live Stream")
        # Initialize in fullscreen mode
        self.root.attributes('-fullscreen', True)
        # Add key binding to exit fullscreen with Escape key
        self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())
        self.fullscreen = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize managers
        self.camera_manager = CameraManager(camera_index=0, target_fps=30)
        self.cell_detector = CellDetector()
        self.aoi_manager = None  # Will be initialized after canvas creation
        
        # UI update variables
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.render_running = False
        self.photo_image = None
        
        # Display variables
        self.display_width = 0
        self.display_height = 0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.last_frame_update_time = 0
        
        # Cell detection variables
        self.cell_detection_active = False
        self.cell_detection_thread = None
        self.cell_detection_interval = 0.05  # 20 FPS for cell detection
        self.last_detection_time = 0
        self.detected_cells = []
        
        # Debug window variables
        self.debug_window = None
        self.debug_canvas = None
        self.debug_photo = None
        self.show_debug = False
        
        # Create UI
        self.create_ui()
        
        # Initialize AOI manager after canvas is created
        self.aoi_manager = AOIManager(self.canvas)
        
        # Start camera
        self.start_camera()
        
        # Start rendering thread
        self.start_render_thread()
        
        # Make sure the window is visible
        self.root.update()
    
    def create_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for video display
        video_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Video canvas
        self.canvas = tk.Canvas(
            video_frame, 
            bg="#f0f0f0",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for AOI drawing
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # FPS counter
        self.fps_var = tk.StringVar(value="FPS: 0")
        fps_label = ttk.Label(video_frame, textvariable=self.fps_var, font=("Arial", 10))
        fps_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Starting camera...")
        status_label = ttk.Label(video_frame, textvariable=self.status_var, font=("Arial", 9))
        status_label.pack(side=tk.BOTTOM, anchor=tk.W, padx=5, pady=5)
        
        # Right panel for controls
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Create control panels
        self.create_title_panel(control_frame)
        self.create_camera_panel(control_frame)
        self.create_cell_detection_panel(control_frame)
        self.create_aoi_panel(control_frame)
        self.create_exit_panel(control_frame)
    
    def create_title_panel(self, parent):
        """Create title panel"""
        title_label = ttk.Label(parent, text="USB Camera Live Stream", font=("Arial", 12, "bold"))
        title_label.pack(pady=10)
    
    def create_camera_panel(self, parent):
        """Create camera settings panel"""
        camera_frame = ttk.LabelFrame(parent, text="Camera Settings")
        camera_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Camera Index selection
        ttk.Label(camera_frame, text="Camera Index:").pack(anchor=tk.W, padx=5, pady=(5,0))
        camera_index_frame = ttk.Frame(camera_frame)
        camera_index_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.camera_index_var = tk.IntVar(value=0)
        camera_index_spinbox = ttk.Spinbox(
            camera_index_frame,
            from_=0,
            to=10,
            textvariable=self.camera_index_var,
            width=10,
            state="readonly"
        )
        camera_index_spinbox.pack(side=tk.LEFT, padx=(0,5))
        
        # Reconnect button
        reconnect_button = ttk.Button(
            camera_index_frame,
            text="Reconnect",
            command=self.reconnect_camera
        )
        reconnect_button.pack(side=tk.LEFT)
        
        # Camera info display
        self.camera_info_var = tk.StringVar(value="Resolution: Not connected")
        ttk.Label(camera_frame, textvariable=self.camera_info_var).pack(anchor=tk.W, padx=5, pady=5)
    
    def create_cell_detection_panel(self, parent):
        """Create cell detection control panel"""
        cell_frame = ttk.LabelFrame(parent, text="Cell Detection")
        cell_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start/Stop buttons
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
        
        # Debug window button
        self.debug_button = ttk.Button(
            cell_frame,
            text="Show Debug Window",
            command=self.toggle_debug_window
        )
        self.debug_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Parameter controls
        param_notebook = ttk.Notebook(cell_frame)
        param_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CLAHE parameters tab
        self.create_clahe_tab(param_notebook)
        
        # Area parameters tab
        self.create_area_tab(param_notebook)
        
        # Perimeter parameters tab
        self.create_perimeter_tab(param_notebook)
        
        # Shape parameters tab
        self.create_shape_tab(param_notebook)
        
        # Edge detection parameters tab
        self.create_edge_tab(param_notebook)
        
        # Watershed parameters tab
        self.create_watershed_tab(param_notebook)
    
    def create_clahe_tab(self, notebook):
        """Create CLAHE parameters tab"""
        clahe_frame = ttk.Frame(notebook)
        notebook.add(clahe_frame, text="CLAHE")
        
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
    
    def create_area_tab(self, notebook):
        """Create area parameters tab"""
        area_frame = ttk.Frame(notebook)
        notebook.add(area_frame, text="Area")
        
        # Area Min
        ttk.Label(area_frame, text="Min Area:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.area_min_var = tk.IntVar(value=50)
        area_min_scale = ttk.Scale(
            area_frame,
            from_=10,
            to=200,
            orient=tk.HORIZONTAL,
            variable=self.area_min_var,
            command=self.update_area_min
        )
        area_min_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.area_min_value_label = ttk.Label(area_frame, text="50")
        self.area_min_value_label.pack(anchor=tk.E, padx=5)
        
        # Area Max
        ttk.Label(area_frame, text="Max Area:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.area_max_var = tk.IntVar(value=300)
        area_max_scale = ttk.Scale(
            area_frame,
            from_=100,
            to=1000,
            orient=tk.HORIZONTAL,
            variable=self.area_max_var,
            command=self.update_area_max
        )
        area_max_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.area_max_value_label = ttk.Label(area_frame, text="300")
        self.area_max_value_label.pack(anchor=tk.E, padx=5)
    
    def create_perimeter_tab(self, notebook):
        """Create perimeter parameters tab"""
        perimeter_frame = ttk.Frame(notebook)
        notebook.add(perimeter_frame, text="Perimeter")
        
        # Min Perimeter
        ttk.Label(perimeter_frame, text="Min Perimeter:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.min_perimeter_var = tk.IntVar(value=100)
        min_perimeter_scale = ttk.Scale(
            perimeter_frame,
            from_=10,
            to=500,
            orient=tk.HORIZONTAL,
            variable=self.min_perimeter_var,
            command=self.update_min_perimeter
        )
        min_perimeter_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.min_perimeter_value_label = ttk.Label(perimeter_frame, text="100")
        self.min_perimeter_value_label.pack(anchor=tk.E, padx=5)
        
        # Max Perimeter
        ttk.Label(perimeter_frame, text="Max Perimeter:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.max_perimeter_var = tk.IntVar(value=300)
        max_perimeter_scale = ttk.Scale(
            perimeter_frame,
            from_=100,
            to=1000,
            orient=tk.HORIZONTAL,
            variable=self.max_perimeter_var,
            command=self.update_max_perimeter
        )
        max_perimeter_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.max_perimeter_value_label = ttk.Label(perimeter_frame, text="300")
        self.max_perimeter_value_label.pack(anchor=tk.E, padx=5)
    
    def create_shape_tab(self, notebook):
        """Create shape parameters tab"""
        shape_frame = ttk.Frame(notebook)
        notebook.add(shape_frame, text="Shape")
        
        # Min Circularity
        ttk.Label(shape_frame, text="Min Circularity:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.min_circularity_var = tk.DoubleVar(value=0.8)
        min_circularity_scale = ttk.Scale(
            shape_frame,
            from_=0.1,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.min_circularity_var,
            command=self.update_min_circularity
        )
        min_circularity_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.min_circularity_value_label = ttk.Label(shape_frame, text="0.8")
        self.min_circularity_value_label.pack(anchor=tk.E, padx=5)
        
        # Max Circularity
        ttk.Label(shape_frame, text="Max Circularity:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.max_circularity_var = tk.DoubleVar(value=12.0)
        max_circularity_scale = ttk.Scale(
            shape_frame,
            from_=1.0,
            to=20.0,
            orient=tk.HORIZONTAL,
            variable=self.max_circularity_var,
            command=self.update_max_circularity
        )
        max_circularity_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.max_circularity_value_label = ttk.Label(shape_frame, text="12.0")
        self.max_circularity_value_label.pack(anchor=tk.E, padx=5)
        
        # Eccentricity Threshold
        ttk.Label(shape_frame, text="Eccentricity Threshold:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.eccentricity_var = tk.DoubleVar(value=0.98)
        eccentricity_scale = ttk.Scale(
            shape_frame,
            from_=0.5,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.eccentricity_var,
            command=self.update_eccentricity
        )
        eccentricity_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.eccentricity_value_label = ttk.Label(shape_frame, text="0.98")
        self.eccentricity_value_label.pack(anchor=tk.E, padx=5)
        
        # Aspect Ratio Threshold
        ttk.Label(shape_frame, text="Aspect Ratio Threshold:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.aspect_ratio_var = tk.DoubleVar(value=1.5)
        aspect_ratio_scale = ttk.Scale(
            shape_frame,
            from_=1.0,
            to=3.0,
            orient=tk.HORIZONTAL,
            variable=self.aspect_ratio_var,
            command=self.update_aspect_ratio
        )
        aspect_ratio_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.aspect_ratio_value_label = ttk.Label(shape_frame, text="1.5")
        self.aspect_ratio_value_label.pack(anchor=tk.E, padx=5)
    
    def create_edge_tab(self, notebook):
        """Create edge detection parameters tab"""
        edge_frame = ttk.Frame(notebook)
        notebook.add(edge_frame, text="Edge")
        
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
        
        # Min Object Size
        ttk.Label(edge_frame, text="Min Object Size:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.min_object_size_var = tk.IntVar(value=15)
        min_object_size_scale = ttk.Scale(
            edge_frame,
            from_=5,
            to=50,
            orient=tk.HORIZONTAL,
            variable=self.min_object_size_var,
            command=self.update_min_object_size
        )
        min_object_size_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.min_object_size_value_label = ttk.Label(edge_frame, text="15")
        self.min_object_size_value_label.pack(anchor=tk.E, padx=5)
    
    def create_watershed_tab(self, notebook):
        """Create watershed parameters tab"""
        watershed_frame = ttk.Frame(notebook)
        notebook.add(watershed_frame, text="Watershed")
        
        # Use Watershed checkbox
        self.use_watershed_var = tk.BooleanVar(value=True)
        use_watershed_check = ttk.Checkbutton(
            watershed_frame,
            text="Enable Watershed Segmentation",
            variable=self.use_watershed_var,
            command=self.update_use_watershed
        )
        use_watershed_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # Distance Threshold
        ttk.Label(watershed_frame, text="Distance Threshold:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.watershed_distance_var = tk.IntVar(value=10)
        watershed_distance_scale = ttk.Scale(
            watershed_frame,
            from_=5,
            to=30,
            orient=tk.HORIZONTAL,
            variable=self.watershed_distance_var,
            command=self.update_watershed_distance
        )
        watershed_distance_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.watershed_distance_value_label = ttk.Label(watershed_frame, text="10")
        self.watershed_distance_value_label.pack(anchor=tk.E, padx=5)
        
        # Footprint Size
        ttk.Label(watershed_frame, text="Footprint Size:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.watershed_footprint_var = tk.IntVar(value=3)
        watershed_footprint_scale = ttk.Scale(
            watershed_frame,
            from_=2,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.watershed_footprint_var,
            command=self.update_watershed_footprint
        )
        watershed_footprint_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.watershed_footprint_value_label = ttk.Label(watershed_frame, text="3")
        self.watershed_footprint_value_label.pack(anchor=tk.E, padx=5)
        
        # Compactness
        ttk.Label(watershed_frame, text="Compactness:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.watershed_compactness_var = tk.DoubleVar(value=0.5)
        watershed_compactness_scale = ttk.Scale(
            watershed_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.watershed_compactness_var,
            command=self.update_watershed_compactness
        )
        watershed_compactness_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.watershed_compactness_value_label = ttk.Label(watershed_frame, text="0.5")
        self.watershed_compactness_value_label.pack(anchor=tk.E, padx=5)
        
        # Min Area for Watershed
        ttk.Label(watershed_frame, text="Min Area for Watershed:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.watershed_min_area_var = tk.IntVar(value=500)
        watershed_min_area_scale = ttk.Scale(
            watershed_frame,
            from_=200,
            to=1000,
            orient=tk.HORIZONTAL,
            variable=self.watershed_min_area_var,
            command=self.update_watershed_min_area
        )
        watershed_min_area_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.watershed_min_area_value_label = ttk.Label(watershed_frame, text="500")
        self.watershed_min_area_value_label.pack(anchor=tk.E, padx=5)
        
        # Area Threshold Small
        ttk.Label(watershed_frame, text="Area Threshold Small:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.area_threshold_small_var = tk.IntVar(value=200)
        area_threshold_small_scale = ttk.Scale(
            watershed_frame,
            from_=50,
            to=500,
            orient=tk.HORIZONTAL,
            variable=self.area_threshold_small_var,
            command=self.update_area_threshold_small
        )
        area_threshold_small_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.area_threshold_small_value_label = ttk.Label(watershed_frame, text="200")
        self.area_threshold_small_value_label.pack(anchor=tk.E, padx=5)
        
        # Area Threshold Large
        ttk.Label(watershed_frame, text="Area Threshold Large:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.area_threshold_large_var = tk.IntVar(value=400)
        area_threshold_large_scale = ttk.Scale(
            watershed_frame,
            from_=200,
            to=800,
            orient=tk.HORIZONTAL,
            variable=self.area_threshold_large_var,
            command=self.update_area_threshold_large
        )
        area_threshold_large_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        self.area_threshold_large_value_label = ttk.Label(watershed_frame, text="400")
        self.area_threshold_large_value_label.pack(anchor=tk.E, padx=5)
    
    def create_aoi_panel(self, parent):
        """Create AOI control panel"""
        aoi_frame = ttk.LabelFrame(parent, text="Area of Interest")
        aoi_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Draw AOI checkbox
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
    
    def create_exit_panel(self, parent):
        """Create exit button panel"""
        exit_button = ttk.Button(
            parent,
            text="Exit",
            command=self.on_closing,
            style="Exit.TButton"
        )
        exit_button.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Configure exit button style
        style = ttk.Style()
        style.configure("Exit.TButton", foreground="red", font=("Arial", 9, "bold"))
    
    def start_camera(self):
        """Start the camera"""
        success, message = self.camera_manager.start_camera()
        if success:
            self.camera_info_var.set(self.camera_manager.get_camera_info())
            self.status_var.set(message)
        else:
            self.status_var.set(message)
            messagebox.showerror("Camera Error", message)
    
    def reconnect_camera(self):
        """Reconnect to camera with selected index"""
        new_index = self.camera_index_var.get()
        self.status_var.set(f"Reconnecting to camera {new_index}...")
        
        success, message = self.camera_manager.reconnect_camera(new_index)
        if success:
            self.camera_info_var.set(self.camera_manager.get_camera_info())
            self.status_var.set(message)
        else:
            self.status_var.set(message)
            messagebox.showerror("Camera Error", message)
    
    def start_render_thread(self):
        """Start the rendering thread"""
        if not self.render_running:
            self.render_running = True
            self.render_thread = threading.Thread(target=self.render_loop, daemon=True)
            self.render_thread.start()
    
    def render_loop(self):
        """Main rendering loop that runs in a separate thread"""
        while self.render_running:
            try:
                # Update frame if new frame is available
                success, frame = self.camera_manager.get_frame()
                if success and frame is not None:
                    # Use root.after to schedule UI update on main thread
                    self.root.after(0, lambda f=frame: self.update_frame(f))
                
                # Calculate FPS
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.camera_manager.frame_count / (current_time - self.last_fps_time)
                    self.root.after(0, lambda: self.fps_var.set(f"FPS: {self.fps:.1f}"))
                    self.camera_manager.frame_count = 0
                    self.last_fps_time = current_time
                
                # Sleep to control update rate - reduced frequency to prevent flashing
                time.sleep(1.0 / 30.0)  # 30 FPS UI update rate
                
            except Exception as e:
                print(f"Error in render loop: {e}")
                time.sleep(0.1)
    
    def update_frame(self, frame):
        """Update the UI with the latest frame"""
        # Limit frame updates to prevent flashing (max 30 FPS)
        current_time = time.time()
        if current_time - self.last_frame_update_time < 1.0 / 30.0:
            return
        self.last_frame_update_time = current_time
        
        try:
            # Get the current canvas size
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                frame_height, frame_width = frame.shape[:2]
                
                # Calculate the display size while maintaining aspect ratio
                camera_aspect_ratio = frame_width / frame_height
                canvas_aspect_ratio = canvas_width / canvas_height
                
                if canvas_aspect_ratio > camera_aspect_ratio:
                    self.display_height = canvas_height
                    self.display_width = int(canvas_height * camera_aspect_ratio)
                    self.display_offset_x = (canvas_width - self.display_width) // 2
                    self.display_offset_y = 0
                else:
                    self.display_width = canvas_width
                    self.display_height = int(canvas_width / camera_aspect_ratio)
                    self.display_offset_x = 0
                    self.display_offset_y = (canvas_height - self.display_height) // 2
                
                # Update AOI manager with display properties
                if self.aoi_manager:
                    self.aoi_manager.set_display_properties(
                        self.display_width, self.display_height,
                        self.display_offset_x, self.display_offset_y,
                        frame_width, frame_height
                    )
                
                # Resize frame for display
                display_frame = cv2.resize(frame, (self.display_width, self.display_height))
                
                # Apply AOI overlay if active
                if self.aoi_manager and self.aoi_manager.has_aoi():
                    display_frame = self.aoi_manager.apply_aoi_overlay(display_frame)
                
                # Draw detected cells if cell detection is active
                if self.cell_detection_active and self.detected_cells:
                    print(f"Drawing {len(self.detected_cells)} detected cells")  # Debug info
                    display_frame = self.draw_detected_cells(display_frame, frame_width, frame_height)
                elif self.cell_detection_active:
                    print("Cell detection active but no cells detected")  # Debug info
                
                # Convert to RGB for display
                display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image and then to PhotoImage
                pil_image = Image.fromarray(display_frame_rgb)
                self.photo_image = ImageTk.PhotoImage(pil_image)
                
                # Update canvas
                if not self.canvas.find_withtag("video"):
                    self.canvas.create_image(
                        self.display_offset_x, self.display_offset_y,
                        anchor=tk.NW,
                        image=self.photo_image,
                        tags=("video",)
                    )
                else:
                    self.canvas.itemconfig("video", image=self.photo_image)
                    self.canvas.coords("video", self.display_offset_x, self.display_offset_y)
                
        except Exception as e:
            print(f"Error updating frame: {e}")
    
    def draw_detected_cells(self, display_frame, original_width, original_height):
        """Draw detected cells on the display frame"""
        try:
            # Scale factor from original image to display image
            scale_x = self.display_width / original_width
            scale_y = self.display_height / original_height
            
            for cell in self.detected_cells:
                # Get cell properties
                centroid = cell['centroid']
                bbox = cell['bbox']
                area = cell['area']
                
                # Scale coordinates to display size
                centroid_x = int(centroid[0] * scale_x)
                centroid_y = int(centroid[1] * scale_y)
                
                bbox_x1 = int(bbox[0] * scale_x)
                bbox_y1 = int(bbox[1] * scale_y)
                bbox_x2 = int(bbox[2] * scale_x)
                bbox_y2 = int(bbox[3] * scale_y)
                
                # Draw centroid (green circle)
                cv2.circle(display_frame, (centroid_x, centroid_y), 3, (0, 255, 0), -1)
                
                # Draw bounding box (blue rectangle)
                cv2.rectangle(display_frame, (bbox_x1, bbox_y1), (bbox_x2, bbox_y2), (255, 0, 0), 2)
                
                # Draw area text (white text with black outline)
                text = f"A:{int(area)}"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
                text_x = centroid_x - text_size[0] // 2
                text_y = centroid_y - 10
                
                # Draw text background (black)
                cv2.rectangle(display_frame, 
                            (text_x - 2, text_y - text_size[1] - 2), 
                            (text_x + text_size[0] + 2, text_y + 2), 
                            (0, 0, 0), -1)
                
                # Draw text (white)
                cv2.putText(display_frame, text, (text_x, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            return display_frame
            
        except Exception as e:
            print(f"Error drawing detected cells: {e}")
            return display_frame
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        if not self.fullscreen:
            self.root.geometry("1200x800")
    
    # Parameter update methods
    def update_clahe_clip(self, value):
        """Update CLAHE clip limit parameter"""
        self.cell_detector.clahe_clip_limit = float(value)
        self.clahe_clip_value_label.config(text=f"{float(value):.1f}")
    
    def update_clahe_tile(self, value):
        """Update CLAHE tile size parameter"""
        self.cell_detector.clahe_tile_size = int(float(value))
        self.clahe_tile_value_label.config(text=str(int(float(value))))
    
    def update_area_min(self, value):
        """Update minimum area parameter"""
        self.cell_detector.area_min = int(float(value))
        self.cell_detector.min_area = int(float(value))
        self.area_min_value_label.config(text=str(int(float(value))))
    
    def update_area_max(self, value):
        """Update maximum area parameter"""
        self.cell_detector.area_max = int(float(value))
        self.cell_detector.max_area = int(float(value))
        self.area_max_value_label.config(text=str(int(float(value))))
    
    def update_min_perimeter(self, value):
        """Update minimum perimeter parameter"""
        self.cell_detector.min_perimeter = int(float(value))
        self.min_perimeter_value_label.config(text=str(int(float(value))))
    
    def update_max_perimeter(self, value):
        """Update maximum perimeter parameter"""
        self.cell_detector.max_perimeter = int(float(value))
        self.max_perimeter_value_label.config(text=str(int(float(value))))
    
    def update_min_circularity(self, value):
        """Update minimum circularity parameter"""
        self.cell_detector.min_circularity = float(value)
        self.min_circularity_value_label.config(text=f"{float(value):.2f}")
    
    def update_max_circularity(self, value):
        """Update maximum circularity parameter"""
        self.cell_detector.max_circularity = float(value)
        self.max_circularity_value_label.config(text=f"{float(value):.1f}")
    
    def update_eccentricity(self, value):
        """Update eccentricity threshold parameter"""
        self.cell_detector.eccentricity_threshold = float(value)
        self.eccentricity_value_label.config(text=f"{float(value):.2f}")
    
    def update_aspect_ratio(self, value):
        """Update aspect ratio threshold parameter"""
        self.cell_detector.aspect_ratio_threshold = float(value)
        self.aspect_ratio_value_label.config(text=f"{float(value):.1f}")
    
    def update_canny_low(self, value):
        """Update Canny low threshold parameter"""
        self.cell_detector.canny_low = int(float(value))
        self.canny_low_value_label.config(text=str(int(float(value))))
    
    def update_canny_high(self, value):
        """Update Canny high threshold parameter"""
        self.cell_detector.canny_high = int(float(value))
        self.canny_high_value_label.config(text=str(int(float(value))))
    
    def update_edge_threshold(self, value):
        """Update edge threshold parameter"""
        self.cell_detector.edge_threshold = int(float(value))
        self.edge_threshold_value_label.config(text=str(int(float(value))))
    
    def update_min_object_size(self, value):
        """Update minimum object size parameter"""
        self.cell_detector.min_object_size = int(float(value))
        self.min_object_size_value_label.config(text=str(int(float(value))))
    
    def update_use_watershed(self):
        """Update use watershed parameter"""
        self.cell_detector.use_watershed = self.use_watershed_var.get()
    
    def update_watershed_distance(self, value):
        """Update watershed distance threshold parameter"""
        self.cell_detector.watershed_distance_threshold = int(float(value))
        self.watershed_distance_value_label.config(text=str(int(float(value))))
    
    def update_watershed_footprint(self, value):
        """Update watershed footprint size parameter"""
        self.cell_detector.watershed_footprint_size = int(float(value))
        self.watershed_footprint_value_label.config(text=str(int(float(value))))
    
    def update_watershed_compactness(self, value):
        """Update watershed compactness parameter"""
        self.cell_detector.watershed_compactness = float(value)
        self.watershed_compactness_value_label.config(text=f"{float(value):.2f}")
    
    def update_watershed_min_area(self, value):
        """Update watershed minimum area parameter"""
        self.cell_detector.watershed_min_area = int(float(value))
        self.watershed_min_area_value_label.config(text=str(int(float(value))))
    
    def update_area_threshold_small(self, value):
        """Update area threshold small parameter"""
        self.cell_detector.area_threshold_small = int(float(value))
        self.area_threshold_small_value_label.config(text=str(int(float(value))))
    
    def update_area_threshold_large(self, value):
        """Update area threshold large parameter"""
        self.cell_detector.area_threshold_large = int(float(value))
        self.area_threshold_large_value_label.config(text=str(int(float(value))))
    
    # Cell detection methods
    def start_cell_detection(self):
        """Start cell detection in a separate thread"""
        if not self.cell_detection_active:
            self.cell_detection_active = True
            self.start_detection_button.config(state=tk.DISABLED)
            self.stop_detection_button.config(state=tk.NORMAL)
            
            self.cell_detection_thread = threading.Thread(target=self.cell_detection_loop, daemon=True)
            self.cell_detection_thread.start()
            
            self.status_var.set("Cell detection started")
    
    def stop_cell_detection(self):
        """Stop cell detection"""
        self.cell_detection_active = False
        self.start_detection_button.config(state=tk.NORMAL)
        self.stop_detection_button.config(state=tk.DISABLED)
        self.status_var.set("Cell detection stopped")
    
    def cell_detection_loop(self):
        """Cell detection loop that runs in a separate thread"""
        while self.cell_detection_active:
            try:
                current_time = time.time()
                if current_time - self.last_detection_time >= self.cell_detection_interval:
                    success, frame = self.camera_manager.get_frame()
                    if success and frame is not None:
                        # Get AOI coordinates for detection
                        aoi_coords = None
                        if self.aoi_manager:
                            aoi_coords = self.aoi_manager.get_aoi_coords()
                        
                        # Detect cells with debug information if debug window is open
                        if self.show_debug:
                            self.detected_cells, debug_image = self.cell_detector.detect_cells(frame, aoi_coords, return_debug=True)
                            # Update debug window with binary segmentation result
                            if debug_image is not None:
                                self.root.after(0, lambda: self.update_debug_window(debug_image))
                        else:
                            self.detected_cells = self.cell_detector.detect_cells(frame, aoi_coords)
                        
                        # Update cell count
                        cell_count = len(self.detected_cells)
                        self.cell_count_var.set(f"Cells: {cell_count}")
                        
                        # Debug info
                        if cell_count > 0:
                            print(f"Detected {cell_count} cells - First cell area: {self.detected_cells[0]['area']:.1f}")
                        else:
                            print("No cells detected - check detection parameters")
                        
                        self.last_detection_time = current_time
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in cell detection loop: {e}")
                time.sleep(0.1)
    
    # AOI methods
    def toggle_aoi_drawing(self):
        """Toggle AOI drawing mode"""
        if self.aoi_manager:
            self.aoi_manager.set_active(self.draw_aoi_var.get())
            if self.draw_aoi_var.get():
                self.status_var.set("Click and drag to draw Area of Interest")
            else:
                self.status_var.set("AOI drawing disabled")
    
    def clear_aoi(self):
        """Clear the AOI"""
        if self.aoi_manager:
            message = self.aoi_manager.clear_aoi()
            self.status_var.set(message)
    
    def update_aoi_overlay(self, value=None):
        """Update AOI overlay opacity"""
        if self.aoi_manager:
            self.aoi_manager.set_opacity(self.opacity_var.get())
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        if self.aoi_manager:
            message = self.aoi_manager.on_canvas_click(event)
            if message:
                self.status_var.set(message)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag events"""
        if self.aoi_manager:
            message = self.aoi_manager.on_canvas_drag(event)
            if message:
                self.status_var.set(message)
    
    def on_canvas_release(self, event):
        """Handle canvas release events"""
        if self.aoi_manager:
            message = self.aoi_manager.on_canvas_release(event)
            if message:
                self.status_var.set(message)
    
    def toggle_debug_window(self):
        """Toggle the debug window for showing intermediate processing steps"""
        if self.debug_window is None or not self.debug_window.winfo_exists():
            self.create_debug_window()
            self.show_debug = True
            self.debug_button.config(text="Hide Debug Window")
        else:
            self.debug_window.destroy()
            self.debug_window = None
            self.show_debug = False
            self.debug_button.config(text="Show Debug Window")
    
    def create_debug_window(self):
        """Create a debug window to show intermediate processing steps"""
        self.debug_window = tk.Toplevel(self.root)
        self.debug_window.title("Cell Detection Debug - Binary Segmentation")
        self.debug_window.geometry("600x500")
        
        # Create canvas for debug image
        self.debug_canvas = tk.Canvas(self.debug_window, bg="black")
        self.debug_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add label
        info_label = ttk.Label(
            self.debug_window, 
            text="Binary Segmentation Result (White = Detected Objects)",
            font=("Arial", 10, "bold")
        )
        info_label.pack(pady=5)
        
        # Handle window closing
        self.debug_window.protocol("WM_DELETE_WINDOW", self.close_debug_window)
    
    def close_debug_window(self):
        """Close the debug window"""
        self.show_debug = False
        self.debug_button.config(text="Show Debug Window")
        if self.debug_window:
            self.debug_window.destroy()
            self.debug_window = None
    
    def update_debug_window(self, debug_image):
        """Update the debug window with the latest processing result"""
        if not self.show_debug or self.debug_window is None or not self.debug_window.winfo_exists():
            return
        
        try:
            # Resize debug image to fit window
            canvas_width = self.debug_canvas.winfo_width()
            canvas_height = self.debug_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calculate display size maintaining aspect ratio
                img_height, img_width = debug_image.shape[:2]
                aspect_ratio = img_width / img_height
                canvas_aspect = canvas_width / canvas_height
                
                if canvas_aspect > aspect_ratio:
                    display_height = canvas_height - 20
                    display_width = int(display_height * aspect_ratio)
                else:
                    display_width = canvas_width - 20
                    display_height = int(display_width / aspect_ratio)
                
                # Resize and convert to displayable format
                resized_debug = cv2.resize(debug_image, (display_width, display_height))
                
                # Convert binary image to RGB for display
                if len(resized_debug.shape) == 2:
                    debug_rgb = cv2.cvtColor(resized_debug, cv2.COLOR_GRAY2RGB)
                else:
                    debug_rgb = resized_debug
                
                # Convert to PIL and display
                pil_debug = Image.fromarray(debug_rgb)
                self.debug_photo = ImageTk.PhotoImage(pil_debug)
                
                # Clear canvas and display image
                self.debug_canvas.delete("all")
                offset_x = (canvas_width - display_width) // 2
                offset_y = (canvas_height - display_height) // 2
                
                self.debug_canvas.create_image(
                    offset_x, offset_y,
                    anchor=tk.NW,
                    image=self.debug_photo
                )
                
        except Exception as e:
            print(f"Error updating debug window: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        self.render_running = False
        self.cell_detection_active = False
        
        if self.debug_window:
            self.debug_window.destroy()
        
        if self.camera_manager:
            self.camera_manager.stop_camera()
        
        self.root.destroy()
