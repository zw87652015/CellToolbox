"""
TIFF Cropping and R Channel Extraction Tool
Allows users to crop TIFF images with RGGB block alignment and extract R channel data
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading


class ImageCropper:
    def __init__(self, root):
        self.root = root
        self.root.title("TIFF Cropper & R Channel Extractor")
        self.root.geometry("1200x800")
        
        # Image data
        self.original_image = None
        self.current_image = None
        self.cropped_image = None
        self.r_channel = None
        self.image_path = None
        
        # Crop selection
        self.crop_start = None
        self.crop_end = None
        self.crop_rect_id = None
        self.is_selecting = False
        
        # Last crop area (x1, y1, x2, y2)
        self.last_crop_area = None
        
        # Display scaling
        self.display_scale = 1.0
        self.max_display_size = (800, 600)
        
        # Exposure enhancement parameters
        self.brightness = 35  # -100 to +100
        self.contrast = 3.0    # 0.1 to 3.0
        self.gamma = 1.0       # 0.1 to 3.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # File operations
        file_frame = ttk.LabelFrame(control_frame, text="File Operations", padding=10)
        file_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(file_frame, text="Open TIFF", command=self.open_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="Reset Crop", command=self.reset_crop).pack(side=tk.LEFT, padx=(0, 5))
        
        # Processing operations
        process_frame = ttk.LabelFrame(control_frame, text="Processing", padding=10)
        process_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        ttk.Button(process_frame, text="Extract R Channel", command=self.extract_r_channel).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(process_frame, text="Save Current Image", command=self.save_current_image).pack(side=tk.LEFT, padx=(0, 5))
        
        # Exposure enhancement controls
        exposure_frame = ttk.LabelFrame(main_frame, text="Exposure Enhancement", padding=10)
        exposure_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # Brightness control
        brightness_frame = ttk.Frame(exposure_frame)
        brightness_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Label(brightness_frame, text="Brightness:").pack(side=tk.TOP, anchor=tk.W)
        self.brightness_var = tk.DoubleVar(value=35)
        self.brightness_scale = ttk.Scale(brightness_frame, from_=-100, to=100, 
                                        variable=self.brightness_var, orient=tk.HORIZONTAL,
                                        command=self.on_exposure_change)
        self.brightness_scale.pack(side=tk.TOP, fill=tk.X)
        self.brightness_label = ttk.Label(brightness_frame, text="35")
        self.brightness_label.pack(side=tk.TOP)
        
        # Contrast control
        contrast_frame = ttk.Frame(exposure_frame)
        contrast_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Label(contrast_frame, text="Contrast:").pack(side=tk.TOP, anchor=tk.W)
        self.contrast_var = tk.DoubleVar(value=3.0)
        self.contrast_scale = ttk.Scale(contrast_frame, from_=0.1, to=3.0, 
                                      variable=self.contrast_var, orient=tk.HORIZONTAL,
                                      command=self.on_exposure_change)
        self.contrast_scale.pack(side=tk.TOP, fill=tk.X)
        self.contrast_label = ttk.Label(contrast_frame, text="3.0")
        self.contrast_label.pack(side=tk.TOP)
        
        # Gamma control
        gamma_frame = ttk.Frame(exposure_frame)
        gamma_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Label(gamma_frame, text="Gamma:").pack(side=tk.TOP, anchor=tk.W)
        self.gamma_var = tk.DoubleVar(value=1.0)
        self.gamma_scale = ttk.Scale(gamma_frame, from_=0.1, to=3.0, 
                                   variable=self.gamma_var, orient=tk.HORIZONTAL,
                                   command=self.on_exposure_change)
        self.gamma_scale.pack(side=tk.TOP, fill=tk.X)
        self.gamma_label = ttk.Label(gamma_frame, text="1.0")
        self.gamma_label.pack(side=tk.TOP)
        
        # Reset button
        reset_frame = ttk.Frame(exposure_frame)
        reset_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(reset_frame, text="Reset\nExposure", command=self.reset_exposure).pack()
        
        # Crop coordinates input
        crop_input_frame = ttk.LabelFrame(main_frame, text="Crop Coordinates", padding=10)
        crop_input_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # Coordinate input fields
        coords_frame = ttk.Frame(crop_input_frame)
        coords_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # X1, Y1 inputs
        xy1_frame = ttk.Frame(coords_frame)
        xy1_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(xy1_frame, text="X1:").pack(side=tk.LEFT)
        self.x1_var = tk.StringVar()
        self.x1_entry = ttk.Entry(xy1_frame, textvariable=self.x1_var, width=8)
        self.x1_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(xy1_frame, text="Y1:").pack(side=tk.LEFT)
        self.y1_var = tk.StringVar()
        self.y1_entry = ttk.Entry(xy1_frame, textvariable=self.y1_var, width=8)
        self.y1_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # X2, Y2 inputs
        xy2_frame = ttk.Frame(coords_frame)
        xy2_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(xy2_frame, text="X2:").pack(side=tk.LEFT)
        self.x2_var = tk.StringVar()
        self.x2_entry = ttk.Entry(xy2_frame, textvariable=self.x2_var, width=8)
        self.x2_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(xy2_frame, text="Y2:").pack(side=tk.LEFT)
        self.y2_var = tk.StringVar()
        self.y2_entry = ttk.Entry(xy2_frame, textvariable=self.y2_var, width=8)
        self.y2_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Crop control buttons
        crop_buttons_frame = ttk.Frame(crop_input_frame)
        crop_buttons_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(crop_buttons_frame, text="Apply Crop", command=self.apply_manual_crop).pack(side=tk.TOP, pady=(0, 5))
        ttk.Button(crop_buttons_frame, text="Use Last Crop", command=self.use_last_crop).pack(side=tk.TOP, pady=(0, 5))
        ttk.Button(crop_buttons_frame, text="Clear Crop", command=self.clear_crop_inputs).pack(side=tk.TOP)
        
        # Image display area
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(display_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='gray')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(display_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # Info panel
        info_frame = ttk.LabelFrame(display_frame, text="Information", padding=10)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        self.info_text = tk.Text(info_frame, width=30, height=20, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Open a TIFF file to begin")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)
        
    def log_info(self, message):
        """Add message to info panel"""
        self.info_text.insert(tk.END, f"{message}\n")
        self.info_text.see(tk.END)
        self.root.update_idletasks()
        
    def on_exposure_change(self, value=None):
        """Handle exposure parameter changes"""
        # Update parameter values
        self.brightness = self.brightness_var.get()
        self.contrast = self.contrast_var.get()
        self.gamma = self.gamma_var.get()
        
        # Update labels
        self.brightness_label.config(text=f"{self.brightness:.1f}")
        self.contrast_label.config(text=f"{self.contrast:.2f}")
        self.gamma_label.config(text=f"{self.gamma:.2f}")
        
        # Update display if image is loaded
        if self.current_image is not None:
            self.display_image()
            
    def reset_exposure(self):
        """Reset exposure parameters to defaults"""
        self.brightness_var.set(0.0)
        self.contrast_var.set(1.0)
        self.gamma_var.set(1.0)
        self.on_exposure_change()
        self.log_info("Reset exposure parameters")
        
    def apply_exposure_enhancement(self, image):
        """Apply exposure enhancement to image"""
        if image is None:
            return None
            
        # Convert to float for processing
        enhanced = image.astype(np.float32)
        
        # Apply brightness adjustment
        if self.brightness != 0:
            if image.dtype == np.uint16:
                brightness_scale = 655.35  # 65535 / 100
            else:
                brightness_scale = 2.55    # 255 / 100
            enhanced = enhanced + (self.brightness * brightness_scale)
        
        # Apply contrast adjustment
        if self.contrast != 1.0:
            # Apply contrast around the middle value
            if image.dtype == np.uint16:
                mid_value = 32767.5  # Middle of 16-bit range
            else:
                mid_value = 127.5    # Middle of 8-bit range
            enhanced = (enhanced - mid_value) * self.contrast + mid_value
        
        # Apply gamma correction
        if self.gamma != 1.0:
            # Normalize to 0-1 range
            if image.dtype == np.uint16:
                max_value = 65535.0
            else:
                max_value = 255.0
                
            normalized = np.clip(enhanced / max_value, 0, 1)
            gamma_corrected = np.power(normalized, 1.0 / self.gamma)
            enhanced = gamma_corrected * max_value
        
        # Clip to valid range and convert back to original dtype
        if image.dtype == np.uint16:
            enhanced = np.clip(enhanced, 0, 65535).astype(np.uint16)
        else:
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
            
        return enhanced
        
    def _load_image_unicode_safe(self, image_path):
        """Load image with Unicode path support"""
        try:
            # Method 1: Try standard OpenCV method (works for ASCII paths)
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if image is not None:
                return image
            
            # Method 2: Try numpy + cv2.imdecode for Unicode paths
            # Read file as binary data
            with open(image_path, 'rb') as f:
                file_bytes = f.read()
            
            # Convert to numpy array
            file_array = np.frombuffer(file_bytes, dtype=np.uint8)
            
            # Decode using OpenCV
            image = cv2.imdecode(file_array, cv2.IMREAD_UNCHANGED)
            
            if image is not None:
                return image
            
            # Method 3: Try PIL as fallback for TIFF files
            from PIL import Image as PILImage
            
            pil_image = PILImage.open(image_path)
            
            # Convert PIL image to numpy array
            if pil_image.mode == 'I;16':  # 16-bit grayscale
                image = np.array(pil_image, dtype=np.uint16)
            elif pil_image.mode == 'L':   # 8-bit grayscale
                image = np.array(pil_image, dtype=np.uint8)
            elif pil_image.mode == 'I':   # 32-bit integer
                image = np.array(pil_image, dtype=np.uint32)
            else:
                # Convert to grayscale if needed
                pil_image = pil_image.convert('L')
                image = np.array(pil_image, dtype=np.uint8)
            
            return image
            
        except Exception as e:
            print(f"All image loading methods failed for {image_path}: {str(e)}")
            return None

    def open_image(self):
        """Open and display a TIFF image"""
        file_path = filedialog.askopenfilename(
            title="Select TIFF Image",
            filetypes=[("TIFF files", "*.tif *.tiff"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Load image using Unicode-safe method
            self.original_image = self._load_image_unicode_safe(file_path)
            if self.original_image is None:
                raise ValueError("Could not load image - check file path and format")
                
            self.image_path = file_path
            self.current_image = self.original_image.copy()
            
            # Log image info
            height, width = self.original_image.shape[:2]
            dtype = self.original_image.dtype
            
            self.log_info(f"Loaded: {os.path.basename(file_path)}")
            self.log_info(f"Size: {width} x {height}")
            self.log_info(f"Type: {dtype}")
            
            # Check RGGB alignment
            rggb_aligned = (width % 2 == 0) and (height % 2 == 0)
            self.log_info(f"RGGB Aligned: {'Yes' if rggb_aligned else 'No'}")
            
            if not rggb_aligned:
                self.log_info("Warning: Image dimensions not even - RGGB pattern may be misaligned")
            
            self.display_image()
            self.status_var.set(f"Loaded: {os.path.basename(file_path)} ({width}x{height})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            
    def display_image(self):
        """Display the current image on canvas"""
        if self.current_image is None:
            return
            
        # Apply exposure enhancement
        enhanced_image = self.apply_exposure_enhancement(self.current_image)
        
        # Calculate display scale
        height, width = enhanced_image.shape[:2]
        scale_x = self.max_display_size[0] / width
        scale_y = self.max_display_size[1] / height
        self.display_scale = min(scale_x, scale_y, 1.0)  # Don't upscale
        
        # Resize for display
        if self.display_scale < 1.0:
            display_width = int(width * self.display_scale)
            display_height = int(height * self.display_scale)
            display_image = cv2.resize(enhanced_image, (display_width, display_height))
        else:
            display_image = enhanced_image.copy()
            display_width, display_height = width, height
        
        # Normalize for display (handle 16-bit images)
        if display_image.dtype == np.uint16:
            # Normalize 16-bit to 8-bit for display
            display_image = (display_image / 256).astype(np.uint8)
        
        # Convert to PIL Image
        if len(display_image.shape) == 2:  # Grayscale
            pil_image = Image.fromarray(display_image, mode='L')
        else:  # Color
            pil_image = Image.fromarray(cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB))
            
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(pil_image)
        
        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def start_crop(self, event):
        """Start crop selection"""
        if self.current_image is None:
            return
            
        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        self.crop_start = (int(canvas_x / self.display_scale), int(canvas_y / self.display_scale))
        self.is_selecting = True
        
        # Remove previous crop rectangle
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
            
    def update_crop(self, event):
        """Update crop selection rectangle"""
        if not self.is_selecting or self.current_image is None:
            return
            
        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        current_pos = (int(canvas_x / self.display_scale), int(canvas_y / self.display_scale))
        
        # Calculate RGGB-aligned rectangle
        aligned_rect = self.align_to_rggb(self.crop_start, current_pos)
        
        # Convert back to canvas coordinates for display
        x1, y1, x2, y2 = aligned_rect
        canvas_x1 = x1 * self.display_scale
        canvas_y1 = y1 * self.display_scale
        canvas_x2 = x2 * self.display_scale
        canvas_y2 = y2 * self.display_scale
        
        # Remove previous rectangle
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
            
        # Draw new rectangle
        self.crop_rect_id = self.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline='red', width=2
        )
        
        # Update status
        width = x2 - x1
        height = y2 - y1
        self.status_var.set(f"Selecting: {width} x {height} (RGGB aligned)")
        
    def end_crop(self, event):
        """End crop selection"""
        if not self.is_selecting or self.current_image is None:
            return
            
        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        current_pos = (int(canvas_x / self.display_scale), int(canvas_y / self.display_scale))
        
        # Calculate final RGGB-aligned rectangle
        aligned_rect = self.align_to_rggb(self.crop_start, current_pos)
        x1, y1, x2, y2 = aligned_rect
        
        # Perform crop
        if x2 > x1 and y2 > y1:
            self.cropped_image = self.original_image[y1:y2, x1:x2].copy()
            self.current_image = self.cropped_image.copy()
            
            # Record last crop area
            self.last_crop_area = (x1, y1, x2, y2)
            
            # Update coordinate input fields
            self.update_crop_inputs(x1, y1, x2, y2)
            
            # Log crop info
            crop_width = x2 - x1
            crop_height = y2 - y1
            self.log_info(f"Cropped to: {crop_width} x {crop_height}")
            self.log_info(f"Region: ({x1},{y1}) to ({x2},{y2})")
            
            # Update display
            self.display_image()
            self.status_var.set(f"Cropped: {crop_width} x {crop_height}")
        
        self.is_selecting = False
        
    def align_to_rggb(self, start, end):
        """Align rectangle to RGGB 2x2 blocks"""
        x1, y1 = start
        x2, y2 = end
        
        # Ensure proper order
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        # Align to even coordinates (RGGB blocks are 2x2)
        x1 = (x1 // 2) * 2
        y1 = (y1 // 2) * 2
        x2 = ((x2 + 1) // 2) * 2  # Round up to next even
        y2 = ((y2 + 1) // 2) * 2  # Round up to next even
        
        # Ensure within image bounds
        if self.current_image is not None:
            height, width = self.current_image.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)
        
        return x1, y1, x2, y2
        
    def reset_crop(self):
        """Reset to original image"""
        if self.original_image is None:
            return
            
        self.current_image = self.original_image.copy()
        self.cropped_image = None
        self.r_channel = None
        
        # Remove crop rectangle
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None
            
        self.display_image()
        self.log_info("Reset to original image")
        self.status_var.set("Reset to original image")
        
    def update_crop_inputs(self, x1, y1, x2, y2):
        """Update crop coordinate input fields"""
        self.x1_var.set(str(x1))
        self.y1_var.set(str(y1))
        self.x2_var.set(str(x2))
        self.y2_var.set(str(y2))
        
    def clear_crop_inputs(self):
        """Clear crop coordinate input fields"""
        self.x1_var.set("")
        self.y1_var.set("")
        self.x2_var.set("")
        self.y2_var.set("")
        
    def use_last_crop(self):
        """Use the last recorded crop area"""
        if self.last_crop_area is None:
            messagebox.showinfo("Info", "No previous crop area recorded")
            return
            
        x1, y1, x2, y2 = self.last_crop_area
        self.update_crop_inputs(x1, y1, x2, y2)
        self.log_info(f"Loaded last crop area: ({x1},{y1}) to ({x2},{y2})")
        
    def apply_manual_crop(self):
        """Apply crop using manually entered coordinates"""
        if self.original_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            # Parse coordinates
            x1 = int(self.x1_var.get()) if self.x1_var.get() else 0
            y1 = int(self.y1_var.get()) if self.y1_var.get() else 0
            x2 = int(self.x2_var.get()) if self.x2_var.get() else self.original_image.shape[1]
            y2 = int(self.y2_var.get()) if self.y2_var.get() else self.original_image.shape[0]
            
            # Validate coordinates
            height, width = self.original_image.shape[:2]
            if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
                messagebox.showerror("Error", f"Coordinates out of bounds. Image size: {width} x {height}")
                return
                
            if x1 >= x2 or y1 >= y2:
                messagebox.showerror("Error", "Invalid coordinates. X2 must be > X1 and Y2 must be > Y1")
                return
            
            # Align to RGGB blocks
            aligned_rect = self.align_to_rggb((x1, y1), (x2, y2))
            x1, y1, x2, y2 = aligned_rect
            
            # Update input fields with aligned coordinates
            self.update_crop_inputs(x1, y1, x2, y2)
            
            # Perform crop
            self.cropped_image = self.original_image[y1:y2, x1:x2].copy()
            self.current_image = self.cropped_image.copy()
            
            # Record last crop area
            self.last_crop_area = (x1, y1, x2, y2)
            
            # Log crop info
            crop_width = x2 - x1
            crop_height = y2 - y1
            self.log_info(f"Manual crop applied: {crop_width} x {crop_height}")
            self.log_info(f"RGGB-aligned region: ({x1},{y1}) to ({x2},{y2})")
            
            # Update display
            self.display_image()
            self.status_var.set(f"Manual crop: {crop_width} x {crop_height}")
            
            # Draw crop rectangle on canvas
            self.draw_crop_rectangle(x1, y1, x2, y2)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer coordinates")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply crop: {str(e)}")
            
    def draw_crop_rectangle(self, x1, y1, x2, y2):
        """Draw crop rectangle on canvas"""
        # Remove previous rectangle
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
            
        # Convert to canvas coordinates
        canvas_x1 = x1 * self.display_scale
        canvas_y1 = y1 * self.display_scale
        canvas_x2 = x2 * self.display_scale
        canvas_y2 = y2 * self.display_scale
        
        # Draw new rectangle
        self.crop_rect_id = self.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline='red', width=2
        )
        
    def extract_r_channel(self):
        """Extract R channel using [0::2, 0::2] indexing"""
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            # Extract R channel (top-left of each 2x2 RGGB block)
            self.r_channel = self.current_image[0::2, 0::2].copy()
            
            # Log extraction info
            original_height, original_width = self.current_image.shape[:2]
            r_height, r_width = self.r_channel.shape[:2]
            
            self.log_info(f"Extracted R channel:")
            self.log_info(f"Original: {original_width} x {original_height}")
            self.log_info(f"R channel: {r_width} x {r_height}")
            self.log_info(f"Reduction: {original_width//r_width}x")
            
            # Update display to show R channel
            self.current_image = self.r_channel.copy()
            self.display_image()
            
            self.status_var.set(f"R channel extracted: {r_width} x {r_height}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract R channel: {str(e)}")
            
    def save_current_image(self):
        """Save the currently displayed image as TIFF"""
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
        
        # Apply current exposure enhancement to get what user sees
        enhanced_image = self.apply_exposure_enhancement(self.current_image)
        
        # Generate default filename based on current state
        if self.image_path:
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
        else:
            base_name = "image"
            
        # Determine suffix based on current state
        if self.r_channel is not None and np.array_equal(self.current_image, self.r_channel):
            suffix = "r_channel"
        elif self.cropped_image is not None and np.array_equal(self.current_image, self.cropped_image):
            suffix = "cropped"
        else:
            suffix = "processed"
            
        default_name = f"{base_name}_{suffix}.tif"
        
        # Ask user for save location
        save_path = filedialog.asksaveasfilename(
            title="Save Current Image",
            defaultextension=".tif",
            initialfile=default_name,  # Fixed: use initialfile instead of initialname
            filetypes=[("TIFF files", "*.tif"), ("All files", "*.*")]
        )
        
        if not save_path:
            return
            
        try:
            # Save using Unicode-safe method
            success = self._save_image_unicode_safe(enhanced_image, save_path)
            
            if success:
                height, width = enhanced_image.shape[:2]
                self.log_info(f"Saved current image: {os.path.basename(save_path)}")
                self.log_info(f"Size: {width} x {height}")
                self.status_var.set(f"Saved: {os.path.basename(save_path)}")
                messagebox.showinfo("Success", f"Image saved successfully:\n{save_path}")
            else:
                raise RuntimeError("All save methods failed")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")
        
    def _save_image_unicode_safe(self, image, output_path):
        """Save image with Unicode path support"""
        try:
            # Method 1: Try direct cv2.imwrite first
            success = cv2.imwrite(output_path, image)
            if success:
                return True
            else:
                raise RuntimeError("cv2.imwrite returned False")
                
        except Exception as e1:
            print(f"cv2.imwrite failed, trying alternative method: {str(e1)}")
            
            try:
                # Method 2: Use PIL for Unicode path support
                from PIL import Image as PILImage
                
                # Handle different image types
                if image.dtype == np.uint16:
                    # 16-bit grayscale
                    pil_image = PILImage.fromarray(image, mode='I;16')
                elif image.dtype == np.uint8:
                    if len(image.shape) == 2:
                        # 8-bit grayscale
                        pil_image = PILImage.fromarray(image, mode='L')
                    else:
                        # 8-bit color - convert BGR to RGB
                        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        pil_image = PILImage.fromarray(image_rgb, mode='RGB')
                else:
                    # Convert to 16-bit
                    image_16 = image.astype(np.uint16)
                    pil_image = PILImage.fromarray(image_16, mode='I;16')
                
                # Save with PIL
                pil_image.save(output_path, format='TIFF', compression='lzw')
                return True
                
            except Exception as e2:
                print(f"PIL method failed, trying encoded path: {str(e2)}")
                
                try:
                    # Method 3: Use cv2.imencode and write binary
                    # Encode image to memory
                    success, encoded_img = cv2.imencode('.tiff', image)
                    if not success:
                        raise RuntimeError("cv2.imencode failed")
                    
                    # Write binary data to file
                    with open(output_path, 'wb') as f:
                        f.write(encoded_img.tobytes())
                    
                    return True
                    
                except Exception as e3:
                    print(f"All save methods failed: cv2.imwrite={str(e1)}, PIL={str(e2)}, binary={str(e3)}")
                    
                    # Final fallback: try saving to a simple ASCII path first, then copy
                    try:
                        import tempfile
                        import shutil
                        
                        # Create temporary file with ASCII name
                        with tempfile.NamedTemporaryFile(suffix='.tiff', delete=False) as tmp_file:
                            temp_path = tmp_file.name
                        
                        # Save to temp path
                        success = cv2.imwrite(temp_path, image)
                        if success:
                            # Copy to final destination
                            shutil.copy2(temp_path, output_path)
                            os.unlink(temp_path)  # Clean up temp file
                            return True
                        else:
                            raise RuntimeError("Even temp file method failed")
                            
                    except Exception as e4:
                        print(f"All save methods failed including temp file: {str(e4)}")
                        return False

def main():
    """Main entry point"""
    root = tk.Tk()
    app = ImageCropper(root)
    
    # Add instructions
    instructions = """Instructions:
1. Click 'Open TIFF' to load an image
2. Adjust exposure controls for better visualization:
   - Brightness: -100 to +100 (darker/brighter)
   - Contrast: 0.1 to 3.0 (lower/higher contrast)
   - Gamma: 0.1 to 3.0 (shadow/highlight adjustment)
3. Crop the image (two methods):
   - Method A: Click and drag to select crop area
   - Method B: Enter coordinates (X1,Y1,X2,Y2) and click 'Apply Crop'
4. Use crop controls:
   - 'Use Last Crop': Reload previous crop coordinates
   - 'Clear Crop': Clear coordinate input fields
5. Click 'Extract R Channel' to get R[0::2,0::2] if needed
6. Click 'Save Current Image' to save what you see as TIFF

The crop area automatically snaps to even coordinates to maintain RGGB alignment.
Last crop coordinates are remembered and can be reused on other images.
The save button saves exactly what you see on screen with all enhancements applied."""
    
    app.log_info(instructions)
    
    root.mainloop()


if __name__ == "__main__":
    main()
