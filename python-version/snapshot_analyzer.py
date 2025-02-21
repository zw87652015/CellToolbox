import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from skimage import measure
import pandas as pd
from PIL import Image, ImageTk

class SnapshotAnalyzer:
    def __init__(self, master, ui_instance):
        self.master = master  # The root window
        self.ui = ui_instance  # The UnifiedUI instance
        self.results_data = []
        self.create_results_window()
        
    def create_results_window(self):
        """Create the window to display analysis results"""
        self.window = tk.Toplevel(self.master)
        self.window.title("Snapshot Analysis Results")
        self.window.geometry("800x600")
        self.window.attributes('-topmost', True)  # Make analysis window stay on top
        
        # Add Calculate Thresholds button at the top
        self.calc_button = ttk.Button(
            self.window, 
            text="Calculate Optimal Thresholds",
            command=self.calculate_optimal_thresholds
        )
        self.calc_button.pack(pady=10)
        
        # Create treeview for results
        columns = ('timestamp', 'area', 'perimeter', 'circularity', 'label')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings')
        
        # Set column headings
        self.tree.heading('timestamp', text='Time')
        self.tree.heading('area', text='Area')
        self.tree.heading('perimeter', text='Perimeter')
        self.tree.heading('circularity', text='Circularity')
        self.tree.heading('label', text='Label')
        
        # Set column widths
        for col in columns:
            self.tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def analyze_snapshot(self, frame, regions):
        """Create a dialog for labeling detected regions"""
        dialog = tk.Toplevel(self.master)
        dialog.title("Label Detected Regions")
        dialog.attributes('-topmost', True)  # Make analysis window stay on top
        dialog.geometry("1200x800")
        
        # Create main container
        main_container = ttk.Frame(dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame for image
        image_frame = ttk.Frame(main_container)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right frame for controls
        control_frame = ttk.Frame(main_container)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Create a canvas and scrollbar for scrolling
        control_canvas = tk.Canvas(control_frame, width=300)  # Fixed width for controls
        scrollbar = ttk.Scrollbar(control_frame, orient=tk.VERTICAL, command=control_canvas.yview)
        
        # Create a frame inside the canvas for the controls
        control_container = ttk.Frame(control_canvas)
        control_container.bind("<Configure>", 
            lambda e: control_canvas.configure(scrollregion=control_canvas.bbox("all")))
        
        # Add the frame to the canvas
        control_canvas.create_window((0, 0), window=control_container, anchor=tk.NW)
        control_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add mousewheel scrolling
        def _on_mousewheel(event):
            control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        control_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Add a title for the controls
        ttk.Label(control_container, text="Region Labels", 
                 font=('Arial', 12, 'bold')).pack(pady=(0,10))
        
        # Process regions
        processed_regions = []
        
        for i, prop in enumerate(regions):
            processed_regions.append((prop.bbox, prop, i))
        
        # Sort regions by area (largest first)
        processed_regions.sort(key=lambda x: (x[1].area), reverse=True)
        
        # Display frame with boxes
        display_frame = frame.copy()
        for i, (box, _, _) in enumerate(processed_regions):
            y1, x1, y2, x2 = box
            # Draw box with index
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Put index number above the box
            label_x = x1
            label_y = max(y1 - 10, 20)  # Ensure text doesn't go above image
            cv2.putText(display_frame, str(i+1), (label_x, label_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Convert frame to PhotoImage
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        # Calculate scaling factor to fit the window while maintaining aspect ratio
        height, width = display_frame_rgb.shape[:2]
        max_size = 800
        scale = min(max_size/width, max_size/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        display_frame_rgb = cv2.resize(display_frame_rgb, (new_width, new_height))
        
        img = Image.fromarray(display_frame_rgb)
        photo = ImageTk.PhotoImage(image=img)
        
        # Create canvas for image
        canvas = tk.Canvas(image_frame, width=new_width, height=new_height)
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        canvas.image = photo  # Keep a reference
        
        # Create controls for regions
        var_list = []
        
        for i, (_, prop, orig_idx) in enumerate(processed_regions):
            var = tk.StringVar(value="ignore")
            var_list.append((var, orig_idx))
            
            # Create frame for each region
            region_frame = ttk.LabelFrame(control_container, text=f"Region {i+1}")
            region_frame.pack(fill=tk.X, pady=5, padx=5)
            
            # Add region properties
            circularity = 4 * np.pi * prop.area / (prop.perimeter ** 2)
            info = f"Area: {prop.area:.1f}\nPerim: {prop.perimeter:.1f}\nCirc: {circularity:.2f}"
            ttk.Label(region_frame, text=info).pack(pady=2)
            
            # Radio buttons in a horizontal frame
            radio_frame = ttk.Frame(region_frame)
            radio_frame.pack(fill=tk.X, pady=2)
            ttk.Radiobutton(radio_frame, text="Cell", variable=var, 
                          value="cell").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(radio_frame, text="Not Cell", variable=var, 
                          value="not_cell").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(radio_frame, text="Ignore", variable=var, 
                          value="ignore").pack(side=tk.LEFT, padx=5)
        
        def save_labels():
            import time
            timestamp = time.strftime("%H:%M:%S")
            
            # Store the labeled data
            for var, orig_idx in var_list:
                if var.get() != "ignore":
                    prop = regions[orig_idx]
                    circularity = 4 * np.pi * prop.area / (prop.perimeter ** 2)
                    self.results_data.append({
                        'timestamp': timestamp,
                        'area': prop.area,
                        'perimeter': prop.perimeter,
                        'circularity': circularity,
                        'label': var.get()
                    })
                    
                    # Add to treeview
                    self.tree.insert('', 'end', values=(
                        timestamp,
                        f"{prop.area:.1f}",
                        f"{prop.perimeter:.1f}",
                        f"{circularity:.2f}",
                        var.get()
                    ))
            
            # Unbind mousewheel before destroying
            control_canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
        
        # Save button at the bottom
        ttk.Button(control_container, text="Save Labels", 
                  command=save_labels).pack(pady=10)
        
    def find_optimal_threshold(self, cell_values, not_cell_values, current_min, current_max, margin=0.1):
        """Find optimal threshold between cell and not-cell distributions, considering current parameters"""
        if len(cell_values) == 0 or len(not_cell_values) == 0:
            return current_min, current_max
            
        # Calculate statistics
        cell_mean = np.mean(cell_values)
        cell_std = np.std(cell_values)
        not_cell_mean = np.mean(not_cell_values)
        not_cell_std = np.std(not_cell_values)
        
        # Calculate new thresholds based on selections
        new_min = cell_mean - cell_std
        new_max = cell_mean + cell_std
        
        # Adjust thresholds based on non-cell distribution
        if cell_mean < not_cell_mean:
            # Cells are smaller/lower than non-cells
            potential_max = not_cell_mean - not_cell_std
            if potential_max < new_max:
                new_max = potential_max
        else:
            # Cells are larger/higher than non-cells
            potential_min = not_cell_mean + not_cell_std
            if potential_min > new_min:
                new_min = potential_min
        
        # Consider current parameters in the refinement
        # Use weighted average between current and new parameters
        # Weight new parameters less to make them act more as a refinement
        weight_current = 0.7  # Give more weight to current parameters
        weight_new = 0.3     # Give less weight to new parameters
        
        refined_min = (current_min * weight_current + new_min * weight_new)
        refined_max = (current_max * weight_current + new_max * weight_new)
        
        # Ensure we don't exclude clear cell examples
        cell_q1 = np.percentile(cell_values, 25)
        cell_q3 = np.percentile(cell_values, 75)
        cell_iqr = cell_q3 - cell_q1
        
        # Expand bounds if they're too tight, but consider current bounds
        if refined_min > cell_q1 - 0.5 * cell_iqr:
            refined_min = min(current_min, cell_q1 - 0.5 * cell_iqr)
        if refined_max < cell_q3 + 0.5 * cell_iqr:
            refined_max = max(current_max, cell_q3 + 0.5 * cell_iqr)
        
        # Ensure bounds are within reasonable range
        refined_min = max(refined_min, min(current_min, np.min(cell_values) * 0.9))
        refined_max = min(refined_max, max(current_max, np.max(cell_values) * 1.1))
        
        return refined_min, refined_max
        
    def calculate_optimal_thresholds(self):
        """Calculate optimal thresholds based on labeled data using statistical analysis"""
        if not self.results_data:
            messagebox.showwarning("No Data", "No labeled data available for analysis")
            return
            
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(self.results_data)
        cells = df[df['label'] == 'cell']
        not_cells = df[df['label'] == 'not_cell']
        
        if cells.empty or not_cells.empty:
            messagebox.showwarning("Insufficient Data", 
                "Need both cell and non-cell examples for analysis")
            return
            
        # Get current parameter values
        try:
            current_area_min = float(self.ui.area_min.get())
            current_area_max = float(self.ui.area_max.get())
            current_perimeter_min = float(self.ui.perimeter_min.get())
            current_perimeter_max = float(self.ui.perimeter_max.get())
            current_circularity_min = float(self.ui.circularity_min.get())
            current_circularity_max = float(self.ui.circularity_max.get())
        except ValueError:
            messagebox.showwarning("Invalid Parameters", 
                "Current parameters are invalid. Please ensure all parameters are numbers.")
            return
            
        # Calculate refined thresholds for each parameter
        area_min, area_max = self.find_optimal_threshold(
            cells['area'].values, 
            not_cells['area'].values,
            current_area_min,
            current_area_max
        )
        
        perimeter_min, perimeter_max = self.find_optimal_threshold(
            cells['perimeter'].values,
            not_cells['perimeter'].values,
            current_perimeter_min,
            current_perimeter_max
        )
        
        circularity_min, circularity_max = self.find_optimal_threshold(
            cells['circularity'].values,
            not_cells['circularity'].values,
            current_circularity_min,
            current_circularity_max
        )
        
        # Add validation
        if any(v is None for v in [area_min, area_max, perimeter_min, 
                                 perimeter_max, circularity_min, circularity_max]):
            messagebox.showwarning("Calculation Error", 
                "Could not determine optimal thresholds. Please provide more examples.")
            return
            
        # Update main UI parameters
        self.ui.area_min.set(f"{area_min:.1f}")
        self.ui.area_max.set(f"{area_max:.1f}")
        self.ui.perimeter_min.set(f"{perimeter_min:.1f}")
        self.ui.perimeter_max.set(f"{perimeter_max:.1f}")
        self.ui.circularity_min.set(f"{circularity_min:.2f}")
        self.ui.circularity_max.set(f"{circularity_max:.2f}")
        
        # Show results with more detailed information and separation quality
        def get_separation_quality(cell_vals, not_cell_vals):
            c_mean = np.mean(cell_vals)
            c_std = np.std(cell_vals)
            nc_mean = np.mean(not_cell_vals)
            nc_std = np.std(not_cell_vals)
            separation = abs(c_mean - nc_mean) / (c_std + nc_std)
            return "Good" if separation > 1 else "Moderate" if separation > 0.5 else "Poor"
        
        messagebox.showinfo("Thresholds Updated", 
            f"New thresholds calculated and applied:\n\n"
            f"Area: {area_min:.1f} - {area_max:.1f}\n"
            f"  Cell mean: {cells['area'].mean():.1f} ± {cells['area'].std():.1f}\n"
            f"  Non-cell mean: {not_cells['area'].mean():.1f} ± {not_cells['area'].std():.1f}\n"
            f"  Separation: {get_separation_quality(cells['area'], not_cells['area'])}\n\n"
            f"Perimeter: {perimeter_min:.1f} - {perimeter_max:.1f}\n"
            f"  Cell mean: {cells['perimeter'].mean():.1f} ± {cells['perimeter'].std():.1f}\n"
            f"  Non-cell mean: {not_cells['perimeter'].mean():.1f} ± {not_cells['perimeter'].std():.1f}\n"
            f"  Separation: {get_separation_quality(cells['perimeter'], not_cells['perimeter'])}\n\n"
            f"Circularity: {circularity_min:.2f} - {circularity_max:.2f}\n"
            f"  Cell mean: {cells['circularity'].mean():.2f} ± {cells['circularity'].std():.2f}\n"
            f"  Non-cell mean: {not_cells['circularity'].mean():.2f} ± {not_cells['circularity'].std():.2f}\n"
            f"  Separation: {get_separation_quality(cells['circularity'], not_cells['circularity'])}")
