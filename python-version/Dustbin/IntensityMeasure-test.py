"""
Intensity Measure - TIFF Image Cell Detection
--------------------------------------------
A tool for detecting and analyzing cells in TIFF images using the same algorithms
as the ToupCam SingleDroplet detection system.
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from skimage import filters, morphology, measure
import os
import json
import time

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

def detect_cells_in_roi(image, roi_rect, params=None):
    """
    Detect cells within the specified region of interest using Kirsch operators
    
    Args:
        image: The input image (BGR format)
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
    
    # Extract ROI from image
    x, y, w, h = roi_rect
    roi = image[y:y+h, x:x+w]
    
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
            
            # Adjust coordinates to original image
            cx += x
            cy += y
            bx += x
            by += y
            
            # Create cell object
            cell = DetectedCell((cx, cy), radius, contour, (bx, by, bw, bh))
            detected_cells.append(cell)
    
    return detected_cells

def downsample_2x2(image):
    """
    Downsample image by taking top-left pixel from each 2x2 block
    
    Args:
        image: Input image (BGR format)
        
    Returns:
        Downsampled image with half width and half height
    """
    if image is None:
        return None
    
    h, w = image.shape[:2]
    
    # Calculate new dimensions (half size)
    new_h = h // 2
    new_w = w // 2
    
    # Create output image
    if len(image.shape) == 3:  # Color image
        downsampled = np.zeros((new_h, new_w, image.shape[2]), dtype=image.dtype)
    else:  # Grayscale image
        downsampled = np.zeros((new_h, new_w), dtype=image.dtype)
    
    # Sample every 2nd pixel starting from (0,0)
    # This takes Line1Row1, Line1Row3, Line1Row5, etc.
    # and Line3Row1, Line3Row3, Line3Row5, etc.
    for i in range(new_h):
        for j in range(new_w):
            # Take pixel from (2*i, 2*j) position in original image
            if len(image.shape) == 3:
                downsampled[i, j] = image[2*i, 2*j]
            else:
                downsampled[i, j] = image[2*i, 2*j]
    
    return downsampled

class IntensityMeasureApp:
    """Main application for TIFF image cell detection and analysis"""
    
    def __init__(self, root=None):
        # Create or use provided root window
        if root is None:
            self.root = tk.Tk()
            self.root.title("Intensity Measure - TIFF Cell Detection")
            self.owns_root = True
        else:
            self.root = root
            self.owns_root = False
        
        # Initialize variables
        self.current_image = None
        self.original_image = None
        self.image_path = None
        self.rect = None
        self.rect_start = None
        self.rect_end = None
        self.detected_cells = []
        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        
        # Detection parameters
        self.detection_params = {
            'area': (100, 5000),
            'perimeter': (30, 1000),
            'circularity': (0.2, 1.0)
        }
        
        # Exposure adjustment
        self.exposure_value = 1.0  # Default exposure multiplier
        
        # Downsampling
        self.downsampled_image = None  # The 2x2 downsampled image used for processing
        self.scale_factor = 2  # 2x2 downsampling factor
        
        # Zoom functionality
        self.zoom_level = 1.0  # Current zoom level
        self.min_zoom = 0.1    # Minimum zoom level
        self.max_zoom = 5.0    # Maximum zoom level
        
        # Pan functionality
        self.pan_offset_x = 0  # Pan offset in pixels
        self.pan_offset_y = 0  # Pan offset in pixels
        self.is_panning = False  # Track if currently panning
        self.last_pan_x = 0    # Last mouse position for panning
        self.last_pan_y = 0    # Last mouse position for panning
        self.roi_drawing = False  # Track if drawing ROI
        
        # Create UI
        self.create_ui()
        
        # Set up protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        """Create the application UI"""
        # Create frames
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.Frame(main_frame, width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create image canvas
        self.canvas = tk.Canvas(display_frame, width=800, height=600, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for ROI drawing
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Bind mouse events for panning (right-click drag)
        self.canvas.bind("<ButtonPress-3>", self.on_pan_start)
        self.canvas.bind("<B3-Motion>", self.on_pan_move)
        self.canvas.bind("<ButtonRelease-3>", self.on_pan_end)
        
        # Bind mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux
        
        # File operations
        file_frame = ttk.LabelFrame(control_frame, text="File Operations")
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Button(file_frame, text="Open TIFF Image", command=self.open_image).pack(fill=tk.X, pady=2)
        
        # ROI operations
        roi_frame = ttk.LabelFrame(control_frame, text="ROI Operations")
        roi_frame.pack(fill=tk.X, pady=5)
        ttk.Button(roi_frame, text="Detect Cells", command=self.detect_cells).pack(fill=tk.X, pady=2)
        ttk.Button(roi_frame, text="Clear ROI", command=self.clear_roi).pack(fill=tk.X, pady=2)
        ttk.Button(roi_frame, text="Map Back", command=self.map_back_to_original).pack(fill=tk.X, pady=2)
        ttk.Button(roi_frame, text="Save Results", command=self.save_results).pack(fill=tk.X, pady=2)
        
        # Detection parameters
        params_frame = ttk.LabelFrame(control_frame, text="Detection Parameters")
        params_frame.pack(fill=tk.X, pady=5)
        
        # Area range
        ttk.Label(params_frame, text="Area Range:").pack(anchor=tk.W)
        area_frame = ttk.Frame(params_frame)
        area_frame.pack(fill=tk.X, pady=2)
        self.area_min_var = tk.StringVar(value="100")
        self.area_max_var = tk.StringVar(value="5000")
        ttk.Entry(area_frame, textvariable=self.area_min_var, width=8).pack(side=tk.LEFT)
        ttk.Label(area_frame, text=" - ").pack(side=tk.LEFT)
        ttk.Entry(area_frame, textvariable=self.area_max_var, width=8).pack(side=tk.LEFT)
        
        # Circularity range
        ttk.Label(params_frame, text="Circularity Range:").pack(anchor=tk.W)
        circ_frame = ttk.Frame(params_frame)
        circ_frame.pack(fill=tk.X, pady=2)
        self.circ_min_var = tk.StringVar(value="0.2")
        self.circ_max_var = tk.StringVar(value="1.0")
        ttk.Entry(circ_frame, textvariable=self.circ_min_var, width=8).pack(side=tk.LEFT)
        ttk.Label(circ_frame, text=" - ").pack(side=tk.LEFT)
        ttk.Entry(circ_frame, textvariable=self.circ_max_var, width=8).pack(side=tk.LEFT)
        
        ttk.Button(params_frame, text="Update Parameters", command=self.update_parameters).pack(fill=tk.X, pady=5)
        
        # Exposure adjustment
        exposure_frame = ttk.LabelFrame(control_frame, text="Exposure Adjustment")
        exposure_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(exposure_frame, text="Exposure Multiplier:").pack(anchor=tk.W)
        self.exposure_var = tk.DoubleVar(value=1.0)
        exposure_scale = ttk.Scale(
            exposure_frame, 
            from_=0.1, 
            to=3.0, 
            variable=self.exposure_var, 
            orient=tk.HORIZONTAL,
            command=self.on_exposure_change
        )
        exposure_scale.pack(fill=tk.X, padx=5, pady=2)
        
        # Exposure value display and controls
        exposure_control_frame = ttk.Frame(exposure_frame)
        exposure_control_frame.pack(fill=tk.X, pady=2)
        
        self.exposure_label = ttk.Label(exposure_control_frame, text="1.0x")
        self.exposure_label.pack(side=tk.LEFT)
        
        ttk.Button(exposure_control_frame, text="Reset", command=self.reset_exposure, width=8).pack(side=tk.RIGHT, padx=2)
        ttk.Button(exposure_control_frame, text="Auto", command=self.auto_exposure, width=8).pack(side=tk.RIGHT, padx=2)
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(control_frame, text="Zoom Controls")
        zoom_frame.pack(fill=tk.X, pady=5)
        
        zoom_buttons_frame = ttk.Frame(zoom_frame)
        zoom_buttons_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(zoom_buttons_frame, text="Zoom In", command=self.zoom_in, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_buttons_frame, text="Zoom Out", command=self.zoom_out, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_buttons_frame, text="Fit", command=self.zoom_fit, width=8).pack(side=tk.LEFT, padx=2)
        
        # Second row of zoom controls
        zoom_buttons_frame2 = ttk.Frame(zoom_frame)
        zoom_buttons_frame2.pack(fill=tk.X, pady=2)
        
        ttk.Button(zoom_buttons_frame2, text="Reset Pan", command=self.reset_pan, width=10).pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = ttk.Label(zoom_frame, text="Zoom: 100%")
        self.zoom_label.pack(pady=2)
        
        # Pan instructions
        pan_info = ttk.Label(zoom_frame, text="Right-click + drag to pan when zoomed", font=('Arial', 8))
        pan_info.pack(pady=2)
        
        # Cell information display
        info_frame = ttk.LabelFrame(control_frame, text="Cell Information")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.cell_info_var = tk.StringVar(value="No image loaded")
        cell_info_label = ttk.Label(info_frame, textvariable=self.cell_info_var, justify=tk.LEFT, wraplength=200)
        cell_info_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Please open a TIFF image")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def open_image(self):
        """Open and load a TIFF image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("TIFF files", "*.tif *.tiff"),
                ("All image files", "*.tif *.tiff *.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Debug: Print the file path to check encoding
                print(f"Selected file path: {file_path}")
                print(f"Path exists: {os.path.exists(file_path)}")
                print(f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'} bytes")
                
                # Load image using OpenCV with Unicode path support
                # Use numpy and cv2.imdecode to handle paths with Chinese characters
                try:
                    # Method 1: Try direct cv2.imread first
                    self.original_image = cv2.imread(file_path, cv2.IMREAD_COLOR)
                    
                    if self.original_image is None:
                        # Method 2: Use numpy fromfile for Unicode path support
                        print(f"Trying numpy fromfile method for path: {file_path}")
                        image_array = np.fromfile(file_path, dtype=np.uint8)
                        self.original_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    
                    if self.original_image is None:
                        # Method 3: Use PIL as fallback for better Unicode support
                        print(f"Trying PIL method for path: {file_path}")
                        from PIL import Image as PILImage
                        pil_image = PILImage.open(file_path)
                        # Convert PIL image to OpenCV format
                        if pil_image.mode == 'RGB':
                            self.original_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                        elif pil_image.mode == 'RGBA':
                            self.original_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)
                        elif pil_image.mode == 'L':
                            gray_array = np.array(pil_image)
                            self.original_image = cv2.cvtColor(gray_array, cv2.COLOR_GRAY2BGR)
                        else:
                            # Convert to RGB first, then to BGR
                            rgb_image = pil_image.convert('RGB')
                            self.original_image = cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)
                        
                    if self.original_image is None:
                        messagebox.showerror("Error", "Could not load the image file. Please check if the file is a valid image.")
                        return
                        
                except Exception as load_error:
                    print(f"Image loading error: {load_error}")
                    messagebox.showerror("Error", f"Could not load the image file: {str(load_error)}")
                    return
                
                self.image_path = file_path
                
                # Apply 2x2 downsampling to create the working image
                print(f"Original image size: {self.original_image.shape[:2]}")
                self.downsampled_image = downsample_2x2(self.original_image)
                print(f"Downsampled image size: {self.downsampled_image.shape[:2]}")
                
                # Reset exposure to default when loading new image
                self.exposure_var.set(1.0)
                self.exposure_value = 1.0
                self.exposure_label.config(text="1.0x")
                # Use downsampled image as the current working image
                self.current_image = self.downsampled_image.copy()
                
                # Clear previous ROI and detections
                self.clear_roi()
                
                # Display the image
                self.display_image()
                
                # Update status
                filename = os.path.basename(file_path)
                h, w = self.original_image.shape[:2]
                self.status_var.set(f"Loaded: {filename} ({w}x{h})")
                self.cell_info_var.set(f"Image loaded: {w}x{h} pixels\nDraw ROI to detect cells")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def display_image(self):
        """Display the current image on the canvas"""
        if self.current_image is None:
            return
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Use default canvas size if not yet rendered
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 600
        
        # Convert BGR to RGB for display
        image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        
        # Calculate scaling to fit canvas while maintaining aspect ratio
        h, w = image_rgb.shape[:2]
        scale_x = canvas_width / w
        scale_y = canvas_height / h
        base_scale = min(scale_x, scale_y)  # Base scale to fit entirely
        
        # Apply zoom level to the base scale
        scale = base_scale * self.zoom_level
        
        # Calculate new dimensions
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Resize image to fit canvas
        image_resized = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # Convert to PhotoImage for display
        img = Image.fromarray(image_resized)
        photo = ImageTk.PhotoImage(image=img)
        
        # Clear canvas and center the image with pan offset
        self.canvas.delete("all")
        base_x_offset = (canvas_width - new_width) // 2
        base_y_offset = (canvas_height - new_height) // 2
        
        # Apply pan offset
        x_offset = base_x_offset + self.pan_offset_x
        y_offset = base_y_offset + self.pan_offset_y
        
        self.canvas.create_image(x_offset, y_offset, image=photo, anchor=tk.NW)
        self.canvas.image = photo  # Keep a reference to prevent garbage collection
        
        # Store scaling factors for coordinate conversion
        self.display_scale = scale
        self.display_offset_x = x_offset
        self.display_offset_y = y_offset
        
        # Redraw ROI and cells if they exist (only if display parameters are stable)
        if hasattr(self, 'display_scale') and hasattr(self, 'display_offset_x'):
            self.draw_persistent_roi()
            self.draw_cell_outlines()
    
    def on_mouse_down(self, event):
        """Handle mouse button press for ROI drawing"""
        if self.current_image is None:
            return
        
        # Don't start ROI drawing if currently panning
        if self.is_panning:
            return
        
        # Convert display coordinates to image coordinates
        image_x, image_y = self.display_to_image_coords(event.x, event.y)
        if image_x is None:
            return
        
        # Clear previous rectangle
        self.canvas.delete("roi_rect")
        
        # Store start position and mark as ROI drawing
        self.rect_start = (image_x, image_y)
        self.rect_end = (image_x, image_y)
        self.roi_drawing = True
    
    def on_mouse_move(self, event):
        """Handle mouse movement for ROI drawing"""
        if not self.rect_start or self.current_image is None or not self.roi_drawing:
            return
        
        # Don't draw ROI if panning
        if self.is_panning:
            return
        
        # Convert display coordinates to image coordinates
        image_x, image_y = self.display_to_image_coords(event.x, event.y)
        if image_x is None:
            return
        
        # Update end position
        self.rect_end = (image_x, image_y)
        
        # Draw rectangle preview
        self.draw_roi_rectangle()
    
    def on_mouse_up(self, event):
        """Handle mouse button release for ROI drawing"""
        if not self.rect_start or self.current_image is None or not self.roi_drawing:
            return
        
        # Convert display coordinates to image coordinates
        image_x, image_y = self.display_to_image_coords(event.x, event.y)
        if image_x is None:
            return
        
        # Update end position
        self.rect_end = (image_x, image_y)
        
        # Finalize ROI rectangle
        self.finalize_roi_rectangle()
        
        # End ROI drawing
        self.roi_drawing = False
    
    def display_to_image_coords(self, display_x, display_y):
        """Convert display coordinates to image coordinates"""
        if not hasattr(self, 'display_scale'):
            return None, None
        
        # Account for offset and scaling
        image_x = (display_x - self.display_offset_x) / self.display_scale
        image_y = (display_y - self.display_offset_y) / self.display_scale
        
        # Clamp to image bounds
        h, w = self.current_image.shape[:2]
        image_x = max(0, min(image_x, w - 1))
        image_y = max(0, min(image_y, h - 1))
        
        return int(image_x), int(image_y)
    
    def image_to_display_coords(self, image_x, image_y):
        """Convert image coordinates to display coordinates"""
        if not hasattr(self, 'display_scale'):
            return None, None
        
        display_x = int(image_x * self.display_scale + self.display_offset_x)
        display_y = int(image_y * self.display_scale + self.display_offset_y)
        
        return display_x, display_y
    
    def on_pan_start(self, event):
        """Handle right mouse button press for panning"""
        if self.current_image is None:
            return
        
        self.is_panning = True
        self.last_pan_x = event.x
        self.last_pan_y = event.y
        self.canvas.config(cursor="hand2")  # Change cursor to indicate panning
    
    def on_pan_move(self, event):
        """Handle mouse movement during panning"""
        if not self.is_panning or self.current_image is None:
            return
        
        # Calculate pan delta
        delta_x = event.x - self.last_pan_x
        delta_y = event.y - self.last_pan_y
        
        # Update pan offset
        self.pan_offset_x += delta_x
        self.pan_offset_y += delta_y
        
        # Update last position
        self.last_pan_x = event.x
        self.last_pan_y = event.y
        
        # Redraw image with new pan offset
        self.display_image()
    
    def on_pan_end(self, event):
        """Handle right mouse button release for panning"""
        self.is_panning = False
        self.canvas.config(cursor="")  # Reset cursor
    
    def reset_pan(self):
        """Reset pan offset to center"""
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        if self.current_image is not None:
            self.display_image()
    
    def draw_roi_rectangle(self):
        """Draw ROI rectangle preview on canvas"""
        if not self.rect_start or not self.rect_end:
            return
        
        # Clear previous rectangle
        self.canvas.delete("roi_rect")
        
        # Convert image coordinates to display coordinates
        x1_display, y1_display = self.image_to_display_coords(*self.rect_start)
        x2_display, y2_display = self.image_to_display_coords(*self.rect_end)
        
        if x1_display is None or x2_display is None:
            return
        
        # Ensure proper rectangle coordinates
        left = min(x1_display, x2_display)
        top = min(y1_display, y2_display)
        right = max(x1_display, x2_display)
        bottom = max(y1_display, y2_display)
        
        # Draw rectangle outline
        self.canvas.create_rectangle(
            left, top, right, bottom,
            outline='red',
            width=2,
            tags="roi_rect"
        )
    
    def finalize_roi_rectangle(self):
        """Finalize ROI rectangle and store it"""
        if not self.rect_start or not self.rect_end:
            return
        
        # Get image coordinates
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        
        # Ensure proper rectangle coordinates
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # Calculate width and height
        width = right - left
        height = bottom - top
        
        # Store ROI rectangle in image coordinates
        if width > 10 and height > 10:  # Minimum size check
            self.rect = (left, top, width, height)
            self.status_var.set(f"ROI set: {width}x{height} at ({left}, {top})")
            print(f"ROI finalized: x={left}, y={top}, w={width}, h={height}")
        else:
            self.status_var.set("ROI too small, please draw a larger area")
            self.canvas.delete("roi_rect")
    
    def draw_persistent_roi(self):
        """Draw persistent ROI rectangle on canvas"""
        if not self.rect:
            return
        
        # Check if display parameters are available
        if not hasattr(self, 'display_scale') or not hasattr(self, 'display_offset_x'):
            print("Warning: Display parameters not available for ROI drawing")
            return
        
        # Clear previous ROI drawings
        self.canvas.delete("persistent_roi")
        
        x, y, w, h = self.rect
        
        # Convert to display coordinates
        x1_display, y1_display = self.image_to_display_coords(x, y)
        x2_display, y2_display = self.image_to_display_coords(x + w, y + h)
        
        if x1_display is None or x2_display is None:
            return
        
        # Draw ROI rectangle outline
        self.canvas.create_rectangle(
            x1_display, y1_display, x2_display, y2_display,
            outline='red',
            width=2,
            tags="persistent_roi"
        )
        
        # Add ROI label with corner positions
        roi_info = f"ROI: {w}x{h}\nTL:({x},{y}) BR:({x+w},{y+h})"
        self.canvas.create_text(
            x1_display + 5, y1_display - 25,
            text=roi_info,
            fill='red',
            font=('Arial', 8, 'bold'),
            anchor=tk.NW,
            tags="persistent_roi"
        )
    
    def detect_cells(self):
        """Detect cells in the current ROI"""
        if not self.rect:
            messagebox.showwarning("No ROI", "Please draw a ROI first")
            return
        
        if self.current_image is None:
            messagebox.showwarning("No Image", "Please load an image first")
            return
        
        try:
            self.status_var.set("Detecting cells...")
            
            # Store current display parameters to prevent displacement
            current_scale = getattr(self, 'display_scale', None)
            current_offset_x = getattr(self, 'display_offset_x', None)
            current_offset_y = getattr(self, 'display_offset_y', None)
            
            # Run cell detection
            self.detected_cells = detect_cells_in_roi(self.current_image, self.rect, self.detection_params)
            
            # Restore display parameters if they were changed
            if current_scale is not None:
                self.display_scale = current_scale
            if current_offset_x is not None:
                self.display_offset_x = current_offset_x
            if current_offset_y is not None:
                self.display_offset_y = current_offset_y
            
            # Update display without triggering a full redraw
            self.draw_cell_outlines()
            self.draw_persistent_roi()  # Redraw ROI to ensure it's in the correct position
            self.update_cell_info()
            
            # Update status
            self.status_var.set(f"Detected {len(self.detected_cells)} cells")
            
        except Exception as e:
            messagebox.showerror("Detection Error", f"Failed to detect cells: {str(e)}")
            self.status_var.set("Cell detection failed")
    
    def draw_cell_outlines(self):
        """Draw outline boxes for detected cells on the canvas"""
        # Clear previous cell outlines
        self.canvas.delete("cell_outline")
        self.canvas.delete("cell_center")
        self.canvas.delete("cell_label")
        
        if not self.detected_cells:
            return
        
        # Check if display parameters are available
        if not hasattr(self, 'display_scale') or not hasattr(self, 'display_offset_x'):
            print("Warning: Display parameters not available for cell outline drawing")
            return
        
        try:
            # Draw outline boxes for each detected cell
            for i, cell in enumerate(self.detected_cells):
                center = cell.center
                radius = cell.radius
                
                # Convert cell coordinates to display coordinates
                display_x, display_y = self.image_to_display_coords(center[0], center[1])
                if display_x is None:
                    continue
                
                display_radius = int(radius * self.display_scale)
                
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
    
    def update_cell_info(self):
        """Update the cell information display"""
        if not self.detected_cells:
            self.cell_info_var.set("No cells detected")
            return
        
        cell_info = f"Detected Cells: {len(self.detected_cells)}\n\n"
        for i, cell in enumerate(self.detected_cells):
            cell_info += f"Cell {i+1}:\n"
            cell_info += f"  Center: ({cell.center[0]:.1f}, {cell.center[1]:.1f})\n"
            cell_info += f"  Radius: {cell.radius:.1f} px\n"
            if cell.bbox:
                cell_info += f"  BBox: {cell.bbox}\n"
            cell_info += "\n"
        
        self.cell_info_var.set(cell_info)
    
    def on_exposure_change(self, value):
        """Handle exposure slider change"""
        try:
            self.exposure_value = float(value)
            self.exposure_label.config(text=f"{self.exposure_value:.1f}x")
            
            # Apply exposure adjustment and update display
            if self.original_image is not None:
                self.apply_exposure_adjustment()
                self.display_image()
                
        except Exception as e:
            print(f"Error adjusting exposure: {e}")
    
    def apply_exposure_adjustment(self):
        """Apply exposure adjustment to the current image"""
        if self.downsampled_image is None:
            return
        
        try:
            # Apply exposure multiplier to downsampled image
            if self.exposure_value == 1.0:
                # No adjustment needed
                self.current_image = self.downsampled_image.copy()
            else:
                # Convert to float for processing
                float_image = self.downsampled_image.astype(np.float32)
                
                # Apply exposure multiplier
                adjusted_image = float_image * self.exposure_value
                
                # Clip values to valid range and convert back to uint8
                adjusted_image = np.clip(adjusted_image, 0, 255)
                self.current_image = adjusted_image.astype(np.uint8)
                
        except Exception as e:
            print(f"Error applying exposure adjustment: {e}")
            self.current_image = self.downsampled_image.copy()
    
    def reset_exposure(self):
        """Reset exposure to default value"""
        self.exposure_var.set(1.0)
        self.exposure_value = 1.0
        self.exposure_label.config(text="1.0x")
        
        if self.downsampled_image is not None:
            self.current_image = self.downsampled_image.copy()
            self.display_image()
    
    def auto_exposure(self):
        """Automatically adjust exposure based on image histogram"""
        if self.downsampled_image is None:
            messagebox.showwarning("No Image", "Please load an image first")
            return
        
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(self.downsampled_image, cv2.COLOR_BGR2GRAY)
            
            # Calculate mean brightness
            mean_brightness = np.mean(gray)
            
            # Target brightness (around 128 for good visibility)
            target_brightness = 128
            
            # Calculate exposure multiplier
            if mean_brightness > 0:
                auto_exposure = target_brightness / mean_brightness
                # Limit the adjustment range
                auto_exposure = np.clip(auto_exposure, 0.1, 3.0)
                
                self.exposure_var.set(auto_exposure)
                self.exposure_value = auto_exposure
                self.exposure_label.config(text=f"{auto_exposure:.1f}x")
                
                self.apply_exposure_adjustment()
                self.display_image()
                
                self.status_var.set(f"Auto exposure applied: {auto_exposure:.1f}x")
            else:
                messagebox.showwarning("Auto Exposure", "Cannot calculate auto exposure for this image")
                
        except Exception as e:
            messagebox.showerror("Auto Exposure Error", f"Failed to apply auto exposure: {str(e)}")
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom"""
        if self.current_image is None:
            return
        
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:  # Zoom in
            zoom_factor = 1.1
        else:  # Zoom out
            zoom_factor = 0.9
        
        # Apply zoom
        new_zoom = self.zoom_level * zoom_factor
        new_zoom = max(self.min_zoom, min(new_zoom, self.max_zoom))
        
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self.update_zoom_display()
            self.display_image()
    
    def zoom_in(self):
        """Zoom in by 20%"""
        new_zoom = self.zoom_level * 1.2
        new_zoom = min(new_zoom, self.max_zoom)
        
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self.update_zoom_display()
            self.display_image()
    
    def zoom_out(self):
        """Zoom out by 20%"""
        new_zoom = self.zoom_level * 0.8
        new_zoom = max(new_zoom, self.min_zoom)
        
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self.update_zoom_display()
            self.display_image()
    
    def zoom_fit(self):
        """Reset zoom to fit image in canvas and reset pan"""
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.update_zoom_display()
        self.display_image()
    
    def update_zoom_display(self):
        """Update zoom level display"""
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_label.config(text=f"Zoom: {zoom_percent}%")
    
    def map_back_to_original(self):
        """Map detected cells back to original image coordinates and display in new window"""
        if not self.detected_cells:
            messagebox.showwarning("No Cells", "No cells detected to map back")
            return
        
        if self.original_image is None:
            messagebox.showwarning("No Original Image", "Original image not available")
            return
        
        try:
            # Create new window for original image display
            map_window = tk.Toplevel(self.root)
            map_window.title("Original Image with Mapped Cells")
            map_window.geometry("1000x800")
            
            # Create frame for controls and canvas
            control_frame = ttk.Frame(map_window)
            control_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Add zoom controls for map window
            ttk.Button(control_frame, text="Zoom In", command=lambda: self.map_zoom(map_canvas, 1.2)).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="Zoom Out", command=lambda: self.map_zoom(map_canvas, 0.8)).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="Fit", command=lambda: self.map_zoom_fit(map_canvas)).pack(side=tk.LEFT, padx=2)
            
            map_zoom_label = ttk.Label(control_frame, text="Zoom: 100%")
            map_zoom_label.pack(side=tk.LEFT, padx=10)
            
            # Create canvas for original image
            map_canvas = tk.Canvas(map_window, bg="gray")
            map_canvas.pack(fill=tk.BOTH, expand=True)
            
            # Store zoom data for this window
            map_canvas.zoom_level = 1.0
            map_canvas.zoom_label = map_zoom_label
            map_canvas.original_image = self.original_image
            map_canvas.detected_cells = self.detected_cells
            map_canvas.scale_factor = self.scale_factor
            
            # Bind mouse wheel for zooming in map window
            map_canvas.bind("<MouseWheel>", lambda e: self.map_mouse_wheel(e, map_canvas))
            map_canvas.bind("<Button-4>", lambda e: self.map_mouse_wheel(e, map_canvas))  # Linux
            map_canvas.bind("<Button-5>", lambda e: self.map_mouse_wheel(e, map_canvas))  # Linux
            
            # Initial display of the map window
            self.draw_map_window(map_canvas)
            
            self.status_var.set(f"Mapped {len(self.detected_cells)} cells to original image")
            
        except Exception as e:
            messagebox.showerror("Mapping Error", f"Failed to map cells to original image: {str(e)}")
    
    def draw_map_window(self, map_canvas):
        """Draw the original image with mapped cells in the map window"""
        try:
            # Display original image
            original_rgb = cv2.cvtColor(map_canvas.original_image, cv2.COLOR_BGR2RGB)
            
            # Calculate scaling to fit window
            canvas_width = map_canvas.winfo_width() or 950
            canvas_height = map_canvas.winfo_height() or 750
            h, w = original_rgb.shape[:2]
            scale_x = canvas_width / w
            scale_y = canvas_height / h
            base_scale = min(scale_x, scale_y)
            
            # Apply zoom level
            scale = base_scale * map_canvas.zoom_level
            
            new_width = int(w * scale)
            new_height = int(h * scale)
            
            # Resize and display original image
            image_resized = cv2.resize(original_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            img = Image.fromarray(image_resized)
            photo = ImageTk.PhotoImage(image=img)
            
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            
            # Clear canvas and display image
            map_canvas.delete("all")
            map_canvas.create_image(x_offset, y_offset, image=photo, anchor=tk.NW)
            map_canvas.image = photo  # Keep reference
            
            # Map cells back to original coordinates and draw them
            for i, cell in enumerate(map_canvas.detected_cells):
                # Map from downsampled coordinates to original coordinates
                orig_center_x = cell.center[0] * map_canvas.scale_factor
                orig_center_y = cell.center[1] * map_canvas.scale_factor
                orig_radius = cell.radius * map_canvas.scale_factor
                
                # Convert to display coordinates
                display_x = int(orig_center_x * scale + x_offset)
                display_y = int(orig_center_y * scale + y_offset)
                display_radius = int(orig_radius * scale)
                
                # Draw cell outline on original image
                x1 = display_x - display_radius
                y1 = display_y - display_radius
                x2 = display_x + display_radius
                y2 = display_y + display_radius
                
                # Draw green outline rectangle
                map_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='lime',
                    width=3,
                    tags="mapped_cell"
                )
                
                # Draw center point
                center_size = 4
                map_canvas.create_oval(
                    display_x - center_size, display_y - center_size,
                    display_x + center_size, display_y + center_size,
                    fill='red',
                    outline='red',
                    tags="mapped_center"
                )
                
                # Draw cell ID label
                map_canvas.create_text(
                    display_x, y1 - 15,
                    text=f"Cell {i+1}",
                    fill='yellow',
                    font=('Arial', 10, 'bold'),
                    tags="mapped_label"
                )
            
            # Add info label
            info_text = f"Original Image: {w}x{h}\nMapped {len(map_canvas.detected_cells)} cells\nZoom: {int(map_canvas.zoom_level * 100)}%"
            map_canvas.create_text(
                10, 10,
                text=info_text,
                fill='white',
                font=('Arial', 10, 'bold'),
                anchor=tk.NW,
                tags="info_label"
            )
            
        except Exception as e:
            print(f"Error drawing map window: {str(e)}")
    
    def map_mouse_wheel(self, event, map_canvas):
        """Handle mouse wheel zoom in map window"""
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:  # Zoom in
            zoom_factor = 1.1
        else:  # Zoom out
            zoom_factor = 0.9
        
        # Apply zoom
        new_zoom = map_canvas.zoom_level * zoom_factor
        new_zoom = max(0.1, min(new_zoom, 5.0))  # Limit zoom range
        
        if new_zoom != map_canvas.zoom_level:
            map_canvas.zoom_level = new_zoom
            zoom_percent = int(map_canvas.zoom_level * 100)
            map_canvas.zoom_label.config(text=f"Zoom: {zoom_percent}%")
            self.draw_map_window(map_canvas)
    
    def map_zoom(self, map_canvas, factor):
        """Zoom map window by factor"""
        new_zoom = map_canvas.zoom_level * factor
        new_zoom = max(0.1, min(new_zoom, 5.0))  # Limit zoom range
        
        if new_zoom != map_canvas.zoom_level:
            map_canvas.zoom_level = new_zoom
            zoom_percent = int(map_canvas.zoom_level * 100)
            map_canvas.zoom_label.config(text=f"Zoom: {zoom_percent}%")
            self.draw_map_window(map_canvas)
    
    def map_zoom_fit(self, map_canvas):
        """Reset map window zoom to fit"""
        map_canvas.zoom_level = 1.0
        map_canvas.zoom_label.config(text="Zoom: 100%")
        self.draw_map_window(map_canvas)
    
    def update_parameters(self):
        """Update detection parameters from UI"""
        try:
            area_min = int(self.area_min_var.get())
            area_max = int(self.area_max_var.get())
            circ_min = float(self.circ_min_var.get())
            circ_max = float(self.circ_max_var.get())
            
            self.detection_params = {
                'area': (area_min, area_max),
                'perimeter': (30, 1000),  # Keep default perimeter range
                'circularity': (circ_min, circ_max)
            }
            
            self.status_var.set("Parameters updated")
            
        except ValueError:
            messagebox.showerror("Invalid Parameters", "Please enter valid numeric values")
    
    def clear_roi(self):
        """Clear the current ROI and detected cells"""
        self.rect = None
        self.rect_start = None
        self.rect_end = None
        self.detected_cells = []
        
        # Clear canvas elements
        self.canvas.delete("roi_rect")
        self.canvas.delete("persistent_roi")
        self.canvas.delete("cell_outline")
        self.canvas.delete("cell_center")
        self.canvas.delete("cell_label")
        
        self.status_var.set("ROI cleared")
        if self.current_image is not None:
            self.cell_info_var.set("ROI cleared\nDraw new ROI to detect cells")
    
    def save_results(self):
        """Save detection results to a JSON file"""
        if not self.detected_cells:
            messagebox.showinfo("No Results", "No cells detected to save")
            return
        
        if not self.image_path:
            messagebox.showwarning("No Image", "No image loaded")
            return
        
        # Generate filename based on image name
        base_name = os.path.splitext(os.path.basename(self.image_path))[0]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_cells_{timestamp}.json"
        
        file_path = filedialog.asksaveasfilename(
            title="Save Cell Detection Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialvalue=filename
        )
        
        if file_path:
            try:
                # Prepare data for saving
                results = {
                    "image_path": self.image_path,
                    "image_size": self.original_image.shape[:2][::-1],  # (width, height)
                    "roi": self.rect,
                    "detection_parameters": self.detection_params,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "cells": [cell.to_dict() for cell in self.detected_cells]
                }
                
                # Save to file
                with open(file_path, 'w') as f:
                    json.dump(results, f, indent=2)
                
                self.status_var.set(f"Results saved: {os.path.basename(file_path)}")
                messagebox.showinfo("Saved", f"Results saved to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save results: {str(e)}")
    
    def on_close(self):
        """Handle window close event"""
        if self.owns_root:
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        if self.owns_root:
            self.root.mainloop()

def main():
    """Main function to start the application"""
    try:
        app = IntensityMeasureApp()
        app.run()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()