"""
ImageProcessor GUI Application
Interactive GUI for Bayer RAW image processing and cell detection
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import cv2
from PIL import Image, ImageTk
from image_processor import ImageProcessor
import threading
import logging


class ImageViewer:
    """Image viewer widget with zoom and pan functionality"""
    
    def __init__(self, parent, title="Image Viewer"):
        self.parent = parent
        self.title = title
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("800x600")
        
        # Image data
        self.original_image = None
        self.display_image = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # UI elements
        self.setup_ui()
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom)  # Linux
        self.canvas.bind("<Button-5>", self.on_zoom)  # Linux
        
        # Variables for dragging
        self.last_x = 0
        self.last_y = 0
        
    def setup_ui(self):
        """Setup user interface"""
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='black')
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Zoom controls
        ttk.Label(control_frame, text="Zoom:").pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Fit", command=self.fit_to_window).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="100%", command=self.zoom_100).pack(side=tk.LEFT, padx=2)
        
        # Scale label
        self.scale_label = ttk.Label(control_frame, text="100%")
        self.scale_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def set_image(self, image_array, colormap=None):
        """Set image to display"""
        if image_array is None:
            return
        
        # Convert to display format
        if len(image_array.shape) == 2:  # Grayscale
            if image_array.dtype != np.uint8:
                # Normalize to 8-bit
                img_min, img_max = image_array.min(), image_array.max()
                if img_max > img_min:
                    display_array = ((image_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
                else:
                    display_array = np.zeros_like(image_array, dtype=np.uint8)
            else:
                display_array = image_array
            
            # Apply colormap if specified
            if colormap:
                if colormap == 'jet':
                    display_array = cv2.applyColorMap(display_array, cv2.COLORMAP_JET)
                    display_array = cv2.cvtColor(display_array, cv2.COLOR_BGR2RGB)
                else:
                    display_array = cv2.cvtColor(display_array, cv2.COLOR_GRAY2RGB)
            else:
                display_array = cv2.cvtColor(display_array, cv2.COLOR_GRAY2RGB)
        else:
            display_array = image_array
        
        self.original_image = display_array
        
        # Auto-scale large images to fit memory constraints
        if display_array is not None:
            height, width = display_array.shape[:2]
            total_pixels = width * height
            
            # Auto-scale very large images for initial display
            if total_pixels > 25_000_000:  # > 25 megapixels
                # Scale to fit within reasonable memory limits
                safe_scale = (16_000_000 / total_pixels) ** 0.5
                self.scale_factor = min(safe_scale, 0.5)
                print(f"Large image detected ({width}x{height}), auto-scaling to {int(self.scale_factor*100)}%")
            elif total_pixels > 10_000_000:  # > 10 megapixels
                self.scale_factor = 0.7
                print(f"Medium-large image detected, auto-scaling to 70%")
        
        self.update_display()
    
    def update_display(self):
        """Update canvas display with memory management"""
        if self.original_image is None:
            return
        
        try:
            # Calculate display size
            height, width = self.original_image.shape[:2]
            new_width = int(width * self.scale_factor)
            new_height = int(height * self.scale_factor)
            
            # Memory safety: limit maximum display size to prevent memory errors
            max_display_pixels = 16_000_000  # ~16 megapixels max for display
            current_pixels = new_width * new_height
            
            if current_pixels > max_display_pixels:
                # Calculate safe scale factor
                safe_scale = (max_display_pixels / (width * height)) ** 0.5
                new_width = int(width * safe_scale)
                new_height = int(height * safe_scale)
                actual_scale = safe_scale
                print(f"Memory protection: Limiting display to {new_width}x{new_height}")
            else:
                actual_scale = self.scale_factor
            
            # Create display image efficiently
            display_image = self._create_display_image(new_width, new_height)
            
            if display_image is None:
                print("Failed to create display image")
                return
            
            # Convert to PIL Image with memory optimization
            if len(display_image.shape) == 2:  # Grayscale
                # Normalize to 8-bit for display
                if display_image.dtype == np.uint16:
                    # Use percentile-based normalization for better contrast
                    p1, p99 = np.percentile(display_image, [1, 99])
                    display_image = np.clip((display_image - p1) / (p99 - p1) * 255, 0, 255).astype(np.uint8)
                elif display_image.dtype == np.float32:
                    display_image = (np.clip(display_image, 0, 1) * 255).astype(np.uint8)
                
                pil_image = Image.fromarray(display_image, mode='L')
            else:
                pil_image = Image.fromarray(display_image)
            
            # Create PhotoImage with error handling
            try:
                self.display_image = ImageTk.PhotoImage(pil_image)
            except (MemoryError, tk.TclError) as e:
                print(f"Display memory error: {e}")
                # Try with even smaller image
                small_width = min(new_width // 2, 2000)
                small_height = min(new_height // 2, 2000)
                small_image = self._create_display_image(small_width, small_height)
                if small_image is not None:
                    if small_image.dtype == np.uint16:
                        p1, p99 = np.percentile(small_image, [1, 99])
                        small_image = np.clip((small_image - p1) / (p99 - p1) * 255, 0, 255).astype(np.uint8)
                    pil_image = Image.fromarray(small_image, mode='L')
                    self.display_image = ImageTk.PhotoImage(pil_image)
                    actual_scale = min(small_width / width, small_height / height)
                else:
                    return
            
            # Clear canvas and add image
            self.canvas.delete("all")
            self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.NW, image=self.display_image)
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Update scale label with actual scale
            self.scale_label.config(text=f"{int(actual_scale * 100)}%")
            
        except Exception as e:
            print(f"Error updating display: {e}")
            # Fallback: show error message on canvas
            self.canvas.delete("all")
            self.canvas.create_text(200, 100, text=f"Display Error: {str(e)}", fill="red", font=("Arial", 12))
    
    def _create_display_image(self, target_width, target_height):
        """Create display image with efficient resizing"""
        try:
            height, width = self.original_image.shape[:2]
            
            # Use area interpolation for downsampling, nearest for upsampling
            if target_width < width or target_height < height:
                interpolation = cv2.INTER_AREA  # Better for downsampling
            else:
                interpolation = cv2.INTER_NEAREST  # Preserve pixels for upsampling
            
            # Resize image
            resized = cv2.resize(self.original_image, (target_width, target_height), interpolation=interpolation)
            return resized
            
        except Exception as e:
            print(f"Error creating display image: {e}")
            return None
    
    def zoom_in(self):
        """Zoom in with memory safety"""
        # Check if image is very large and limit zoom
        if self.original_image is not None:
            height, width = self.original_image.shape[:2]
            total_pixels = width * height
            
            # For very large images, use smaller zoom increments
            if total_pixels > 20_000_000:  # > 20 megapixels
                zoom_factor = 1.2
                max_scale = 2.0
            elif total_pixels > 10_000_000:  # > 10 megapixels  
                zoom_factor = 1.3
                max_scale = 4.0
            else:
                zoom_factor = 1.5
                max_scale = 10.0
            
            new_scale = self.scale_factor * zoom_factor
            if new_scale <= max_scale:
                self.scale_factor = new_scale
            else:
                print(f"Maximum zoom reached for large image ({max_scale}x)")
                
        self.update_display()
    
    def zoom_out(self):
        """Zoom out"""
        self.scale_factor /= 1.5
        if self.scale_factor < 0.1:
            self.scale_factor = 0.1
        self.update_display()
    
    def zoom_100(self):
        """Reset to 100% zoom"""
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update_display()
    
    def fit_to_window(self):
        """Fit image to window"""
        if self.original_image is None:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_height, img_width = self.original_image.shape[:2]
        
        if canvas_width > 1 and canvas_height > 1:
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            self.scale_factor = min(scale_x, scale_y)
            self.offset_x = 0
            self.offset_y = 0
            self.update_display()
    
    def on_click(self, event):
        """Handle mouse click"""
        self.last_x = event.x
        self.last_y = event.y
    
    def on_drag(self, event):
        """Handle mouse drag for panning"""
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        
        self.offset_x += dx
        self.offset_y += dy
        
        self.last_x = event.x
        self.last_y = event.y
        
        self.update_display()
    
    def on_zoom(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0 or event.num == 4:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1
            if self.scale_factor < 0.1:
                self.scale_factor = 0.1
        
        self.update_display()


class MainApplication:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ImageProcessor - Bayer RAW Cell Detection")
        
        # Set initial geometry and minimum size
        self.root.geometry("450x700")
        self.root.minsize(400, 600)
        
        # Center window on screen
        self.center_window()
        
        # Initialize processor
        self.processor = ImageProcessor()
        
        # Image viewers
        self.viewers = {}
        
        # File paths
        self.main_image_path = None
        self.dark_field_path = None
        self.output_dir = None
        
        # ROI variables
        self.roi_coords = None  # ROI coordinates (x1, y1, x2, y2)
        self.roi_drawing = False  # ROI drawing state
        
        # Calibration variables
        self.calibration_mode = None  # 'background', 'cell', or None
        self.background_coords = None  # Background region coordinates
        self.cell_coords = None  # Cell region coordinates
        self.background_intensity = None  # Mean background intensity
        self.cell_intensity = None  # Mean cell intensity
        self.suggested_threshold = None  # Calculated threshold
        
        # Processing state
        self.processing_complete = False
        
        # Setup UI
        self.setup_ui()
        
        # Setup logging display
        self.setup_logging()
    
    def center_window(self):
        """Center the main window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup main user interface"""
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Main image selection
        ttk.Label(file_frame, text="Main Image (16-bit TIFF):").pack(anchor=tk.W)
        main_img_frame = ttk.Frame(file_frame)
        main_img_frame.pack(fill=tk.X, pady=(2, 5))
        
        self.main_img_var = tk.StringVar()
        ttk.Entry(main_img_frame, textvariable=self.main_img_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(main_img_frame, text="Browse", command=self.select_main_image).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Dark field selection
        ttk.Label(file_frame, text="Dark Field (Optional):").pack(anchor=tk.W)
        dark_frame = ttk.Frame(file_frame)
        dark_frame.pack(fill=tk.X, pady=(2, 5))
        
        self.dark_field_var = tk.StringVar()
        ttk.Entry(dark_frame, textvariable=self.dark_field_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dark_frame, text="Browse", command=self.select_dark_field).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Output directory selection
        ttk.Label(file_frame, text="Output Directory:").pack(anchor=tk.W)
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.output_dir_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_dir_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse", command=self.select_output_dir).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Processing steps section
        steps_frame = ttk.LabelFrame(main_frame, text="Processing Steps", padding=10)
        steps_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Step 1: Load and view main image
        step1_frame = ttk.Frame(steps_frame)
        step1_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step1_frame, text="1. Load Main Image:").pack(side=tk.LEFT)
        self.btn_load_main = ttk.Button(step1_frame, text="Load & View", command=self.load_main_image, state="disabled")
        self.btn_load_main.pack(side=tk.RIGHT)
        
        # Step 2: Bayer split
        step2_frame = ttk.Frame(steps_frame)
        step2_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step2_frame, text="2. Bayer Split (RGGB):").pack(side=tk.LEFT)
        self.btn_bayer_split = ttk.Button(step2_frame, text="Split & View R", command=self.bayer_split, state="disabled")
        self.btn_bayer_split.pack(side=tk.RIGHT)
        
        # Step 3: Dark field subtraction
        step3_frame = ttk.Frame(steps_frame)
        step3_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step3_frame, text="3. Dark Field Subtraction:").pack(side=tk.LEFT)
        self.btn_dark_subtract = ttk.Button(step3_frame, text="Subtract & View", command=self.dark_field_subtraction, state="disabled")
        self.btn_dark_subtract.pack(side=tk.RIGHT)
        
        # Step 4: Contrast enhancement with controls
        step4_frame = ttk.Frame(steps_frame)
        step4_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step4_frame, text="4. Enhance Contrast:").pack(side=tk.LEFT)
        self.btn_enhance = ttk.Button(step4_frame, text="Enhance & View", command=self.enhance_contrast, state="disabled")
        self.btn_enhance.pack(side=tk.RIGHT)
        
        # Enhancement parameter controls
        enhance_controls_frame = ttk.Frame(steps_frame)
        enhance_controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # CLAHE Clip Limit
        clahe_frame = ttk.Frame(enhance_controls_frame)
        clahe_frame.pack(fill=tk.X, pady=1)
        ttk.Label(clahe_frame, text="CLAHE Clip:", width=12).pack(side=tk.LEFT)
        self.clahe_var = tk.DoubleVar(value=self.processor.config.get('contrast_enhancement', {}).get('clahe_clip_limit', 1.2))
        self.clahe_scale = ttk.Scale(clahe_frame, from_=0.5, to=5.0, variable=self.clahe_var, 
                                   orient=tk.HORIZONTAL, length=150, command=self.on_enhancement_change)
        self.clahe_scale.pack(side=tk.LEFT, padx=5)
        self.clahe_entry = ttk.Entry(clahe_frame, textvariable=self.clahe_var, width=6)
        self.clahe_entry.pack(side=tk.LEFT, padx=2)
        self.clahe_entry.bind('<Return>', self.on_enhancement_entry_change)
        
        # Tile Size
        tile_frame = ttk.Frame(enhance_controls_frame)
        tile_frame.pack(fill=tk.X, pady=1)
        ttk.Label(tile_frame, text="Tile Size:", width=12).pack(side=tk.LEFT)
        self.tile_var = tk.IntVar(value=self.processor.config.get('contrast_enhancement', {}).get('clahe_tile_size', 4))
        self.tile_scale = ttk.Scale(tile_frame, from_=2, to=16, variable=self.tile_var, 
                                  orient=tk.HORIZONTAL, length=150, command=self.on_enhancement_change)
        self.tile_scale.pack(side=tk.LEFT, padx=5)
        self.tile_entry = ttk.Entry(tile_frame, textvariable=self.tile_var, width=6)
        self.tile_entry.pack(side=tk.LEFT, padx=2)
        self.tile_entry.bind('<Return>', self.on_enhancement_entry_change)
        
        # Gamma
        gamma_frame = ttk.Frame(enhance_controls_frame)
        gamma_frame.pack(fill=tk.X, pady=1)
        ttk.Label(gamma_frame, text="Gamma:", width=12).pack(side=tk.LEFT)
        self.gamma_var = tk.DoubleVar(value=self.processor.config.get('contrast_enhancement', {}).get('gamma', 0.95))
        self.gamma_scale = ttk.Scale(gamma_frame, from_=0.3, to=3, variable=self.gamma_var, 
                                   orient=tk.HORIZONTAL, length=150, command=self.on_enhancement_change)
        self.gamma_scale.pack(side=tk.LEFT, padx=5)
        self.gamma_entry = ttk.Entry(gamma_frame, textvariable=self.gamma_var, width=6)
        self.gamma_entry.pack(side=tk.LEFT, padx=2)
        self.gamma_entry.bind('<Return>', self.on_enhancement_entry_change)
        
        # Real-time update checkbox
        realtime_frame = ttk.Frame(enhance_controls_frame)
        realtime_frame.pack(fill=tk.X, pady=1)
        self.realtime_var = tk.BooleanVar(value=False)
        self.realtime_check = ttk.Checkbutton(realtime_frame, text="Real-time update", 
                                            variable=self.realtime_var)
        self.realtime_check.pack(side=tk.LEFT)
        
        # Reset button
        ttk.Button(realtime_frame, text="Reset to Default", command=self.reset_enhancement_params).pack(side=tk.RIGHT)
        
        # Step 5: Gaussian filtering
        step5_frame = ttk.Frame(steps_frame)
        step5_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step5_frame, text="5. Gaussian Filter:").pack(side=tk.LEFT)
        self.btn_gaussian = ttk.Button(step5_frame, text="Filter & View", command=self.gaussian_filter, state="disabled")
        self.btn_gaussian.pack(side=tk.RIGHT)
        
        # Step 6: ROI Selection (Optional)
        step6_frame = ttk.Frame(steps_frame)
        step6_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step6_frame, text="6. Select ROI (Optional):").pack(side=tk.LEFT)
        roi_buttons_frame = ttk.Frame(step6_frame)
        roi_buttons_frame.pack(side=tk.RIGHT)
        self.btn_draw_roi = ttk.Button(roi_buttons_frame, text="Draw ROI", command=self.draw_roi, state="disabled")
        self.btn_draw_roi.pack(side=tk.LEFT, padx=2)
        self.btn_clear_roi = ttk.Button(roi_buttons_frame, text="Clear ROI", command=self.clear_roi, state="disabled")
        self.btn_clear_roi.pack(side=tk.LEFT, padx=2)
        
        # Step 7: Threshold Calibration
        step7_frame = ttk.Frame(steps_frame)
        step7_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step7_frame, text="7. Calibrate Threshold:").pack(side=tk.LEFT)
        calibration_buttons_frame = ttk.Frame(step7_frame)
        calibration_buttons_frame.pack(side=tk.RIGHT)
        self.btn_calibrate = ttk.Button(calibration_buttons_frame, text="Calibrate", command=self.calibrate_threshold, state="disabled")
        self.btn_calibrate.pack(side=tk.LEFT, padx=2)
        self.btn_threshold = ttk.Button(calibration_buttons_frame, text="Auto Threshold", command=self.auto_threshold, state="disabled")
        self.btn_threshold.pack(side=tk.LEFT, padx=2)
        
        # Calibration controls
        calibration_controls_frame = ttk.Frame(steps_frame)
        calibration_controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Threshold value control
        threshold_frame = ttk.Frame(calibration_controls_frame)
        threshold_frame.pack(fill=tk.X, pady=1)
        ttk.Label(threshold_frame, text="Threshold:", width=12).pack(side=tk.LEFT)
        self.threshold_var = tk.DoubleVar(value=0)
        self.threshold_scale = ttk.Scale(threshold_frame, from_=0, to=65535, variable=self.threshold_var, 
                                       orient=tk.HORIZONTAL, length=150, command=self.on_threshold_change)
        self.threshold_scale.pack(side=tk.LEFT, padx=5)
        self.threshold_entry = ttk.Entry(threshold_frame, textvariable=self.threshold_var, width=8)
        self.threshold_entry.pack(side=tk.LEFT, padx=2)
        self.threshold_entry.bind('<Return>', self.on_threshold_entry_change)
        
        # Calibration info display
        info_frame = ttk.Frame(calibration_controls_frame)
        info_frame.pack(fill=tk.X, pady=1)
        self.calibration_info = tk.StringVar(value="Background: -- | Cell: -- | Suggested: --")
        ttk.Label(info_frame, textvariable=self.calibration_info, font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Real-time preview checkbox
        preview_frame = ttk.Frame(calibration_controls_frame)
        preview_frame.pack(fill=tk.X, pady=1)
        self.threshold_preview_var = tk.BooleanVar(value=False)
        self.threshold_preview_check = ttk.Checkbutton(preview_frame, text="Real-time preview", 
                                                     variable=self.threshold_preview_var)
        self.threshold_preview_check.pack(side=tk.LEFT)
        
        # Step 8: Contour detection
        step8_frame = ttk.Frame(steps_frame)
        step8_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step8_frame, text="8. Find Contours:").pack(side=tk.LEFT)
        self.btn_contours = ttk.Button(step8_frame, text="Find & View", command=self.find_contours, state="disabled")
        self.btn_contours.pack(side=tk.RIGHT)
        
        # Step 9: Intensity measurement
        step9_frame = ttk.Frame(steps_frame)
        step9_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step9_frame, text="9. Measure Intensity:").pack(side=tk.LEFT)
        self.btn_measure = ttk.Button(step9_frame, text="Measure & Display", command=self.measure_intensity, state="disabled")
        self.btn_measure.pack(side=tk.RIGHT)
        
        # Step 10: Save results
        step10_frame = ttk.Frame(steps_frame)
        step10_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step10_frame, text="10. Save Results:").pack(side=tk.LEFT)
        self.btn_save = ttk.Button(step10_frame, text="Save CSV & Image", command=self.save_results, state="disabled")
        self.btn_save.pack(side=tk.RIGHT)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status text
        self.status_text = tk.Text(status_frame, height=8, wrap=tk.WORD)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial status
        self.log_status("Ready. Please select main image file to begin.")
    
    def setup_logging(self):
        """Setup logging to display in status text"""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + "\n")
                self.text_widget.see(tk.END)
                self.text_widget.update()
        
        # Add text handler to processor logger
        text_handler = TextHandler(self.status_text)
        text_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.processor.logger.addHandler(text_handler)
    
    def log_status(self, message):
        """Log status message"""
        self.status_text.insert(tk.END, f"INFO: {message}\n")
        self.status_text.see(tk.END)
        self.status_text.update()
    
    def reset_processing_buttons(self):
        """Reset all processing buttons to initial state"""
        # Disable all processing buttons except load_main
        self.btn_bayer_split.config(state="disabled")
        self.btn_dark_subtract.config(state="disabled")
        self.btn_enhance.config(state="disabled")
        self.btn_gaussian.config(state="disabled")
        self.btn_draw_roi.config(state="disabled")
        self.btn_clear_roi.config(state="disabled")
        self.btn_calibrate.config(state="disabled")
        self.btn_threshold.config(state="disabled")
        self.btn_contours.config(state="disabled")
        self.btn_measure.config(state="disabled")
        self.btn_save.config(state="disabled")
        
        # Reset ROI
        self.roi_coords = None
        self.roi_drawing = False
        
        # Reset calibration
        self.calibration_mode = None
        self.background_coords = None
        self.cell_coords = None
        self.background_intensity = None
        self.cell_intensity = None
        self.suggested_threshold = None
        self.threshold_var.set(0)
        self.calibration_info.set("Background: -- | Cell: -- | Suggested: --")
        
        # Clear processor state
        if hasattr(self, 'processor'):
            self.processor.raw_image = None
            self.processor.r_raw = None
            self.processor.r_flu = None
            if hasattr(self.processor, 'r_enhanced'):
                self.processor.r_enhanced = None
            self.processor.r_gau = None
            self.processor.r_bin = None
            self.processor.dark_field = None
            self.processor.contours = []
            self.processor.cell_data = []
    
    def close_all_viewers(self):
        """Close all image viewer windows"""
        viewers_to_close = list(self.viewers.keys())
        for viewer_name in viewers_to_close:
            if viewer_name in self.viewers:
                try:
                    self.viewers[viewer_name].window.destroy()
                except:
                    pass  # Window might already be closed
                del self.viewers[viewer_name]
    
    def select_main_image(self):
        """Select main image file"""
        # Store current geometry
        current_geometry = self.root.geometry()
        
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Select Main Image (16-bit TIFF)",
            filetypes=[("TIFF files", "*.tiff *.tif"), ("All files", "*.*")]
        )
        
        # Restore geometry after dialog
        self.root.geometry(current_geometry)
        self.root.focus_force()
        
        if filename:
            # Normalize path separators for Windows
            self.main_image_path = os.path.normpath(filename)
            self.main_img_var.set(self.main_image_path)
            self.btn_load_main.config(state="normal")
            
            # Reset all processing buttons when new image is selected
            self.reset_processing_buttons()
            
            # Close any existing image viewers
            self.close_all_viewers()
            
            self.log_status(f"Selected main image: {os.path.basename(self.main_image_path)}")
            self.log_status("Processing buttons reset - ready for new image processing")
    
    def select_dark_field(self):
        """Select dark field image file"""
        # Store current geometry
        current_geometry = self.root.geometry()
        
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Select Dark Field Image (16-bit TIFF)",
            filetypes=[("TIFF files", "*.tiff *.tif"), ("All files", "*.*")]
        )
        
        # Restore geometry after dialog
        self.root.geometry(current_geometry)
        self.root.focus_force()
        
        if filename:
            # Normalize path separators for Windows
            self.dark_field_path = os.path.normpath(filename)
            self.dark_field_var.set(self.dark_field_path)
            self.log_status(f"Selected dark field: {os.path.basename(self.dark_field_path)}")
    
    def select_output_dir(self):
        """Select output directory"""
        # Store current geometry
        current_geometry = self.root.geometry()
        
        dirname = filedialog.askdirectory(
            parent=self.root,
            title="Select Output Directory"
        )
        
        # Restore geometry after dialog
        self.root.geometry(current_geometry)
        self.root.focus_force()
        
        if dirname:
            # Normalize path separators for Windows
            self.output_dir = os.path.normpath(dirname)
            self.output_dir_var.set(self.output_dir)
            self.log_status(f"Selected output directory: {self.output_dir}")
    
    def load_main_image(self):
        """Load and display main image"""
        try:
            # Check if image path is selected
            if not self.main_image_path:
                messagebox.showwarning("No Image Selected", "Please select a main image file first.")
                return
            
            # Reset processing state when loading new image
            self.reset_processing_buttons()
            self.close_all_viewers()
            
            # Check if file exists
            if not os.path.exists(self.main_image_path):
                error_msg = f"Image file not found: {self.main_image_path}"
                self.log_status(f"ERROR: {error_msg}")
                messagebox.showerror("File Not Found", error_msg)
                return
            
            self.log_status(f"Loading image: {os.path.basename(self.main_image_path)}")
            self.processor.raw_image = self.processor.load_image(self.main_image_path)
            
            # Create viewer for main image
            if "main" in self.viewers:
                self.viewers["main"].window.destroy()
            
            self.viewers["main"] = ImageViewer(self.root, "Main Image (RAW)")
            self.viewers["main"].set_image(self.processor.raw_image)
            
            self.btn_bayer_split.config(state="normal")
            self.log_status("Main image loaded successfully")
            
        except Exception as e:
            error_msg = f"Failed to load main image: {str(e)}"
            self.log_status(f"ERROR: {error_msg}")
            messagebox.showerror("Error Loading Image", error_msg)
    
    def bayer_split(self):
        """Perform Bayer split and display R channel"""
        try:
            channels = self.processor.split_bayer_rggb(self.processor.raw_image)
            self.processor.r_raw = channels['R']
            
            # Create viewer for R channel
            if "r_raw" in self.viewers:
                self.viewers["r_raw"].window.destroy()
            
            self.viewers["r_raw"] = ImageViewer(self.root, "R Channel (Raw)")
            self.viewers["r_raw"].set_image(self.processor.r_raw)
            
            self.btn_dark_subtract.config(state="normal")
            self.log_status("Bayer split completed, R channel displayed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to split Bayer pattern: {str(e)}")
    
    def dark_field_subtraction(self):
        """Perform dark field subtraction"""
        try:
            self.processor.dark_field = self.processor.calculate_dark_field(self.processor.r_raw, self.dark_field_path)
            self.processor.r_flu = self.processor.subtract_dark_field(self.processor.r_raw, self.processor.dark_field)
            
            # Create viewer for fluorescence image
            if "r_flu" in self.viewers:
                self.viewers["r_flu"].window.destroy()
            
            self.viewers["r_flu"] = ImageViewer(self.root, "R Channel (Fluorescence)")
            self.viewers["r_flu"].set_image(self.processor.r_flu)
            
            self.btn_enhance.config(state="normal")
            self.log_status("Dark field subtraction completed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to subtract dark field: {str(e)}")
    
    def enhance_contrast(self):
        """Enhance contrast for better cell detection"""
        try:
            self.processor.r_enhanced = self.processor.enhance_contrast_for_detection(self.processor.r_flu)
            
            # Create viewer for enhanced image
            if "r_enhanced" in self.viewers:
                self.viewers["r_enhanced"].window.destroy()
            
            self.viewers["r_enhanced"] = ImageViewer(self.root, "R Channel (Enhanced)")
            self.viewers["r_enhanced"].set_image(self.processor.r_enhanced)
            
            self.btn_gaussian.config(state="normal")
            self.log_status("Contrast enhancement completed - cells should be more visible")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enhance contrast: {str(e)}")
    
    def on_enhancement_change(self, value=None):
        """Handle slider changes for enhancement parameters"""
        # Update config with current slider values
        self.processor.config['contrast_enhancement']['clahe_clip_limit'] = self.clahe_var.get()
        self.processor.config['contrast_enhancement']['clahe_tile_size'] = int(self.tile_var.get())
        self.processor.config['contrast_enhancement']['gamma'] = self.gamma_var.get()
        
        # If real-time update is enabled and we have processed data, re-enhance
        if (self.realtime_var.get() and 
            hasattr(self.processor, 'r_flu') and 
            self.processor.r_flu is not None):
            try:
                # Re-enhance with new parameters
                self.processor.r_enhanced = self.processor.enhance_contrast_for_detection(self.processor.r_flu)
                
                # Update viewer if it exists
                if "r_enhanced" in self.viewers:
                    self.viewers["r_enhanced"].set_image(self.processor.r_enhanced)
                
                # Update status
                self.log_status(f"Parameters updated: CLAHE={self.clahe_var.get():.1f}, Tile={int(self.tile_var.get())}, Gamma={self.gamma_var.get():.2f}")
                
            except Exception as e:
                self.log_status(f"Error updating enhancement: {str(e)}")
    
    def on_enhancement_entry_change(self, event=None):
        """Handle text entry changes for enhancement parameters"""
        try:
            # Validate and update sliders from text entries
            clahe_val = max(0.5, min(5.0, float(self.clahe_entry.get())))
            tile_val = max(2, min(16, int(self.tile_entry.get())))
            gamma_val = max(0.3, min(1.5, float(self.gamma_entry.get())))
            
            # Update variables (this will trigger slider update)
            self.clahe_var.set(clahe_val)
            self.tile_var.set(tile_val)
            self.gamma_var.set(gamma_val)
            
            # Trigger enhancement update
            self.on_enhancement_change()
            
        except ValueError:
            # Invalid input, reset to current slider values
            self.clahe_entry.delete(0, tk.END)
            self.clahe_entry.insert(0, f"{self.clahe_var.get():.1f}")
            self.tile_entry.delete(0, tk.END)
            self.tile_entry.insert(0, str(int(self.tile_var.get())))
            self.gamma_entry.delete(0, tk.END)
            self.gamma_entry.insert(0, f"{self.gamma_var.get():.2f}")
    
    def reset_enhancement_params(self):
        """Reset enhancement parameters to default values"""
        # Default values
        default_clahe = 1.2
        default_tile = 4
        default_gamma = 0.95
        
        # Update sliders
        self.clahe_var.set(default_clahe)
        self.tile_var.set(default_tile)
        self.gamma_var.set(default_gamma)
        
        # Update config
        self.processor.config['contrast_enhancement']['clahe_clip_limit'] = default_clahe
        self.processor.config['contrast_enhancement']['clahe_tile_size'] = default_tile
        self.processor.config['contrast_enhancement']['gamma'] = default_gamma
        
        # Trigger update if real-time is enabled
        self.on_enhancement_change()
        
        self.log_status("Enhancement parameters reset to defaults")
    
    def gaussian_filter(self):
        """Apply Gaussian filtering"""
        try:
            # Use enhanced image if available, otherwise use original fluorescence image
            source_image = getattr(self.processor, 'r_enhanced', self.processor.r_flu)
            self.processor.r_gau = self.processor.apply_gaussian_filter(source_image)
            
            # Create viewer for filtered image
            if "r_gau" in self.viewers:
                self.viewers["r_gau"].window.destroy()
            
            self.viewers["r_gau"] = ImageViewer(self.root, "R Channel (Gaussian Filtered)")
            self.viewers["r_gau"].set_image(self.processor.r_gau)
            
            # Enable ROI, calibration, and threshold buttons
            self.btn_draw_roi.config(state="normal")
            self.btn_clear_roi.config(state="normal")
            self.btn_calibrate.config(state="normal")
            self.btn_threshold.config(state="normal")
            self.log_status("Gaussian filtering completed - you can now draw ROI, calibrate threshold, or proceed to auto thresholding")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply Gaussian filter: {str(e)}")
    
    def draw_roi(self):
        """Enable ROI drawing mode on the Gaussian filtered image"""
        try:
            if "r_gau" not in self.viewers:
                messagebox.showwarning("No Image", "Please complete Gaussian filtering first.")
                return
            
            # Add ROI drawing capability to the viewer
            viewer = self.viewers["r_gau"]
            self.setup_roi_drawing(viewer)
            
            self.log_status("ROI drawing enabled - click and drag on the image to select region")
            messagebox.showinfo("ROI Drawing", 
                              "Click and drag on the Gaussian filtered image to draw a rectangular ROI.\n"
                              "The ROI will be used to limit cell detection to the selected area.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable ROI drawing: {str(e)}")
    
    def setup_roi_drawing(self, viewer):
        """Setup ROI drawing on an image viewer"""
        # Store original image for ROI overlay
        viewer.roi_start = None
        viewer.roi_end = None
        viewer.roi_rect_id = None
        
        # Bind mouse events for ROI drawing
        viewer.canvas.bind("<Button-1>", lambda e: self.roi_mouse_down(e, viewer))
        viewer.canvas.bind("<B1-Motion>", lambda e: self.roi_mouse_drag(e, viewer))
        viewer.canvas.bind("<ButtonRelease-1>", lambda e: self.roi_mouse_up(e, viewer))
    
    def roi_mouse_down(self, event, viewer):
        """Handle mouse down for ROI drawing"""
        # Convert canvas coordinates to image coordinates
        canvas_x = viewer.canvas.canvasx(event.x)
        canvas_y = viewer.canvas.canvasy(event.y)
        
        # Account for image offset and scale
        image_x = (canvas_x - viewer.offset_x) / viewer.scale_factor
        image_y = (canvas_y - viewer.offset_y) / viewer.scale_factor
        
        viewer.roi_start = (image_x, image_y)
        self.roi_drawing = True
    
    def roi_mouse_drag(self, event, viewer):
        """Handle mouse drag for ROI drawing"""
        if not self.roi_drawing or viewer.roi_start is None:
            return
        
        # Convert canvas coordinates to image coordinates
        canvas_x = viewer.canvas.canvasx(event.x)
        canvas_y = viewer.canvas.canvasy(event.y)
        
        image_x = (canvas_x - viewer.offset_x) / viewer.scale_factor
        image_y = (canvas_y - viewer.offset_y) / viewer.scale_factor
        
        viewer.roi_end = (image_x, image_y)
        
        # Update rectangle on canvas
        self.update_roi_rectangle(viewer)
    
    def roi_mouse_up(self, event, viewer):
        """Handle mouse up for ROI drawing"""
        if not self.roi_drawing or viewer.roi_start is None:
            return
        
        # Convert canvas coordinates to image coordinates
        canvas_x = viewer.canvas.canvasx(event.x)
        canvas_y = viewer.canvas.canvasy(event.y)
        
        image_x = (canvas_x - viewer.offset_x) / viewer.scale_factor
        image_y = (canvas_y - viewer.offset_y) / viewer.scale_factor
        
        viewer.roi_end = (image_x, image_y)
        
        # Finalize ROI coordinates
        if viewer.roi_start and viewer.roi_end:
            x1, y1 = viewer.roi_start
            x2, y2 = viewer.roi_end
            
            # Ensure coordinates are in correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Clamp to image bounds
            height, width = self.processor.r_gau.shape[:2]
            x1 = max(0, min(width-1, x1))
            x2 = max(0, min(width-1, x2))
            y1 = max(0, min(height-1, y1))
            y2 = max(0, min(height-1, y2))
            
            self.roi_coords = (int(x1), int(y1), int(x2), int(y2))
            
            self.log_status(f"ROI selected: ({int(x1)}, {int(y1)}) to ({int(x2)}, {int(y2)})")
        
        self.roi_drawing = False
    
    def update_roi_rectangle(self, viewer):
        """Update ROI rectangle on canvas"""
        if not viewer.roi_start or not viewer.roi_end:
            return
        
        # Convert image coordinates to canvas coordinates
        x1, y1 = viewer.roi_start
        x2, y2 = viewer.roi_end
        
        canvas_x1 = x1 * viewer.scale_factor + viewer.offset_x
        canvas_y1 = y1 * viewer.scale_factor + viewer.offset_y
        canvas_x2 = x2 * viewer.scale_factor + viewer.offset_x
        canvas_y2 = y2 * viewer.scale_factor + viewer.offset_y
        
        # Remove previous rectangle
        if viewer.roi_rect_id:
            viewer.canvas.delete(viewer.roi_rect_id)
        
        # Draw new rectangle
        viewer.roi_rect_id = viewer.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline="red", width=2, tags="roi"
        )
    
    def clear_roi(self):
        """Clear the current ROI selection"""
        try:
            self.roi_coords = None
            self.roi_drawing = False
            
            # Remove ROI rectangle from all viewers
            for viewer in self.viewers.values():
                if hasattr(viewer, 'roi_rect_id') and viewer.roi_rect_id:
                    viewer.canvas.delete(viewer.roi_rect_id)
                    viewer.roi_rect_id = None
                viewer.roi_start = None
                viewer.roi_end = None
            
            self.log_status("ROI cleared - cell detection will use entire image")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear ROI: {str(e)}")
    
    def calibrate_threshold(self):
        """Start threshold calibration process"""
        try:
            if "r_gau" not in self.viewers:
                messagebox.showwarning("No Image", "Please complete Gaussian filtering first.")
                return
            
            # Reset calibration state
            self.background_coords = None
            self.cell_coords = None
            self.background_intensity = None
            self.cell_intensity = None
            self.suggested_threshold = None
            
            # Start calibration process
            self.calibration_mode = 'background'
            
            # Setup calibration drawing on viewer
            viewer = self.viewers["r_gau"]
            self.setup_calibration_drawing(viewer)
            
            # Show instructions
            self.log_status("Calibration started - draw rectangle around BACKGROUND area")
            messagebox.showinfo("Threshold Calibration", 
                              "Step 1: Draw a rectangle around a BACKGROUND area (no cells)\n"
                              "Step 2: Draw a rectangle around a CELL area\n"
                              "The system will calculate the optimal threshold automatically.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start calibration: {str(e)}")
    
    def setup_calibration_drawing(self, viewer):
        """Setup calibration rectangle drawing on viewer"""
        # Store calibration state in viewer
        viewer.cal_start = None
        viewer.cal_end = None
        viewer.cal_rect_id = None
        
        # Bind mouse events for calibration drawing
        viewer.canvas.bind("<Button-1>", lambda e: self.cal_mouse_down(e, viewer))
        viewer.canvas.bind("<B1-Motion>", lambda e: self.cal_mouse_drag(e, viewer))
        viewer.canvas.bind("<ButtonRelease-1>", lambda e: self.cal_mouse_up(e, viewer))
    
    def cal_mouse_down(self, event, viewer):
        """Handle mouse down for calibration drawing"""
        if self.calibration_mode is None:
            return
        
        # Convert canvas coordinates to image coordinates
        canvas_x = viewer.canvas.canvasx(event.x)
        canvas_y = viewer.canvas.canvasy(event.y)
        
        image_x = (canvas_x - viewer.offset_x) / viewer.scale_factor
        image_y = (canvas_y - viewer.offset_y) / viewer.scale_factor
        
        viewer.cal_start = (image_x, image_y)
    
    def cal_mouse_drag(self, event, viewer):
        """Handle mouse drag for calibration drawing"""
        if self.calibration_mode is None or viewer.cal_start is None:
            return
        
        # Convert canvas coordinates to image coordinates
        canvas_x = viewer.canvas.canvasx(event.x)
        canvas_y = viewer.canvas.canvasy(event.y)
        
        image_x = (canvas_x - viewer.offset_x) / viewer.scale_factor
        image_y = (canvas_y - viewer.offset_y) / viewer.scale_factor
        
        viewer.cal_end = (image_x, image_y)
        
        # Update rectangle on canvas
        self.update_calibration_rectangle(viewer)
    
    def cal_mouse_up(self, event, viewer):
        """Handle mouse up for calibration drawing"""
        if self.calibration_mode is None or viewer.cal_start is None:
            return
        
        # Convert canvas coordinates to image coordinates
        canvas_x = viewer.canvas.canvasx(event.x)
        canvas_y = viewer.canvas.canvasy(event.y)
        
        image_x = (canvas_x - viewer.offset_x) / viewer.scale_factor
        image_y = (canvas_y - viewer.offset_y) / viewer.scale_factor
        
        viewer.cal_end = (image_x, image_y)
        
        # Process calibration rectangle
        if viewer.cal_start and viewer.cal_end:
            x1, y1 = viewer.cal_start
            x2, y2 = viewer.cal_end
            
            # Ensure coordinates are in correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Clamp to image bounds
            height, width = self.processor.r_gau.shape[:2]
            x1 = max(0, min(width-1, x1))
            x2 = max(0, min(width-1, x2))
            y1 = max(0, min(height-1, y1))
            y2 = max(0, min(height-1, y2))
            
            coords = (int(x1), int(y1), int(x2), int(y2))
            
            if self.calibration_mode == 'background':
                self.background_coords = coords
                self.calculate_background_intensity()
                
                # Move to cell calibration
                self.calibration_mode = 'cell'
                self.log_status("Background selected - now draw rectangle around CELL area")
                messagebox.showinfo("Calibration Step 2", 
                                  "Good! Now draw a rectangle around a CELL area.\n"
                                  "Make sure the rectangle contains mostly cell pixels.")
                
            elif self.calibration_mode == 'cell':
                self.cell_coords = coords
                self.calculate_cell_intensity()
                self.calculate_suggested_threshold()
                
                # Finish calibration
                self.calibration_mode = None
                self.log_status(f"Calibration complete - suggested threshold: {self.suggested_threshold:.1f}")
                
                # Update threshold slider
                self.threshold_var.set(self.suggested_threshold)
                
                # Update threshold scale range based on image
                max_val = self.processor.r_gau.max()
                self.threshold_scale.configure(to=max_val)
        
        # Reset drawing state
        viewer.cal_start = None
        viewer.cal_end = None
    
    def update_calibration_rectangle(self, viewer):
        """Update calibration rectangle on canvas"""
        if not viewer.cal_start or not viewer.cal_end:
            return
        
        # Convert image coordinates to canvas coordinates
        x1, y1 = viewer.cal_start
        x2, y2 = viewer.cal_end
        
        canvas_x1 = x1 * viewer.scale_factor + viewer.offset_x
        canvas_y1 = y1 * viewer.scale_factor + viewer.offset_y
        canvas_x2 = x2 * viewer.scale_factor + viewer.offset_x
        canvas_y2 = y2 * viewer.scale_factor + viewer.offset_y
        
        # Remove previous rectangle
        if viewer.cal_rect_id:
            viewer.canvas.delete(viewer.cal_rect_id)
        
        # Choose color based on calibration mode
        color = "blue" if self.calibration_mode == 'background' else "orange"
        
        # Draw new rectangle
        viewer.cal_rect_id = viewer.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline=color, width=3, tags="calibration"
        )
    
    def calculate_background_intensity(self):
        """Calculate mean intensity in background region"""
        if self.background_coords:
            x1, y1, x2, y2 = self.background_coords
            
            # Ensure valid region
            if x2 > x1 and y2 > y1:
                region = self.processor.r_gau[y1:y2, x1:x2]
                if region.size > 0:
                    self.background_intensity = np.mean(region)
                    self.log_status(f"Background intensity calculated: {self.background_intensity:.1f}")
                else:
                    self.log_status("Error: Background region is empty")
            else:
                self.log_status("Error: Invalid background region coordinates")
            
            self.update_calibration_info()
    
    def calculate_cell_intensity(self):
        """Calculate mean intensity in cell region"""
        if self.cell_coords:
            x1, y1, x2, y2 = self.cell_coords
            
            # Ensure valid region
            if x2 > x1 and y2 > y1:
                region = self.processor.r_gau[y1:y2, x1:x2]
                if region.size > 0:
                    self.cell_intensity = np.mean(region)
                    self.log_status(f"Cell intensity calculated: {self.cell_intensity:.1f}")
                else:
                    self.log_status("Error: Cell region is empty")
            else:
                self.log_status("Error: Invalid cell region coordinates")
            
            self.update_calibration_info()
    
    def calculate_suggested_threshold(self):
        """Calculate suggested threshold based on background and cell intensities"""
        if self.background_intensity is not None and self.cell_intensity is not None:
            # Validate that cell intensity is higher than background
            if self.cell_intensity > self.background_intensity:
                # Use midpoint between background and cell intensities
                self.suggested_threshold = (self.background_intensity + self.cell_intensity) / 2
                self.log_status(f"Threshold calculated: {self.suggested_threshold:.1f} (between {self.background_intensity:.1f} and {self.cell_intensity:.1f})")
            else:
                # If cell intensity is not higher, use a conservative approach
                self.suggested_threshold = self.background_intensity + abs(self.cell_intensity - self.background_intensity) * 0.5
                self.log_status(f"Warning: Cell intensity ({self.cell_intensity:.1f}) not higher than background ({self.background_intensity:.1f})")
                messagebox.showwarning("Calibration Warning", 
                                     f"Cell intensity ({self.cell_intensity:.1f}) is not significantly higher than background ({self.background_intensity:.1f}).\n"
                                     f"Please select a brighter cell region or check your image quality.")
            
            self.update_calibration_info()
        else:
            self.log_status("Error: Cannot calculate threshold - missing intensity values")
    
    def update_calibration_info(self):
        """Update calibration information display"""
        bg_text = f"{self.background_intensity:.1f}" if self.background_intensity is not None else "--"
        cell_text = f"{self.cell_intensity:.1f}" if self.cell_intensity is not None else "--"
        thresh_text = f"{self.suggested_threshold:.1f}" if self.suggested_threshold is not None else "--"
        
        self.calibration_info.set(f"Background: {bg_text} | Cell: {cell_text} | Suggested: {thresh_text}")
    
    def on_threshold_change(self, value=None):
        """Handle threshold slider changes"""
        if (self.threshold_preview_var.get() and 
            hasattr(self.processor, 'r_gau') and 
            self.processor.r_gau is not None):
            try:
                # Apply threshold with current value
                threshold_val = self.threshold_var.get()
                binary = (self.processor.r_gau > threshold_val).astype(np.uint8)
                
                # Apply ROI mask if exists
                if self.roi_coords:
                    x1, y1, x2, y2 = self.roi_coords
                    mask = np.zeros_like(binary, dtype=np.uint8)
                    mask[y1:y2, x1:x2] = 1
                    binary = cv2.bitwise_and(binary, mask)
                
                # Update binary viewer if it exists
                if "r_bin" in self.viewers:
                    self.viewers["r_bin"].set_image(binary * 255)
                
            except Exception as e:
                self.log_status(f"Error in threshold preview: {str(e)}")
    
    def on_threshold_entry_change(self, event=None):
        """Handle threshold text entry changes"""
        try:
            # Validate and update slider from text entry
            max_val = self.processor.r_gau.max() if hasattr(self.processor, 'r_gau') else 65535
            threshold_val = max(0, min(max_val, float(self.threshold_entry.get())))
            
            # Update variable (this will trigger slider update)
            self.threshold_var.set(threshold_val)
            
            # Trigger threshold update
            self.on_threshold_change()
            
        except ValueError:
            # Invalid input, reset to current slider value
            self.threshold_entry.delete(0, tk.END)
            self.threshold_entry.insert(0, f"{self.threshold_var.get():.1f}")
    
    def auto_threshold(self):
        """Apply thresholding (automatic or calibrated)"""
        try:
            # Use calibrated threshold if available, otherwise use automatic
            if self.suggested_threshold is not None and self.threshold_var.get() > 0:
                # Use manual/calibrated threshold
                threshold_val = self.threshold_var.get()
                binary = (self.processor.r_gau > threshold_val).astype(np.uint8)
                
                # Apply ROI mask if exists
                if self.roi_coords:
                    x1, y1, x2, y2 = self.roi_coords
                    mask = np.zeros_like(binary, dtype=np.uint8)
                    mask[y1:y2, x1:x2] = 1
                    binary = cv2.bitwise_and(binary, mask)
                    self.log_status(f"Manual threshold ({threshold_val:.1f}) applied to ROI: ({x1}, {y1}) to ({x2}, {y2})")
                else:
                    self.log_status(f"Manual threshold ({threshold_val:.1f}) applied to entire image")
                    
            else:
                # Use automatic thresholding
                if self.roi_coords:
                    x1, y1, x2, y2 = self.roi_coords
                    roi_image = self.processor.r_gau.copy()
                    
                    # Create mask for ROI
                    mask = np.zeros_like(roi_image, dtype=np.uint8)
                    mask[y1:y2, x1:x2] = 255
                    
                    # Apply automatic thresholding only to ROI area
                    binary = self.processor.apply_threshold(roi_image)
                    
                    # Apply ROI mask to binary result
                    binary = cv2.bitwise_and(binary, mask)
                    
                    self.log_status(f"Auto thresholding applied to ROI: ({x1}, {y1}) to ({x2}, {y2})")
                else:
                    binary = self.processor.apply_threshold(self.processor.r_gau)
                    self.log_status("Auto thresholding applied to entire image")
            
            self.processor.r_bin = self.processor.post_process_binary(binary)
            
            # Create viewer for binary image
            if "r_bin" in self.viewers:
                self.viewers["r_bin"].window.destroy()
            
            self.viewers["r_bin"] = ImageViewer(self.root, "Binary Image (Thresholded)")
            self.viewers["r_bin"].set_image(self.processor.r_bin * 255)  # Convert to 0-255 range
            
            # Enable next step (contour detection)
            self.btn_contours.config(state="normal")
            
            # Log completion status
            if self.roi_coords:
                roi_area = (self.roi_coords[2] - self.roi_coords[0]) * (self.roi_coords[3] - self.roi_coords[1])
                self.log_status(f"Thresholding completed - ROI area: {roi_area} pixels - Next: Find Contours")
            else:
                height, width = self.processor.r_bin.shape[:2]
                self.log_status(f"Thresholding completed - full image processed ({width}x{height} pixels) - Next: Find Contours")
            
            # Show success message if using calibrated threshold
            if self.suggested_threshold is not None and self.threshold_var.get() > 0:
                threshold_val = self.threshold_var.get()
                messagebox.showinfo("Threshold Applied", 
                                  f"Calibrated threshold ({threshold_val:.1f}) applied successfully!\n"
                                  f"Background: {self.background_intensity:.1f}\n"
                                  f"Cell: {self.cell_intensity:.1f}\n"
                                  f"You can now proceed to 'Find Contours'.")
            
        except Exception as e:
            self.log_status(f"ERROR in thresholding: {str(e)}")
            messagebox.showerror("Threshold Error", f"Failed to apply threshold: {str(e)}\n\nPlease try:\n1. Re-run calibration\n2. Check image quality\n3. Adjust threshold manually")
    
    def find_contours(self):
        """Find and display contours"""
        try:
            self.processor.contours = self.processor.find_contours(self.processor.r_bin)
            
            # Create contour overlay image
            contour_image = cv2.cvtColor((self.processor.r_flu / self.processor.r_flu.max() * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)
            
            # Draw contours
            for contour in self.processor.contours:
                cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)
            
            # Create viewer for contours
            if "r_contour" in self.viewers:
                self.viewers["r_contour"].window.destroy()
            
            self.viewers["r_contour"] = ImageViewer(self.root, "Contours")
            self.viewers["r_contour"].set_image(contour_image)
            
            self.btn_measure.config(state="normal")
            self.log_status(f"Found {len(self.processor.contours)} contours")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to find contours: {str(e)}")
    
    def measure_intensity(self):
        """Measure cell intensity and display results"""
        try:
            self.processor.cell_data = self.processor.measure_intensity(self.processor.r_flu, self.processor.contours)
            
            # Create enhanced contour image with area labels
            contour_image = cv2.cvtColor((self.processor.r_flu / self.processor.r_flu.max() * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)
            
            # Draw contours and labels (area + mean intensity)
            for i, (contour, cell_data) in enumerate(zip(self.processor.contours, self.processor.cell_data)):
                # Draw contour
                cv2.drawContours(contour_image, [contour], -1, (0, 255, 0), 2)
                
                # Find top-left point of contour for label placement
                x, y, w, h = cv2.boundingRect(contour)
                
                # Create labels for area, mean intensity, and integrated intensity
                area_text = f"A:{cell_data['area_pixel']}"
                mean_intensity_text = f"Mean:{cell_data['mean_intensity']:.1f}"
                total_intensity_text = f"Total:{cell_data['total_intensity']:.0f}"
                
                # Draw labels with proper spacing
                cv2.putText(contour_image, area_text, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
                cv2.putText(contour_image, mean_intensity_text, (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
                cv2.putText(contour_image, total_intensity_text, (x, y-35), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
            
            # Update contour viewer
            if "r_contour" in self.viewers:
                self.viewers["r_contour"].set_image(contour_image)
            
            # Enable save button
            self.btn_save.config(state="normal")
            
            # Log results
            if self.processor.cell_data:
                avg_mean_intensity = np.mean([cell['mean_intensity'] for cell in self.processor.cell_data])
                avg_total_intensity = np.mean([cell['total_intensity'] for cell in self.processor.cell_data])
                total_integrated = np.sum([cell['total_intensity'] for cell in self.processor.cell_data])
                self.log_status(f"Measured {len(self.processor.cell_data)} cells - "
                              f"Avg mean: {avg_mean_intensity:.2f}, Avg total: {avg_total_intensity:.0f}, "
                              f"Sum integrated: {total_integrated:.0f}")
            else:
                self.log_status("No cells detected")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to measure intensity: {str(e)}")
    
    def save_results(self):
        """Save CSV and overlay image results"""
        try:
            if not self.output_dir:
                # Store current geometry
                current_geometry = self.root.geometry()
                
                self.output_dir = filedialog.askdirectory(
                    parent=self.root,
                    title="Select Output Directory"
                )
                
                # Restore geometry after dialog
                self.root.geometry(current_geometry)
                self.root.focus_force()
                
                if not self.output_dir:
                    return
                # Normalize path separators for Windows
                self.output_dir = os.path.normpath(self.output_dir)
                self.output_dir_var.set(self.output_dir)
            
            base_filename = os.path.splitext(os.path.basename(self.main_image_path))[0]
            
            # Check if we have the required data
            if not hasattr(self.processor, 'cell_data') or not self.processor.cell_data:
                messagebox.showwarning("No Data", 
                                     "No cell data available to save.\n"
                                     "Please complete the full processing pipeline:\n"
                                     "1. Load & process image\n"
                                     "2. Find contours\n"
                                     "3. Measure intensity")
                return
            
            if not hasattr(self.processor, 'contours') or not self.processor.contours:
                messagebox.showwarning("No Contours", 
                                     "No contours available for overlay image.\n"
                                     "Please complete contour detection first.")
                return
            
            # Save results
            self.processor.save_results(self.output_dir, base_filename)
            
            # Verify files were created
            csv_path = os.path.join(self.output_dir, f"{base_filename}-cells.csv")
            overlay_path = os.path.join(self.output_dir, f"{base_filename}-cells-overlay.tiff")
            
            files_created = []
            if os.path.exists(csv_path):
                files_created.append("CSV data file")
            if os.path.exists(overlay_path):
                files_created.append("Overlay image with detected cells")
            
            if files_created:
                files_list = "\n".join([f"✓ {file}" for file in files_created])
                self.log_status(f"Results saved to: {self.output_dir}")
                messagebox.showinfo("Success", 
                                  f"Results saved successfully!\n\n"
                                  f"Files created:\n{files_list}\n\n"
                                  f"Location: {self.output_dir}")
            else:
                self.log_status("ERROR: No files were created")
                messagebox.showerror("Save Error", "No files were created. Check the log for errors.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {str(e)}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainApplication()
    app.run()
