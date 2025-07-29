"""
GPU-accelerated USB Camera Live Stream Application
This module provides the main application class with GPU-accelerated cell detection.
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time

from camera_manager import CameraManager
from cell_detector_gpu import CellDetectorGPU  # Use GPU version
from aoi_manager import AOIManager

class USBCameraLiveGPU:
    """Main application class for GPU-accelerated USB camera live stream with cell detection"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("USB Camera Live Stream - GPU Accelerated")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize components
        self.camera_manager = CameraManager()
        self.cell_detector = CellDetectorGPU()  # Use GPU version
        # AOI manager will be initialized after UI setup
        
        # Application state
        self.running = False
        self.detection_enabled = False
        self.show_aoi = False
        self.fullscreen = False
        self.debug_window = None
        self.debug_window_open = False
        
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
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # GPU status
        self.gpu_status = "GPU: " + ("Available" if self.cell_detector.gpu_available else "Not Available")
        
        # Setup UI
        self.setup_ui()
        
        # Initialize AOI manager with video canvas
        self.aoi_manager = AOIManager(self.video_canvas)
        
        # Start fullscreen
        self.toggle_fullscreen()
        
        # Start camera
        self.start_camera()
    
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
        debug_btn = tk.Button(detection_frame, text="Show Debug Window", 
                            command=self.toggle_debug_window)
        debug_btn.pack(pady=5)
        
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
        """Camera capture loop - 30 FPS"""
        while self.running:
            success, frame = self.camera_manager.get_frame()
            if success and frame is not None:
                with self.frame_lock:
                    self.current_frame = frame.copy()
            time.sleep(1/30)  # 30 FPS
    
    def detection_loop(self):
        """Cell detection loop - 10 FPS for GPU efficiency"""
        while self.running:
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
                    
                    # Store detection results
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
            
            time.sleep(1/50)  # 50 FPS for detection
    
    def render_loop(self):
        """Rendering loop - 60 FPS"""
        while self.running:
            if self.current_frame is not None:
                with self.frame_lock:
                    frame_to_display = self.current_frame.copy()
                
                # Create display frame
                display_frame = self.create_display_frame(frame_to_display)
                
                # Update display
                self.root.after(0, lambda df=display_frame: self.update_display(df))
                
                # Update FPS
                self.update_fps()
            
            time.sleep(1/60)  # 60 FPS
    
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
        
        # Draw detected cells
        if self.detection_enabled and hasattr(self.cell_detector, 'detected_cells') and self.cell_detector.detected_cells:
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
    
    def update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
            
            # Update FPS label
            self.root.after(0, lambda: self.fps_label.config(text=f"FPS: {self.current_fps}"))
    
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
    
    def on_closing(self):
        """Handle application closing"""
        print("Closing application...")
        self.running = False
        self.stop_camera()
        if self.debug_window:
            self.debug_window.destroy()
        self.root.destroy()
