import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk

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
        self.white_rectangles_window.geometry("800x600")
        self.white_rectangles_window.minsize(640, 480)
        
        # Flag for quitting
        self.quit_flag = False
        
        # Create frames
        self.create_parameter_frame()
        self.create_video_frames()
        
        # Initialize parameters with default values
        self._parameters = {
            'area': (50, 4000),
            'perimeter': (50, 300),
            'circularity': (0.8, 1.8),
            'cell_memory_frames': 5,
            'max_movement': 200,
            'distance_threshold': 50
        }
        
        # Set up window close handlers
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.cell_detection_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.white_rectangles_window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle window close event"""
        self.quit_flag = True
        self.root.quit()
    
    def create_parameter_frame(self):
        # Parameter control panel
        param_frame = ttk.Frame(self.root, padding="10")
        param_frame.pack(fill='both', expand=True)
        
        # Parameter variables
        self.area_min = tk.StringVar(value="50")
        self.area_max = tk.StringVar(value="4000")
        self.perimeter_min = tk.StringVar(value="50")
        self.perimeter_max = tk.StringVar(value="300")
        self.circularity_min = tk.StringVar(value="0.8")
        self.circularity_max = tk.StringVar(value="1.8")
        self.cell_memory_frames = tk.StringVar(value="5")
        self.max_movement = tk.StringVar(value="200")
        self.distance_threshold = tk.StringVar(value="50")
        
        # Cell Detection Parameters section
        detection_frame = ttk.LabelFrame(param_frame, text="Cell Detection Parameters", padding="5")
        detection_frame.pack(pady=5, fill='x')
        
        # Area controls
        area_frame = ttk.Frame(detection_frame)
        area_frame.pack(pady=5, fill='x')
        ttk.Label(area_frame, text="Area:").pack(side=tk.LEFT)
        ttk.Entry(area_frame, textvariable=self.area_min, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(area_frame, text="<").pack(side=tk.LEFT)
        ttk.Entry(area_frame, textvariable=self.area_max, width=8).pack(side=tk.LEFT, padx=5)
        
        # Perimeter controls
        perimeter_frame = ttk.Frame(detection_frame)
        perimeter_frame.pack(pady=5, fill='x')
        ttk.Label(perimeter_frame, text="Perimeter:").pack(side=tk.LEFT)
        ttk.Entry(perimeter_frame, textvariable=self.perimeter_min, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(perimeter_frame, text="<").pack(side=tk.LEFT)
        ttk.Entry(perimeter_frame, textvariable=self.perimeter_max, width=8).pack(side=tk.LEFT, padx=5)
        
        # Circularity controls
        circularity_frame = ttk.Frame(detection_frame)
        circularity_frame.pack(pady=5, fill='x')
        ttk.Label(circularity_frame, text="Circularity:").pack(side=tk.LEFT)
        ttk.Entry(circularity_frame, textvariable=self.circularity_min, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(circularity_frame, text="<").pack(side=tk.LEFT)
        ttk.Entry(circularity_frame, textvariable=self.circularity_max, width=8).pack(side=tk.LEFT, padx=5)
        
        # Tracking Parameters section
        tracking_frame = ttk.LabelFrame(param_frame, text="Cell Tracking Parameters", padding="5")
        tracking_frame.pack(pady=5, fill='x')
        
        # Cell Memory Frames control
        memory_frame = ttk.Frame(tracking_frame)
        memory_frame.pack(pady=5, fill='x')
        ttk.Label(memory_frame, text="Cell Memory Frames:").pack(side=tk.LEFT)
        ttk.Entry(memory_frame, textvariable=self.cell_memory_frames, width=8).pack(side=tk.LEFT, padx=5)
        
        # Max Movement control
        movement_frame = ttk.Frame(tracking_frame)
        movement_frame.pack(pady=5, fill='x')
        ttk.Label(movement_frame, text="Max Movement (px):").pack(side=tk.LEFT)
        ttk.Entry(movement_frame, textvariable=self.max_movement, width=8).pack(side=tk.LEFT, padx=5)
        
        # Distance Threshold control
        distance_frame = ttk.Frame(tracking_frame)
        distance_frame.pack(pady=5, fill='x')
        ttk.Label(distance_frame, text="Distance Threshold:").pack(side=tk.LEFT)
        ttk.Entry(distance_frame, textvariable=self.distance_threshold, width=8).pack(side=tk.LEFT, padx=5)
        
        # Buttons at the bottom
        ttk.Button(param_frame, text="Update Parameters", command=self._update_parameters).pack(pady=5, fill='x')
        ttk.Button(param_frame, text="Quit", command=self.on_closing).pack(pady=5, fill='x')
    
    def create_video_frames(self):
        # Create canvas for cell detection window
        self.cell_detection_canvas = tk.Canvas(self.cell_detection_window)
        self.cell_detection_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for white rectangles window
        self.white_rectangles_canvas = tk.Canvas(self.white_rectangles_window)
        self.white_rectangles_canvas.pack(fill=tk.BOTH, expand=True)
    
    def update_frame(self, frame, canvas, window_name):
        """Update a video frame in the specified canvas"""
        if frame is None:
            return
        
        # Get canvas size
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Only resize if canvas has valid dimensions
            # Convert frame to PIL Image
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            
            # Calculate aspect ratio preserving resize dimensions
            img_ratio = frame.shape[1] / frame.shape[0]
            canvas_ratio = canvas_width / canvas_height
            
            if canvas_ratio > img_ratio:
                # Canvas is wider than image
                height = canvas_height
                width = int(height * img_ratio)
            else:
                # Canvas is taller than image
                width = canvas_width
                height = int(width / img_ratio)
            
            # Resize image
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image=image)
            
            # Update canvas
            canvas.delete("all")
            canvas.create_image(canvas_width//2, canvas_height//2, image=photo, anchor=tk.CENTER)
            canvas.image = photo  # Keep a reference to avoid garbage collection
    
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
