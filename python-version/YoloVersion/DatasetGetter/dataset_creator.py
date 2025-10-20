"""
YOLO Dataset Creator from JPG Images
Creates training datasets by detecting cells in JPG images with ROI selection.
Each detected cell is cropped with background margin for YOLO training.
"""

import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from skimage import filters, morphology, measure
import json
from datetime import datetime
import multiprocessing as mp
from functools import partial


class DetectedCell:
    """Class to store information about a detected cell"""
    def __init__(self, center, radius, contour=None, bbox=None):
        self.center = center  # (x, y) tuple
        self.radius = radius  # estimated radius
        self.contour = contour  # OpenCV contour points
        self.bbox = bbox  # Bounding box (x, y, w, h)


def process_single_image_for_batch(args):
    """
    Process a single image for batch processing (used by multiprocessing).
    
    Args:
        args: Tuple of (img_path, output_dir, params_dict)
    
    Returns:
        Tuple of (success, img_file, num_cells, error_msg)
    """
    img_path, output_dir, params_dict = args
    img_file = os.path.basename(img_path)
    
    # Note: On Windows, multiprocessing may still show all cores active in Task Manager
    # because Python spawns processes differently. The Pool(processes=N) limits
    # concurrent workers, but individual processes may briefly use any available core.
    
    try:
        # Extract parameters
        min_size = params_dict['min_size']
        max_size = params_dict['max_size']
        expansion_percent = params_dict['expansion_percent']
        detection_params = params_dict['detection_params']
        
        # Load image
        image = cv2.imread(img_path)
        if image is None:
            return (False, img_file, 0, "Failed to load image")
        
        # Detect cells in whole image
        h, w = image.shape[:2]
        roi = (0, 0, w, h)
        all_cells = detect_cells_in_roi(image, roi, detection_params)
        
        # Apply size filter
        filtered_cells = []
        for cell in all_cells:
            bx, by, bw, bh = cell.bbox
            if min_size <= bw <= max_size and min_size <= bh <= max_size:
                filtered_cells.append(cell)
        
        # Generate YOLO labels
        expansion_ratio = expansion_percent / 100.0
        yolo_labels = []
        
        for cell in filtered_cells:
            bx, by, bw, bh = cell.bbox
            
            # Expand bbox
            expansion_w = int(bw * expansion_ratio)
            expansion_h = int(bh * expansion_ratio)
            
            expanded_x = max(0, bx - expansion_w)
            expanded_y = max(0, by - expansion_h)
            expanded_w = min(w - expanded_x, bw + 2*expansion_w)
            expanded_h = min(h - expanded_y, bh + 2*expansion_h)
            
            # YOLO format (normalized)
            center_x = (expanded_x + expanded_w / 2) / w
            center_y = (expanded_y + expanded_h / 2) / h
            norm_width = expanded_w / w
            norm_height = expanded_h / h
            
            yolo_labels.append(f"0 {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}")
        
        # Save files
        img_name = os.path.splitext(img_file)[0]
        
        # Copy image
        import shutil
        shutil.copy(img_path, os.path.join(output_dir, img_file))
        
        # Save label
        label_path = os.path.join(output_dir, f"{img_name}.txt")
        with open(label_path, 'w') as f:
            f.write('\n'.join(yolo_labels))
        
        # Create annotated visualization
        vis_image = image.copy()
        for cell in filtered_cells:
            bx, by, bw, bh = cell.bbox
            expansion_w = int(bw * expansion_ratio)
            expansion_h = int(bh * expansion_ratio)
            expanded_x = max(0, bx - expansion_w)
            expanded_y = max(0, by - expansion_h)
            expanded_w = min(w - expanded_x, bw + 2*expansion_w)
            expanded_h = min(h - expanded_y, bh + 2*expansion_h)
            
            # Draw expanded bbox (green)
            cv2.rectangle(vis_image, (expanded_x, expanded_y), 
                         (expanded_x + expanded_w, expanded_y + expanded_h), 
                         (0, 255, 0), 2)
            # Draw center point (red)
            center_x_px = int(expanded_x + expanded_w / 2)
            center_y_px = int(expanded_y + expanded_h / 2)
            cv2.circle(vis_image, (center_x_px, center_y_px), 3, (0, 0, 255), -1)
        
        # Save annotated image
        vis_filename = f"{img_name}_annotated.jpg"
        vis_path = os.path.join(output_dir, vis_filename)
        cv2.imwrite(vis_path, vis_image)
        
        return (True, img_file, len(filtered_cells), None)
        
    except Exception as e:
        return (False, img_file, 0, str(e))


def detect_cells_in_roi(image, roi_rect, params=None):
    """
    Detect cells within the specified region of interest using Kirsch edge detection.
    
    Args:
        image: Input image (BGR format)
        roi_rect: Rectangle defining the ROI (x, y, width, height)
        params: Optional parameters for cell detection
        
    Returns:
        List of DetectedCell objects
    """
    if roi_rect is None or roi_rect[2] <= 0 or roi_rect[3] <= 0:
        return []
    
    if params is None:
        params = {
            'area': (100, 5000),
            'perimeter': (30, 1000),
            'circularity': (0.2, 1.0)
        }
    
    # Extract ROI
    x, y, w, h = roi_rect
    roi = image[y:y+h, x:x+w]
    
    if roi.size == 0:
        return []
    
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # CLAHE enhancement
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(10, 10))
    enhanced = clahe.apply(gray)
    
    # Gaussian blur
    float_img = enhanced.astype(np.float32) / 255.0
    denoised = cv2.GaussianBlur(float_img, (3, 3), 2)
    
    # Kirsch edge detection
    kirsch_kernels = [
        np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float32),
        np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float32),
        np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float32),
        np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float32)
    ]
    
    binary = np.zeros(denoised.shape, dtype=bool)
    for kernel in kirsch_kernels:
        filtered = cv2.filter2D(denoised, -1, kernel)
        filtered = np.abs(filtered)
        filtered_min, filtered_max = np.min(filtered), np.max(filtered)
        if filtered_max > filtered_min:
            filtered_norm = (filtered - filtered_min) / (filtered_max - filtered_min)
            binary |= filtered_norm > filters.threshold_otsu(filtered_norm)
    
    binary = binary.astype(np.uint8) * 255
    
    # Morphological processing
    binary = morphology.remove_small_objects(binary.astype(bool), min_size=100)
    binary = morphology.thin(binary, max_num_iter=1)
    binary = morphology.remove_small_holes(binary.astype(bool), area_threshold=100)
    binary = binary.astype(np.uint8) * 255
    
    # Eccentricity filtering
    labeled = measure.label(binary)
    props = measure.regionprops(labeled)
    mask = np.zeros_like(binary, dtype=bool)
    for prop in props:
        if (prop.eccentricity < 0.99 and prop.area > 100) or (prop.area > 300):
            mask[labeled == prop.label] = True
    binary = mask.astype(np.uint8) * 255
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Process contours
    detected_cells = []
    area_min, area_max = params['area']
    perimeter_min, perimeter_max = params['perimeter']
    circularity_min, circularity_max = params['circularity']
    
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        if (area_min <= area <= area_max and
            perimeter_min <= perimeter <= perimeter_max and
            circularity_min <= circularity <= circularity_max):
            
            bx, by, bw, bh = cv2.boundingRect(contour)
            moments = cv2.moments(contour)
            if moments["m00"] != 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
            else:
                cx = bx + bw // 2
                cy = by + bh // 2
            
            radius = (bw + bh) / 4
            
            # Adjust to original frame coordinates
            cx += x
            cy += y
            bx += x
            by += y
            
            cell = DetectedCell((cx, cy), radius, contour, (bx, by, bw, bh))
            detected_cells.append(cell)
    
    return detected_cells


class DatasetCreatorApp:
    """Main application for creating YOLO training datasets"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Dataset Creator - Cell Detection")
        self.root.geometry("1200x800")
        
        # Variables
        self.image = None
        self.image_path = None
        self.display_image = None
        self.roi_rect = None
        self.roi_start = None
        self.roi_end = None
        self.detected_cells = []
        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.margin_ratio = 0.3  # 30% margin around cell
        
        # Detection parameters
        self.params = {
            'area': (100, 5000),
            'perimeter': (30, 1000),
            'circularity': (0.2, 1.0)
        }
        
        # Output directory
        self.output_dir = os.path.join(os.path.dirname(__file__), 'saved')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Image navigation
        self.current_folder = None
        self.folder_images = []
        self.current_image_index = -1
        
        # Manual labeling mode
        self.manual_mode = False
        self.manual_boxes = []  # List of (x, y, w, h) bounding boxes
        self.drawing_box = False
        self.box_start = None
        self.selected_box_index = -1
        self.selected_cell_index = -1
        
        # Zoom functionality
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        
        self.create_ui()
    
    def create_ui(self):
        """Create the application UI"""
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - controls
        control_frame = ttk.Frame(main_frame, width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Right panel - image display
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for image
        self.canvas = tk.Canvas(display_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Mouse wheel zoom
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down
        
        # Keyboard shortcuts
        self.root.bind("<s>", lambda e: self.save_yolo_labels())
        self.root.bind("<S>", lambda e: self.save_yolo_labels())
        self.root.bind("<r>", lambda e: self.detect_cells_whole_image())  # R = detect cells
        self.root.bind("<R>", lambda e: self.detect_cells_whole_image())
        self.root.bind("<Right>", lambda e: self.load_next_image())
        self.root.bind("<Left>", lambda e: self.load_previous_image())
        self.root.bind("<d>", lambda e: self.load_next_image())  # D = next image
        self.root.bind("<D>", lambda e: self.load_next_image())
        self.root.bind("<a>", lambda e: self.load_previous_image())
        self.root.bind("<A>", lambda e: self.load_previous_image())
        self.root.bind("<Delete>", lambda e: self.delete_selected_box())  # Delete = delete box
        self.root.bind("<m>", lambda e: self.toggle_manual_mode())
        self.root.bind("<M>", lambda e: self.toggle_manual_mode())
        self.root.bind("<plus>", lambda e: self.zoom_in())
        self.root.bind("<equal>", lambda e: self.zoom_in())  # + without shift
        self.root.bind("<minus>", lambda e: self.zoom_out())
        self.root.bind("<0>", lambda e: self.reset_zoom())  # Reset to 100%
        
        # Control buttons
        ttk.Label(control_frame, text="YOLO Dataset Creator", font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Button(control_frame, text="Load Image", command=self.load_image).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Detect Cells (ROI)", command=self.detect_cells).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Detect Cells (Whole Image)", command=self.detect_cells_whole_image).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Save YOLO Labels", command=self.save_yolo_labels).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Manual labeling controls
        self.manual_mode_btn = ttk.Button(control_frame, text="Manual Mode: OFF", command=self.toggle_manual_mode)
        self.manual_mode_btn.pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Clear All Labels", command=self.clear_all_labels).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Batch Process Folder", command=self.batch_process_folder).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Clear ROI", command=self.clear_roi).pack(fill=tk.X, pady=5)
        
        # Parameters
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(control_frame, text="Detection Parameters", font=('Arial', 10, 'bold')).pack()
        
        # Bounding box expansion ratio
        ttk.Label(control_frame, text="BBox Expansion (%):").pack(anchor=tk.W, padx=5, pady=(10,0))
        self.margin_var = tk.StringVar(value="10")
        margin_frame = ttk.Frame(control_frame)
        margin_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Entry(margin_frame, textvariable=self.margin_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(margin_frame, text="(0-50)").pack(side=tk.LEFT)
        
        # Size filter
        ttk.Label(control_frame, text="Min Cell Size (pixels):").pack(anchor=tk.W, padx=5, pady=(10,0))
        self.min_size_var = tk.StringVar(value="20")
        min_size_frame = ttk.Frame(control_frame)
        min_size_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Entry(min_size_frame, textvariable=self.min_size_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(min_size_frame, text="bbox width/height").pack(side=tk.LEFT)
        
        ttk.Label(control_frame, text="Max Cell Size (pixels):").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.max_size_var = tk.StringVar(value="200")
        max_size_frame = ttk.Frame(control_frame)
        max_size_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Entry(max_size_frame, textvariable=self.max_size_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(max_size_frame, text="bbox width/height").pack(side=tk.LEFT)
        
        # Info display
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(control_frame, text="Information", font=('Arial', 10, 'bold')).pack()
        
        self.info_text = tk.Text(control_frame, height=15, width=30, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Load an image to start")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_image(self):
        """Load a JPG image"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.image = cv2.imread(file_path)
        if self.image is None:
            messagebox.showerror("Error", "Failed to load image")
            return
        
        self.image_path = file_path
        self.roi_rect = None
        self.detected_cells = []
        
        # Update folder navigation
        folder = os.path.dirname(file_path)
        if folder != self.current_folder:
            self.current_folder = folder
            self.folder_images = sorted([f for f in os.listdir(folder) 
                                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        
        # Find current image index
        filename = os.path.basename(file_path)
        if filename in self.folder_images:
            self.current_image_index = self.folder_images.index(filename)
        
        self.update_display()
        nav_info = f"[{self.current_image_index + 1}/{len(self.folder_images)}]" if self.folder_images else ""
        self.status_var.set(f"Loaded: {os.path.basename(file_path)} {nav_info}")
        self.update_info(f"Image loaded {nav_info}. Draw ROI to detect cells.")
    
    def update_display(self):
        """Update the canvas with current image"""
        if self.image is None:
            return
        
        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 600
        
        # Calculate scaling with zoom
        h, w = self.image.shape[:2]
        scale_x = canvas_width / w
        scale_y = canvas_height / h
        scale = min(scale_x, scale_y) * self.zoom_level  # Apply zoom
        
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Create display image
        display_img = self.image.copy()
        
        # Draw ROI rectangle
        if self.roi_rect:
            x, y, rw, rh = self.roi_rect
            cv2.rectangle(display_img, (x, y), (x+rw, y+rh), (0, 255, 0), 2)
        
        # Draw detected cells
        for i, cell in enumerate(self.detected_cells):
            cx, cy = cell.center
            bx, by, bw, bh = cell.bbox
            
            # Highlight selected cell
            color = (255, 255, 0) if i == self.selected_cell_index else (255, 0, 0)  # Yellow if selected, blue otherwise
            thickness = 3 if i == self.selected_cell_index else 2
            
            # Draw bounding box
            cv2.rectangle(display_img, (bx, by), (bx+bw, by+bh), color, thickness)
            
            # Draw center
            cv2.circle(display_img, (int(cx), int(cy)), 3, (0, 0, 255), -1)
            
            # Draw label
            cv2.putText(display_img, f"Cell {i+1}", (bx, by-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Draw manual boxes
        for i, (bx, by, bw, bh) in enumerate(self.manual_boxes):
            # Highlight selected box
            color = (255, 255, 0) if i == self.selected_box_index else (0, 255, 255)  # Yellow if selected, cyan otherwise
            thickness = 3 if i == self.selected_box_index else 2
            cv2.rectangle(display_img, (bx, by), (bx+bw, by+bh), color, thickness)
            
            # Draw label
            cv2.putText(display_img, f"Box {i+1}", (bx, by-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Convert and resize
        display_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        display_img = cv2.resize(display_img, (new_width, new_height))
        
        # Convert to PhotoImage
        img = Image.fromarray(display_img)
        photo = ImageTk.PhotoImage(image=img)
        
        # Display
        self.canvas.delete("all")
        x_offset = (canvas_width - new_width) // 2
        y_offset = (canvas_height - new_height) // 2
        self.canvas.create_image(x_offset, y_offset, image=photo, anchor=tk.NW)
        self.canvas.image = photo
        
        # Store scaling factors
        self.display_scale = scale
        self.display_offset_x = x_offset
        self.display_offset_y = y_offset
    
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        if self.image is None:
            return
        
        # Convert display to image coordinates
        img_x = int((event.x - self.display_offset_x) / self.display_scale)
        img_y = int((event.y - self.display_offset_y) / self.display_scale)
        
        if self.manual_mode:
            # Manual mode: check if clicking on existing manual box
            self.selected_box_index = -1
            self.selected_cell_index = -1
            
            # Check manual boxes first
            for i, (bx, by, bw, bh) in enumerate(self.manual_boxes):
                if bx <= img_x <= bx + bw and by <= img_y <= by + bh:
                    self.selected_box_index = i
                    self.update_info(f"Selected manual box {i+1}. Press Delete to remove.")
                    self.update_display()
                    return
            
            # Check auto-detected cells
            for i, cell in enumerate(self.detected_cells):
                bx, by, bw, bh = cell.bbox
                if bx <= img_x <= bx + bw and by <= img_y <= by + bh:
                    self.selected_cell_index = i
                    self.update_info(f"Selected detected cell {i+1}. Press Delete to remove.")
                    self.update_display()
                    return
            
            # Start drawing new box
            self.drawing_box = True
            self.box_start = (img_x, img_y)
        else:
            # ROI mode
            self.roi_start = (img_x, img_y)
            self.roi_end = None
    
    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if self.image is None:
            return
        
        # Convert display to image coordinates
        img_x = int((event.x - self.display_offset_x) / self.display_scale)
        img_y = int((event.y - self.display_offset_y) / self.display_scale)
        
        if self.manual_mode and self.drawing_box and self.box_start:
            # Draw temporary box
            self.update_display()
            x1 = int(self.box_start[0] * self.display_scale) + self.display_offset_x
            y1 = int(self.box_start[1] * self.display_scale) + self.display_offset_y
            x2 = int(img_x * self.display_scale) + self.display_offset_x
            y2 = int(img_y * self.display_scale) + self.display_offset_y
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='cyan', width=2, tags='temp_box')
        elif not self.manual_mode and self.roi_start:
            # ROI mode
            self.roi_end = (img_x, img_y)
            self.update_display()
            
            # Draw temporary rectangle
            if self.roi_start and self.roi_end:
                x1 = int(self.roi_start[0] * self.display_scale) + self.display_offset_x
                y1 = int(self.roi_start[1] * self.display_scale) + self.display_offset_y
                x2 = int(self.roi_end[0] * self.display_scale) + self.display_offset_x
                y2 = int(self.roi_end[1] * self.display_scale) + self.display_offset_y
                self.canvas.create_rectangle(x1, y1, x2, y2, outline='yellow', width=2, tags='temp_roi')
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if self.image is None:
            return
        
        # Convert display to image coordinates
        img_x = int((event.x - self.display_offset_x) / self.display_scale)
        img_y = int((event.y - self.display_offset_y) / self.display_scale)
        
        if self.manual_mode and self.drawing_box and self.box_start:
            # Finish drawing manual box
            x1, y1 = self.box_start
            x2, y2 = img_x, img_y
            
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            # Clamp to image bounds
            img_h, img_w = self.image.shape[:2]
            x = max(0, min(x, img_w))
            y = max(0, min(y, img_h))
            w = min(w, img_w - x)
            h = min(h, img_h - y)
            
            # Add box if it's large enough
            if w > 10 and h > 10:
                self.manual_boxes.append((x, y, w, h))
                self.update_info(f"Added box {len(self.manual_boxes)}: {w}x{h} at ({x},{y})")
            
            self.drawing_box = False
            self.box_start = None
            self.update_display()
        elif not self.manual_mode and self.roi_start:
            # ROI mode
            self.roi_end = (img_x, img_y)
            
            # Calculate ROI rectangle
            x1, y1 = self.roi_start
            x2, y2 = self.roi_end
            
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            # Clamp to image bounds
            img_h, img_w = self.image.shape[:2]
            x = max(0, min(x, img_w))
            y = max(0, min(y, img_h))
            w = min(w, img_w - x)
            h = min(h, img_h - y)
            
            if w > 10 and h > 10:
                self.roi_rect = (x, y, w, h)
                self.update_info(f"ROI set: {w}x{h} at ({x}, {y})")
            
            self.roi_start = None
            self.roi_end = None
            self.update_display()
    
    def detect_cells(self):
        """Detect cells in the ROI"""
        if self.image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        if self.roi_rect is None:
            messagebox.showwarning("Warning", "Please draw an ROI first")
            return
        
        # Parse and validate size filter
        try:
            min_size = int(self.min_size_var.get())
            max_size = int(self.max_size_var.get())
            if min_size < 1 or max_size < min_size:
                messagebox.showerror("Error", "Invalid size filter. Min must be >= 1 and Max must be >= Min")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid size values. Please enter integers")
            return
        
        self.status_var.set("Detecting cells...")
        self.root.update()
        
        # Detect all cells
        all_cells = detect_cells_in_roi(self.image, self.roi_rect, self.params)
        
        # Apply size filter
        self.detected_cells = []
        filtered_count = 0
        for cell in all_cells:
            bx, by, bw, bh = cell.bbox
            # Filter by both width and height
            if min_size <= bw <= max_size and min_size <= bh <= max_size:
                self.detected_cells.append(cell)
            else:
                filtered_count += 1
        
        self.update_display()
        info_msg = f"Detected {len(self.detected_cells)} cells"
        if filtered_count > 0:
            info_msg += f" ({filtered_count} filtered by size)"
        self.update_info(info_msg)
        self.status_var.set(f"Detected {len(self.detected_cells)} cells")
    
    def save_yolo_labels(self):
        """Save YOLO format labels for detected cells and manual boxes"""
        if self.image is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return
        
        # Allow saving even with no detections (for manual labeling or empty labels)
        if not self.detected_cells and not self.manual_boxes:
            confirm = messagebox.askyesno("No Labels", 
                "No cells detected and no manual boxes drawn.\n\n"
                "Save empty label file?")
            if not confirm:
                return
        
        # Parse and validate expansion percentage
        try:
            expansion_percent = float(self.margin_var.get())
            if expansion_percent < 0 or expansion_percent > 50:
                messagebox.showerror("Error", "BBox expansion must be between 0 and 50")
                return
            expansion_ratio = expansion_percent / 100.0
        except ValueError:
            messagebox.showerror("Error", "Invalid expansion value. Please enter a number between 0 and 50")
            return
        
        img_name = os.path.splitext(os.path.basename(self.image_path))[0]
        
        # Save directly in output directory (no subfolder)
        session_dir = self.output_dir
        os.makedirs(session_dir, exist_ok=True)
        
        # Get image dimensions for normalization
        img_height, img_width = self.image.shape[:2]
        
        # Generate YOLO labels from detected cells
        yolo_labels = []
        for i, cell in enumerate(self.detected_cells):
            bx, by, bw, bh = cell.bbox
            
            # Expand bounding box
            expansion_w = int(bw * expansion_ratio)
            expansion_h = int(bh * expansion_ratio)
            
            expanded_x = max(0, bx - expansion_w)
            expanded_y = max(0, by - expansion_h)
            expanded_w = min(img_width - expanded_x, bw + 2*expansion_w)
            expanded_h = min(img_height - expanded_y, bh + 2*expansion_h)
            
            # Calculate YOLO format (normalized center_x, center_y, width, height)
            center_x = (expanded_x + expanded_w / 2) / img_width
            center_y = (expanded_y + expanded_h / 2) / img_height
            norm_width = expanded_w / img_width
            norm_height = expanded_h / img_height
            
            yolo_labels.append(f"0 {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}")
        
        # Add manual boxes to YOLO labels
        for i, (bx, by, bw, bh) in enumerate(self.manual_boxes):
            # Manual boxes already have correct dimensions, just apply expansion
            expansion_w = int(bw * expansion_ratio)
            expansion_h = int(bh * expansion_ratio)
            
            expanded_x = max(0, bx - expansion_w)
            expanded_y = max(0, by - expansion_h)
            expanded_w = min(img_width - expanded_x, bw + 2*expansion_w)
            expanded_h = min(img_height - expanded_y, bh + 2*expansion_h)
            
            # Calculate YOLO format
            center_x = (expanded_x + expanded_w / 2) / img_width
            center_y = (expanded_y + expanded_h / 2) / img_height
            norm_width = expanded_w / img_width
            norm_height = expanded_h / img_height
            
            # YOLO format: class_id center_x center_y width height
            # class_id = 0 for "cell"
            yolo_labels.append(f"0 {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}")
        
        # Save YOLO label file
        label_filename = f"{img_name}.txt"
        label_path = os.path.join(session_dir, label_filename)
        with open(label_path, 'w') as f:
            f.write('\n'.join(yolo_labels))
        
        # Copy original image to session directory
        import shutil
        image_filename = f"{img_name}.jpg"
        image_dest = os.path.join(session_dir, image_filename)
        shutil.copy(self.image_path, image_dest)
        
        # Save metadata (optional - one per image)
        metadata_filename = f"{img_name}_metadata.json"
        metadata_path = os.path.join(session_dir, metadata_filename)
        with open(metadata_path, 'w') as f:
            json.dump({
                'source_image': self.image_path,
                'image_size': {'width': img_width, 'height': img_height},
                'roi': self.roi_rect,
                'expansion_percent': expansion_percent,
                'expansion_ratio': expansion_ratio,
                'num_cells': len(self.detected_cells),
                'num_manual_boxes': len(self.manual_boxes),
                'total_labels': len(yolo_labels),
                'yolo_format': 'class_id center_x center_y width height (normalized)',
                'class_names': {0: 'cell'}
            }, f, indent=2)
        
        # Create annotated visualization
        vis_image = self.image.copy()
        
        # Draw detected cells (after deletions)
        for cell in self.detected_cells:
            bx, by, bw, bh = cell.bbox
            expansion_w = int(bw * expansion_ratio)
            expansion_h = int(bh * expansion_ratio)
            expanded_x = max(0, bx - expansion_w)
            expanded_y = max(0, by - expansion_h)
            expanded_w = min(img_width - expanded_x, bw + 2*expansion_w)
            expanded_h = min(img_height - expanded_y, bh + 2*expansion_h)
            
            # Draw expanded bbox (green for auto-detected)
            cv2.rectangle(vis_image, (expanded_x, expanded_y), 
                         (expanded_x + expanded_w, expanded_y + expanded_h), 
                         (0, 255, 0), 2)
            # Draw center point
            center_x_px = int(expanded_x + expanded_w / 2)
            center_y_px = int(expanded_y + expanded_h / 2)
            cv2.circle(vis_image, (center_x_px, center_y_px), 3, (0, 0, 255), -1)
        
        # Draw manual boxes
        for i, (bx, by, bw, bh) in enumerate(self.manual_boxes):
            expansion_w = int(bw * expansion_ratio)
            expansion_h = int(bh * expansion_ratio)
            expanded_x = max(0, bx - expansion_w)
            expanded_y = max(0, by - expansion_h)
            expanded_w = min(img_width - expanded_x, bw + 2*expansion_w)
            expanded_h = min(img_height - expanded_y, bh + 2*expansion_h)
            
            # Draw expanded bbox (cyan for manual)
            cv2.rectangle(vis_image, (expanded_x, expanded_y), 
                         (expanded_x + expanded_w, expanded_y + expanded_h), 
                         (255, 255, 0), 2)  # Yellow for manual boxes
            # Draw center point
            center_x_px = int(expanded_x + expanded_w / 2)
            center_y_px = int(expanded_y + expanded_h / 2)
            cv2.circle(vis_image, (center_x_px, center_y_px), 3, (255, 0, 255), -1)  # Magenta center
        
        vis_filename = f"{img_name}_annotated.jpg"
        vis_path = os.path.join(session_dir, vis_filename)
        cv2.imwrite(vis_path, vis_image)
        
        # Log results
        total_labels = len(self.detected_cells) + len(self.manual_boxes)
        self.update_info(f"=== YOLO Labels Saved ===")
        self.update_info(f"Auto-detected cells: {len(self.detected_cells)}")
        self.update_info(f"Manual boxes: {len(self.manual_boxes)}")
        self.update_info(f"Total labels: {total_labels}")
        self.update_info(f"Files saved:")
        self.update_info(f"  - {label_filename}")
        self.update_info(f"  - {image_filename}")
        self.update_info(f"  - {vis_filename}")
        self.update_info(f"  - {metadata_filename}")
        self.update_info(f"Output directory: {session_dir}")
        self.update_info("")
        self.status_var.set(f"Saved {total_labels} labels ({len(self.detected_cells)} auto + {len(self.manual_boxes)} manual)")
    
    def detect_cells_whole_image(self):
        """Detect cells in the whole image (no ROI required)"""
        if self.image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        # Parse and validate size filter
        try:
            min_size = int(self.min_size_var.get())
            max_size = int(self.max_size_var.get())
            if min_size < 1 or max_size < min_size:
                messagebox.showerror("Error", "Invalid size filter. Min must be >= 1 and Max must be >= Min")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid size values. Please enter integers")
            return
        
        self.status_var.set("Detecting cells in whole image...")
        self.root.update()
        
        # Use whole image as ROI
        h, w = self.image.shape[:2]
        whole_image_roi = (0, 0, w, h)
        
        # Detect all cells
        all_cells = detect_cells_in_roi(self.image, whole_image_roi, self.params)
        
        # Apply size filter
        self.detected_cells = []
        filtered_count = 0
        for cell in all_cells:
            bx, by, bw, bh = cell.bbox
            if min_size <= bw <= max_size and min_size <= bh <= max_size:
                self.detected_cells.append(cell)
            else:
                filtered_count += 1
        
        self.update_display()
        info_msg = f"Detected {len(self.detected_cells)} cells (whole image)"
        if filtered_count > 0:
            info_msg += f" ({filtered_count} filtered by size)"
        self.update_info(info_msg)
        self.status_var.set(f"Detected {len(self.detected_cells)} cells")
    
    def batch_process_folder(self):
        """Batch process all images in a folder"""
        if self.image_path is None:
            messagebox.showwarning("Warning", "Please load an image first to set the source folder")
            return
        
        # Parse and validate parameters
        try:
            min_size = int(self.min_size_var.get())
            max_size = int(self.max_size_var.get())
            expansion_percent = float(self.margin_var.get())
            
            if min_size < 1 or max_size < min_size:
                messagebox.showerror("Error", "Invalid size filter")
                return
            if expansion_percent < 0 or expansion_percent > 50:
                messagebox.showerror("Error", "BBox expansion must be between 0 and 50")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values")
            return
        
        # Get source folder
        source_folder = os.path.dirname(self.image_path)
        
        # Get all image files
        image_files = [f for f in os.listdir(source_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if len(image_files) == 0:
            messagebox.showwarning("Warning", "No image files found in folder")
            return
        
        # Confirm batch processing
        from tkinter import simpledialog
        confirm = messagebox.askyesno(
            "Batch Process",
            f"Found {len(image_files)} images in:\n{source_folder}\n\n"
            f"Parameters:\n"
            f"- Size filter: {min_size}-{max_size} pixels\n"
            f"- BBox expansion: {expansion_percent}%\n\n"
            f"Process all images?"
        )
        
        if not confirm:
            return
        
        # Detect CPU cores and use 3/4 of them
        max_cores = mp.cpu_count()
        num_cores = max(6, int(max_cores * 0.75))  # Use 3/4 of cores, minimum 6
        
        # Create batch output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = os.path.join(self.output_dir, f"batch_{timestamp}")
        os.makedirs(batch_dir, exist_ok=True)
        
        # Prepare parameters for multiprocessing
        params_dict = {
            'min_size': min_size,
            'max_size': max_size,
            'expansion_percent': expansion_percent,
            'detection_params': self.params
        }
        
        # Prepare image paths
        image_paths = [os.path.join(source_folder, f) for f in image_files]
        process_args = [(img_path, batch_dir, params_dict) for img_path in image_paths]
        
        # Process images
        print(f"\n{'='*60}")
        print(f"=== Batch Processing Started ===")
        print(f"Total images: {len(image_files)}")
        print(f"CPU cores: {num_cores}/{max_cores} (using 75%)")
        print(f"Note: Task Manager may show all cores active due to Windows process scheduling,")
        print(f"      but only {num_cores} images are processed concurrently.")
        print(f"Output: {batch_dir}")
        print(f"{'='*60}\n")
        
        self.update_info(f"\n=== Batch Processing Started ===")
        self.update_info(f"Total images: {len(image_files)}")
        self.update_info(f"CPU cores: {num_cores}/{max_cores} (using 75%)")
        self.update_info(f"Output: {batch_dir}\n")
        
        processed_count = 0
        total_cells = 0
        skipped_files = []
        
        # Use multiprocessing pool with maxtasksperchild to limit resource usage
        with mp.Pool(processes=num_cores, maxtasksperchild=10) as pool:
            # Process images in parallel
            for idx, result in enumerate(pool.imap_unordered(process_single_image_for_batch, process_args), 1):
                success, img_file, num_cells, error_msg = result
                
                if success:
                    processed_count += 1
                    total_cells += num_cells
                else:
                    skipped_files.append(f"{img_file} (Error: {error_msg})")
                
                # Terminal logging (always works)
                if idx % 10 == 0 or idx == len(image_files):
                    print(f"[{idx}/{len(image_files)}] Processed {processed_count} images, {total_cells} cells detected")
                
                # Update UI (non-blocking)
                try:
                    self.status_var.set(f"Processing {idx}/{len(image_files)}")
                    if idx % 50 == 0 or idx == len(image_files):
                        self.update_info(f"Processed {idx}/{len(image_files)} images...")
                    self.root.update_idletasks()
                except:
                    pass  # Continue even if UI fails
        
        # Save batch summary
        summary_path = os.path.join(batch_dir, 'batch_summary.json')
        with open(summary_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'source_folder': source_folder,
                'total_images': len(image_files),
                'processed': processed_count,
                'skipped': len(skipped_files),
                'total_cells_detected': total_cells,
                'parameters': {
                    'min_size': min_size,
                    'max_size': max_size,
                    'expansion_percent': expansion_percent
                },
                'skipped_files': skipped_files
            }, f, indent=2)
        
        # Final report (terminal)
        print(f"\n{'='*60}")
        print(f"=== Batch Processing Complete ===")
        print(f"Processed: {processed_count}/{len(image_files)} images")
        print(f"Total cells detected: {total_cells}")
        if skipped_files:
            print(f"Skipped: {len(skipped_files)} files")
            for skip in skipped_files[:5]:  # Show first 5 skipped files
                print(f"  - {skip}")
            if len(skipped_files) > 5:
                print(f"  ... and {len(skipped_files)-5} more")
        print(f"Output directory: {batch_dir}")
        print(f"{'='*60}\n")
        
        # Final report (UI)
        self.update_info(f"\n=== Batch Processing Complete ===")
        self.update_info(f"Processed: {processed_count}/{len(image_files)} images")
        self.update_info(f"Total cells: {total_cells}")
        if skipped_files:
            self.update_info(f"Skipped: {len(skipped_files)} files")
        self.update_info(f"Output: {batch_dir}\n")
        
        try:
            self.status_var.set(f"Batch complete: {processed_count} images, {total_cells} cells")
        except:
            pass
    
    def clear_roi(self):
        """Clear the ROI and detected cells"""
        self.roi_rect = None
        self.detected_cells = []
        self.update_display()
        self.update_info("ROI cleared")
    
    def update_info(self, message):
        """Update info text"""
        self.info_text.insert(tk.END, f"{message}\n")
        self.info_text.see(tk.END)
    
    def load_next_image(self):
        """Load the next image in the folder"""
        if not self.folder_images or self.current_image_index < 0:
            self.update_info("No folder loaded. Load an image first.")
            return
        
        # Move to next image
        next_index = (self.current_image_index + 1) % len(self.folder_images)
        next_path = os.path.join(self.current_folder, self.folder_images[next_index])
        
        # Load the image
        self.image = cv2.imread(next_path)
        if self.image is None:
            self.update_info(f"Failed to load: {self.folder_images[next_index]}")
            return
        
        self.image_path = next_path
        self.current_image_index = next_index
        self.roi_rect = None
        self.detected_cells = []
        self.manual_boxes = []  # Clear manual boxes when changing images
        self.selected_box_index = -1
        self.selected_cell_index = -1
        
        self.update_display()
        nav_info = f"[{self.current_image_index + 1}/{len(self.folder_images)}]"
        self.status_var.set(f"Loaded: {self.folder_images[next_index]} {nav_info}")
        self.update_info(f"→ Next image {nav_info}: {self.folder_images[next_index]}")
    
    def load_previous_image(self):
        """Load the previous image in the folder"""
        if not self.folder_images or self.current_image_index < 0:
            self.update_info("No folder loaded. Load an image first.")
            return
        
        # Move to previous image
        prev_index = (self.current_image_index - 1) % len(self.folder_images)
        prev_path = os.path.join(self.current_folder, self.folder_images[prev_index])
        
        # Load the image
        self.image = cv2.imread(prev_path)
        if self.image is None:
            self.update_info(f"Failed to load: {self.folder_images[prev_index]}")
            return
        
        self.image_path = prev_path
        self.current_image_index = prev_index
        self.roi_rect = None
        self.detected_cells = []
        self.manual_boxes = []  # Clear manual boxes when changing images
        self.selected_box_index = -1
        self.selected_cell_index = -1
        
        self.update_display()
        nav_info = f"[{self.current_image_index + 1}/{len(self.folder_images)}]"
        self.status_var.set(f"Loaded: {self.folder_images[prev_index]} {nav_info}")
        self.update_info(f"← Previous image {nav_info}: {self.folder_images[prev_index]}")
    
    def toggle_manual_mode(self):
        """Toggle between manual labeling mode and ROI mode"""
        self.manual_mode = not self.manual_mode
        
        if self.manual_mode:
            self.manual_mode_btn.config(text="Manual Mode: ON")
            self.update_info("=== Manual Mode ON ===")
            self.update_info("Draw boxes: Click and drag")
            self.update_info("Delete box: Click box, press D or Delete")
            self.update_info("Save: Press S")
            self.status_var.set("Manual Mode: Draw bounding boxes")
        else:
            self.manual_mode_btn.config(text="Manual Mode: OFF")
            self.update_info("=== Manual Mode OFF ===")
            self.update_info("ROI mode active")
            self.status_var.set("ROI Mode: Draw ROI for detection")
        
        self.update_display()
    
    def delete_selected_box(self):
        """Delete the currently selected manual box or detected cell"""
        if self.selected_box_index >= 0 and self.selected_box_index < len(self.manual_boxes):
            # Delete manual box
            deleted_box = self.manual_boxes.pop(self.selected_box_index)
            self.update_info(f"Deleted manual box {self.selected_box_index + 1}")
            self.selected_box_index = -1
            self.update_display()
        elif self.selected_cell_index >= 0 and self.selected_cell_index < len(self.detected_cells):
            # Delete detected cell
            deleted_cell = self.detected_cells.pop(self.selected_cell_index)
            self.update_info(f"Deleted detected cell {self.selected_cell_index + 1}")
            self.selected_cell_index = -1
            self.update_display()
        else:
            self.update_info("No box selected. Click a box to select it.")
    
    def clear_all_labels(self):
        """Clear all manual boxes and detected cells"""
        if self.manual_boxes or self.detected_cells:
            confirm = messagebox.askyesno("Clear All", 
                f"Clear {len(self.manual_boxes)} manual boxes and {len(self.detected_cells)} detected cells?")
            if confirm:
                self.manual_boxes = []
                self.detected_cells = []
                self.selected_box_index = -1
                self.update_info("Cleared all labels")
                self.update_display()
        else:
            self.update_info("No labels to clear")
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom"""
        if self.image is None:
            return
        
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down / zoom out
            self.zoom_out()
        elif event.num == 4 or event.delta > 0:  # Scroll up / zoom in
            self.zoom_in()
    
    def zoom_in(self):
        """Zoom in on the image"""
        if self.image is None:
            return
        
        old_zoom = self.zoom_level
        self.zoom_level = min(self.zoom_level + self.zoom_step, self.max_zoom)
        
        if self.zoom_level != old_zoom:
            self.update_display()
            self.status_var.set(f"Zoom: {int(self.zoom_level * 100)}%")
            self.update_info(f"Zoom: {int(self.zoom_level * 100)}%")
    
    def zoom_out(self):
        """Zoom out on the image"""
        if self.image is None:
            return
        
        old_zoom = self.zoom_level
        self.zoom_level = max(self.zoom_level - self.zoom_step, self.min_zoom)
        
        if self.zoom_level != old_zoom:
            self.update_display()
            self.status_var.set(f"Zoom: {int(self.zoom_level * 100)}%")
            self.update_info(f"Zoom: {int(self.zoom_level * 100)}%")
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if self.image is None:
            return
        
        self.zoom_level = 1.0
        self.update_display()
        self.status_var.set(f"Zoom: 100%")
        self.update_info("Zoom reset to 100%")


def main():
    root = tk.Tk()
    app = DatasetCreatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
