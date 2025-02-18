import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from skimage import measure

class UnifiedUI:
    def __init__(self):
        # Create the main control window
        self.root = tk.Tk()
        self.root.title("Cell Detection Control Panel")
        self.root.geometry("400x600")
        self.root.minsize(350, 500)
        
        # Create separate windows for video displays
        self.cell_detection_window = tk.Toplevel(self.root)
        self.cell_detection_window.title("Cell Detection View")
        self.cell_detection_window.geometry("640x480")
        self.cell_detection_window.minsize(320, 240)
        
        self.white_rectangles_window = tk.Toplevel(self.root)
        self.white_rectangles_window.title("White Rectangles View")
        
        # Get screen width and height
        screen_width = self.white_rectangles_window.winfo_screenwidth()
        screen_height = self.white_rectangles_window.winfo_screenheight()
        
        # Initialize in fullscreen mode
        self.white_rectangles_window.attributes('-fullscreen', True)
        self.white_rectangles_window.attributes('-topmost', True)
        
        # Add key binding to exit fullscreen (Escape key)
        def toggle_fullscreen(event=None):
            is_fullscreen = self.white_rectangles_window.attributes('-fullscreen')
            if is_fullscreen:
                self.white_rectangles_window.attributes('-fullscreen', False)
                self.white_rectangles_window.geometry("800x600")
            else:
                self.white_rectangles_window.attributes('-fullscreen', True)
        
        self.white_rectangles_window.bind('<Escape>', toggle_fullscreen)
        self.white_rectangles_window.bind('<Key-F11>', toggle_fullscreen)
        
        # Flag for quitting
        self.quit_flag = False
        
        # Create buttons frame
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add parameter analysis snapshot button
        param_snapshot_frame = ttk.LabelFrame(buttons_frame, text="Parameter Analysis")
        param_snapshot_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(param_snapshot_frame, text="Take Snapshot for Parameter Analysis",
                  command=self.take_param_snapshot).pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(param_snapshot_frame, 
                 text="(Opens analysis window to calculate optimal parameters)",
                 wraplength=350, justify=tk.CENTER).pack(pady=(0,5))
        
        # Add processing steps snapshot button
        process_snapshot_frame = ttk.LabelFrame(buttons_frame, text="Processing Steps")
        process_snapshot_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(process_snapshot_frame, text="Save Processing Steps Snapshot",
                  command=self.take_process_snapshot).pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(process_snapshot_frame, 
                 text="(Saves all intermediate processing steps to 'cam-process' folder)",
                 wraplength=350, justify=tk.CENTER).pack(pady=(0,5))
        
        # Initialize parameters with default values
        self._parameters = {
            'area': (100, 5000),
            'perimeter': (30, 1000),
            'circularity': (0.2, 2),
            'cell_memory_frames': 5,
            'max_movement': 200,
            'distance_threshold': 50
        }
        
        # Create parameter variables
        self.area_min = tk.StringVar(value="100")
        self.area_max = tk.StringVar(value="5000")
        self.perimeter_min = tk.StringVar(value="30")
        self.perimeter_max = tk.StringVar(value="1000")
        self.circularity_min = tk.StringVar(value="0.2")
        self.circularity_max = tk.StringVar(value="2")
        self.cell_memory_frames = tk.StringVar(value="5")
        self.max_movement = tk.StringVar(value="200")
        self.distance_threshold = tk.StringVar(value="50")
        
        # Initialize snapshot analyzer
        from snapshot_analyzer import SnapshotAnalyzer
        self.snapshot_analyzer = SnapshotAnalyzer(self.root, self)
        
        # Create frames
        self.create_parameter_frame()
        self.create_video_frames()
        
        # Variable to store the current frame
        self.current_frame = None
        self.current_frame2 = None
        
        # Set up window close handlers
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.cell_detection_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.white_rectangles_window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle window close event"""
        self.quit_flag = True
        self.root.quit()
    
    def create_parameter_frame(self):
        """Create the frame containing parameter controls"""
        param_frame = ttk.LabelFrame(self.root, text="Parameters")
        param_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Area controls
        area_frame = ttk.Frame(param_frame)
        area_frame.pack(pady=5, fill='x')
        ttk.Label(area_frame, text="Area:").pack(side=tk.LEFT)
        ttk.Entry(area_frame, textvariable=self.area_min, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(area_frame, text="<").pack(side=tk.LEFT)
        ttk.Entry(area_frame, textvariable=self.area_max, width=8).pack(side=tk.LEFT, padx=5)
        
        # Perimeter controls
        perimeter_frame = ttk.Frame(param_frame)
        perimeter_frame.pack(pady=5, fill='x')
        ttk.Label(perimeter_frame, text="Perimeter:").pack(side=tk.LEFT)
        ttk.Entry(perimeter_frame, textvariable=self.perimeter_min, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(perimeter_frame, text="<").pack(side=tk.LEFT)
        ttk.Entry(perimeter_frame, textvariable=self.perimeter_max, width=8).pack(side=tk.LEFT, padx=5)
        
        # Circularity controls
        circularity_frame = ttk.Frame(param_frame)
        circularity_frame.pack(pady=5, fill='x')
        ttk.Label(circularity_frame, text="Circularity:").pack(side=tk.LEFT)
        ttk.Entry(circularity_frame, textvariable=self.circularity_min, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(circularity_frame, text="<").pack(side=tk.LEFT)
        ttk.Entry(circularity_frame, textvariable=self.circularity_max, width=8).pack(side=tk.LEFT, padx=5)
        
        # Cell Memory Frames control
        memory_frame = ttk.Frame(param_frame)
        memory_frame.pack(pady=5, fill='x')
        ttk.Label(memory_frame, text="Memory Frames:").pack(side=tk.LEFT)
        ttk.Entry(memory_frame, textvariable=self.cell_memory_frames, width=8).pack(side=tk.LEFT, padx=5)
        
        # Max Movement control
        movement_frame = ttk.Frame(param_frame)
        movement_frame.pack(pady=5, fill='x')
        ttk.Label(movement_frame, text="Max Movement:").pack(side=tk.LEFT)
        ttk.Entry(movement_frame, textvariable=self.max_movement, width=8).pack(side=tk.LEFT, padx=5)
        
        # Distance Threshold control
        distance_frame = ttk.Frame(param_frame)
        distance_frame.pack(pady=5, fill='x')
        ttk.Label(distance_frame, text="Distance Threshold:").pack(side=tk.LEFT)
        ttk.Entry(distance_frame, textvariable=self.distance_threshold, width=8).pack(side=tk.LEFT, padx=5)
        
        # Add buttons frame
        button_frame = ttk.Frame(param_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add update parameters button
        def update_parameters():
            try:
                # Update the parameters dictionary with current values
                self._parameters.update({
                    'area': (float(self.area_min.get()), float(self.area_max.get())),
                    'perimeter': (float(self.perimeter_min.get()), float(self.perimeter_max.get())),
                    'circularity': (float(self.circularity_min.get()), float(self.circularity_max.get())),
                    'cell_memory_frames': int(self.cell_memory_frames.get()),
                    'max_movement': int(self.max_movement.get()),
                    'distance_threshold': int(self.distance_threshold.get())
                })
                
                messagebox.showinfo("Success", 
                    "Parameters have been updated successfully!")
                
            except ValueError as e:
                messagebox.showerror("Invalid Value", 
                    "Please ensure all values are valid numbers.")
            except Exception as e:
                messagebox.showerror("Error", 
                    f"Error updating parameters: {str(e)}")
        
        ttk.Button(button_frame, text="Update Parameters",
                  command=update_parameters).pack(side=tk.TOP, pady=2, fill=tk.X)
        
        # Add quit button
        ttk.Button(button_frame, text="Quit",
                  command=self.on_closing).pack(side=tk.TOP, pady=2, fill=tk.X)
    
    def create_video_frames(self):
        """Create frames for displaying video feeds"""
        # Create a frame to hold the label in the cell detection window
        cell_frame = ttk.Frame(self.cell_detection_window)
        cell_frame.pack(fill='both', expand=True)
        self.cell_detection_label = ttk.Label(cell_frame)
        self.cell_detection_label.pack(fill='both', expand=True)
        
        # Create a frame to hold the label in the white rectangles window
        white_frame = ttk.Frame(self.white_rectangles_window)
        white_frame.pack(fill='both', expand=True)
        self.white_rectangles_label = ttk.Label(white_frame)
        self.white_rectangles_label.pack(fill='both', expand=True)
        
        # Bind configure event to handle window resizing
        self.white_rectangles_window.bind('<Configure>', self._on_resize)
    
    def _on_resize(self, event):
        """Handle window resize events"""
        if hasattr(self, 'current_frame2') and self.current_frame2 is not None:
            self._update_white_rectangles_display()
    
    def _update_white_rectangles_display(self):
        """Update white rectangles display with proper scaling"""
        if self.current_frame2 is None:
            return
            
        # Get current window size
        win_width = self.white_rectangles_window.winfo_width()
        win_height = self.white_rectangles_window.winfo_height()
        
        # Check if window has valid dimensions
        if win_width <= 0 or win_height <= 0:
            return
            
        # Get image size
        img_height, img_width = self.current_frame2.shape[:2]
        
        # Calculate scaling factor to maintain aspect ratio
        scale = min(win_width/img_width, win_height/img_height)
        
        # Ensure scale is positive and results in valid dimensions
        if scale <= 0:
            return
            
        new_width = max(1, int(img_width * scale))
        new_height = max(1, int(img_height * scale))
        
        try:
            # Resize the image
            frame2_rgb = cv2.cvtColor(self.current_frame2, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(frame2_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Convert to PhotoImage
            frame2_img = Image.fromarray(resized)
            frame2_photo = ImageTk.PhotoImage(image=frame2_img)
            
            # Update label
            self.white_rectangles_label.configure(image=frame2_photo)
            self.white_rectangles_label.image = frame2_photo
        except cv2.error:
            # If resize fails, skip this update
            pass
    
    def update_video_display(self, frame1, frame2):
        """Update the video display windows with new frames"""
        if self.quit_flag:
            return
            
        # Store current frames
        self.set_current_frame(frame1)
        self.current_frame2 = frame2.copy()  # Store frame2 for resize handling
        
        # Update cell detection display (normal size)
        frame1_rgb = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        frame1_img = Image.fromarray(frame1_rgb)
        frame1_photo = ImageTk.PhotoImage(image=frame1_img)
        self.cell_detection_label.configure(image=frame1_photo)
        self.cell_detection_label.image = frame1_photo
        
        # Update white rectangles display with scaling
        self._update_white_rectangles_display()
        
        # Process events
        self.root.update()
    
    def get_parameters(self):
        """Get the current parameter values"""
        return self._parameters
    
    def take_param_snapshot(self):
        """Capture and analyze current frame for parameter adjustment"""
        if self.current_frame is not None:
            frame = self.current_frame.copy()
            from cell_tracking_for_usbcam import process_frame
            processed_frame = process_frame(frame, self.get_parameters())
            
            # Get enhanced image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(10, 10))
            enhanced = clahe.apply(gray)
            enhanced_frame = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            final_seg = processed_frame[2]
            labeled = measure.label(final_seg)
            regions = measure.regionprops(labeled)
            
            self.snapshot_analyzer.analyze_snapshot(enhanced_frame, regions)
        else:
            messagebox.showwarning("No Frame", "No camera frame available")
    
    def take_process_snapshot(self):
        """Take a snapshot and save all processing steps"""
        if self.current_frame is not None:
            import os
            from cell_tracking_for_usbcam import process_frame_debug
            
            # Create cam-process directory if it doesn't exist
            process_dir = 'cam-process'
            if not os.path.exists(process_dir):
                os.makedirs(process_dir)
            
            # Save original frame
            cv2.imwrite(os.path.join(process_dir, '0-Original.png'), self.current_frame)
            
            # Process frame with debug output
            process_frame_debug(self.current_frame, process_dir)
            
            messagebox.showinfo("Snapshot", "Processing steps saved in 'cam-process' folder")
        else:
            messagebox.showwarning("Snapshot", "No frame available")
    
    def set_current_frame(self, frame):
        """Store the current frame for snapshot"""
        self.current_frame = frame.copy() if frame is not None else None
    
    def update(self):
        """Update the tkinter windows"""
        self.root.update()
        self.cell_detection_window.update()
        self.white_rectangles_window.update()
    
    @property
    def parameters(self):
        """Get current parameter values"""
        return self._parameters
    
    def _update_parameters(self):
        """Update parameters from UI values"""
        try:
            self._parameters['area'] = (int(self.area_min.get()), int(self.area_max.get()))
            self._parameters['perimeter'] = (int(self.perimeter_min.get()), int(self.perimeter_max.get()))
            self._parameters['circularity'] = (float(self.circularity_min.get()), float(self.circularity_max.get()))
            self._parameters['cell_memory_frames'] = int(self.cell_memory_frames.get())
            self._parameters['max_movement'] = int(self.max_movement.get())
            self._parameters['distance_threshold'] = int(self.distance_threshold.get())
        except ValueError:
            print("Please enter valid numbers for all parameters")

if __name__ == "__main__":
    ui = UnifiedUI()
    ui.update()
    ui.root.mainloop()
