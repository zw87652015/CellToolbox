import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import rawpy
import numpy as np
import cv2
from PIL import Image, ImageTk
import os
import threading
from pathlib import Path

class DemosaicUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RAW Image Demosaic Processor")
        self.root.geometry("1200x800")
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_folder = tk.StringVar(value=str(Path.cwd()))
        self.processing = False
        
        # Image data storage
        self.raw_image = None
        self.rgb_image = None
        self.r_channel = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Input RAW File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.input_file, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(file_frame, text="Browse", command=self.browse_input_file).grid(row=0, column=2)
        
        ttk.Label(file_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Entry(file_frame, textvariable=self.output_folder, state="readonly").grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(5, 0))
        ttk.Button(file_frame, text="Browse", command=self.browse_output_folder).grid(row=1, column=2, pady=(5, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.process_btn = ttk.Button(control_frame, text="Process Image", command=self.process_image)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = ttk.Button(control_frame, text="Save Results", command=self.save_results, state="disabled")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=(10, 0))
        
        # Image display area
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.columnconfigure(2, weight=1)
        display_frame.rowconfigure(1, weight=1)
        
        # Image display labels
        ttk.Label(display_frame, text="Raw Image (Visible)", font=('Arial', 10, 'bold')).grid(row=0, column=0, pady=(0, 5))
        ttk.Label(display_frame, text="Demosaiced RGB", font=('Arial', 10, 'bold')).grid(row=0, column=1, pady=(0, 5))
        ttk.Label(display_frame, text="Red Channel", font=('Arial', 10, 'bold')).grid(row=0, column=2, pady=(0, 5))
        
        # Image canvases
        self.canvas_raw = tk.Canvas(display_frame, bg='gray', width=350, height=250)
        self.canvas_raw.grid(row=1, column=0, padx=(0, 5), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.canvas_rgb = tk.Canvas(display_frame, bg='gray', width=350, height=250)
        self.canvas_rgb.grid(row=1, column=1, padx=2.5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.canvas_red = tk.Canvas(display_frame, bg='gray', width=350, height=250)
        self.canvas_red.grid(row=1, column=2, padx=(5, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def browse_input_file(self):
        """Browse for input RAW file"""
        filetypes = [
            ("RAW TIFF files", "*.tif *.tiff"),
            ("All RAW files", "*.raw *.dng *.cr2 *.nef *.arw *.orf *.rw2"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select RAW Image File",
            filetypes=filetypes
        )
        
        if filename:
            self.input_file.set(filename)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")
            
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.output_folder.get()
        )
        
        if folder:
            self.output_folder.set(folder)
            self.status_var.set(f"Output folder: {folder}")
            
    def process_image(self):
        """Process the RAW image in a separate thread"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file first.")
            return
            
        if self.processing:
            return
            
        # Start processing in separate thread
        self.processing = True
        self.process_btn.config(state="disabled")
        self.progress.start()
        self.status_var.set("Processing image...")
        
        thread = threading.Thread(target=self._process_image_thread)
        thread.daemon = True
        thread.start()
        
    def _process_image_thread(self):
        """Process image in background thread"""
        try:
            # Load RAW image
            self.root.after(0, lambda: self.status_var.set("Loading RAW image..."))
            
            with rawpy.imread(self.input_file.get()) as raw:
                # Get raw visible image
                self.raw_image = raw.raw_image_visible.astype(np.float32)
                
                # Process to RGB
                self.root.after(0, lambda: self.status_var.set("Demosaicing image..."))
                self.rgb_image = raw.postprocess(
                    demosaic_algorithm=rawpy.DemosaicAlgorithm(0),
                    output_bps=16,
                    no_auto_bright=True,
                    gamma=(1, 1)
                )
                
                # Extract red channel
                self.root.after(0, lambda: self.status_var.set("Extracting red channel..."))
                self.r_channel = self.rgb_image[:, :, 0]
                
            # Update UI in main thread
            self.root.after(0, self._update_display)
            
        except Exception as e:
            self.root.after(0, lambda: self._handle_error(str(e)))
            
    def _handle_error(self, error_msg):
        """Handle processing errors"""
        self.processing = False
        self.process_btn.config(state="normal")
        self.progress.stop()
        self.status_var.set("Error occurred")
        messagebox.showerror("Processing Error", f"Error processing image:\n{error_msg}")
        
    def _update_display(self):
        """Update image displays after processing"""
        try:
            # Display raw image (normalized)
            raw_display = self.normalize_for_display(self.raw_image)
            self.display_image(self.canvas_raw, raw_display, is_grayscale=True)
            
            # Display RGB image
            rgb_display = self.normalize_for_display(self.rgb_image)
            self.display_image(self.canvas_rgb, rgb_display)
            
            # Display red channel
            red_display = self.normalize_for_display(self.r_channel)
            self.display_image(self.canvas_red, red_display, is_grayscale=True)
            
            # Enable save button
            self.save_btn.config(state="normal")
            self.status_var.set("Processing complete")
            
        except Exception as e:
            self._handle_error(str(e))
        finally:
            self.processing = False
            self.process_btn.config(state="normal")
            self.progress.stop()
            
    def normalize_for_display(self, image):
        """Normalize image for display (0-255 range)"""
        if image is None:
            return None
            
        # Handle different bit depths
        if image.dtype == np.uint16:
            # Convert 16-bit to 8-bit
            normalized = (image / 65535.0 * 255).astype(np.uint8)
        elif image.dtype == np.float32:
            # Normalize float32 to 0-255
            img_min, img_max = image.min(), image.max()
            if img_max > img_min:
                normalized = ((image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
            else:
                normalized = np.zeros_like(image, dtype=np.uint8)
        else:
            normalized = image.astype(np.uint8)
            
        return normalized
        
    def display_image(self, canvas, image, is_grayscale=False):
        """Display image on canvas"""
        if image is None:
            return
            
        # Get canvas dimensions
        canvas.update()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        # Resize image to fit canvas
        if len(image.shape) == 3:
            h, w = image.shape[:2]
        else:
            h, w = image.shape
            
        # Calculate scaling factor
        scale = min(canvas_width / w, canvas_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize image
        if len(image.shape) == 3:
            resized = cv2.resize(image, (new_w, new_h))
            if not is_grayscale:
                # Convert BGR to RGB for display
                resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        else:
            resized = cv2.resize(image, (new_w, new_h))
            
        # Convert to PIL Image
        if is_grayscale and len(resized.shape) == 2:
            pil_image = Image.fromarray(resized, mode='L')
        else:
            pil_image = Image.fromarray(resized)
            
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(pil_image)
        
        # Clear canvas and display image
        canvas.delete("all")
        x = (canvas_width - new_w) // 2
        y = (canvas_height - new_h) // 2
        canvas.create_image(x, y, anchor=tk.NW, image=photo)
        
        # Keep reference to prevent garbage collection
        canvas.image = photo
        
    def save_results(self):
        """Save processed images"""
        if self.rgb_image is None or self.r_channel is None:
            messagebox.showerror("Error", "No processed images to save.")
            return
            
        try:
            # Get base filename
            input_path = Path(self.input_file.get())
            base_name = input_path.stem
            output_dir = Path(self.output_folder.get())
            
            # Save RGB image
            rgb_path = output_dir / f"{base_name}_demosaiced_rgb.tiff"
            cv2.imwrite(str(rgb_path), self.rgb_image)
            
            # Save red channel
            red_path = output_dir / f"{base_name}_red_channel.tiff"
            cv2.imwrite(str(red_path), self.r_channel)
            
            # Save raw visible (if available)
            if self.raw_image is not None:
                raw_path = output_dir / f"{base_name}_raw_visible.tiff"
                # Convert to 16-bit for saving
                raw_16bit = (self.raw_image / self.raw_image.max() * 65535).astype(np.uint16)
                cv2.imwrite(str(raw_path), raw_16bit)
            
            self.status_var.set(f"Images saved to {output_dir}")
            messagebox.showinfo("Success", f"Images saved successfully to:\n{output_dir}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving images:\n{str(e)}")

def main():
    root = tk.Tk()
    app = DemosaicUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
