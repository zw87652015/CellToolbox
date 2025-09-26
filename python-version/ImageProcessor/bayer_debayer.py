#!/usr/bin/env python3
"""
Bayer Debayer Tool
A GUI application to apply various debayering algorithms to merged Bayer channel images.
Designed for processing merged RAW Bayer images from ToupCam SingleDroplet detection.

Author: AI Assistant
Date: 2025-09-24
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import os
from pathlib import Path
from datetime import datetime

class BayerDebayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Bayer Debayer Tool - ToupCam Image Processor")
        self.root.geometry("900x700")
        
        # File paths
        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # Image data
        self.input_image = None
        self.debayered_images = {}
        
        # Debayer algorithms available in OpenCV
        self.debayer_algorithms = {
            "Bilinear (RGGB)": cv2.COLOR_BAYER_BG2BGR,
            "Bilinear (GRBG)": cv2.COLOR_BAYER_GB2BGR,
            "Bilinear (GBRG)": cv2.COLOR_BAYER_GR2BGR,
            "Bilinear (BGGR)": cv2.COLOR_BAYER_RG2BGR,
            "VNG (RGGB)": cv2.COLOR_BAYER_BG2BGR_VNG,
            "VNG (GRBG)": cv2.COLOR_BAYER_GB2BGR_VNG,
            "VNG (GBRG)": cv2.COLOR_BAYER_GR2BGR_VNG,
            "VNG (BGGR)": cv2.COLOR_BAYER_RG2BGR_VNG,
            "Edge-Aware (RGGB)": cv2.COLOR_BAYER_BG2BGR_EA,
            "Edge-Aware (GRBG)": cv2.COLOR_BAYER_GB2BGR_EA,
            "Edge-Aware (GBRG)": cv2.COLOR_BAYER_GR2BGR_EA,
            "Edge-Aware (BGGR)": cv2.COLOR_BAYER_RG2BGR_EA
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Bayer Debayer Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input file section
        input_frame = ttk.LabelFrame(main_frame, text="Input Image", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Bayer Image:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(input_frame, textvariable=self.input_path, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(input_frame, text="Browse", command=self.browse_input_file).grid(
            row=0, column=2, pady=2)
        
        # Output directory section
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(output_frame, textvariable=self.output_dir).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir).grid(
            row=0, column=2, pady=2)
        
        # Algorithm selection section
        algo_frame = ttk.LabelFrame(main_frame, text="Debayer Algorithms", padding="10")
        algo_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        algo_frame.columnconfigure(0, weight=1)
        algo_frame.columnconfigure(1, weight=1)
        
        # Create checkboxes for each algorithm
        self.algorithm_vars = {}
        row = 0
        col = 0
        for algo_name in self.debayer_algorithms.keys():
            var = tk.BooleanVar()
            self.algorithm_vars[algo_name] = var
            ttk.Checkbutton(algo_frame, text=algo_name, variable=var).grid(
                row=row, column=col, sticky=tk.W, pady=2, padx=5)
            
            col += 1
            if col > 1:  # Two columns
                col = 0
                row += 1
        
        # Select/Deselect all buttons
        select_frame = ttk.Frame(algo_frame)
        select_frame.grid(row=row+1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(select_frame, text="Select All", command=self.select_all_algorithms).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="Deselect All", command=self.deselect_all_algorithms).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="Select VNG Only", command=self.select_vng_only).pack(
            side=tk.LEFT, padx=5)
        
        # Processing options
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.save_individual = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Save individual debayered images", 
                       variable=self.save_individual).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.create_comparison = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Create comparison grid image", 
                       variable=self.create_comparison).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.enhance_contrast = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Apply contrast enhancement", 
                       variable=self.enhance_contrast).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Load & Preview", command=self.load_and_preview).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Process All", command=self.process_all_algorithms).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_all).pack(
            side=tk.LEFT, padx=5)
        
        # Status and info section
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # Text widget for information display
        self.info_text = tk.Text(info_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.log_info("Bayer Debayer Tool initialized successfully.")
        self.log_info("Load a merged Bayer channel image to apply debayering algorithms.")
        
        # Set default selections
        self.select_vng_only()
        
    def log_info(self, message):
        """Add information to the info text widget"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.info_text.see(tk.END)
        self.root.update_idletasks()
        
    def browse_input_file(self):
        """Browse for input Bayer image file"""
        filename = filedialog.askopenfilename(
            title="Select Bayer Image File",
            filetypes=[("TIFF files", "*.tif *.tiff"), ("PNG files", "*.png"), 
                      ("JPEG files", "*.jpg *.jpeg"), ("All files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            self.log_info(f"Input file selected: {Path(filename).name}")
            
            # Auto-set output directory
            if not self.output_dir.get():
                input_path = Path(filename)
                output_folder = input_path.parent / "debayered_results"
                self.output_dir.set(str(output_folder))
                self.log_info(f"Output directory auto-set: {output_folder.name}")
    
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
            self.log_info(f"Output directory set: {Path(directory).name}")
    
    def select_all_algorithms(self):
        """Select all debayer algorithms"""
        for var in self.algorithm_vars.values():
            var.set(True)
        self.log_info("All algorithms selected")
    
    def deselect_all_algorithms(self):
        """Deselect all debayer algorithms"""
        for var in self.algorithm_vars.values():
            var.set(False)
        self.log_info("All algorithms deselected")
    
    def select_vng_only(self):
        """Select only VNG algorithms (recommended for quality)"""
        self.deselect_all_algorithms()
        for algo_name, var in self.algorithm_vars.items():
            if "VNG" in algo_name:
                var.set(True)
        self.log_info("VNG algorithms selected (recommended)")
    
    def load_image(self):
        """Load the input Bayer image"""
        if not self.input_path.get():
            messagebox.showerror("No Input File", "Please select an input Bayer image file.")
            return False
        
        try:
            self.status_var.set("Loading image...")
            
            # Load image as grayscale (Bayer pattern)
            self.input_image = cv2.imread(self.input_path.get(), cv2.IMREAD_GRAYSCALE)
            
            if self.input_image is None:
                messagebox.showerror("Load Error", "Failed to load the input image file.")
                return False
            
            # Log image information
            height, width = self.input_image.shape
            self.log_info(f"Image loaded successfully:")
            self.log_info(f"  Dimensions: {width}x{height}")
            self.log_info(f"  Data type: {self.input_image.dtype}")
            self.log_info(f"  Value range: {self.input_image.min()} - {self.input_image.max()}")
            
            return True
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading image: {str(e)}")
            self.log_info(f"Error loading image: {str(e)}")
            return False
    
    def apply_debayer_algorithm(self, algorithm_name, cv_code):
        """Apply a specific debayer algorithm"""
        try:
            # Apply debayering
            debayered = cv2.cvtColor(self.input_image, cv_code)
            
            # Apply contrast enhancement if requested
            if self.enhance_contrast.get():
                # Convert to LAB color space for better contrast enhancement
                lab = cv2.cvtColor(debayered, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                
                # Merge back and convert to BGR
                lab = cv2.merge([l, a, b])
                debayered = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return debayered
            
        except Exception as e:
            self.log_info(f"Error applying {algorithm_name}: {str(e)}")
            return None
    
    def load_and_preview(self):
        """Load image and create a quick preview"""
        if not self.load_image():
            return
        
        try:
            # Create preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Bayer Image Preview")
            preview_window.geometry("800x600")
            
            # Create notebook for tabs
            notebook = ttk.Notebook(preview_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Original image tab
            orig_frame = ttk.Frame(notebook)
            notebook.add(orig_frame, text="Original Bayer")
            
            # Scale image for preview
            height, width = self.input_image.shape
            max_size = 400
            if width > max_size or height > max_size:
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                preview_orig = cv2.resize(self.input_image, (new_width, new_height))
            else:
                preview_orig = self.input_image.copy()
            
            # Convert grayscale to RGB for display
            preview_orig_rgb = cv2.cvtColor(preview_orig, cv2.COLOR_GRAY2RGB)
            
            # Display original
            from PIL import Image, ImageTk
            pil_orig = Image.fromarray(preview_orig_rgb)
            photo_orig = ImageTk.PhotoImage(pil_orig)
            
            label_orig = ttk.Label(orig_frame, image=photo_orig)
            label_orig.image = photo_orig  # Keep reference
            label_orig.pack(expand=True)
            
            # Quick debayer preview (VNG RGGB)
            if cv2.COLOR_BAYER_BG2BGR_VNG in self.debayer_algorithms.values():
                debayer_frame = ttk.Frame(notebook)
                notebook.add(debayer_frame, text="VNG Preview")
                
                quick_debayer = self.apply_debayer_algorithm("VNG Preview", cv2.COLOR_BAYER_BG2BGR_VNG)
                if quick_debayer is not None:
                    if width > max_size or height > max_size:
                        quick_preview = cv2.resize(quick_debayer, (new_width, new_height))
                    else:
                        quick_preview = quick_debayer.copy()
                    
                    # Convert BGR to RGB for display
                    quick_preview_rgb = cv2.cvtColor(quick_preview, cv2.COLOR_BGR2RGB)
                    
                    pil_debayer = Image.fromarray(quick_preview_rgb)
                    photo_debayer = ImageTk.PhotoImage(pil_debayer)
                    
                    label_debayer = ttk.Label(debayer_frame, image=photo_debayer)
                    label_debayer.image = photo_debayer  # Keep reference
                    label_debayer.pack(expand=True)
            
            self.log_info("Preview window opened")
            self.status_var.set("Preview displayed")
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error creating preview: {str(e)}")
            self.log_info(f"Error creating preview: {str(e)}")
    
    def process_all_algorithms(self):
        """Process the image with all selected algorithms"""
        if not self.load_image():
            return
        
        if not self.output_dir.get():
            messagebox.showerror("No Output Directory", "Please specify an output directory.")
            return
        
        # Get selected algorithms
        selected_algorithms = [name for name, var in self.algorithm_vars.items() if var.get()]
        
        if not selected_algorithms:
            messagebox.showerror("No Algorithms Selected", "Please select at least one debayer algorithm.")
            return
        
        try:
            # Create output directory
            output_path = Path(self.output_dir.get())
            output_path.mkdir(parents=True, exist_ok=True)
            
            self.status_var.set("Processing algorithms...")
            self.debayered_images = {}
            
            # Get base filename
            input_filename = Path(self.input_path.get()).stem
            
            # Process each selected algorithm
            for i, algo_name in enumerate(selected_algorithms):
                self.log_info(f"Processing {algo_name}...")
                self.status_var.set(f"Processing {algo_name} ({i+1}/{len(selected_algorithms)})")
                
                cv_code = self.debayer_algorithms[algo_name]
                debayered = self.apply_debayer_algorithm(algo_name, cv_code)
                
                if debayered is not None:
                    self.debayered_images[algo_name] = debayered
                    
                    # Save individual image if requested
                    if self.save_individual.get():
                        safe_name = algo_name.replace(" ", "_").replace("(", "").replace(")", "")
                        output_filename = f"{input_filename}_{safe_name}.tif"
                        output_file = output_path / output_filename
                        
                        success = cv2.imwrite(str(output_file), debayered)
                        if success:
                            self.log_info(f"  Saved: {output_filename}")
                        else:
                            self.log_info(f"  Failed to save: {output_filename}")
                
                self.root.update_idletasks()
            
            # Create comparison grid if requested
            if self.create_comparison.get() and len(self.debayered_images) > 1:
                self.create_comparison_grid(output_path, input_filename)
            
            self.status_var.set("Processing completed")
            self.log_info(f"Processing completed. {len(self.debayered_images)} algorithms processed.")
            
            messagebox.showinfo("Processing Complete", 
                              f"Debayering completed!\n"
                              f"Processed {len(self.debayered_images)} algorithms\n"
                              f"Results saved to: {str(output_path)}")
            
        except Exception as e:
            messagebox.showerror("Processing Error", f"Error during processing: {str(e)}")
            self.log_info(f"Error during processing: {str(e)}")
            self.status_var.set("Processing failed")
    
    def create_comparison_grid(self, output_path, input_filename):
        """Create a comparison grid of all debayered results"""
        try:
            self.log_info("Creating comparison grid...")
            
            if not self.debayered_images:
                return
            
            # Calculate grid dimensions
            num_images = len(self.debayered_images)
            grid_cols = min(3, num_images)  # Max 3 columns
            grid_rows = (num_images + grid_cols - 1) // grid_cols
            
            # Get image dimensions (assume all are same size)
            first_image = next(iter(self.debayered_images.values()))
            img_height, img_width = first_image.shape[:2]
            
            # Scale down images for comparison grid
            scale_factor = min(400 / img_width, 300 / img_height)
            if scale_factor > 1:
                scale_factor = 1
            
            scaled_width = int(img_width * scale_factor)
            scaled_height = int(img_height * scale_factor)
            
            # Create comparison grid
            grid_width = grid_cols * scaled_width
            grid_height = grid_rows * (scaled_height + 30)  # +30 for text labels
            
            comparison_grid = np.ones((grid_height, grid_width, 3), dtype=np.uint8) * 255
            
            # Add images to grid
            for i, (algo_name, image) in enumerate(self.debayered_images.items()):
                row = i // grid_cols
                col = i % grid_cols
                
                # Scale image
                scaled_image = cv2.resize(image, (scaled_width, scaled_height))
                
                # Calculate position
                y_start = row * (scaled_height + 30)
                y_end = y_start + scaled_height
                x_start = col * scaled_width
                x_end = x_start + scaled_width
                
                # Place image
                comparison_grid[y_start:y_end, x_start:x_end] = scaled_image
                
                # Add text label
                text_y = y_end + 20
                text_x = x_start + 5
                cv2.putText(comparison_grid, algo_name, (text_x, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Save comparison grid
            comparison_filename = f"{input_filename}_comparison_grid.tif"
            comparison_file = output_path / comparison_filename
            
            success = cv2.imwrite(str(comparison_file), comparison_grid)
            if success:
                self.log_info(f"Comparison grid saved: {comparison_filename}")
            else:
                self.log_info("Failed to save comparison grid")
                
        except Exception as e:
            self.log_info(f"Error creating comparison grid: {str(e)}")
    
    def clear_all(self):
        """Clear all inputs and reset the application"""
        self.input_path.set("")
        self.output_dir.set("")
        
        self.input_image = None
        self.debayered_images = {}
        
        self.deselect_all_algorithms()
        
        self.info_text.delete(1.0, tk.END)
        self.log_info("Application reset. Ready for new image.")
        self.status_var.set("Ready")

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = BayerDebayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
