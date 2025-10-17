"""
Scale Bar Measurement Tool
Allows users to measure scale bars in microscopy images and calculate pixel-to-micron ratios.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import json
from datetime import datetime
import os


class ScaleBarMeasurement:
    """Main application for scale bar measurement"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Scale Bar Measurement Tool")
        self.root.geometry("1200x800")
        
        # Image data
        self.image = None
        self.image_path = None
        self.display_image = None
        
        # Zoom and pan
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        
        # Line drawing
        self.line_start = None
        self.line_end = None
        self.is_drawing = False
        self.temp_line_end = None
        
        # Measurement
        self.real_world_distance = 100.0  # Default 100 μm
        self.pixel_distance = None
        self.pixels_per_micron = None
        
        # Image processing
        self.blur_sigma = 0.0  # Default no blur
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the user interface"""
        # Top control panel
        control_frame = tk.Frame(self.root, bg='lightgray', height=100)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # File controls
        file_frame = tk.LabelFrame(control_frame, text="File", bg='lightgray')
        file_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        tk.Button(file_frame, text="Load Image", command=self.load_image, 
                 width=12, height=2).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="Save Result", command=self.save_result,
                 width=12, height=2).pack(side=tk.LEFT, padx=2)
        
        # Zoom controls
        zoom_frame = tk.LabelFrame(control_frame, text="Zoom", bg='lightgray')
        zoom_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        tk.Button(zoom_frame, text="Zoom In (+)", command=self.zoom_in,
                 width=12, height=1).pack(side=tk.TOP, padx=2, pady=1)
        tk.Button(zoom_frame, text="Zoom Out (-)", command=self.zoom_out,
                 width=12, height=1).pack(side=tk.TOP, padx=2, pady=1)
        tk.Button(zoom_frame, text="Fit (F)", command=self.zoom_fit,
                 width=12, height=1).pack(side=tk.TOP, padx=2, pady=1)
        
        # Measurement controls
        measure_frame = tk.LabelFrame(control_frame, text="Measurement", bg='lightgray')
        measure_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        distance_frame = tk.Frame(measure_frame, bg='lightgray')
        distance_frame.pack(side=tk.TOP, padx=2, pady=2)
        tk.Label(distance_frame, text="Real Distance (μm):", bg='lightgray').pack(side=tk.LEFT)
        self.distance_var = tk.StringVar(value="100.0")
        tk.Entry(distance_frame, textvariable=self.distance_var, width=10).pack(side=tk.LEFT, padx=2)
        
        tk.Button(measure_frame, text="Clear Line", command=self.clear_line,
                 width=12, height=1).pack(side=tk.TOP, padx=2, pady=1)
        
        # Image processing controls
        process_frame = tk.LabelFrame(control_frame, text="Image Processing", bg='lightgray')
        process_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        blur_label_frame = tk.Frame(process_frame, bg='lightgray')
        blur_label_frame.pack(side=tk.TOP, padx=2, pady=2)
        tk.Label(blur_label_frame, text="Gaussian Blur σ:", bg='lightgray').pack(side=tk.LEFT)
        self.blur_value_label = tk.Label(blur_label_frame, text="0.0", bg='lightgray', width=4)
        self.blur_value_label.pack(side=tk.LEFT, padx=5)
        
        self.blur_slider = tk.Scale(process_frame, from_=0, to=5.0, resolution=0.1,
                                   orient=tk.HORIZONTAL, command=self.on_blur_change,
                                   bg='lightgray', length=120)
        self.blur_slider.set(0.0)
        self.blur_slider.pack(side=tk.TOP, padx=2, pady=1)
        
        # Results display
        result_frame = tk.LabelFrame(control_frame, text="Results", bg='lightgray')
        result_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(result_frame, height=4, width=40)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Canvas for image display
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg='gray', cursor='cross')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready. Load an image to begin.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<B3-Motion>', self.on_pan_drag)
        self.canvas.bind('<ButtonRelease-3>', self.on_pan_release)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        
        # Keyboard shortcuts
        self.root.bind('<plus>', lambda e: self.zoom_in())
        self.root.bind('<minus>', lambda e: self.zoom_out())
        self.root.bind('<equal>', lambda e: self.zoom_in())  # For + without shift
        self.root.bind('f', lambda e: self.zoom_fit())
        self.root.bind('F', lambda e: self.zoom_fit())
        
    def load_image_with_chinese_path(self, file_path):
        """Load image with support for Chinese paths"""
        try:
            # Use numpy.fromfile to read file bytes (supports Chinese paths)
            file_bytes = np.fromfile(file_path, dtype=np.uint8)
            
            # Decode image from bytes
            img = cv2.imdecode(file_bytes, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_GRAYSCALE)
            
            return img
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")
    
    def load_image(self):
        """Load a grayscale TIFF image"""
        file_path = filedialog.askopenfilename(
            title="Select Grayscale TIFF Image",
            filetypes=[("TIFF files", "*.tif *.tiff"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Load image with Chinese path support
            img = self.load_image_with_chinese_path(file_path)
            
            if img is None:
                raise ValueError("Failed to load image")
                
            self.image = img
            self.image_path = file_path
            
            # Reset measurement
            self.clear_line()
            self.pixel_distance = None
            self.pixels_per_micron = None
            
            # Reset view
            self.zoom_fit()
            
            self.status_var.set(f"Loaded: {os.path.basename(file_path)} - "
                              f"Size: {img.shape[1]}x{img.shape[0]} - "
                              f"Depth: {img.dtype}")
            
            self.update_result_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{str(e)}")
            
    def on_blur_change(self, value):
        """Handle blur slider change"""
        self.blur_sigma = float(value)
        self.blur_value_label.config(text=f"{self.blur_sigma:.1f}")
        if self.image is not None:
            self.update_display()
    
    def normalize_for_display(self, img):
        """Normalize image to 8-bit for display"""
        if img.dtype == np.uint16:
            # Normalize 16-bit to 8-bit
            img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
            return img_norm.astype(np.uint8)
        elif img.dtype == np.uint8:
            return img
        else:
            # Float image
            img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
            return img_norm.astype(np.uint8)
            
    def update_display(self):
        """Update the canvas with the current image and zoom level"""
        if self.image is None:
            return
            
        # Start with original image
        img_process = self.image.copy()
        
        # Apply Gaussian blur if sigma > 0
        if self.blur_sigma > 0:
            # Calculate kernel size (must be odd)
            ksize = int(2 * np.ceil(3 * self.blur_sigma) + 1)
            if ksize % 2 == 0:
                ksize += 1
            img_process = cv2.GaussianBlur(img_process, (ksize, ksize), self.blur_sigma)
        
        # Normalize to 8-bit
        img_display = self.normalize_for_display(img_process)
        
        # Convert to RGB for colored line drawing
        img_display = cv2.cvtColor(img_display, cv2.COLOR_GRAY2RGB)
        
        # Calculate adaptive line thickness based on image size and zoom
        # Base thickness: 1 pixel for every 500 pixels of image width, minimum 1
        base_thickness = max(1, int(self.image.shape[1] / 500))
        line_thickness = base_thickness
        circle_radius = max(2, base_thickness * 2)
        
        # Draw the line if exists
        if self.line_start and self.line_end:
            cv2.line(img_display, self.line_start, self.line_end, (0, 255, 0), line_thickness)
            cv2.circle(img_display, self.line_start, circle_radius, (255, 0, 0), -1)
            cv2.circle(img_display, self.line_end, circle_radius, (255, 0, 0), -1)
        elif self.line_start and self.temp_line_end:
            # Draw temporary line while dragging
            cv2.line(img_display, self.line_start, self.temp_line_end, (255, 255, 0), line_thickness)
            cv2.circle(img_display, self.line_start, circle_radius, (255, 0, 0), -1)
            
        # Apply zoom
        h, w = img_display.shape[:2]
        new_w = int(w * self.zoom_level)
        new_h = int(h * self.zoom_level)
        
        if self.zoom_level > 1:
            # Use nearest neighbor for pixel-perfect zoom
            img_zoomed = cv2.resize(img_display, (new_w, new_h), 
                                   interpolation=cv2.INTER_NEAREST)
        else:
            img_zoomed = cv2.resize(img_display, (new_w, new_h), 
                                   interpolation=cv2.INTER_AREA)
        
        # Convert to PIL Image
        img_pil = Image.fromarray(img_zoomed)
        self.display_image = ImageTk.PhotoImage(img_pil)
        
        # Update canvas
        self.canvas.delete('all')
        self.canvas.create_image(self.pan_offset_x, self.pan_offset_y, 
                                anchor=tk.NW, image=self.display_image)
        
        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, new_w, new_h))
        
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to image coordinates"""
        img_x = int((canvas_x - self.pan_offset_x) / self.zoom_level)
        img_y = int((canvas_y - self.pan_offset_y) / self.zoom_level)
        return img_x, img_y
        
    def on_mouse_down(self, event):
        """Handle mouse down for line drawing"""
        if self.image is None:
            return
            
        # Convert to image coordinates
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        
        # Check bounds
        if 0 <= img_x < self.image.shape[1] and 0 <= img_y < self.image.shape[0]:
            self.line_start = (img_x, img_y)
            self.is_drawing = True
            self.temp_line_end = (img_x, img_y)
            self.status_var.set("Drawing line... Release to finish.")
            
    def on_mouse_drag(self, event):
        """Handle mouse drag for line drawing"""
        if self.is_drawing and self.image is not None:
            img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
            
            # Clamp to image bounds
            img_x = max(0, min(img_x, self.image.shape[1] - 1))
            img_y = max(0, min(img_y, self.image.shape[0] - 1))
            
            self.temp_line_end = (img_x, img_y)
            self.update_display()
            
    def on_mouse_up(self, event):
        """Handle mouse up to finish line drawing"""
        if self.is_drawing and self.image is not None:
            img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
            
            # Clamp to image bounds
            img_x = max(0, min(img_x, self.image.shape[1] - 1))
            img_y = max(0, min(img_y, self.image.shape[0] - 1))
            
            self.line_end = (img_x, img_y)
            self.is_drawing = False
            self.temp_line_end = None
            
            # Calculate measurement
            self.calculate_measurement()
            self.update_display()
            
    def on_right_click(self, event):
        """Start panning"""
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor='fleur')
        
    def on_pan_drag(self, event):
        """Handle panning"""
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.pan_offset_x += dx
            self.pan_offset_y += dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.update_display()
            
    def on_pan_release(self, event):
        """Stop panning"""
        self.is_panning = False
        self.canvas.config(cursor='cross')
        
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        if self.image is None:
            return
            
        # Get mouse position in image coordinates before zoom
        mouse_img_x, mouse_img_y = self.canvas_to_image_coords(event.x, event.y)
        
        # Zoom
        if event.delta > 0:
            self.zoom_level *= 1.2
        else:
            self.zoom_level /= 1.2
            
        # Clamp zoom level
        self.zoom_level = max(0.1, min(self.zoom_level, 50.0))
        
        # Adjust pan to keep mouse position centered
        self.pan_offset_x = event.x - mouse_img_x * self.zoom_level
        self.pan_offset_y = event.y - mouse_img_y * self.zoom_level
        
        self.update_display()
        self.status_var.set(f"Zoom: {self.zoom_level:.1f}x")
        
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level *= 1.5
        self.zoom_level = min(self.zoom_level, 50.0)
        self.update_display()
        self.status_var.set(f"Zoom: {self.zoom_level:.1f}x")
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_level /= 1.5
        self.zoom_level = max(self.zoom_level, 0.1)
        self.update_display()
        self.status_var.set(f"Zoom: {self.zoom_level:.1f}x")
        
    def zoom_fit(self):
        """Fit image to canvas"""
        if self.image is None:
            return
            
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_h, img_w = self.image.shape[:2]
        
        # Calculate zoom to fit
        zoom_w = canvas_w / img_w
        zoom_h = canvas_h / img_h
        self.zoom_level = min(zoom_w, zoom_h) * 0.95  # 95% to leave some margin
        
        # Center image
        self.pan_offset_x = (canvas_w - img_w * self.zoom_level) / 2
        self.pan_offset_y = (canvas_h - img_h * self.zoom_level) / 2
        
        self.update_display()
        self.status_var.set(f"Zoom: {self.zoom_level:.1f}x (Fit)")
        
    def clear_line(self):
        """Clear the drawn line"""
        self.line_start = None
        self.line_end = None
        self.temp_line_end = None
        self.pixel_distance = None
        self.pixels_per_micron = None
        
        if self.image is not None:
            self.update_display()
            
        self.update_result_display()
        self.status_var.set("Line cleared. Draw a new line.")
        
    def calculate_measurement(self):
        """Calculate pixel-to-micron ratio"""
        if not self.line_start or not self.line_end:
            return
            
        try:
            # Get real world distance
            self.real_world_distance = float(self.distance_var.get())
            
            # Calculate pixel distance
            dx = self.line_end[0] - self.line_start[0]
            dy = self.line_end[1] - self.line_start[1]
            self.pixel_distance = np.sqrt(dx**2 + dy**2)
            
            # Calculate pixels per micron
            if self.pixel_distance > 0:
                self.pixels_per_micron = self.pixel_distance / self.real_world_distance
                
                self.update_result_display()
                self.status_var.set(f"Measurement complete: {self.pixels_per_micron:.4f} pixels/μm")
            else:
                messagebox.showwarning("Warning", "Line length is zero. Please draw a longer line.")
                
        except ValueError:
            messagebox.showerror("Error", "Invalid real world distance. Please enter a valid number.")
            
    def update_result_display(self):
        """Update the results text box"""
        self.result_text.delete(1.0, tk.END)
        
        if self.image_path:
            self.result_text.insert(tk.END, f"Image: {os.path.basename(self.image_path)}\n")
            
        if self.pixel_distance is not None and self.pixels_per_micron is not None:
            self.result_text.insert(tk.END, f"Pixel Distance: {self.pixel_distance:.2f} px\n")
            self.result_text.insert(tk.END, f"Real Distance: {self.real_world_distance:.2f} μm\n")
            self.result_text.insert(tk.END, f"Ratio: {self.pixels_per_micron:.4f} px/μm\n")
            self.result_text.insert(tk.END, f"Inverse: {1/self.pixels_per_micron:.4f} μm/px\n")
        else:
            self.result_text.insert(tk.END, "Draw a line to measure scale bar.\n")
            
    def save_result(self):
        """Save measurement result to JSON file"""
        if self.pixels_per_micron is None:
            messagebox.showwarning("Warning", "No measurement to save. Please draw a line first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Measurement Result",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "image_path": self.image_path,
                "image_size": {"width": int(self.image.shape[1]), "height": int(self.image.shape[0])},
                "line_start": {"x": int(self.line_start[0]), "y": int(self.line_start[1])},
                "line_end": {"x": int(self.line_end[0]), "y": int(self.line_end[1])},
                "pixel_distance": float(self.pixel_distance),
                "real_world_distance_um": float(self.real_world_distance),
                "pixels_per_micron": float(self.pixels_per_micron),
                "microns_per_pixel": float(1 / self.pixels_per_micron)
            }
            
            with open(file_path, 'w') as f:
                json.dump(result, f, indent=2)
                
            messagebox.showinfo("Success", f"Measurement saved to:\n{file_path}")
            self.status_var.set(f"Result saved to {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save result:\n{str(e)}")


def main():
    """Entry point"""
    root = tk.Tk()
    app = ScaleBarMeasurement(root)
    root.mainloop()


if __name__ == "__main__":
    main()
