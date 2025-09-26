#!/usr/bin/env python3
"""
Bayer Channel Merger
A GUI application to merge three TIFF files (R, G, B channels) into a single 3-channel image.
Designed for processing RAW Bayer channel images from ToupCam SingleDroplet detection.

Author: AI Assistant
Date: 2025-09-23
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

class BayerChannelMerger:
    def __init__(self, root):
        self.root = root
        self.root.title("Bayer Channel Merger - ToupCam Image Processor")
        self.root.geometry("800x600")
        
        # File paths
        self.r_channel_path = tk.StringVar()
        self.g_channel_path = tk.StringVar()
        self.b_channel_path = tk.StringVar()
        self.output_path = tk.StringVar()
        
        # Image data
        self.r_image = None
        self.g_image = None
        self.b_image = None
        self.merged_image = None
        
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
        title_label = ttk.Label(main_frame, text="Bayer Channel Merger", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Input Files", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Red channel file
        ttk.Label(file_frame, text="Red Channel (R):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.r_channel_path, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="Browse", 
                  command=lambda: self.browse_file(self.r_channel_path, "Red")).grid(
            row=0, column=2, pady=2)
        
        # Green channel file
        ttk.Label(file_frame, text="Green Channel (G):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.g_channel_path, state="readonly").grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="Browse", 
                  command=lambda: self.browse_file(self.g_channel_path, "Green")).grid(
            row=1, column=2, pady=2)
        
        # Blue channel file
        ttk.Label(file_frame, text="Blue Channel (B):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.b_channel_path, state="readonly").grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="Browse", 
                  command=lambda: self.browse_file(self.b_channel_path, "Blue")).grid(
            row=2, column=2, pady=2)
        
        # Auto-detect button
        ttk.Button(file_frame, text="Auto-Detect Bayer Files", 
                  command=self.auto_detect_files).grid(
            row=3, column=0, columnspan=3, pady=(10, 0))
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(output_frame, textvariable=self.output_path).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(output_frame, text="Browse", 
                  command=self.browse_output_file).grid(row=0, column=2, pady=2)
        
        # Processing options
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.normalize_channels = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Normalize channel intensities", 
                       variable=self.normalize_channels).grid(
            row=0, column=0, sticky=tk.W, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Preview", command=self.preview_merge).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Merge & Save", command=self.merge_and_save).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).pack(
            side=tk.LEFT, padx=5)
        
        # Status and info section
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # Text widget for information display
        self.info_text = tk.Text(info_frame, height=12, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.log_info("Bayer Channel Merger initialized successfully.")
        self.log_info("Load three TIFF files (R, G, B channels) to merge them into a single RGB image.")
        
    def log_info(self, message):
        """Add information to the info text widget"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.info_text.see(tk.END)
        self.root.update_idletasks()
        
    def browse_file(self, path_var, channel_name):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title=f"Select {channel_name} Channel TIFF File",
            filetypes=[("TIFF files", "*.tif *.tiff"), ("All files", "*.*")]
        )
        if filename:
            path_var.set(filename)
            self.log_info(f"{channel_name} channel file selected: {os.path.basename(filename)}")
            
            # Auto-generate output filename if all channels are selected
            if (self.r_channel_path.get() and self.g_channel_path.get() and 
                self.b_channel_path.get() and not self.output_path.get()):
                self.auto_generate_output_path()
    
    def browse_output_file(self):
        """Browse for output file"""
        filename = filedialog.asksaveasfilename(
            title="Save Merged Image As",
            defaultextension=".tif",
            filetypes=[("TIFF files", "*.tif"), ("PNG files", "*.png"), 
                      ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
            self.log_info(f"Output file set: {os.path.basename(filename)}")
    
    def auto_detect_files(self):
        """Auto-detect Bayer channel files in a directory"""
        directory = filedialog.askdirectory(title="Select Directory with Bayer Channel Files")
        if not directory:
            return
            
        # Look for files with Bayer_R, Bayer_G, Bayer_B patterns
        dir_path = Path(directory)
        files = list(dir_path.iterdir())
        r_files = [f.name for f in files if "Bayer_R" in f.name and f.suffix.lower() in ['.tif', '.tiff']]
        g_files = [f.name for f in files if "Bayer_G" in f.name and f.suffix.lower() in ['.tif', '.tiff']]
        b_files = [f.name for f in files if "Bayer_B" in f.name and f.suffix.lower() in ['.tif', '.tiff']]
        
        if r_files and g_files and b_files:
            # Use the most recent files (assuming timestamp in filename)
            r_files.sort(reverse=True)
            g_files.sort(reverse=True)
            b_files.sort(reverse=True)
            
            self.r_channel_path.set(str(dir_path / r_files[0]))
            self.g_channel_path.set(str(dir_path / g_files[0]))
            self.b_channel_path.set(str(dir_path / b_files[0]))
            
            self.log_info("Auto-detected Bayer files:")
            self.log_info(f"  R: {r_files[0]}")
            self.log_info(f"  G: {g_files[0]}")
            self.log_info(f"  B: {b_files[0]}")
            
            self.auto_generate_output_path()
        else:
            messagebox.showwarning("Auto-Detection Failed", 
                                 "Could not find matching Bayer channel files (Bayer_R, Bayer_G, Bayer_B) in the selected directory.")
    
    def auto_generate_output_path(self):
        """Auto-generate output path based on input files"""
        if self.r_channel_path.get():
            r_path = Path(self.r_channel_path.get())
            base_dir = r_path.parent
            # Extract timestamp from filename (assuming format like "12-05-55_Bayer_R.tif")
            r_filename = r_path.name
            if "_Bayer_" in r_filename:
                timestamp = r_filename.split("_Bayer_")[0]
                output_filename = f"{timestamp}_Merged_RGB.tif"
                self.output_path.set(str(base_dir / output_filename))
                self.log_info(f"Auto-generated output filename: {output_filename}")
    
    def load_images(self):
        """Load the three channel images"""
        if not all([self.r_channel_path.get(), self.g_channel_path.get(), self.b_channel_path.get()]):
            messagebox.showerror("Missing Files", "Please select all three channel files (R, G, B).")
            return False
        
        try:
            self.status_var.set("Loading images...")
            
            # Load images
            self.r_image = cv2.imread(self.r_channel_path.get(), cv2.IMREAD_UNCHANGED)
            self.g_image = cv2.imread(self.g_channel_path.get(), cv2.IMREAD_UNCHANGED)
            self.b_image = cv2.imread(self.b_channel_path.get(), cv2.IMREAD_UNCHANGED)
            
            if self.r_image is None or self.g_image is None or self.b_image is None:
                messagebox.showerror("Load Error", "Failed to load one or more image files.")
                return False
            
            # Check dimensions
            r_shape = self.r_image.shape[:2]
            g_shape = self.g_image.shape[:2]
            b_shape = self.b_image.shape[:2]
            
            if not (r_shape == g_shape == b_shape):
                messagebox.showerror("Dimension Mismatch", 
                                   f"Image dimensions don't match:\nR: {r_shape}\nG: {g_shape}\nB: {b_shape}")
                return False
            
            self.log_info(f"Images loaded successfully:")
            self.log_info(f"  Dimensions: {r_shape[1]}x{r_shape[0]}")
            self.log_info(f"  R channel: {self.r_image.dtype}, shape: {self.r_image.shape}")
            self.log_info(f"  G channel: {self.g_image.dtype}, shape: {self.g_image.shape}")
            self.log_info(f"  B channel: {self.b_image.dtype}, shape: {self.b_image.shape}")
            
            return True
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading images: {str(e)}")
            self.log_info(f"Error loading images: {str(e)}")
            return False
    
    def merge_channels(self):
        """Merge the three channels into a single image"""
        if not self.load_images():
            return None
        
        try:
            self.status_var.set("Merging channels...")
            
            # Extract single channels from each image
            # If images are BGR, extract the appropriate channel
            if len(self.r_image.shape) == 3:
                r_channel = self.r_image[:, :, 2]  # Red channel from BGR
                g_channel = self.g_image[:, :, 1]  # Green channel from BGR
                b_channel = self.b_image[:, :, 0]  # Blue channel from BGR
            else:
                # Grayscale images
                r_channel = self.r_image
                g_channel = self.g_image
                b_channel = self.b_image
            
            # Normalize channels if requested
            if self.normalize_channels.get():
                r_channel = cv2.normalize(r_channel, None, 0, 255, cv2.NORM_MINMAX)
                g_channel = cv2.normalize(g_channel, None, 0, 255, cv2.NORM_MINMAX)
                b_channel = cv2.normalize(b_channel, None, 0, 255, cv2.NORM_MINMAX)
                self.log_info("Channels normalized to 0-255 range")
            
            # Standard RGB channel merge (BGR format for OpenCV)
            self.merged_image = cv2.merge([b_channel, g_channel, r_channel])
            self.log_info("Channels merged as RGB image")
            
            # Log statistics
            self.log_info(f"Merged image shape: {self.merged_image.shape}")
            self.log_info(f"Merged image dtype: {self.merged_image.dtype}")
            
            return self.merged_image
            
        except Exception as e:
            messagebox.showerror("Merge Error", f"Error merging channels: {str(e)}")
            self.log_info(f"Error merging channels: {str(e)}")
            return None
    
    def preview_merge(self):
        """Preview the merged image"""
        merged = self.merge_channels()
        if merged is None:
            return
        
        try:
            # Create preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Merge Preview")
            preview_window.geometry("600x400")
            
            # Scale image for preview
            height, width = merged.shape[:2]
            max_size = 500
            if width > max_size or height > max_size:
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                preview_img = cv2.resize(merged, (new_width, new_height))
            else:
                preview_img = merged.copy()
            
            # Convert to RGB for display
            preview_img_rgb = cv2.cvtColor(preview_img, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage
            from PIL import Image, ImageTk
            pil_image = Image.fromarray(preview_img_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Display in label
            label = ttk.Label(preview_window, image=photo)
            label.image = photo  # Keep a reference
            label.pack(expand=True)
            
            self.log_info("Preview window opened")
            self.status_var.set("Preview displayed")
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error creating preview: {str(e)}")
            self.log_info(f"Error creating preview: {str(e)}")
    
    def merge_and_save(self):
        """Merge channels and save the result"""
        if not self.output_path.get():
            messagebox.showerror("No Output File", "Please specify an output file path.")
            return
        
        merged = self.merge_channels()
        if merged is None:
            return
        
        try:
            self.status_var.set("Saving merged image...")
            
            # Save the merged image
            success = cv2.imwrite(self.output_path.get(), merged)
            
            if success:
                output_path = Path(self.output_path.get())
                self.log_info(f"Merged image saved successfully: {output_path.name}")
                self.status_var.set("Merge completed successfully")
                messagebox.showinfo("Success", f"Merged image saved to:\n{str(output_path)}")
            else:
                raise Exception("cv2.imwrite returned False")
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving merged image: {str(e)}")
            self.log_info(f"Error saving merged image: {str(e)}")
            self.status_var.set("Save failed")
    
    def clear_all(self):
        """Clear all inputs and reset the application"""
        self.r_channel_path.set("")
        self.g_channel_path.set("")
        self.b_channel_path.set("")
        self.output_path.set("")
        
        self.r_image = None
        self.g_image = None
        self.b_image = None
        self.merged_image = None
        
        self.info_text.delete(1.0, tk.END)
        self.log_info("Application reset. Ready for new files.")
        self.status_var.set("Ready")

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = BayerChannelMerger(root)
    root.mainloop()

if __name__ == "__main__":
    main()
