"""
Secondary Display for CellToolbox
This script creates a fullscreen black window on the secondary monitor
and displays the AOI as a yellow outline box in the same position as the main application.
"""

import tkinter as tk
import sys
import os
import time
import numpy as np
from PIL import Image, ImageTk

# Import for multi-monitor support
try:
    import win32api
    HAS_WIN32API = True
except ImportError:
    HAS_WIN32API = False
    print("win32api not available. Multi-monitor support will be limited.")
    # You may need to install pywin32: pip install pywin32

def get_monitor_info():
    """Get information about available monitors
    
    Returns:
        list: List of monitor information dictionaries
    """
    monitors = []
    
    if HAS_WIN32API:
        try:
            # Get information for all monitors
            monitor_info = win32api.EnumDisplayMonitors()
            
            # Get detailed information for each monitor
            for i, monitor in enumerate(monitor_info):
                monitor_rect = win32api.GetMonitorInfo(monitor[0])
                work_area = monitor_rect['Work']
                monitor_area = monitor_rect['Monitor']
                is_primary = (monitor_rect['Flags'] == 1)  # Primary monitor has flag value 1
                
                monitors.append({
                    'index': i,
                    'left': monitor_area[0],
                    'top': monitor_area[1],
                    'right': monitor_area[2],
                    'bottom': monitor_area[3],
                    'width': monitor_area[2] - monitor_area[0],
                    'height': monitor_area[3] - monitor_area[1],
                    'work_left': work_area[0],
                    'work_top': work_area[1],
                    'work_right': work_area[2],
                    'work_bottom': work_area[3],
                    'work_width': work_area[2] - work_area[0],
                    'work_height': work_area[3] - work_area[1],
                    'is_primary': is_primary
                })
                
                print(f"Monitor {i}: {'Primary' if is_primary else 'Secondary'}")
                print(f"  Position: ({monitor_area[0]}, {monitor_area[1]}) -> ({monitor_area[2]}, {monitor_area[3]})")
                print(f"  Size: {monitor_area[2] - monitor_area[0]} x {monitor_area[3] - monitor_area[1]}")
                
        except Exception as e:
            print(f"Error getting monitor information: {e}")
    
    # If no monitors detected or win32api not available, create a fallback entry
    if not monitors:
        # Get screen dimensions from tkinter as fallback
        temp_root = tk.Tk()
        screen_width = temp_root.winfo_screenwidth()
        screen_height = temp_root.winfo_screenheight()
        temp_root.destroy()
        
        monitors.append({
            'index': 0,
            'left': 0,
            'top': 0,
            'right': screen_width,
            'bottom': screen_height,
            'width': screen_width,
            'height': screen_height,
            'work_left': 0,
            'work_top': 0,
            'work_right': screen_width,
            'work_bottom': screen_height,
            'work_width': screen_width,
            'work_height': screen_height,
            'is_primary': True
        })
    
    return monitors

class SecondaryDisplay:
    def __init__(self, monitor_info=None):
        """Create a fullscreen black window with AOI display
        
        Args:
            monitor_info: Dictionary with monitor information
        """
        # If no monitor info provided, try to find secondary monitor
        if monitor_info is None:
            monitors = get_monitor_info()
            if len(monitors) > 1:
                # Use the first non-primary monitor
                monitor_info = next((m for m in monitors if not m['is_primary']), monitors[0])
            else:
                # Use the primary monitor if no secondary is available
                monitor_info = monitors[0]
        
        self.monitor = monitor_info
        
        # Create a new Toplevel window
        self.window = tk.Tk()
        self.window.title("Secondary Display")
        
        # Configure window to appear on the specified monitor
        self.window.geometry(f"{self.monitor['width']}x{self.monitor['height']}+{self.monitor['left']}+{self.monitor['top']}")
        
        # Create a canvas with black background
        self.canvas = tk.Canvas(
            self.window, 
            width=self.monitor['width'], 
            height=self.monitor['height'],
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add key binding to exit fullscreen with Escape key
        self.window.bind('<Escape>', lambda e: self.toggle_fullscreen())
        
        # Set to fullscreen after positioning
        self.fullscreen = False
        self.toggle_fullscreen()
        
        # Initialize AOI coordinates
        self.aoi_coords = None
        
        # Store canvas dimensions for scaling
        self.canvas_width = self.monitor['width']
        self.canvas_height = self.monitor['height']
        
        # For storing the AOI rectangle ID
        self.aoi_rect_id = None
        
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        
        # If exiting fullscreen, first restore normal window state
        if not self.fullscreen:
            self.window.attributes('-fullscreen', False)
            # Ensure window is positioned on the correct monitor
            self.window.geometry(f"{self.monitor['width']}x{self.monitor['height']}+{self.monitor['left']}+{self.monitor['top']}")
            self.window.update()
        
        # If entering fullscreen, ensure window is on correct monitor first, then go fullscreen
        if self.fullscreen:
            # First ensure window is positioned on the correct monitor
            self.window.geometry(f"{self.monitor['width']}x{self.monitor['height']}+{self.monitor['left']}+{self.monitor['top']}")
            self.window.update()
            # Then go fullscreen
            self.window.attributes('-fullscreen', True)
    
    def update_aoi(self, aoi_coords, frame_width, frame_height):
        """Update the AOI coordinates and redraw
        
        Args:
            aoi_coords: [x1, y1, x2, y2] coordinates of AOI in the original frame
            frame_width: Width of the original video frame
            frame_height: Height of the original video frame
        """
        self.aoi_coords = aoi_coords
        
        # Clear previous AOI rectangle if it exists
        if self.aoi_rect_id is not None:
            self.canvas.delete(self.aoi_rect_id)
        
        if self.aoi_coords is not None:
            # Calculate aspect ratio of the video
            video_aspect_ratio = frame_width / frame_height
            canvas_aspect_ratio = self.canvas_width / self.canvas_height
            
            # Calculate display dimensions and offsets
            if canvas_aspect_ratio > video_aspect_ratio:
                display_height = self.canvas_height
                display_width = int(display_height * video_aspect_ratio)
                display_offset_x = (self.canvas_width - display_width) // 2
                display_offset_y = 0
            else:
                display_width = self.canvas_width
                display_height = int(display_width / video_aspect_ratio)
                display_offset_x = 0
                display_offset_y = (self.canvas_height - display_height) // 2
            
            # Scale AOI coordinates to match the display size
            scale_x = display_width / frame_width
            scale_y = display_height / frame_height
            
            x1, y1, x2, y2 = self.aoi_coords
            scaled_x1 = int(x1 * scale_x) + display_offset_x
            scaled_y1 = int(y1 * scale_y) + display_offset_y
            scaled_x2 = int(x2 * scale_x) + display_offset_x
            scaled_y2 = int(y2 * scale_y) + display_offset_y
            
            # Draw the AOI rectangle with yellow outline
            self.aoi_rect_id = self.canvas.create_rectangle(
                scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                outline="yellow", width=3
            )
    
    def run(self):
        """Start the main loop"""
        self.window.mainloop()

def main():
    """Run the secondary display as a standalone application"""
    # Get monitor information
    monitors = get_monitor_info()
    
    if len(monitors) < 2:
        print("Warning: Only one monitor detected. Using primary monitor.")
        secondary_monitor = monitors[0]
    else:
        # Use the first non-primary monitor
        secondary_monitor = next((m for m in monitors if not m['is_primary']), monitors[0])
    
    # Create the secondary display
    display = SecondaryDisplay(secondary_monitor)
    
    # Example: Set an AOI (this would normally come from the main application)
    # These are example coordinates - in a real application, they would be passed from the main app
    example_aoi = [100, 100, 500, 400]  # [x1, y1, x2, y2]
    example_frame_width = 1280
    example_frame_height = 720
    
    display.update_aoi(example_aoi, example_frame_width, example_frame_height)
    
    # Start the main loop
    display.run()

if __name__ == "__main__":
    main()
