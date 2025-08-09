"""
GPU-accelerated ToupCam Live Stream Application
This module provides the main application class with GPU-accelerated cell detection.
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import json
import cv2
import numpy as np

from toupcam_camera_manager import ToupCamCameraManager
from cell_detector_gpu import CellDetectorGPU  # Use GPU version
from aoi_manager import AOIManager
from adaptive_cell_tracker import AdaptiveCellTracker
from exposure_control_panel import ExposureControlPanel

class ToupCameraLiveGPU:
    """Main application class for GPU-accelerated ToupCam live stream with cell detection"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ToupCam Live Stream - GPU Accelerated")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize components
        self.camera_manager = ToupCamCameraManager(camera_index=0, target_fps=30)
        self.cell_detector = CellDetectorGPU()  # Use GPU version
        self.cell_tracker = AdaptiveCellTracker(
            max_disappeared=0,  # Reduced from 15 to 5 frames for faster cleanup
            base_search_radius=50,
            min_track_length=3
        )
        # AOI manager will be initialized after UI setup
        
        # Initialize variables
        self.running = False
        self.current_fps = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.detection_enabled = False
        self.show_aoi = False
        self.fullscreen = False  # For main window fullscreen mode
        self.debug_window_open = False
        self.debug_window = None
        self.fullscreen_canvas = None
        self.fullscreen_canvas_open = False
        
        # Tracking state
        self.tracking_enabled = True
        self.show_trajectories = False
        self.tracked_cells = {}
        self.show_predictions = False
        
        # Display settings - Will be set dynamically based on canvas size
        self.display_width = 800  # Initial fallback value
        self.display_height = 600  # Initial fallback value
        
        # Threading
        self.capture_thread = None
        self.detection_thread = None
        self.render_thread = None
        
        # Frame buffers
        self.current_frame = None
        self.display_frame = None
        self.frame_lock = threading.Lock()
        
        # Performance monitoring
        self.current_fps = 0
        
        # GPU status
        self.gpu_status = "GPU: " + ("Available" if self.cell_detector.gpu_available else "Not Available")
        
        # Exposure control panel
        self.exposure_control_panel = None
        
        # Setup UI
        self.setup_ui()
        
        # Initialize AOI manager with video canvas
        self.aoi_manager = AOIManager(self.video_canvas)
        
        # Start fullscreen
        self.toggle_fullscreen()
        
        # Start camera
        self.start_camera()
        
        # Initialize exposure control panel after camera is started
        self.exposure_control_panel = ExposureControlPanel(self.camera_manager, self.root)
    
    def update_display_dimensions(self):
        """Update display dimensions based on actual canvas size"""
        try:
            # Force canvas to update its geometry
            self.video_canvas.update_idletasks()
            
            # Get actual canvas dimensions
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            # Only update if we got valid dimensions
            if canvas_width > 1 and canvas_height > 1:
                self.display_width = canvas_width
                self.display_height = canvas_height
                print(f"Updated display dimensions to: {self.display_width}x{self.display_height}")
            else:
                # Retry after a short delay if dimensions aren't ready
                self.root.after(100, self.update_display_dimensions)
                
        except Exception as e:
            print(f"Error updating display dimensions: {e}")
            # Use fallback dimensions
            self.display_width = 800
            self.display_height = 600
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg='black')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video display using Canvas for AOI drawing support
        self.video_canvas = tk.Canvas(self.main_frame, bg='black', highlightthickness=0)
        self.video_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Control panel
        self.control_panel = tk.Frame(self.main_frame, bg='gray20', width=300)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.control_panel.pack_propagate(False)
        
        self.setup_control_panel()
        
        # Bind events
        self.video_canvas.bind("<Button-1>", self.on_video_click)
        self.video_canvas.bind("<B1-Motion>", self.on_video_drag)
        self.video_canvas.bind("<ButtonRelease-1>", self.on_video_release)
        self.root.bind("<KeyPress-Escape>", self.toggle_fullscreen)
        self.root.bind("<KeyPress-c>", self.clear_aoi_keyboard)  # 'C' key to clear AOI
        self.root.bind("<KeyPress-r>", self.reset_aoi_keyboard)  # 'R' key to reset AOI
        self.root.focus_set()
        
        # Update display dimensions after UI is set up
        self.root.after(100, self.update_display_dimensions)
    
    def setup_control_panel(self):
        """Setup the control panel with GPU status"""
        # Title
        title_label = tk.Label(self.control_panel, text="Cell Detection Control", 
                              bg='gray20', fg='white', font=('Arial', 12, 'bold'))
        title_label.pack(pady=10)
        
        # GPU Status
        gpu_label = tk.Label(self.control_panel, text=self.gpu_status, 
                            bg='gray20', fg='lime' if self.cell_detector.gpu_available else 'orange', 
                            font=('Arial', 10))
        gpu_label.pack(pady=5)
        
        # Camera Settings
        camera_frame = tk.LabelFrame(self.control_panel, text="Camera Settings", 
                                   bg='gray20', fg='white')
        camera_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Camera index
        tk.Label(camera_frame, text="Camera Index:", bg='gray20', fg='white').pack()
        self.camera_var = tk.IntVar(value=0)
        camera_spin = tk.Spinbox(camera_frame, from_=0, to=10, textvariable=self.camera_var, 
                               width=10)
        camera_spin.pack(pady=2)
        
        # Reconnect button
        reconnect_btn = tk.Button(camera_frame, text="Reconnect Camera", 
                                command=self.reconnect_camera)
        reconnect_btn.pack(pady=5)
        
        # Exposure control button
        exposure_btn = tk.Button(camera_frame, text="Exposure Control", 
                           command=self.open_exposure_control,
                           bg='blue', fg='white')
        exposure_btn.pack(pady=5)
        
        # Detection Controls
        detection_frame = tk.LabelFrame(self.control_panel, text="Detection Controls", 
                                      bg='gray20', fg='white')
        detection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Detection toggle
        self.detection_var = tk.BooleanVar()
        detection_check = tk.Checkbutton(detection_frame, text="Enable Detection", 
                                       variable=self.detection_var,
                                       command=self.toggle_detection,
                                       bg='gray20', fg='white', selectcolor='gray30')
        detection_check.pack(pady=2)
        
        # AOI controls
        aoi_frame = tk.Frame(detection_frame, bg='gray20')
        aoi_frame.pack(fill=tk.X, pady=2)
        
        # AOI toggle
        self.aoi_var = tk.BooleanVar()
        aoi_check = tk.Checkbutton(aoi_frame, text="Draw AOI", 
                                 variable=self.aoi_var,
                                 command=self.toggle_aoi,
                                 bg='gray20', fg='white', selectcolor='gray30')
        aoi_check.pack(side=tk.LEFT)
        
        # AOI clear button
        aoi_clear_btn = tk.Button(aoi_frame, text="Clear AOI", 
                                command=self.clear_aoi,
                                bg='orange', fg='white', font=('Arial', 8))
        aoi_clear_btn.pack(side=tk.RIGHT, padx=(5,0))
        
        # Debug window button
        debug_btn = tk.Button(detection_frame, text="Debug Window", 
                            command=self.toggle_debug_window)
        debug_btn.pack(pady=5)
        
        # Tracking Controls
        tracking_frame = tk.LabelFrame(self.control_panel, text="Tracking Controls", 
                                     bg='gray20', fg='white')
        tracking_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Tracking toggle
        self.tracking_var = tk.BooleanVar(value=True)
        tracking_check = tk.Checkbutton(tracking_frame, text="Enable Tracking", 
                                       variable=self.tracking_var,
                                       command=self.toggle_tracking,
                                       bg='gray20', fg='white', selectcolor='gray30')
        tracking_check.pack(pady=2)
        
        # Trajectory toggle
        self.trajectory_var = tk.BooleanVar()
        trajectory_check = tk.Checkbutton(tracking_frame, text="Show Trajectories", 
                                         variable=self.trajectory_var,
                                         command=self.toggle_trajectories,
                                         bg='gray20', fg='white', selectcolor='gray30')
        trajectory_check.pack(pady=2)
        
        # Predictions toggle
        self.predictions_var = tk.BooleanVar()
        predictions_check = tk.Checkbutton(tracking_frame, text="Show Predictions", 
                                          variable=self.predictions_var,
                                          command=self.toggle_predictions,
                                          bg='gray20', fg='white', selectcolor='gray30')
        predictions_check.pack(pady=2)
        
        # Tracking statistics label
        self.tracking_stats_label = tk.Label(tracking_frame, text="Tracking Stats: Ready", 
                                            bg='gray20', fg='cyan', font=('Arial', 9))
        self.tracking_stats_label.pack(pady=2)
        
        # Fullscreen canvas button
        fullscreen_btn = tk.Button(tracking_frame, text="Fullscreen Canvas", 
                                  command=self.toggle_fullscreen_canvas,
                                  bg='purple', fg='white', font=('Arial', 9))
        fullscreen_btn.pack(pady=5)
        
        # Performance monitoring
        perf_frame = tk.LabelFrame(self.control_panel, text="Performance", 
                                 bg='gray20', fg='white')
        perf_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.fps_label = tk.Label(perf_frame, text="FPS: 0", bg='gray20', fg='white')
        self.fps_label.pack(pady=2)
        
        self.detection_count_label = tk.Label(perf_frame, text="Cells: 0", 
                                            bg='gray20', fg='white')
        self.detection_count_label.pack(pady=2)
        
        # GPU Performance Parameters
        gpu_frame = tk.LabelFrame(self.control_panel, text="GPU Parameters", 
                                bg='gray20', fg='white')
        gpu_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # CLAHE parameters
        tk.Label(gpu_frame, text="CLAHE Clip Limit:", bg='gray20', fg='white').pack()
        self.clahe_var = tk.DoubleVar(value=self.cell_detector.clahe_clip_limit)
        clahe_scale = tk.Scale(gpu_frame, from_=1.0, to=5.0, resolution=0.1, 
                             variable=self.clahe_var, orient=tk.HORIZONTAL,
                             command=self.update_clahe_clip_limit,
                             bg='gray20', fg='white', highlightbackground='gray20')
        clahe_scale.pack(fill=tk.X, padx=5)
        
        # Area parameters
        tk.Label(gpu_frame, text="Min Area:", bg='gray20', fg='white').pack()
        self.area_min_var = tk.IntVar(value=self.cell_detector.area_min)
        area_min_scale = tk.Scale(gpu_frame, from_=10, to=200, 
                                variable=self.area_min_var, orient=tk.HORIZONTAL,
                                command=self.update_area_min,
                                bg='gray20', fg='white', highlightbackground='gray20')
        area_min_scale.pack(fill=tk.X, padx=5)
        
        tk.Label(gpu_frame, text="Max Area:", bg='gray20', fg='white').pack()
        self.area_max_var = tk.IntVar(value=self.cell_detector.area_max)
        area_max_scale = tk.Scale(gpu_frame, from_=200, to=1000, 
                                variable=self.area_max_var, orient=tk.HORIZONTAL,
                                command=self.update_area_max,
                                bg='gray20', fg='white', highlightbackground='gray20')
        area_max_scale.pack(fill=tk.X, padx=5)
        
        # Canny parameters
        tk.Label(gpu_frame, text="Canny Low:", bg='gray20', fg='white').pack()
        self.canny_low_var = tk.IntVar(value=self.cell_detector.canny_low)
        canny_low_scale = tk.Scale(gpu_frame, from_=10, to=100, 
                                 variable=self.canny_low_var, orient=tk.HORIZONTAL,
                                 command=self.update_canny_low,
                                 bg='gray20', fg='white', highlightbackground='gray20')
        canny_low_scale.pack(fill=tk.X, padx=5)
        
        tk.Label(gpu_frame, text="Canny High:", bg='gray20', fg='white').pack()
        self.canny_high_var = tk.IntVar(value=self.cell_detector.canny_high)
        canny_high_scale = tk.Scale(gpu_frame, from_=50, to=200, 
                                  variable=self.canny_high_var, orient=tk.HORIZONTAL,
                                  command=self.update_canny_high,
                                  bg='gray20', fg='white', highlightbackground='gray20')
        canny_high_scale.pack(fill=tk.X, padx=5)
        
        # Exit Controls
        exit_frame = tk.LabelFrame(self.control_panel, text="Application", 
                                 bg='gray20', fg='white')
        exit_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Exit button
        exit_btn = tk.Button(exit_frame, text="Exit Application", 
                           command=self.on_closing, bg='red', fg='white')
        exit_btn.pack(fill=tk.X, padx=5, pady=5)
    
    def update_clahe_clip_limit(self, value):
        """Update CLAHE clip limit parameter"""
        self.cell_detector.clahe_clip_limit = float(value)
    
    def update_area_min(self, value):
        """Update minimum area parameter"""
        self.cell_detector.area_min = int(value)
        self.cell_detector.min_area = int(value)
    
    def update_area_max(self, value):
        """Update maximum area parameter"""
        self.cell_detector.area_max = int(value)
        self.cell_detector.max_area = int(value)
    
    def update_canny_low(self, value):
        """Update Canny low threshold"""
        self.cell_detector.canny_low = int(value)
    
    def update_canny_high(self, value):
        """Update Canny high threshold"""
        self.cell_detector.canny_high = int(value)
    
    def start_camera(self):
        """Start camera capture"""
        self.camera_manager.camera_index = self.camera_var.get()
        success, message = self.camera_manager.start_camera()
        if success:
            self.running = True
            self.start_threads()
            print(message)
        else:
            print(f"Failed to start camera: {message}")
    
    def reconnect_camera(self):
        """Reconnect to camera with new index"""
        self.stop_camera()
        time.sleep(0.5)  # Brief pause
        self.start_camera()
    
    def stop_camera(self):
        """Stop camera capture"""
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
        if self.render_thread and self.render_thread.is_alive():
            self.render_thread.join(timeout=1.0)
        self.camera_manager.stop_camera()
    
    def start_threads(self):
        """Start processing threads"""
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.render_thread = threading.Thread(target=self.render_loop, daemon=True)
        
        self.capture_thread.start()
        self.detection_thread.start()
        self.render_thread.start()
    
    def capture_loop(self):
        """Camera capture loop - Unlimited FPS (camera-limited)"""
        frame_skip_counter = 0
        
        while self.running:
            success, frame = self.camera_manager.get_frame()
            if success and frame is not None:
                with self.frame_lock:
                    self.current_frame = frame.copy()
                frame_skip_counter = 0
            else:
                frame_skip_counter += 1
                # Only sleep if no frames are available to prevent busy waiting
                if frame_skip_counter > 5:
                    time.sleep(0.001)  # 1ms sleep to prevent CPU overload when no frames
    
    def detection_loop(self):
        """Cell detection loop - Adaptive FPS based on GPU utilization"""
        # Adaptive FPS control variables
        target_fps = 10  # Starting FPS
        min_sleep = 0.001  # 1ms minimum sleep
        last_processing_time = time.time()
        
        while self.running:
            loop_start = time.time()
            
            if self.detection_enabled and self.current_frame is not None:
                with self.frame_lock:
                    frame_to_process = self.current_frame.copy()
                
                # Get AOI coordinates if enabled
                aoi_coords = None
                if self.show_aoi and self.aoi_manager.has_aoi():
                    # Get AOI coordinates in original image space
                    aoi_coords = self.aoi_manager.get_aoi_coords()
                
                # Perform GPU-accelerated detection
                try:
                    if self.debug_window_open:
                        detected_cells, debug_image = self.cell_detector.detect_cells(
                            frame_to_process, aoi_coords, return_debug=True)
                        self.update_debug_window(debug_image)
                    else:
                        detected_cells = self.cell_detector.detect_cells(
                            frame_to_process, aoi_coords)
                    
                    # Process detections through adaptive tracker
                    if self.tracking_enabled:
                        # Convert detection format for tracker
                        tracker_detections = []
                        for cell in detected_cells:
                            # Handle dictionary format from GPU detector
                            if isinstance(cell, dict):
                                # Get centroid and bbox from detection (in AOI space)
                                aoi_centroid = cell['centroid']
                                aoi_bbox = cell['bbox']  # (x1, y1, x2, y2)
                                aoi_offset = cell.get('aoi_offset', (0, 0))
                                
                                # Convert to original image space for tracking
                                centroid = (aoi_centroid[0] + aoi_offset[0], aoi_centroid[1] + aoi_offset[1])
                                
                                # Convert bbox to original image space and (x, y, w, h) format
                                x1, y1, x2, y2 = aoi_bbox
                                orig_x1 = x1 + aoi_offset[0]
                                orig_y1 = y1 + aoi_offset[1]
                                orig_x2 = x2 + aoi_offset[0]
                                orig_y2 = y2 + aoi_offset[1]
                                tracker_bbox = (orig_x1, orig_y1, orig_x2 - orig_x1, orig_y2 - orig_y1)
                            else:
                                # Handle legacy tuple format (x, y, w, h)
                                x, y, w, h = cell
                                centroid = (x + w/2, y + h/2)
                                tracker_bbox = (x, y, w, h)
                            
                            tracker_detections.append({
                                'centroid': centroid,
                                'bbox': tracker_bbox
                            })
                        
                        # Update tracker
                        self.tracked_cells = self.cell_tracker.update(tracker_detections)
                        
                        # Store tracking results for visualization
                        self.cell_detector.detected_cells = detected_cells
                        
                        # Update UI with tracking info
                        active_tracks = len(self.tracked_cells)
                        total_detections = len(detected_cells)
                        stats = self.cell_tracker.get_statistics()
                        
                        self.root.after(0, lambda: self.detection_count_label.config(
                            text=f"Cells: {total_detections} | Tracks: {active_tracks} | Total: {stats['total_tracked']}"))
                        
                        # Update tracking statistics
                        disappeared_tracks = stats['disappeared_tracks']
                        self.root.after(0, lambda: self.tracking_stats_label.config(
                            text=f"Active: {active_tracks} | Missing: {disappeared_tracks} | Frame: {stats['frame_number']}"))
                        
                        # Update fullscreen canvas with cell positions
                        if self.fullscreen_canvas_open:
                            self.root.after(0, lambda: self.update_fullscreen_canvas_cells(self.tracked_cells))
                        
                        # Debug output
                        if len(detected_cells) > 0:
                            print(f"GPU Detection: Found {len(detected_cells)} cells, {active_tracks} active tracks")
                            # Print first few ACTIVE tracked cells for debugging (only those currently detected)
                            active_tracks_debug = [(cell_id, track_info) for cell_id, track_info in self.tracked_cells.items() 
                                                  if track_info['disappeared_count'] == 0]
                            for i, (cell_id, track_info) in enumerate(active_tracks_debug[:3]):
                                centroid = track_info['centroid']
                                confidence = track_info['confidence']
                                velocity = track_info.get('velocity', (0, 0))
                                print(f"  Active Track {cell_id}: pos=({centroid[0]:.1f},{centroid[1]:.1f}) conf={confidence:.2f} vel=({velocity[0]:.1f},{velocity[1]:.1f})")
                    else:
                        # Store detection results without tracking
                        self.cell_detector.detected_cells = detected_cells
                        
                        # Update detection count
                        self.root.after(0, lambda: self.detection_count_label.config(
                            text=f"Cells: {len(detected_cells)}"))
                        
                        # Debug output
                        if len(detected_cells) > 0:
                            print(f"GPU Detection: Found {len(detected_cells)} cells")
                        
                except Exception as e:
                    print(f"Detection error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Adaptive FPS control
            processing_time = time.time() - loop_start
            
            # Calculate sleep time to maintain target FPS
            sleep_time = max(min_sleep, (1.0 / target_fps) - processing_time)
            time.sleep(sleep_time)
            
            # Dynamically adjust target FPS based on GPU headroom
            gpu_util = self.cell_detector.get_gpu_utilization()  # Requires GPU util monitor
            if gpu_util < 70:  # If GPU utilization <70%
                target_fps = min(60, target_fps * 1.1)  # Increase FPS by 10%
            else:
                target_fps = max(10, target_fps * 0.95)  # Reduce FPS if nearing limit
    
    def render_loop(self):
        """Rendering loop - High FPS display (up to 120 FPS)"""
        last_fps_update = time.time()
        last_frame_id = None
        display_fps_target = 120  # Increase display target FPS
        frame_interval = 1.0 / display_fps_target
        last_render_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # Only render if enough time has passed (frame rate limiting)
            if current_time - last_render_time >= frame_interval:
                if self.current_frame is not None:
                    with self.frame_lock:
                        frame_to_display = self.current_frame.copy()
                        current_frame_id = id(self.current_frame)  # Get frame identity
                    
                    # Only process if we have a new frame (avoid redundant processing)
                    if current_frame_id != last_frame_id:
                        # Create display frame
                        display_frame = self.create_display_frame(frame_to_display)
                        
                        # Update display with higher priority
                        self.root.after_idle(lambda df=display_frame: self.update_display(df))
                        
                        last_frame_id = current_frame_id
                    
                    last_render_time = current_time
            
            # Update FPS display every second using camera manager's actual FPS
            if current_time - last_fps_update >= 1.0:
                if self.camera_manager and self.camera_manager.is_running():
                    # Calculate actual camera FPS from camera manager's frame count
                    camera_fps = self.camera_manager.frame_count
                    self.camera_manager.frame_count = 0  # Reset counter
                    self.current_fps = camera_fps
                    
                    # Update FPS label
                    self.root.after_idle(lambda: self.fps_label.config(text=f"Camera: {camera_fps} FPS"))
                
                last_fps_update = current_time
            
            # Minimal sleep to prevent excessive CPU usage while allowing high FPS
            time.sleep(0.001)  # 1ms sleep instead of 16.7ms (60 FPS)
    
    def create_display_frame(self, frame):
        """Create frame for display with overlays and proper aspect ratio"""
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate the display size while maintaining aspect ratio
        camera_aspect_ratio = frame_width / frame_height
        canvas_aspect_ratio = self.display_width / self.display_height
        
        if canvas_aspect_ratio > camera_aspect_ratio:
            actual_display_height = self.display_height
            actual_display_width = int(self.display_height * camera_aspect_ratio)
            display_offset_x = (self.display_width - actual_display_width) // 2
            display_offset_y = 0
        else:
            actual_display_width = self.display_width
            actual_display_height = int(self.display_width / camera_aspect_ratio)
            display_offset_x = 0
            display_offset_y = (self.display_height - actual_display_height) // 2
        
        # Update AOI manager with display properties
        if self.aoi_manager:
            self.aoi_manager.set_display_properties(
                actual_display_width, actual_display_height,
                display_offset_x, display_offset_y,
                frame_width, frame_height
            )
        
        # Resize frame for display with correct aspect ratio
        display_frame = cv2.resize(frame, (actual_display_width, actual_display_height))
        
        # Create final display frame with proper dimensions
        final_frame = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
        final_frame[display_offset_y:display_offset_y + actual_display_height,
                   display_offset_x:display_offset_x + actual_display_width] = display_frame
        
        # Apply AOI overlay if active
        if self.show_aoi and self.aoi_manager and self.aoi_manager.has_aoi():
            final_frame = self.aoi_manager.apply_aoi_overlay_with_offset(final_frame, display_offset_x, display_offset_y)
        
        # Draw detected cells with tracking
        if self.detection_enabled:
            if self.tracking_enabled and self.tracked_cells:
                self.draw_tracked_cells(final_frame, frame_width, frame_height, display_offset_x, display_offset_y, actual_display_width, actual_display_height)
            elif hasattr(self.cell_detector, 'detected_cells') and self.cell_detector.detected_cells:
                self.draw_detected_cells(final_frame, frame_width, frame_height, display_offset_x, display_offset_y, actual_display_width, actual_display_height)
        
        return final_frame
    
    def draw_detected_cells(self, display_frame, original_width, original_height, display_offset_x, display_offset_y, actual_display_width, actual_display_height):
        """Draw detected cells on display frame with proper coordinate transformation"""
        try:
            # Calculate scaling factors using ACTUAL video display size (not full canvas)
            scale_x = actual_display_width / original_width
            scale_y = actual_display_height / original_height
            
            detected_cells = self.cell_detector.detected_cells
            if not detected_cells:
                return
            
            # Debug: Check data type
            if not isinstance(detected_cells, list):
                print(f"Warning: detected_cells is not a list: {type(detected_cells)}")
                return
            
            for i, cell in enumerate(detected_cells):
                try:
                    # Check if cell is a dictionary
                    if not isinstance(cell, dict):
                        print(f"Warning: cell {i} is not a dict: {type(cell)}, value: {cell}")
                        continue
                    
                    # Safely extract cell properties
                    centroid = cell.get('centroid')
                    bbox = cell.get('bbox')
                    area = cell.get('area', 0)
                    aoi_offset = cell.get('aoi_offset', (0, 0))
                    
                    if not centroid or not bbox:
                        print(f"Warning: cell {i} missing centroid or bbox")
                        continue
                    
                    # Detection results are in AOI/cropped space
                    # First adjust to original image coordinates, then scale to display
                    orig_centroid_x = centroid[0] + aoi_offset[0]
                    orig_centroid_y = centroid[1] + aoi_offset[1]
                    orig_bbox_x1 = bbox[0] + aoi_offset[0]
                    orig_bbox_y1 = bbox[1] + aoi_offset[1]
                    orig_bbox_x2 = bbox[2] + aoi_offset[0]
                    orig_bbox_y2 = bbox[3] + aoi_offset[1]
                    
                    # Scale to display size and add display offset
                    centroid_x = int(orig_centroid_x * scale_x) + display_offset_x
                    centroid_y = int(orig_centroid_y * scale_y) + display_offset_y
                    bbox_x1 = int(orig_bbox_x1 * scale_x) + display_offset_x
                    bbox_y1 = int(orig_bbox_y1 * scale_y) + display_offset_y
                    bbox_x2 = int(orig_bbox_x2 * scale_x) + display_offset_x
                    bbox_y2 = int(orig_bbox_y2 * scale_y) + display_offset_y
                    
                    # Clamp coordinates to video frame boundaries
                    video_x1 = display_offset_x
                    video_y1 = display_offset_y
                    video_x2 = display_offset_x + int(original_width * scale_x)
                    video_y2 = display_offset_y + int(original_height * scale_y)
                    
                    # Only draw if detection is within video frame area
                    if (video_x1 <= centroid_x <= video_x2 and video_y1 <= centroid_y <= video_y2):
                        # Clamp all coordinates to video frame
                        centroid_x = max(video_x1, min(centroid_x, video_x2))
                        centroid_y = max(video_y1, min(centroid_y, video_y2))
                        bbox_x1 = max(video_x1, min(bbox_x1, video_x2))
                        bbox_y1 = max(video_y1, min(bbox_y1, video_y2))
                        bbox_x2 = max(video_x1, min(bbox_x2, video_x2))
                        bbox_y2 = max(video_y1, min(bbox_y2, video_y2))
                    
                        # Debug: Print coordinate transformation for first few cells
                        if i < 3:
                            print(f"Cell {i}: AOI=({centroid[0]:.1f},{centroid[1]:.1f}) + offset{aoi_offset} = orig=({orig_centroid_x:.1f},{orig_centroid_y:.1f}) -> display=({centroid_x},{centroid_y}) [WITHIN FRAME]")
                        
                        # Draw centroid
                        cv2.circle(display_frame, (centroid_x, centroid_y), 3, (0, 255, 0), -1)
                        
                        # Draw bounding box
                        cv2.rectangle(display_frame, (bbox_x1, bbox_y1), (bbox_x2, bbox_y2), (255, 0, 0), 2)
                        
                        # Draw area label
                        cv2.putText(display_frame, f"{int(area)}", 
                                   (bbox_x1, bbox_y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                                   0.5, (255, 255, 255), 1)
                    else:
                        # Debug: Print when detection is outside video frame
                        if i < 3:
                            print(f"Cell {i}: AOI=({centroid[0]:.1f},{centroid[1]:.1f}) + offset{aoi_offset} = orig=({orig_centroid_x:.1f},{orig_centroid_y:.1f}) -> display=({centroid_x},{centroid_y}) [OUTSIDE FRAME - SKIPPED]")
                               
                except Exception as e:
                    print(f"Error drawing cell {i}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in draw_detected_cells: {e}")
    
    def draw_tracked_cells(self, display_frame, original_width, original_height, display_offset_x, display_offset_y, actual_display_width, actual_display_height):
        """Draw tracked cells with IDs, trajectories, and predictions"""
        try:
            # Calculate scaling factors
            scale_x = actual_display_width / original_width
            scale_y = actual_display_height / original_height
            
            # Get trajectories if enabled
            trajectories = {}
            if self.show_trajectories:
                trajectories = self.cell_tracker.get_track_trajectories(min_length=3)
            
            # Draw each tracked cell
            for cell_id, track_info in self.tracked_cells.items():
                try:
                    centroid = track_info['centroid']
                    bbox = track_info['bbox']
                    confidence = track_info['confidence']
                    disappeared_count = track_info['disappeared_count']
                    predicted_pos = track_info.get('predicted_position', centroid)
                    velocity = track_info.get('velocity', (0, 0))
                    search_radius = track_info.get('search_radius', 50)
                    
                    # Transform coordinates to display space
                    # Note: tracked coordinates are already in original image space
                    display_x = int(centroid[0] * scale_x) + display_offset_x
                    display_y = int(centroid[1] * scale_y) + display_offset_y
                    
                    # Transform bounding box
                    x, y, w, h = bbox
                    bbox_x1 = int(x * scale_x) + display_offset_x
                    bbox_y1 = int(y * scale_y) + display_offset_y
                    bbox_x2 = int((x + w) * scale_x) + display_offset_x
                    bbox_y2 = int((y + h) * scale_y) + display_offset_y
                    
                    # Clamp to video frame boundaries
                    video_x1 = display_offset_x
                    video_y1 = display_offset_y
                    video_x2 = display_offset_x + actual_display_width
                    video_y2 = display_offset_y + actual_display_height
                    
                    # Check if cell is within frame
                    if (video_x1 <= display_x <= video_x2 and video_y1 <= display_y <= video_y2):
                        # Choose colors based on track state
                        if disappeared_count > 0:
                            # Disappeared track - red/orange
                            color = (0, 100, 255)  # Orange
                            text_color = (0, 100, 255)
                        else:
                            # Active track - green/blue based on confidence
                            intensity = int(255 * confidence)
                            color = (0, intensity, 255 - intensity)  # Green to yellow
                            text_color = (0, 255, 0)
                        
                        # Draw bounding box
                        thickness = 3 if disappeared_count == 0 else 1
                        cv2.rectangle(display_frame, (bbox_x1, bbox_y1), (bbox_x2, bbox_y2), color, thickness)
                        
                        # Draw centroid
                        cv2.circle(display_frame, (display_x, display_y), 4, color, -1)
                        
                        # Draw cell ID and info
                        label = f"ID:{cell_id}"
                        if disappeared_count > 0:
                            label += f" (miss:{disappeared_count})"
                        
                        # Add confidence and velocity info
                        info_label = f"C:{confidence:.2f} V:({velocity[0]:.1f},{velocity[1]:.1f})"
                        
                        # Draw labels
                        cv2.putText(display_frame, label, 
                                   (bbox_x1, bbox_y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 
                                   0.6, text_color, 2)
                        cv2.putText(display_frame, info_label, 
                                   (bbox_x1, bbox_y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                                   0.4, text_color, 1)
                        
                        # Draw prediction if enabled and different from current position
                        if self.show_predictions and predicted_pos != centroid:
                            pred_x = int(predicted_pos[0] * scale_x) + display_offset_x
                            pred_y = int(predicted_pos[1] * scale_y) + display_offset_y
                            
                            if (video_x1 <= pred_x <= video_x2 and video_y1 <= pred_y <= video_y2):
                                # Draw prediction point
                                cv2.circle(display_frame, (pred_x, pred_y), 3, (255, 255, 0), 1)
                                # Draw line from current to predicted position
                                cv2.line(display_frame, (display_x, display_y), (pred_x, pred_y), (255, 255, 0), 1)
                        
                        # Draw search radius if enabled
                        if self.show_predictions:
                            radius_display = int(search_radius * min(scale_x, scale_y))
                            cv2.circle(display_frame, (display_x, display_y), radius_display, (100, 100, 100), 1)
                        
                        # Draw trajectory if enabled
                        if self.show_trajectories and cell_id in trajectories:
                            trajectory = trajectories[cell_id]
                            points = trajectory['points']
                            if len(points) > 1:
                                # Convert trajectory points to display coordinates
                                display_points = []
                                for point in points[-20:]:  # Show last 20 points
                                    traj_x = int(point[0] * scale_x) + display_offset_x
                                    traj_y = int(point[1] * scale_y) + display_offset_y
                                    if (video_x1 <= traj_x <= video_x2 and video_y1 <= traj_y <= video_y2):
                                        display_points.append((traj_x, traj_y))
                                
                                # Draw trajectory lines
                                if len(display_points) > 1:
                                    for i in range(1, len(display_points)):
                                        alpha = i / len(display_points)  # Fade effect
                                        traj_color = (int(100 * alpha), int(100 * alpha), int(255 * alpha))
                                        cv2.line(display_frame, display_points[i-1], display_points[i], traj_color, 1)
                                        
                except Exception as e:
                    print(f"Error drawing tracked cell {cell_id}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in draw_tracked_cells: {e}")
    
    def update_display(self, display_frame):
        """Update the video display on Canvas"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image and then to PhotoImage
            pil_image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Clear canvas and display new image
            self.video_canvas.delete("video")
            self.video_canvas.create_image(
                self.display_width // 2, self.display_height // 2,
                image=photo, tags="video"
            )
            self.video_canvas.image = photo  # Keep a reference
            
        except Exception as e:
            print(f"Display update error: {e}")
    

    
    def toggle_detection(self):
        """Toggle cell detection"""
        self.detection_enabled = self.detection_var.get()
        print(f"Detection {'enabled' if self.detection_enabled else 'disabled'}")
    
    def toggle_aoi(self):
        """Toggle AOI drawing"""
        self.show_aoi = self.aoi_var.get()
        if self.aoi_manager:
            self.aoi_manager.set_active(self.show_aoi)
            if not self.show_aoi:
                self.aoi_manager.clear_aoi()
        print(f"AOI {'enabled' if self.show_aoi else 'disabled'}")
    
    def clear_aoi(self):
        """Clear the current AOI"""
        if self.aoi_manager:
            self.aoi_manager.clear_aoi()
            print("AOI cleared")
    
    def clear_aoi_keyboard(self, event=None):
        """Clear AOI via keyboard shortcut (C key)"""
        if self.show_aoi:
            self.clear_aoi()
    
    def reset_aoi_keyboard(self, event=None):
        """Reset AOI drawing mode via keyboard shortcut (R key)"""
        if self.show_aoi:
            self.clear_aoi()
            print("Ready to draw new AOI - click and drag on video")
    
    def toggle_debug_window(self):
        """Toggle debug window"""
        if self.debug_window_open:
            self.close_debug_window()
        else:
            self.open_debug_window()
    
    def toggle_tracking(self):
        """Toggle cell tracking"""
        self.tracking_enabled = self.tracking_var.get()
        if not self.tracking_enabled:
            # Clear existing tracks when disabling
            self.tracked_cells = {}
        print(f"Tracking {'enabled' if self.tracking_enabled else 'disabled'}")
    
    def toggle_trajectories(self):
        """Toggle trajectory visualization"""
        self.show_trajectories = self.trajectory_var.get()
        print(f"Trajectories {'enabled' if self.show_trajectories else 'disabled'}")
    
    def toggle_predictions(self):
        """Toggle prediction visualization"""
        self.show_predictions = self.predictions_var.get()
        print(f"Predictions {'enabled' if self.show_predictions else 'disabled'}")
    
    def open_debug_window(self):
        """Open debug window"""
        self.debug_window = tk.Toplevel(self.root)
        self.debug_window.title("Debug - Binary Segmentation")
        self.debug_window.protocol("WM_DELETE_WINDOW", self.close_debug_window)
        
        self.debug_label = tk.Label(self.debug_window)
        self.debug_label.pack()
        
        self.debug_window_open = True
        print("Debug window opened")
    
    def close_debug_window(self):
        """Close debug window"""
        if self.debug_window:
            self.debug_window.destroy()
            self.debug_window = None
        self.debug_window_open = False
        print("Debug window closed")
    
    def update_debug_window(self, debug_image):
        """Update debug window with binary segmentation image"""
        if self.debug_window_open and self.debug_window:
            try:
                # Resize debug image
                debug_resized = cv2.resize(debug_image, (400, 300))
                
                # Convert to PIL and PhotoImage
                pil_debug = Image.fromarray(debug_resized)
                photo_debug = ImageTk.PhotoImage(pil_debug)
                
                # Update debug label
                self.root.after(0, lambda: self.debug_label.configure(image=photo_debug))
                self.root.after(0, lambda: setattr(self.debug_label, 'image', photo_debug))
                
            except Exception as e:
                print(f"Debug window update error: {e}")
    
    def initialize_fullscreen_canvas(self):
        """Initialize a fullscreen black canvas as a separate window"""
        if self.fullscreen_canvas_open:
            print("Fullscreen canvas already open")
            return
            
        try:
            # Create fullscreen window
            self.fullscreen_canvas = tk.Toplevel(self.root)
            self.fullscreen_canvas.title("Fullscreen Canvas")
            self.fullscreen_canvas.configure(bg='black')
            
            # Make it fullscreen
            self.fullscreen_canvas.attributes('-fullscreen', True)
            self.fullscreen_canvas.attributes('-topmost', True)
            
            # Get screen dimensions
            screen_width = self.fullscreen_canvas.winfo_screenwidth()
            screen_height = self.fullscreen_canvas.winfo_screenheight()
            
            # Create black canvas that fills the entire screen
            self.canvas_widget = tk.Canvas(
                self.fullscreen_canvas,
                width=screen_width,
                height=screen_height,
                bg='black',
                highlightthickness=0
            )
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)
            
            # Bind escape key to close
            self.fullscreen_canvas.bind('<Escape>', self.close_fullscreen_canvas)
            self.fullscreen_canvas.bind('<KeyPress>', self.close_fullscreen_canvas)
            
            # Handle window close event
            self.fullscreen_canvas.protocol("WM_DELETE_WINDOW", self.close_fullscreen_canvas)
            
            # Set focus to capture key events
            self.fullscreen_canvas.focus_set()
            
            # Load calibration data and draw FOV border
            calibration_file = "e:/Documents/Codes/Matlab/CellToolbox/python-version/calibration/latest_calibration.json"
            self.homography_matrix = None
            try:
                with open(calibration_file, 'r') as f:
                    calibration_data = json.load(f)
                fov_corners = calibration_data.get('fov_corners', [])
                camera_resolution = calibration_data.get('camera_resolution', {})
                
                if fov_corners and len(fov_corners) == 4 and camera_resolution:
                    # Draw FOV border with thin red lines
                    for i in range(4):
                        start = fov_corners[i]
                        end = fov_corners[(i + 1) % 4]
                        self.canvas_widget.create_line(
                            start[0], start[1], end[0], end[1],
                            fill='red', width=2, tags="fov_border"
                        )
                    
                    # Compute homography matrix for cell position mapping
                    frame_width = camera_resolution['width']
                    frame_height = camera_resolution['height']
                    
                    # Video frame corners (source points)
                    src_pts = np.array([
                        [0, 0],
                        [frame_width, 0],
                        [frame_width, frame_height],
                        [0, frame_height]
                    ], dtype="float32")
                    
                    # FOV corners (destination points)
                    dst_pts = np.array(fov_corners, dtype="float32")
                    
                    # Calculate homography matrix
                    self.homography_matrix, _ = cv2.findHomography(src_pts, dst_pts)
                    
                    print(f"FOV border drawn with {len(fov_corners)} points")
                    print(f"Homography matrix computed for {frame_width}x{frame_height} frame")
                else:
                    print(f"Invalid calibration data: {len(fov_corners) if fov_corners else 0} corners, camera_res: {bool(camera_resolution)}")
            except FileNotFoundError:
                print(f"Calibration file not found: {calibration_file}")
            except Exception as e:
                print(f"Error loading calibration data: {e}")
            
            self.fullscreen_canvas_open = True
            print(f"Fullscreen canvas initialized: {screen_width}x{screen_height}")
            
        except Exception as e:
            print(f"Error initializing fullscreen canvas: {e}")
            self.fullscreen_canvas_open = False
    
    def close_fullscreen_canvas(self, event=None):
        """Close the fullscreen canvas window"""
        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            self.fullscreen_canvas.destroy()
            self.fullscreen_canvas = None
            self.canvas_widget = None
            self.fullscreen_canvas_open = False
            self.homography_matrix = None
            print("Fullscreen canvas closed")
    
    def update_fullscreen_canvas_cells(self, tracked_cells):
        """Update cell positions on the fullscreen canvas"""
        if not self.fullscreen_canvas_open or not self.canvas_widget:
            print(f"Canvas update skipped: canvas_open={self.fullscreen_canvas_open}, widget={self.canvas_widget is not None}")
            return
            
        if not hasattr(self, 'homography_matrix') or self.homography_matrix is None:
            print("Canvas update skipped: homography_matrix not available")
            return
        
        try:
            # Clear previous cell markers
            self.canvas_widget.delete("cell_marker")
            
            print(f"Updating canvas with {len(tracked_cells)} tracked cells")
            
            # Transform and draw each cell
            active_count = 0
            for cell_id, cell in tracked_cells.items():
                # Check if this is a TrackedCell object or dictionary
                if hasattr(cell, 'disappeared_count'):
                    disappeared_count = cell.disappeared_count
                    centroid = cell.centroid
                elif isinstance(cell, dict):
                    disappeared_count = cell.get('disappeared_count', 0)
                    centroid = cell.get('centroid', (0, 0))
                else:
                    print(f"Unknown cell format for cell {cell_id}: {type(cell)}")
                    continue
                    
                if disappeared_count == 0:  # Only show active cells
                    active_count += 1
                    # Get cell centroid
                    cx, cy = centroid
                    print(f"Processing cell {cell_id}: centroid=({cx:.1f}, {cy:.1f})")
                    
                    # Transform position using homography
                    cell_pt = np.array([[[cx, cy]]], dtype="float32")
                    transformed_pt = cv2.perspectiveTransform(cell_pt, self.homography_matrix)
                    screen_x, screen_y = transformed_pt[0][0]
                    
                    print(f"  Transformed to screen: ({screen_x:.1f}, {screen_y:.1f})")
                    
                    # Calculate rectangle size (proportional to FOV)
                    rect_size = 12  # Increased size for visibility
                    
                    # Draw filled white rectangle
                    self.canvas_widget.create_rectangle(
                        screen_x - rect_size/2, screen_y - rect_size/2,
                        screen_x + rect_size/2, screen_y + rect_size/2,
                        fill="white", outline="gray", width=1, tags="cell_marker"
                    )
                    
                    # Draw cell ID
                    self.canvas_widget.create_text(
                        screen_x, screen_y - rect_size - 8,
                        text=str(cell_id), fill="yellow", font=("Arial", 10, "bold"),
                        tags="cell_marker"
                    )
                    
                    print(f"  Drew rectangle at ({screen_x:.1f}, {screen_y:.1f})")
            
            print(f"Canvas update complete: {active_count} active cells drawn")
        
        except Exception as e:
            print(f"Error updating fullscreen canvas cells: {e}")
            import traceback
            traceback.print_exc()
    
    def toggle_fullscreen_canvas(self):
        """Toggle the fullscreen canvas window"""
        if self.fullscreen_canvas_open:
            self.close_fullscreen_canvas()
        else:
            self.initialize_fullscreen_canvas()
    
    def on_video_click(self, event):
        """Handle video click for AOI drawing"""
        if self.show_aoi:
            self.aoi_manager.on_canvas_click(event)
    
    def on_video_drag(self, event):
        """Handle video drag for AOI drawing"""
        if self.show_aoi:
            self.aoi_manager.on_canvas_drag(event)
    
    def on_video_release(self, event):
        """Handle video release for AOI drawing"""
        if self.show_aoi:
            self.aoi_manager.on_canvas_release(event)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        if not self.fullscreen:
            self.root.geometry("1600x1000")
        print(f"Fullscreen {'enabled' if self.fullscreen else 'disabled'}")
    
    def open_exposure_control(self):
        """Open the exposure control panel"""
        if self.exposure_control_panel:
            self.exposure_control_panel.open_panel()
    
    def on_closing(self):
        """Handle application closing"""
        print("Closing application...")
        self.running = False
        
        # Close exposure control panel if open
        if self.exposure_control_panel:
            self.exposure_control_panel.close_panel()
        
        self.stop_camera()
        if self.debug_window:
            self.debug_window.destroy()
        self.root.destroy()
