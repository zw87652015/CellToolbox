"""
Negative Sample Creator for YOLO Training

This tool helps create negative samples (background regions without cells) 
to improve YOLO model's ability to distinguish cells from background.

Usage:
    python negative_sample_creator.py

Features:
    - Draw ROI to define search area
    - Automatically extract random background patches
    - Generate empty YOLO label files
    - Configurable patch sizes and count
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
from datetime import datetime


class NegativeSampleCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Negative Sample Creator - YOLO Training")
        self.root.geometry("1200x800")
        
        # Image data
        self.image = None
        self.image_path = None
        self.roi_rect = None
        self.roi_start = None
        self.roi_end = None
        
        # Display parameters
        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        
        # Negative samples
        self.negative_patches = []  # List of (x, y, w, h) patches
        self.selected_patch_index = -1
        
        # Output directory
        self.output_dir = os.path.join(os.path.dirname(__file__), 'negative_samples')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Parameters
        self.num_patches = 5
        self.min_patch_size = 100
        self.max_patch_size = 400
        
        self.create_ui()
    
    def create_ui(self):
        """Create the application UI"""
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - controls
        control_frame = ttk.Frame(main_frame, width=300)
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
        
        # Control buttons
        ttk.Label(control_frame, text="Negative Sample Creator", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Button(control_frame, text="Load Image", 
                  command=self.load_image).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Instructions
        ttk.Label(control_frame, text="Instructions:", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0,5))
        
        instructions = [
            "1. Load an image",
            "2. Draw ROI (drag mouse)",
            "3. Generate patches",
            "4. Review patches",
            "5. Save negative samples"
        ]
        for inst in instructions:
            ttk.Label(control_frame, text=inst, 
                     font=('Arial', 9)).pack(anchor=tk.W, padx=10)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Parameters
        ttk.Label(control_frame, text="Parameters", 
                 font=('Arial', 10, 'bold')).pack(pady=(0,5))
        
        # Number of patches
        ttk.Label(control_frame, text="Number of patches:").pack(anchor=tk.W, padx=5)
        self.num_patches_var = tk.StringVar(value="5")
        ttk.Entry(control_frame, textvariable=self.num_patches_var, 
                 width=10).pack(anchor=tk.W, padx=5, pady=(0,5))
        
        # Min patch size
        ttk.Label(control_frame, text="Min patch size (px):").pack(anchor=tk.W, padx=5)
        self.min_size_var = tk.StringVar(value="100")
        ttk.Entry(control_frame, textvariable=self.min_size_var, 
                 width=10).pack(anchor=tk.W, padx=5, pady=(0,5))
        
        # Max patch size
        ttk.Label(control_frame, text="Max patch size (px):").pack(anchor=tk.W, padx=5)
        self.max_size_var = tk.StringVar(value="400")
        ttk.Entry(control_frame, textvariable=self.max_size_var, 
                 width=10).pack(anchor=tk.W, padx=5, pady=(0,10))
        
        # Action buttons
        ttk.Button(control_frame, text="Generate Patches", 
                  command=self.generate_patches).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Clear Patches", 
                  command=self.clear_patches).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Save Negative Samples", 
                  command=self.save_negative_samples).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Info panel
        ttk.Label(control_frame, text="Info", 
                 font=('Arial', 10, 'bold')).pack(pady=(0,5))
        
        info_frame = ttk.Frame(control_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(info_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.info_text = tk.Text(info_frame, height=15, width=35, 
                                yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.info_text.yview)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.update_info("Welcome! Load an image to start.")
    
    def load_image(self):
        """Load an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.image = cv2.imread(file_path)
        if self.image is None:
            messagebox.showerror("Error", "Failed to load image")
            return
        
        self.image_path = file_path
        self.roi_rect = None
        self.negative_patches = []
        
        self.update_display()
        self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
        self.update_info(f"Image loaded: {os.path.basename(file_path)}")
        self.update_info(f"Size: {self.image.shape[1]}x{self.image.shape[0]}")
        self.update_info("Draw ROI by dragging mouse on image")
    
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
        
        # Calculate scaling
        h, w = self.image.shape[:2]
        scale_x = canvas_width / w
        scale_y = canvas_height / h
        scale = min(scale_x, scale_y)
        
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Create display image
        display_img = self.image.copy()
        
        # Draw ROI rectangle
        if self.roi_rect:
            x, y, rw, rh = self.roi_rect
            cv2.rectangle(display_img, (x, y), (x+rw, y+rh), (0, 255, 0), 2)
            cv2.putText(display_img, "ROI", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw negative patches
        for i, (px, py, pw, ph) in enumerate(self.negative_patches):
            # Highlight selected patch
            color = (255, 255, 0) if i == self.selected_patch_index else (255, 0, 255)  # Yellow if selected, magenta otherwise
            thickness = 3 if i == self.selected_patch_index else 2
            cv2.rectangle(display_img, (px, py), (px+pw, py+ph), color, thickness)
            
            # Draw label
            cv2.putText(display_img, f"Neg {i+1}", (px, py-5), 
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
        self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=photo)
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
        
        self.roi_start = (img_x, img_y)
        self.roi_end = None
    
    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if self.image is None or self.roi_start is None:
            return
        
        # Convert display to image coordinates
        img_x = int((event.x - self.display_offset_x) / self.display_scale)
        img_y = int((event.y - self.display_offset_y) / self.display_scale)
        
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
        if self.image is None or self.roi_start is None:
            return
        
        # Convert display to image coordinates
        img_x = int((event.x - self.display_offset_x) / self.display_scale)
        img_y = int((event.y - self.display_offset_y) / self.display_scale)
        
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
            self.update_info("Click 'Generate Patches' to create negative samples")
        
        self.roi_start = None
        self.roi_end = None
        self.update_display()
    
    def generate_patches(self):
        """Generate random negative patches within ROI"""
        if self.image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        if self.roi_rect is None:
            messagebox.showwarning("Warning", "Please draw an ROI first")
            return
        
        # Parse parameters
        try:
            num_patches = int(self.num_patches_var.get())
            min_size = int(self.min_size_var.get())
            max_size = int(self.max_size_var.get())
            
            if num_patches < 1 or num_patches > 20:
                messagebox.showerror("Error", "Number of patches must be between 1 and 20")
                return
            if min_size < 50 or min_size > max_size:
                messagebox.showerror("Error", "Invalid patch size range")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values")
            return
        
        # Get ROI bounds
        roi_x, roi_y, roi_w, roi_h = self.roi_rect
        
        # Generate random patches
        self.negative_patches = []
        attempts = 0
        max_attempts = num_patches * 100
        
        while len(self.negative_patches) < num_patches and attempts < max_attempts:
            attempts += 1
            
            # Random patch size
            patch_w = np.random.randint(min_size, max_size + 1)
            patch_h = np.random.randint(min_size, max_size + 1)
            
            # Random position within ROI
            if patch_w > roi_w or patch_h > roi_h:
                continue
            
            patch_x = roi_x + np.random.randint(0, roi_w - patch_w + 1)
            patch_y = roi_y + np.random.randint(0, roi_h - patch_h + 1)
            
            # Check overlap with existing patches (optional - allow some overlap)
            overlap = False
            for ex_x, ex_y, ex_w, ex_h in self.negative_patches:
                # Check if patches overlap significantly (>50%)
                x_overlap = max(0, min(patch_x + patch_w, ex_x + ex_w) - max(patch_x, ex_x))
                y_overlap = max(0, min(patch_y + patch_h, ex_y + ex_h) - max(patch_y, ex_y))
                overlap_area = x_overlap * y_overlap
                
                if overlap_area > 0.5 * min(patch_w * patch_h, ex_w * ex_h):
                    overlap = True
                    break
            
            if not overlap:
                self.negative_patches.append((patch_x, patch_y, patch_w, patch_h))
        
        self.update_display()
        self.update_info(f"Generated {len(self.negative_patches)} negative patches")
        for i, (px, py, pw, ph) in enumerate(self.negative_patches):
            self.update_info(f"  Patch {i+1}: {pw}x{ph} at ({px},{py})")
        
        self.status_var.set(f"Generated {len(self.negative_patches)} patches")
    
    def clear_patches(self):
        """Clear all generated patches"""
        self.negative_patches = []
        self.selected_patch_index = -1
        self.update_display()
        self.update_info("Patches cleared")
        self.status_var.set("Patches cleared")
    
    def save_negative_samples(self):
        """Save negative sample patches and empty label files"""
        if self.image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        if not self.negative_patches:
            messagebox.showwarning("Warning", "Please generate patches first")
            return
        
        img_name = os.path.splitext(os.path.basename(self.image_path))[0]
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        saved_count = 0
        for i, (px, py, pw, ph) in enumerate(self.negative_patches):
            # Extract patch from image
            patch = self.image[py:py+ph, px:px+pw]
            
            # Generate filename
            patch_name = f"{img_name}_neg_{i+1}"
            
            # Save patch image
            img_filename = f"{patch_name}.jpg"
            img_path = os.path.join(self.output_dir, img_filename)
            cv2.imwrite(img_path, patch)
            
            # Save empty label file (no objects)
            label_filename = f"{patch_name}.txt"
            label_path = os.path.join(self.output_dir, label_filename)
            with open(label_path, 'w') as f:
                pass  # Empty file - no labels
            
            saved_count += 1
        
        # Save metadata
        metadata = {
            'source_image': self.image_path,
            'roi': self.roi_rect,
            'num_patches': len(self.negative_patches),
            'patches': [
                {'id': i+1, 'x': px, 'y': py, 'width': pw, 'height': ph}
                for i, (px, py, pw, ph) in enumerate(self.negative_patches)
            ],
            'purpose': 'negative_samples',
            'description': 'Background regions with no cells for YOLO training'
        }
        
        metadata_path = os.path.join(self.output_dir, f"{img_name}_negative_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.update_info(f"\n=== Negative Samples Saved ===")
        self.update_info(f"Patches saved: {saved_count}")
        self.update_info(f"Output directory: {self.output_dir}")
        self.update_info(f"Files: {saved_count} images + {saved_count} empty labels")
        self.update_info("")
        
        self.status_var.set(f"Saved {saved_count} negative samples")
        
        messagebox.showinfo("Success", 
                           f"Saved {saved_count} negative samples\n\n"
                           f"Location: {self.output_dir}\n\n"
                           f"Each patch has:\n"
                           f"  - Image file (.jpg)\n"
                           f"  - Empty label file (.txt)")
    
    def update_info(self, message):
        """Update info text"""
        self.info_text.insert(tk.END, f"{message}\n")
        self.info_text.see(tk.END)


def main():
    root = tk.Tk()
    app = NegativeSampleCreator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
