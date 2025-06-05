import cv2
import numpy as np
from skimage import filters, morphology, measure, segmentation
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import time
import json
import scipy.ndimage as ndi

class ParameterVisualizationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cell Detection Parameter Visualization")
        self.root.geometry("1600x900")
        
        # Enable mousewheel scrolling
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Default parameters
        self.params = {
            'clahe_clip_limit': 2.5,
            'clahe_tile_size': 10,
            'min_object_size': 15,
            'eccentricity_threshold': 0.98,
            'area_threshold_small': 200,
            'area_threshold_large': 400,
            'area_min': 50,
            'area_max': 300,
            'perimeter_min': 100,
            'perimeter_max': 300,
            'circularity_min': 0.8,
            'circularity_max': 12,
            'aspect_ratio_threshold': 1.5,
            'use_watershed': True,
            'watershed_distance_threshold': 10,
            'watershed_footprint_size': 3,
            'watershed_compactness': 0.5,
            'watershed_min_area': 500
        }
        
        # Image path
        self.image_path = None
        self.original_image = None
        
        # Create main frames
        self.create_frames()
        
        # Create parameter controls
        self.create_parameter_controls()
        
        # Create image display area
        self.create_image_display()
        
        # Create menu
        self.create_menu()
    
    def create_frames(self):
        # Create a frame to hold the scrollable control panel
        self.control_container = ttk.Frame(self.root)
        self.control_container.pack(side=tk.LEFT, fill=tk.Y)
        
        # Add a scrollbar to the control container
        self.scrollbar = ttk.Scrollbar(self.control_container, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a canvas for scrolling
        self.control_canvas = tk.Canvas(self.control_container, width=300, yscrollcommand=self.scrollbar.set)
        self.control_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        
        # Configure the scrollbar to work with the canvas
        self.scrollbar.config(command=self.control_canvas.yview)
        
        # Create a frame inside the canvas for the controls
        self.control_frame = ttk.Frame(self.control_canvas, padding="10")
        
        # Add the control frame to the canvas
        self.control_canvas_window = self.control_canvas.create_window((0, 0), window=self.control_frame, anchor=tk.NW)
        
        # Right frame for images
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Configure the canvas to resize with the frame
        self.control_frame.bind("<Configure>", self.on_frame_configure)
        self.control_canvas.bind("<Configure>", self.on_canvas_configure)
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_separator()
        file_menu.add_command(label="Save Parameters", command=self.save_parameters)
        file_menu.add_command(label="Load Parameters", command=self.load_parameters)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
    
    def on_frame_configure(self, event):
        # Update the scrollregion when the size of the frame changes
        self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        # Update the width of the window when the canvas changes size
        self.control_canvas.itemconfig(self.control_canvas_window, width=event.width)
    
    def create_parameter_controls(self):
        # Title
        ttk.Label(self.control_frame, text="Parameter Controls", font=("Arial", 14, "bold")).pack(pady=10)
        
        # CLAHE parameters
        ttk.Label(self.control_frame, text="CLAHE Parameters", font=("Arial", 12)).pack(pady=(10, 5), anchor="w")
        
        # CLAHE Clip Limit
        clip_limit_frame = ttk.Frame(self.control_frame)
        clip_limit_frame.pack(fill=tk.X, pady=2)
        ttk.Label(clip_limit_frame, text="Clip Limit:").pack(side=tk.LEFT)
        self.clahe_clip_var = tk.DoubleVar(value=self.params['clahe_clip_limit'])
        self.clahe_clip_value_label = ttk.Label(clip_limit_frame, text=f"{self.params['clahe_clip_limit']:.2f}")
        self.clahe_clip_value_label.pack(side=tk.RIGHT)
        clahe_clip_scale = ttk.Scale(self.control_frame, from_=0.5, to=5.0, 
                                    variable=self.clahe_clip_var, 
                                    command=lambda x: self.update_param('clahe_clip_limit', float(x)))
        clahe_clip_scale.pack(fill=tk.X, pady=2)
        
        # CLAHE Tile Size
        tile_size_frame = ttk.Frame(self.control_frame)
        tile_size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(tile_size_frame, text="Tile Size:").pack(side=tk.LEFT)
        self.clahe_tile_var = tk.IntVar(value=self.params['clahe_tile_size'])
        self.clahe_tile_value_label = ttk.Label(tile_size_frame, text=f"{self.params['clahe_tile_size']}")
        self.clahe_tile_value_label.pack(side=tk.RIGHT)
        clahe_tile_scale = ttk.Scale(self.control_frame, from_=2, to=20, 
                                    variable=self.clahe_tile_var,
                                    command=lambda x: self.update_param('clahe_tile_size', int(float(x))))
        clahe_tile_scale.pack(fill=tk.X, pady=2)
        
        # Segmentation parameters
        ttk.Label(self.control_frame, text="Segmentation Parameters", font=("Arial", 12)).pack(pady=(15, 5), anchor="w")
        
        # Min Object Size
        min_size_frame = ttk.Frame(self.control_frame)
        min_size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(min_size_frame, text="Min Object Size:").pack(side=tk.LEFT)
        self.min_size_var = tk.IntVar(value=self.params['min_object_size'])
        self.min_size_value_label = ttk.Label(min_size_frame, text=f"{self.params['min_object_size']}")
        self.min_size_value_label.pack(side=tk.RIGHT)
        min_size_scale = ttk.Scale(self.control_frame, from_=5, to=50, 
                                  variable=self.min_size_var,
                                  command=lambda x: self.update_param('min_object_size', int(float(x))))
        min_size_scale.pack(fill=tk.X, pady=2)
        
        # Eccentricity Threshold
        eccentricity_frame = ttk.Frame(self.control_frame)
        eccentricity_frame.pack(fill=tk.X, pady=2)
        ttk.Label(eccentricity_frame, text="Eccentricity Threshold:").pack(side=tk.LEFT)
        self.eccentricity_var = tk.DoubleVar(value=self.params['eccentricity_threshold'])
        self.eccentricity_value_label = ttk.Label(eccentricity_frame, text=f"{self.params['eccentricity_threshold']:.2f}")
        self.eccentricity_value_label.pack(side=tk.RIGHT)
        eccentricity_scale = ttk.Scale(self.control_frame, from_=0.5, to=1.0, 
                                      variable=self.eccentricity_var,
                                      command=lambda x: self.update_param('eccentricity_threshold', float(x)))
        eccentricity_scale.pack(fill=tk.X, pady=2)
        
        # Area Thresholds for Segmentation
        area_small_frame = ttk.Frame(self.control_frame)
        area_small_frame.pack(fill=tk.X, pady=2)
        ttk.Label(area_small_frame, text="Area Threshold Small:").pack(side=tk.LEFT)
        self.area_small_var = tk.IntVar(value=self.params['area_threshold_small'])
        self.area_small_value_label = ttk.Label(area_small_frame, text=f"{self.params['area_threshold_small']}")
        self.area_small_value_label.pack(side=tk.RIGHT)
        area_small_scale = ttk.Scale(self.control_frame, from_=50, to=500, 
                                    variable=self.area_small_var,
                                    command=lambda x: self.update_param('area_threshold_small', int(float(x))))
        area_small_scale.pack(fill=tk.X, pady=2)
        
        area_large_frame = ttk.Frame(self.control_frame)
        area_large_frame.pack(fill=tk.X, pady=2)
        ttk.Label(area_large_frame, text="Area Threshold Large:").pack(side=tk.LEFT)
        self.area_large_var = tk.IntVar(value=self.params['area_threshold_large'])
        self.area_large_value_label = ttk.Label(area_large_frame, text=f"{self.params['area_threshold_large']}")
        self.area_large_value_label.pack(side=tk.RIGHT)
        area_large_scale = ttk.Scale(self.control_frame, from_=200, to=1000, 
                                    variable=self.area_large_var,
                                    command=lambda x: self.update_param('area_threshold_large', int(float(x))))
        area_large_scale.pack(fill=tk.X, pady=2)
        
        # Final filtering parameters
        ttk.Label(self.control_frame, text="Final Filtering Parameters", font=("Arial", 12)).pack(pady=(15, 5), anchor="w")
        
        # Area Range
        area_min_frame = ttk.Frame(self.control_frame)
        area_min_frame.pack(fill=tk.X, pady=2)
        ttk.Label(area_min_frame, text="Area Min:").pack(side=tk.LEFT)
        self.area_min_var = tk.IntVar(value=self.params['area_min'])
        self.area_min_value_label = ttk.Label(area_min_frame, text=f"{self.params['area_min']}")
        self.area_min_value_label.pack(side=tk.RIGHT)
        area_min_scale = ttk.Scale(self.control_frame, from_=5, to=300, 
                                  variable=self.area_min_var,
                                  command=lambda x: self.update_param('area_min', int(float(x))))
        area_min_scale.pack(fill=tk.X, pady=2)
        
        area_max_frame = ttk.Frame(self.control_frame)
        area_max_frame.pack(fill=tk.X, pady=2)
        ttk.Label(area_max_frame, text="Area Max:").pack(side=tk.LEFT)
        self.area_max_var = tk.IntVar(value=self.params['area_max'])
        self.area_max_value_label = ttk.Label(area_max_frame, text=f"{self.params['area_max']}")
        self.area_max_value_label.pack(side=tk.RIGHT)
        area_max_scale = ttk.Scale(self.control_frame, from_=50, to=1200, 
                                  variable=self.area_max_var,
                                  command=lambda x: self.update_param('area_max', int(float(x))))
        area_max_scale.pack(fill=tk.X, pady=2)
        
        # Perimeter Range
        perimeter_min_frame = ttk.Frame(self.control_frame)
        perimeter_min_frame.pack(fill=tk.X, pady=2)
        ttk.Label(perimeter_min_frame, text="Perimeter Min:").pack(side=tk.LEFT)
        self.perimeter_min_var = tk.IntVar(value=self.params['perimeter_min'])
        self.perimeter_min_value_label = ttk.Label(perimeter_min_frame, text=f"{self.params['perimeter_min']}")
        self.perimeter_min_value_label.pack(side=tk.RIGHT)
        perimeter_min_scale = ttk.Scale(self.control_frame, from_=5, to=200, 
                                       variable=self.perimeter_min_var,
                                       command=lambda x: self.update_param('perimeter_min', int(float(x))))
        perimeter_min_scale.pack(fill=tk.X, pady=2)
        
        perimeter_max_frame = ttk.Frame(self.control_frame)
        perimeter_max_frame.pack(fill=tk.X, pady=2)
        ttk.Label(perimeter_max_frame, text="Perimeter Max:").pack(side=tk.LEFT)
        self.perimeter_max_var = tk.IntVar(value=self.params['perimeter_max'])
        self.perimeter_max_value_label = ttk.Label(perimeter_max_frame, text=f"{self.params['perimeter_max']}")
        self.perimeter_max_value_label.pack(side=tk.RIGHT)
        perimeter_max_scale = ttk.Scale(self.control_frame, from_=50, to=400, 
                                       variable=self.perimeter_max_var,
                                       command=lambda x: self.update_param('perimeter_max', int(float(x))))
        perimeter_max_scale.pack(fill=tk.X, pady=2)
        
        # Circularity Range
        circularity_min_frame = ttk.Frame(self.control_frame)
        circularity_min_frame.pack(fill=tk.X, pady=2)
        ttk.Label(circularity_min_frame, text="Circularity Min:").pack(side=tk.LEFT)
        self.circularity_min_var = tk.DoubleVar(value=self.params['circularity_min'])
        self.circularity_min_value_label = ttk.Label(circularity_min_frame, text=f"{self.params['circularity_min']:.2f}")
        self.circularity_min_value_label.pack(side=tk.RIGHT)
        circularity_min_scale = ttk.Scale(self.control_frame, from_=0.1, to=5.0, 
                                         variable=self.circularity_min_var,
                                         command=lambda x: self.update_param('circularity_min', float(x)))
        circularity_min_scale.pack(fill=tk.X, pady=2)
        
        circularity_max_frame = ttk.Frame(self.control_frame)
        circularity_max_frame.pack(fill=tk.X, pady=2)
        ttk.Label(circularity_max_frame, text="Circularity Max:").pack(side=tk.LEFT)
        self.circularity_max_var = tk.DoubleVar(value=self.params['circularity_max'])
        self.circularity_max_value_label = ttk.Label(circularity_max_frame, text=f"{self.params['circularity_max']:.2f}")
        self.circularity_max_value_label.pack(side=tk.RIGHT)
        circularity_max_scale = ttk.Scale(self.control_frame, from_=5.0, to=20.0, 
                                         variable=self.circularity_max_var,
                                         command=lambda x: self.update_param('circularity_max', float(x)))
        circularity_max_scale.pack(fill=tk.X, pady=2)
        
        # Aspect Ratio Threshold
        aspect_ratio_frame = ttk.Frame(self.control_frame)
        aspect_ratio_frame.pack(fill=tk.X, pady=2)
        ttk.Label(aspect_ratio_frame, text="Aspect Ratio Threshold:").pack(side=tk.LEFT)
        self.aspect_ratio_var = tk.DoubleVar(value=self.params['aspect_ratio_threshold'])
        self.aspect_ratio_value_label = ttk.Label(aspect_ratio_frame, text=f"{self.params['aspect_ratio_threshold']:.2f}")
        self.aspect_ratio_value_label.pack(side=tk.RIGHT)
        aspect_ratio_scale = ttk.Scale(self.control_frame, from_=1.0, to=3.0, 
                                       variable=self.aspect_ratio_var,
                                       command=lambda x: self.update_param('aspect_ratio_threshold', float(x)))
        aspect_ratio_scale.pack(fill=tk.X, pady=2)
        
        # Watershed Segmentation Parameters
        ttk.Label(self.control_frame, text="Watershed Segmentation", font=("Arial", 12)).pack(pady=(15, 5), anchor="w")
        
        # Enable/Disable Watershed
        watershed_enable_frame = ttk.Frame(self.control_frame)
        watershed_enable_frame.pack(fill=tk.X, pady=2)
        ttk.Label(watershed_enable_frame, text="Use Watershed:").pack(side=tk.LEFT)
        self.watershed_var = tk.BooleanVar(value=self.params['use_watershed'])
        self.watershed_checkbox = ttk.Checkbutton(watershed_enable_frame, variable=self.watershed_var,
                                            command=lambda: self.update_param('use_watershed', self.watershed_var.get()))
        self.watershed_checkbox.pack(side=tk.RIGHT)
        
        # Distance Threshold
        distance_threshold_frame = ttk.Frame(self.control_frame)
        distance_threshold_frame.pack(fill=tk.X, pady=2)
        ttk.Label(distance_threshold_frame, text="Distance Threshold:").pack(side=tk.LEFT)
        self.distance_threshold_var = tk.IntVar(value=self.params['watershed_distance_threshold'])
        self.distance_threshold_value_label = ttk.Label(distance_threshold_frame, text=f"{self.params['watershed_distance_threshold']}")
        self.distance_threshold_value_label.pack(side=tk.RIGHT)
        distance_threshold_scale = ttk.Scale(self.control_frame, from_=1, to=50, 
                                        variable=self.distance_threshold_var,
                                        command=lambda x: self.update_param('watershed_distance_threshold', int(float(x))))
        distance_threshold_scale.pack(fill=tk.X, pady=2)
        
        # Footprint Size
        footprint_size_frame = ttk.Frame(self.control_frame)
        footprint_size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(footprint_size_frame, text="Footprint Size:").pack(side=tk.LEFT)
        self.footprint_size_var = tk.IntVar(value=self.params['watershed_footprint_size'])
        self.footprint_size_value_label = ttk.Label(footprint_size_frame, text=f"{self.params['watershed_footprint_size']}")
        self.footprint_size_value_label.pack(side=tk.RIGHT)
        footprint_size_scale = ttk.Scale(self.control_frame, from_=1, to=10, 
                                     variable=self.footprint_size_var,
                                     command=lambda x: self.update_param('watershed_footprint_size', int(float(x))))
        footprint_size_scale.pack(fill=tk.X, pady=2)
        
        # Compactness
        compactness_frame = ttk.Frame(self.control_frame)
        compactness_frame.pack(fill=tk.X, pady=2)
        ttk.Label(compactness_frame, text="Compactness:").pack(side=tk.LEFT)
        self.compactness_var = tk.DoubleVar(value=self.params['watershed_compactness'])
        self.compactness_value_label = ttk.Label(compactness_frame, text=f"{self.params['watershed_compactness']:.2f}")
        self.compactness_value_label.pack(side=tk.RIGHT)
        compactness_scale = ttk.Scale(self.control_frame, from_=0.0, to=1.0, 
                                  variable=self.compactness_var,
                                  command=lambda x: self.update_param('watershed_compactness', float(x)))
        compactness_scale.pack(fill=tk.X, pady=2)
        
        # Minimum Area for Watershed
        min_area_frame = ttk.Frame(self.control_frame)
        min_area_frame.pack(fill=tk.X, pady=2)
        ttk.Label(min_area_frame, text="Min Area for Watershed:").pack(side=tk.LEFT)
        self.watershed_min_area_var = tk.IntVar(value=self.params['watershed_min_area'])
        self.watershed_min_area_value_label = ttk.Label(min_area_frame, text=f"{self.params['watershed_min_area']}")
        self.watershed_min_area_value_label.pack(side=tk.RIGHT)
        min_area_scale = ttk.Scale(self.control_frame, from_=100, to=1000, 
                              variable=self.watershed_min_area_var,
                              command=lambda x: self.update_param('watershed_min_area', int(float(x))))
        min_area_scale.pack(fill=tk.X, pady=2)
        
        # Add parameter save/load buttons
        param_buttons_frame = ttk.Frame(self.control_frame)
        param_buttons_frame.pack(fill=tk.X, pady=10)
        
        save_btn = ttk.Button(param_buttons_frame, text="Save Parameters", command=self.save_parameters)
        save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        load_btn = ttk.Button(param_buttons_frame, text="Load Parameters", command=self.load_parameters)
        load_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        
        # Status label
        self.status_label = ttk.Label(self.control_frame, text="No image loaded")
        self.status_label.pack(pady=10)
    
    def create_image_display(self):
        # Create three image frames
        self.image_display_frame = ttk.Frame(self.image_frame)
        self.image_display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Labeled Image
        self.labeled_frame = ttk.LabelFrame(self.image_display_frame, text="17-Labeled")
        self.labeled_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.labeled_canvas = tk.Canvas(self.labeled_frame, width=500, height=500)
        self.labeled_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Parameters Image
        self.params_frame = ttk.LabelFrame(self.image_display_frame, text="18.5-Parameters")
        self.params_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.params_canvas = tk.Canvas(self.params_frame, width=500, height=500)
        self.params_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Final Result Image
        self.final_frame = ttk.LabelFrame(self.image_display_frame, text="19-FinalResult")
        self.final_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.final_canvas = tk.Canvas(self.final_frame, width=500, height=500)
        self.final_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.image_display_frame.grid_columnconfigure(0, weight=1)
        self.image_display_frame.grid_columnconfigure(1, weight=1)
        self.image_display_frame.grid_columnconfigure(2, weight=1)
        self.image_display_frame.grid_rowconfigure(0, weight=1)
    
    def update_param(self, param_name, value):
        self.params[param_name] = value
        
        # Update the value label
        if param_name == 'clahe_clip_limit':
            self.clahe_clip_value_label.config(text=f"{value:.2f}")
        elif param_name == 'clahe_tile_size':
            self.clahe_tile_value_label.config(text=f"{value}")
        elif param_name == 'min_object_size':
            self.min_size_value_label.config(text=f"{value}")
        elif param_name == 'eccentricity_threshold':
            self.eccentricity_value_label.config(text=f"{value:.2f}")
        elif param_name == 'area_threshold_small':
            self.area_small_value_label.config(text=f"{value}")
        elif param_name == 'area_threshold_large':
            self.area_large_value_label.config(text=f"{value}")
        elif param_name == 'area_min':
            self.area_min_value_label.config(text=f"{value}")
        elif param_name == 'area_max':
            self.area_max_value_label.config(text=f"{value}")
        elif param_name == 'perimeter_min':
            self.perimeter_min_value_label.config(text=f"{value}")
        elif param_name == 'perimeter_max':
            self.perimeter_max_value_label.config(text=f"{value}")
        elif param_name == 'circularity_min':
            self.circularity_min_value_label.config(text=f"{value:.2f}")
        elif param_name == 'circularity_max':
            self.circularity_max_value_label.config(text=f"{value:.2f}")
        elif param_name == 'aspect_ratio_threshold':
            self.aspect_ratio_value_label.config(text=f"{value:.2f}")
        elif param_name == 'watershed_distance_threshold':
            self.distance_threshold_value_label.config(text=f"{value}")
        elif param_name == 'watershed_footprint_size':
            self.footprint_size_value_label.config(text=f"{value}")
        elif param_name == 'watershed_compactness':
            self.compactness_value_label.config(text=f"{value:.2f}")
        elif param_name == 'watershed_min_area':
            self.watershed_min_area_value_label.config(text=f"{value}")
        
        # Process the image automatically when a parameter changes
        if self.image_path is not None and self.original_image is not None:
            self.process_current_image()
        
    def save_parameters(self):
        """Save current parameters to a JSON file with auto-generated filename"""
        try:
            # Create parameters directory if it doesn't exist
            params_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters")
            if not os.path.exists(params_dir):
                os.makedirs(params_dir)
            
            # Generate filename based on current date and time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # If an image is loaded, include its name in the parameter filename
            if self.image_path:
                image_name = os.path.splitext(os.path.basename(self.image_path))[0]
                default_filename = f"params_{image_name}_{timestamp}.json"
            else:
                default_filename = f"params_{timestamp}.json"
            
            # Use the root window as parent to prevent dialog from getting stuck
            file_path = filedialog.asksaveasfilename(
                title="Save Parameters",
                initialdir=params_dir,
                initialfile=default_filename,
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                parent=self.root
            )
            
            # Check if file_path is empty (user canceled)
            if not file_path:
                self.status_label.config(text="Save canceled")
                return
                
            # Save the parameters
            with open(file_path, 'w') as f:
                json.dump(self.params, f, indent=4)
            self.status_label.config(text=f"Parameters saved to {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save parameters: {str(e)}")
            self.status_label.config(text="Error saving parameters")
    
    def load_parameters(self):
        """Load parameters from a JSON file"""
        try:
            # Get the parameters directory
            params_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters")
            if os.path.exists(params_dir):
                initial_dir = params_dir
            else:
                initial_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Use the root window as parent to prevent dialog from getting stuck
            file_path = filedialog.askopenfilename(
                title="Load Parameters",
                initialdir=initial_dir,
                filetypes=[("JSON files", "*.json")],
                parent=self.root
            )
            
            # Check if file_path is empty (user canceled)
            if not file_path:
                self.status_label.config(text="Load canceled")
                return
            
            # Load the parameters
            with open(file_path, 'r') as f:
                loaded_params = json.load(f)
            
            # Update parameters
            for key, value in loaded_params.items():
                if key in self.params:
                    self.params[key] = value
            
            # Update UI controls
            self.update_ui_from_params()
            
            self.status_label.config(text=f"Parameters loaded from {os.path.basename(file_path)}")
            
            # Process image if one is loaded
            if self.image_path is not None and self.original_image is not None:
                self.process_current_image()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load parameters: {str(e)}")
            self.status_label.config(text="Error loading parameters")
    
    def update_ui_from_params(self):
        """Update UI controls based on loaded parameters"""
        # Update sliders and value labels
        self.clahe_clip_var.set(self.params['clahe_clip_limit'])
        self.clahe_clip_value_label.config(text=f"{self.params['clahe_clip_limit']:.2f}")
        
        self.clahe_tile_var.set(self.params['clahe_tile_size'])
        self.clahe_tile_value_label.config(text=f"{self.params['clahe_tile_size']}")
        
        self.min_size_var.set(self.params['min_object_size'])
        self.min_size_value_label.config(text=f"{self.params['min_object_size']}")
        
        self.eccentricity_var.set(self.params['eccentricity_threshold'])
        self.eccentricity_value_label.config(text=f"{self.params['eccentricity_threshold']:.2f}")
        
        self.area_small_var.set(self.params['area_threshold_small'])
        self.area_small_value_label.config(text=f"{self.params['area_threshold_small']}")
        
        self.area_large_var.set(self.params['area_threshold_large'])
        self.area_large_value_label.config(text=f"{self.params['area_threshold_large']}")
        
        self.area_min_var.set(self.params['area_min'])
        self.area_min_value_label.config(text=f"{self.params['area_min']}")
        
        self.area_max_var.set(self.params['area_max'])
        self.area_max_value_label.config(text=f"{self.params['area_max']}")
        
        self.perimeter_min_var.set(self.params['perimeter_min'])
        self.perimeter_min_value_label.config(text=f"{self.params['perimeter_min']}")
        
        self.perimeter_max_var.set(self.params['perimeter_max'])
        self.perimeter_max_value_label.config(text=f"{self.params['perimeter_max']}")
        
        self.circularity_min_var.set(self.params['circularity_min'])
        self.circularity_min_value_label.config(text=f"{self.params['circularity_min']:.2f}")
        
        self.circularity_max_var.set(self.params['circularity_max'])
        self.circularity_max_value_label.config(text=f"{self.params['circularity_max']:.2f}")
        
        self.aspect_ratio_var.set(self.params['aspect_ratio_threshold'])
        self.aspect_ratio_value_label.config(text=f"{self.params['aspect_ratio_threshold']:.2f}")
        
        # Update watershed parameters
        if 'use_watershed' in self.params:
            self.watershed_var.set(self.params['use_watershed'])
        
        if 'watershed_distance_threshold' in self.params:
            self.distance_threshold_var.set(self.params['watershed_distance_threshold'])
            self.distance_threshold_value_label.config(text=f"{self.params['watershed_distance_threshold']}")
        
        if 'watershed_footprint_size' in self.params:
            self.footprint_size_var.set(self.params['watershed_footprint_size'])
            self.footprint_size_value_label.config(text=f"{self.params['watershed_footprint_size']}")
        
        if 'watershed_compactness' in self.params:
            self.compactness_var.set(self.params['watershed_compactness'])
            self.compactness_value_label.config(text=f"{self.params['watershed_compactness']:.2f}")
            
        if 'watershed_min_area' in self.params:
            self.watershed_min_area_var.set(self.params['watershed_min_area'])
            self.watershed_min_area_value_label.config(text=f"{self.params['watershed_min_area']}")
    
    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")]
        )
        
        if file_path:
            self.image_path = file_path
            try:
                # Try to load the image using a normalized path to handle non-ASCII characters
                normalized_path = os.path.normpath(file_path)
                self.original_image = cv2.imread(normalized_path)
                
                # If the image is still None, try with PIL and convert to OpenCV format
                if self.original_image is None:
                    pil_image = Image.open(file_path)
                    self.original_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    
                if self.original_image is not None:
                    self.status_label.config(text="Image loaded - Processing...")
                    self.process_current_image()
                else:
                    self.status_label.config(text="Error: Could not load image")
                    messagebox.showerror("Error", f"Failed to load image: {os.path.basename(file_path)}")
            except Exception as e:
                self.status_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                print(f"Error loading image: {str(e)}")
        else:
            self.status_label.config(text="Image loading cancelled")
    
    def process_current_image(self):
        if self.image_path is None or self.original_image is None:
            return
        
        # Process the image with current parameters
        start_time = time.time()
        
        # Get parameters
        clahe_clip_limit = self.params['clahe_clip_limit']
        clahe_tile_size = self.params['clahe_tile_size']
        min_object_size = self.params['min_object_size']
        eccentricity_threshold = self.params['eccentricity_threshold']
        area_threshold_small = self.params['area_threshold_small']
        area_threshold_large = self.params['area_threshold_large']
        area_min = self.params['area_min']
        area_max = self.params['area_max']
        perimeter_min = self.params['perimeter_min']
        perimeter_max = self.params['perimeter_max']
        circularity_min = self.params['circularity_min']
        circularity_max = self.params['circularity_max']
        aspect_ratio_threshold = self.params['aspect_ratio_threshold']
        
        # Process the image (simplified version of the original process_image function)
        org = self.original_image.copy()
        
        # Convert BGR to RGB (OpenCV uses BGR by default)
        org_rgb = cv2.cvtColor(org, cv2.COLOR_BGR2RGB)
        
        # Convert to grayscale
        gray_image = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_tile_size, clahe_tile_size))
        enhanced_image = clahe.apply(gray_image)
        
        # Convert to double (float) and denoise
        double_image = enhanced_image.astype(np.float32) / 255.0
        denoised_image = cv2.GaussianBlur(double_image, (3, 3), 2)
        
        # Binary image
        binary_image1 = cv2.adaptiveThreshold(org[:,:,2], 255, 
                                           cv2.ADAPTIVE_THRESH_MEAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
        binary_image2 = cv2.adaptiveThreshold(org[:,:,2], 255, 
                                           cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
        binary_image = binary_image1 | binary_image2
        binary_image = ~binary_image
        
        # Edge detection
        edge_canny = cv2.Canny((denoised_image * 255).astype(np.uint8), 30, 150)
        
        # Convert to 8-bit for OpenCV edge detection
        img_8bit = (denoised_image * 255).astype(np.uint8)
        
        # Prewitt
        kernelx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
        kernely = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
        img_prewittx = cv2.filter2D(img_8bit, -1, kernelx)
        img_prewitty = cv2.filter2D(img_8bit, -1, kernely)
        edge_prewitt = np.sqrt(img_prewittx**2 + img_prewitty**2)
        edge_prewitt = edge_prewitt > 30
        
        # Roberts
        roberts_x = np.array([[1, 0], [0, -1]])
        roberts_y = np.array([[0, 1], [-1, 0]])
        img_robertsx = cv2.filter2D(img_8bit, -1, roberts_x)
        img_robertsy = cv2.filter2D(img_8bit, -1, roberts_y)
        edge_roberts = np.sqrt(img_robertsx**2 + img_robertsy**2)
        edge_roberts = edge_roberts > 30
        
        # Sobel
        sobelx = cv2.Sobel(img_8bit, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(img_8bit, cv2.CV_64F, 0, 1, ksize=3)
        edge_sobel = np.sqrt(sobelx**2 + sobely**2)
        edge_sobel = edge_sobel > 30
        
        # Edge combination
        roi_edge = edge_canny.astype(bool) | edge_prewitt | edge_roberts | edge_sobel
        
        # Kirsch operators
        kirsch_kernels = [
            np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float32),
            np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float32),
            np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float32),
            np.array([[-3, -3, -3], [5, 0, -3], [5, 5, -3]], dtype=np.float32),
            np.array([[-3, -3, -3], [-3, 0, -3], [5, 5, 5]], dtype=np.float32),
            np.array([[-3, -3, -3], [-3, 0, 5], [-3, 5, 5]], dtype=np.float32),
            np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float32),
            np.array([[-3, 5, 5], [-3, 0, 5], [-3, -3, -3]], dtype=np.float32)
        ]
        
        kirsch_outputs = []
        for kernel in kirsch_kernels:
            # Apply Kirsch filter (keeping float32)
            filtered = cv2.filter2D(denoised_image.astype(np.float32), -1, kernel)
            
            # Convert to absolute values
            filtered = np.abs(filtered)
            
            # Normalize to 0-1 range
            filtered_min = np.min(filtered)
            filtered_max = np.max(filtered)
            if filtered_max > filtered_min:  # Avoid division by zero
                filtered_norm = (filtered - filtered_min) / (filtered_max - filtered_min)
            else:
                filtered_norm = np.zeros_like(filtered)
            
            # Calculate Otsu threshold
            binary = filtered_norm > filters.threshold_otsu(filtered_norm)
            kirsch_outputs.append(binary)
        
        i9 = np.zeros_like(kirsch_outputs[0], dtype=bool)
        for output in kirsch_outputs:
            i9 = i9 | output
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        i9 = cv2.erode(i9.astype(np.uint8), kernel, iterations=1)
        i9 = cv2.morphologyEx(i9, cv2.MORPH_CLOSE, kernel)
        
        # Combine segmentations
        roi_seg = roi_edge | i9.astype(bool) | binary_image.astype(bool)
        
        # Pre-processing to reduce noise
        roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=min_object_size)
        
        small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        roi_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_OPEN, small_kernel)
        
        # Final processing
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=2)
        
        final_seg = morphology.remove_small_objects(final_seg.astype(bool), min_size=min_object_size)
        
        # Fill holes
        final_seg = morphology.remove_small_holes(final_seg)
        
        # Remove small areas
        final_seg = morphology.remove_small_objects(final_seg, min_size=100)
        
        # Clean up
        final_seg = morphology.thin(final_seg, max_num_iter=1)
        
        # Additional cleaning steps
        final_seg = morphology.remove_small_objects(final_seg, min_size=min_object_size)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        final_seg = cv2.morphologyEx(final_seg.astype(np.uint8), cv2.MORPH_OPEN, kernel)
        
        # Calculate and filter based on eccentricity
        labeled = measure.label(final_seg)
        props = measure.regionprops(labeled)
        mask = np.zeros_like(final_seg, dtype=bool)
        
        for prop in props:
            if (prop.eccentricity < eccentricity_threshold and prop.area > area_threshold_small) or (prop.area > area_threshold_large):
                mask[labeled == prop.label] = True
        
        final_seg = mask
        
        # Apply watershed segmentation to separate touching cells if enabled
        if self.params['use_watershed']:
            # Get watershed parameters
            distance_threshold = self.params['watershed_distance_threshold']
            footprint_size = self.params['watershed_footprint_size']
            compactness = self.params['watershed_compactness']
            watershed_min_area = self.params['watershed_min_area']
            
            # First, get the original labeled image and region properties
            original_labeled = measure.label(final_seg)
            original_props = measure.regionprops(original_labeled)
            
            # Create a mask for large objects that need watershed segmentation
            large_objects_mask = np.zeros_like(final_seg, dtype=bool)
            for prop in original_props:
                if prop.area > watershed_min_area:
                    large_objects_mask[original_labeled == prop.label] = True
            
            # Create a mask for small objects that don't need watershed segmentation
            small_objects_mask = final_seg & ~large_objects_mask
            
            # Only apply watershed to large objects
            if np.any(large_objects_mask):
                # Distance transform on large objects only
                distance = ndi.distance_transform_edt(large_objects_mask)
                
                # Apply threshold to distance map to find markers
                # This helps identify separate cells even when they're touching
                distance_peaks = distance > distance_threshold
                
                # Clean up the peaks to get better markers
                distance_peaks = morphology.remove_small_objects(distance_peaks, min_size=2)
                
                # Label the peaks as markers
                markers = measure.label(distance_peaks)
                
                # Apply watershed segmentation to large objects only
                # Use the negative distance as the input for watershed
                watershed_labels = segmentation.watershed(-distance, markers, mask=large_objects_mask, 
                                                        compactness=compactness)
                
                # Combine the watershed segmentation of large objects with the small objects
                # First, get the maximum label from watershed_labels
                max_watershed_label = np.max(watershed_labels) if np.any(watershed_labels) else 0
                
                # Label the small objects starting from max_watershed_label + 1
                small_objects_labeled = measure.label(small_objects_mask)
                small_objects_labeled[small_objects_labeled > 0] += max_watershed_label
                
                # Combine the two labeled images
                combined_labels = watershed_labels.copy()
                combined_labels[small_objects_mask] = small_objects_labeled[small_objects_mask]
                
                # Final labeled image
                labeled_image = combined_labels
            else:
                # If no large objects, just use the original labeling
                labeled_image = original_labeled
        else:
            # Label connected components without watershed
            labeled_image = measure.label(final_seg)
        
        # Calculate region properties based on the final labeled image (after watershed if enabled)
        # This ensures that the properties are calculated for the separated cells
        watershed_props = measure.regionprops(labeled_image)
        
        # Create the three output images
        
        # 1. Labeled Image
        rgb_label = segmentation.mark_boundaries(org_rgb, labeled_image)
        
        # 2. Parameters Image
        fig_params = plt.figure(figsize=(6, 6), dpi=100)
        ax_params = fig_params.add_subplot(111)
        ax_params.imshow(org_rgb)
        
        # Use the watershed_props instead of props to display parameters for separated cells
        for prop in watershed_props:
            area = prop.area
            perimeter = prop.perimeter
            circularity = (perimeter * perimeter) / (4 * np.pi * area)
            
            # Get centroid for text placement
            centroid = prop.centroid
            
            # Draw text with parameter values
            ax_params.text(centroid[1], centroid[0], 
                    f'A:{area:.0f}\nP:{perimeter:.0f}\nC:{circularity:.2f}',
                    color='yellow', fontsize=8, ha='center', va='center',
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', pad=1))
            
            # Draw bounding box for all objects
            bbox = prop.bbox
            height = bbox[2] - bbox[0]
            width = bbox[3] - bbox[1]
            rect = plt.Rectangle((bbox[1], bbox[0]), width, height,
                               fill=False, edgecolor='yellow')
            ax_params.add_patch(rect)
        
        ax_params.set_axis_off()
        ax_params.set_title('Objects with Area(A), Perimeter(P), and Circularity(C) values')
        fig_params.tight_layout()
        
        # 3. Final Result Image
        fig_final = plt.figure(figsize=(6, 6), dpi=100)
        ax_final = fig_final.add_subplot(111)
        ax_final.imshow(org_rgb)
        
        # Use the watershed_props instead of props for the final result image
        for prop in watershed_props:
            area = prop.area
            perimeter = prop.perimeter
            circularity = (perimeter * perimeter) / (4 * np.pi * area)
            
            if (area_min < area < area_max and 
                perimeter_min < perimeter < perimeter_max and 
                circularity_min < circularity < circularity_max):
                
                bbox = prop.bbox
                height = bbox[2] - bbox[0]
                width = bbox[3] - bbox[1]
                
                if ((height > width and aspect_ratio_threshold * width > height) or 
                    (width > height and aspect_ratio_threshold * height > width) or 
                    (height == width)):
                    rect = plt.Rectangle((bbox[1], bbox[0]), width, height,
                                      fill=False, edgecolor='red')
                    ax_final.add_patch(rect)
        
        ax_final.set_axis_off()
        fig_final.tight_layout()
        
        # Convert figures to images for display
        # For labeled image
        labeled_img = self.fig_to_img(rgb_label)
        
        # For parameters image
        params_img = self.fig_to_img_from_fig(fig_params)
        plt.close(fig_params)
        
        # For final result image
        final_img = self.fig_to_img_from_fig(fig_final)
        plt.close(fig_final)
        
        # Update the UI with the new images
        self.update_image_display(labeled_img, params_img, final_img)
        
        end_time = time.time()
        processing_time = end_time - start_time
        # Update status label with processing time
        self.status_label.config(text=f"Processing time: {processing_time:.2f} seconds")
    
    def fig_to_img(self, img_array):
        """Convert a numpy array to a PhotoImage"""
        # Convert to uint8 if it's a float array
        if img_array.dtype == np.float64 or img_array.dtype == np.float32:
            img_array = (img_array * 255).astype(np.uint8)
        
        # Convert to PIL Image
        img = Image.fromarray(img_array)
        
        # Resize to fit canvas
        img = img.resize((500, 500), Image.LANCZOS)
        
        # Convert to PhotoImage
        return ImageTk.PhotoImage(img)
    
    def fig_to_img_from_fig(self, fig):
        """Convert a matplotlib figure to a PhotoImage"""
        # Draw the figure on a canvas
        fig.canvas.draw()
        
        # Convert canvas to image
        img = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
        
        # Resize to fit canvas
        img = img.resize((500, 500), Image.LANCZOS)
        
        # Convert to PhotoImage
        return ImageTk.PhotoImage(img)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling in the control panel"""
        # Scroll 2 units for every mouse wheel click
        self.control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def update_image_display(self, labeled_img, params_img, final_img):
        """Update the image canvases with new images"""
        # Store references to prevent garbage collection
        self.labeled_img_ref = labeled_img
        self.params_img_ref = params_img
        self.final_img_ref = final_img
        
        # Update canvases
        self.labeled_canvas.create_image(0, 0, anchor=tk.NW, image=self.labeled_img_ref)
        self.params_canvas.create_image(0, 0, anchor=tk.NW, image=self.params_img_ref)
        self.final_canvas.create_image(0, 0, anchor=tk.NW, image=self.final_img_ref)

if __name__ == "__main__":
    root = tk.Tk()
    app = ParameterVisualizationUI(root)
    root.mainloop()
