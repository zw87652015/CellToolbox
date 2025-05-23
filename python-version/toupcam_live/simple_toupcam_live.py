"""
Simple ToupCam Live Stream
This script provides a basic live stream from a ToupCam camera using the same default exposure parameters
as the full toupcam_live_control.py implementation.
"""

import sys
import os
import ctypes
import time
import threading
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import messagebox

# Add the toupcam SDK path to the Python path
sdk_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'toupcamsdk.20241216', 'python')
sys.path.append(sdk_path)

# Add the DLL directory to the PATH environment variable
dll_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'toupcamsdk.20241216', 'win', 'x64')
os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']

# Explicitly load the DLL using ctypes
toupcam_dll_path = os.path.join(dll_path, 'toupcam.dll')
if os.path.exists(toupcam_dll_path):
    try:
        toupcam_dll = ctypes.WinDLL(toupcam_dll_path)
        print(f"Successfully loaded ToupCam DLL from: {toupcam_dll_path}")
    except Exception as e:
        print(f"Error loading ToupCam DLL: {e}")
else:
    print(f"ToupCam DLL not found at: {toupcam_dll_path}")

try:
    import toupcam
    print(f"Successfully imported toupcam module from: {sdk_path}")
except ImportError as e:
    print(f"Error importing toupcam module: {e}")
    print(f"Check if the path is correct: {sdk_path}")
    sys.exit(1)

class SimpleToupCamLive:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple ToupCam Live Stream")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Camera variables
        self.hcam = None
        self.cam_buffer = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.running = False
        
        # Default exposure parameters (same as in toupcam_live_control.py)
        self.exposure_time = 8333  # 8.333ms in microseconds
        
        # UI update variables
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.new_frame_available = False
        self.frame_lock = threading.Lock()
        self.render_running = False
        
        # AOI (Area of Interest) variables
        self.aoi_active = False  # Flag to enable/disable AOI drawing
        self.aoi_rect = None     # Canvas rectangle object
        self.aoi_overlay = None  # Canvas overlay object
        self.aoi_coords = [0, 0, 0, 0]  # [start_x, start_y, end_x, end_y]
        self.aoi_drawing = False  # Flag to indicate active drawing
        self.aoi_adjusting = False  # Flag to indicate border adjustment
        self.aoi_adjust_handle = None  # Which handle is being adjusted
        self.aoi_handle_size = 8  # Size of adjustment handles
        self.aoi_handles = []  # List of handle objects on canvas
        self.aoi_handle_coords = {}  # Coordinates of handles
        
        # Create UI
        self.create_ui()
        
        # Start camera
        self.start_camera()
        
        # Start rendering thread
        self.start_render_thread()
        
        # Make sure the window is visible
        self.root.update()
    
    def create_ui(self):
        """Create a user interface with canvas for video display and control panel"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for video display
        video_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Video canvas - use a light gray background to better see the video boundaries
        self.canvas = tk.Canvas(
            video_frame, 
            bg="#f0f0f0",  # Light gray background
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for AOI drawing
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # FPS counter
        self.fps_label = ttk.Label(video_frame, text="FPS: 0")
        self.fps_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # Right panel for controls
        control_frame = ttk.Frame(main_frame, width=200, borderwidth=2, relief="groove")
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)  # Prevent shrinking
        
        # Title for control panel
        ttk.Label(control_frame, text="Controls", font=("Arial", 12, "bold")).pack(pady=10)
        
        # AOI controls
        aoi_frame = ttk.LabelFrame(control_frame, text="Area of Interest")
        aoi_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Draw AOI button
        self.draw_aoi_var = tk.BooleanVar(value=False)
        self.draw_aoi_button = ttk.Checkbutton(
            aoi_frame,
            text="Draw AOI",
            variable=self.draw_aoi_var,
            command=self.toggle_aoi_drawing
        )
        self.draw_aoi_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Clear AOI button
        self.clear_aoi_button = ttk.Button(
            aoi_frame,
            text="Clear AOI",
            command=self.clear_aoi
        )
        self.clear_aoi_button.pack(fill=tk.X, padx=5, pady=5)
        
        # AOI Opacity slider
        ttk.Label(aoi_frame, text="Overlay Opacity:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.opacity_var = tk.DoubleVar(value=0.5)
        opacity_scale = ttk.Scale(
            aoi_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.opacity_var,
            command=self.update_aoi_overlay
        )
        opacity_scale.pack(fill=tk.X, padx=5, pady=(0,5))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def start_camera(self):
        """Initialize and start the camera with default exposure parameters"""
        devices = toupcam.Toupcam.EnumV2()
        if not devices:
            self.status_var.set("No camera found")
            messagebox.showerror(
                "Camera Error", 
                "No ToupCam cameras found. Please connect a camera and restart the application."
            )
            return
        
        device = devices[0]  # Use the first camera
        
        try:
            # Open the camera
            self.hcam = toupcam.Toupcam.Open(None)
            if not self.hcam:
                self.status_var.set("Failed to open camera")
                return
            
            # Get camera properties
            self.frame_width, self.frame_height = self.hcam.get_Size()
            print(f"Camera resolution: {self.frame_width}x{self.frame_height}")
            
            # Set camera properties for optimal performance
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BYTEORDER, 0)  # RGB
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_UPSIDE_DOWN, 0)  # Normal orientation
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimize frame queue
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_CALLBACK_THREAD, 1)  # Enable dedicated callback thread
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_THREAD_PRIORITY, 2)  # Set high thread priority
            
            # Disable auto exposure
            self.hcam.put_AutoExpoEnable(False)
            
            # Set anti-flicker to 60Hz (for 16.67ms exposure)
            self.hcam.put_HZ(2)  # 2 = 60Hz
            
            # Set exposure time (in microseconds)
            self.hcam.put_ExpoTime(self.exposure_time)  # 8.333ms
            
            # Set other camera options
            self.hcam.put_Brightness(0)
            self.hcam.put_Contrast(0)
            self.hcam.put_Gamma(100)  # 1.0
            
            # Allocate buffer for image data
            buffer_size = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(buffer_size)
            
            # Pre-allocate numpy array for frame buffer to avoid memory allocations
            self.frame_buffer_shape = (self.frame_height, toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3, 3)
            
            # Register callback
            self.hcam.StartPullModeWithCallback(self.on_frame, self)
            
            # Set running flag to True to enable image processing
            self.running = True
            
            self.status_var.set(f"Camera started: {device.displayname}")
            
        except Exception as e:
            self.status_var.set(f"Error starting camera: {str(e)}")
            messagebox.showerror("Camera Error", f"Error starting camera: {str(e)}")
    
    def on_frame(self, nEvent, ctx):
        """Camera event callback function"""
        try:
            if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
                ctx.process_image()
            elif nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
                ctx.status_var.set("Camera disconnected")
        except Exception as e:
            print(f"[ERROR] Exception in on_frame: {e}")
    
    def process_image(self):
        """Process the image from the camera"""
        if not self.running or not self.hcam:
            return
            
        # Track frame timing for FPS calculation
        current_time = time.time()
            
        try:
            # Pull the image from the camera
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Convert the raw buffer to a numpy array
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8).reshape(self.frame_buffer_shape)
            frame = frame[:, :self.frame_width, :]
            
            # Store the frame
            with self.frame_lock:
                self.frame_buffer = frame
                self.new_frame_available = True
            
            # Count frames for FPS calculation
            self.frame_count += 1
            if current_time - self.last_fps_time >= 1.0:
                self.fps = self.frame_count / (current_time - self.last_fps_time)
                self.fps_label.configure(text=f"FPS: {self.fps:.1f}")
                self.status_var.set(f"Camera running: {self.fps:.1f} FPS")
                self.frame_count = 0
                self.last_fps_time = current_time
                
        except toupcam.HRESULTException as ex:
            print(f"[ERROR] Error pulling image: 0x{ex.hr & 0xffffffff:x}")
        except Exception as e:
            print(f"[ERROR] process_image exception: {e}")
    
    def update_frame(self):
        """Update the UI with the latest frame"""
        if not self.running or self.frame_buffer is None:
            return
            
        # Get the current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Calculate aspect ratio
            aspect_ratio = self.frame_width / self.frame_height
            
            if canvas_width / canvas_height > aspect_ratio:
                # Canvas is wider than the frame
                display_height = canvas_height
                display_width = int(display_height * aspect_ratio)
            else:
                # Canvas is taller than the frame
                display_width = canvas_width
                display_height = int(display_width / aspect_ratio)
            
            # Use the full canvas size for display, stretching if needed
            display_width = canvas_width
            display_height = canvas_height
            
            # Store display dimensions for coordinate mapping
            self.display_width = display_width
            self.display_height = display_height
            self.display_offset_x = 0  # No offset
            self.display_offset_y = 0  # No offset
            
            # Convert BGR to RGB for display
            rgb_frame = cv2.cvtColor(self.frame_buffer, cv2.COLOR_BGR2RGB)
            
            # Resize the frame to fill the entire canvas
            display_frame = cv2.resize(rgb_frame, (display_width, display_height), 
                                      interpolation=cv2.INTER_LINEAR)
            
            # Apply AOI overlay if active
            if hasattr(self, 'aoi_coords') and all(coord != 0 for coord in self.aoi_coords):
                # Create a copy of the frame for overlay
                overlay = display_frame.copy()
                
                # Create a mask for the AOI (white inside AOI, black outside)
                mask = np.zeros((display_height, display_width), dtype=np.uint8)
                x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)  # Fill rectangle with white
                
                # Darken areas outside AOI
                alpha = self.opacity_var.get()  # Get opacity from slider
                overlay_dark = cv2.addWeighted(overlay, 1-alpha, np.zeros_like(overlay), alpha, 0)
                
                # Apply mask: keep original inside AOI, darkened outside
                mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
                display_frame = np.where(mask_3ch > 0, display_frame, overlay_dark)
            
            # Convert to PhotoImage
            img = Image.fromarray(display_frame)
            self.photo_image = ImageTk.PhotoImage(image=img)
            
            # If this is the first frame, create the image on the canvas
            if not self.canvas.find_withtag("video"):
                self.canvas.create_image(
                    0, 0,  # Position at top-left corner
                    anchor=tk.NW,  # Northwest anchor (top-left)
                    image=self.photo_image,
                    tags=("video",)
                )
            else:
                # Update the existing image
                self.canvas.itemconfig("video", image=self.photo_image)
                
            # Update AOI rectangle if it exists
            if self.aoi_rect:
                x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
                self.canvas.coords(self.aoi_rect, x1, y1, x2, y2)
                
                # Update handle positions
                self.update_handle_positions()
    
    def start_render_thread(self):
        """Start a dedicated thread for rendering frames"""
        self.render_running = True
        self.render_thread = threading.Thread(target=self.render_loop)
        self.render_thread.daemon = True
        self.render_thread.start()
        print("Render thread started")
    
    def render_loop(self):
        """Continuously render frames at a high rate"""
        try:
            while self.render_running:
                if self.running and self.frame_buffer is not None:
                    # Use tkinter's thread-safe after method to update UI
                    self.root.after_idle(self.update_frame)
                    
                # Sleep briefly to avoid excessive CPU usage
                time.sleep(0.01)  # 10ms = potential for 100fps
        except Exception as e:
            print(f"Error in render loop: {str(e)}")
        
        print("Render thread exiting")
    
    def on_closing(self):
        """Clean up resources when closing the application"""
        print("Closing application and cleaning up resources...")
        
        # Stop render thread
        self.render_running = False
        if hasattr(self, 'render_thread') and self.render_thread.is_alive():
            self.render_thread.join(timeout=1.0)
        
        # Stop camera
        self.cleanup_camera()
        
        # Force quit the application after a short delay
        self.root.after(100, self._force_quit)
    
    def _force_quit(self):
        """Force quit the application"""
        try:
            self.root.quit()
            print("Application quit successfully")
        except Exception as e:
            print(f"Error during quit: {e}")
            # As a last resort
            try:
                self.root.destroy()
                print("Application destroyed")
            except Exception as e:
                print(f"Error during destroy: {e}")
    
    def cleanup_camera(self):
        """Clean up camera resources with timeout protection"""
        if self.hcam:
            print("Starting camera cleanup...")
            camera_ref = self.hcam
            self.hcam = None  # Immediately set to None to prevent further access
            self.running = False  # Stop any ongoing camera operations
            
            try:
                # Create a thread to handle camera cleanup with timeout
                def cleanup_camera_thread():
                    try:
                        print("Attempting to stop camera...")
                        try:
                            camera_ref.Stop()
                            print("Camera stopped successfully")
                        except Exception as e:
                            print(f"Error stopping camera: {e}")
                        
                        print("Attempting to close camera...")
                        try:
                            camera_ref.Close()
                            print("Camera closed successfully")
                        except Exception as e:
                            print(f"Error closing camera: {e}")
                        
                    except Exception as e:
                        print(f"Error in camera cleanup thread: {e}")
                
                # Start and wait for cleanup thread with timeout
                cleanup_thread = threading.Thread(target=cleanup_camera_thread, daemon=True)
                cleanup_thread.start()
                
                # Only wait a short time - don't let it block the application exit
                print("Waiting for camera cleanup...")
                cleanup_thread.join(timeout=1.0)  # Wait up to 1 second for cleanup
                
                if cleanup_thread.is_alive():
                    print("WARNING: Camera cleanup timed out, abandoning camera resources")
                else:
                    print("Camera cleanup completed")
                    
            except Exception as e:
                print(f"Error during camera cleanup: {e}")
    
    def toggle_aoi_drawing(self):
        """Toggle AOI drawing mode"""
        self.aoi_active = self.draw_aoi_var.get()
        if self.aoi_active:
            self.status_var.set("Click and drag to draw Area of Interest")
        else:
            self.status_var.set("AOI drawing disabled")
    
    def clear_aoi(self):
        """Clear the AOI rectangle"""
        if self.aoi_rect:
            self.canvas.delete(self.aoi_rect)
            self.aoi_rect = None
        
        # Clear handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
        
        # Reset AOI coordinates
        self.aoi_coords = [0, 0, 0, 0]
        self.status_var.set("AOI cleared")
    
    def get_adjusted_aoi_coords(self):
        """Return AOI coordinates adjusted to ensure x1<x2 and y1<y2"""
        x1, y1, x2, y2 = self.aoi_coords
        # Ensure x1 < x2 and y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        return [x1, y1, x2, y2]
    
    def update_aoi_overlay(self, *args):
        """Update the AOI overlay based on opacity slider"""
        # Force a frame update to refresh the overlay
        if hasattr(self, 'aoi_coords') and all(coord != 0 for coord in self.aoi_coords):
            self.update_frame()
    
    def on_canvas_click(self, event):
        """Handle mouse click on canvas"""
        x, y = event.x, event.y
        
        # Check if we're in AOI drawing mode
        if not self.aoi_active:
            return
        
        # Check if we're clicking on a handle
        for handle_id, handle_pos in self.aoi_handle_coords.items():
            hx, hy = handle_pos
            if abs(x - hx) <= self.aoi_handle_size and abs(y - hy) <= self.aoi_handle_size:
                self.aoi_adjusting = True
                self.aoi_adjust_handle = handle_id
                return
        
        # Start drawing new AOI
        self.aoi_drawing = True
        self.aoi_coords = [x, y, x, y]  # Initialize with click position
        
        # Create or update rectangle
        if self.aoi_rect:
            self.canvas.coords(self.aoi_rect, x, y, x, y)
        else:
            self.aoi_rect = self.canvas.create_rectangle(
                x, y, x, y,
                outline="yellow",
                width=2,
                tags=("aoi",)
            )
        
        # Clear existing handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
    
    def on_canvas_release(self, event):
        """Handle mouse release on canvas"""
        if self.aoi_drawing or self.aoi_adjusting:
            # Finalize the AOI
            x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
            
            # Ensure minimum size
            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                self.status_var.set("AOI too small, try again")
                self.clear_aoi()
            else:
                self.status_var.set(f"AOI set: ({x1},{y1}) to ({x2},{y2})")
                # Create handles for the AOI
                self.create_aoi_handles()
            
            self.aoi_drawing = False
            self.aoi_adjusting = False
            self.aoi_adjust_handle = None
        
    def on_canvas_drag(self, event):
        """Handle mouse drag on canvas"""
        x, y = event.x, event.y
        
        # Constrain to canvas bounds
        x = max(0, min(x, self.canvas.winfo_width()))
        y = max(0, min(y, self.canvas.winfo_height()))
        
        if self.aoi_drawing:
            # Update end coordinates while drawing
            self.aoi_coords[2] = x
            self.aoi_coords[3] = y
            
            # Update rectangle
            x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
            self.canvas.coords(self.aoi_rect, x1, y1, x2, y2)
            
        elif self.aoi_adjusting and self.aoi_adjust_handle:
            # Adjust the appropriate corner or edge
            x1, y1, x2, y2 = self.aoi_coords
            
            if self.aoi_adjust_handle == "nw":
                self.aoi_coords[0] = x
                self.aoi_coords[1] = y
            elif self.aoi_adjust_handle == "ne":
                self.aoi_coords[2] = x
                self.aoi_coords[1] = y
            elif self.aoi_adjust_handle == "se":
                self.aoi_coords[2] = x
                self.aoi_coords[3] = y
            elif self.aoi_adjust_handle == "sw":
                self.aoi_coords[0] = x
                self.aoi_coords[3] = y
            elif self.aoi_adjust_handle == "n":
                self.aoi_coords[1] = y
            elif self.aoi_adjust_handle == "e":
                self.aoi_coords[2] = x
            elif self.aoi_adjust_handle == "s":
                self.aoi_coords[3] = y
            elif self.aoi_adjust_handle == "w":
                self.aoi_coords[0] = x
            
            # Update rectangle
            x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
            self.canvas.coords(self.aoi_rect, x1, y1, x2, y2)
            
            # Update handles
            self.update_handle_positions()
    
    def create_aoi_handles(self):
        """Create handles for adjusting the AOI"""
        # Clear existing handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
        
        x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
        
        # Create corner handles
        handle_positions = {
            "nw": (x1, y1),
            "ne": (x2, y1),
            "se": (x2, y2),
            "sw": (x1, y2),
            "n": ((x1 + x2) // 2, y1),
            "e": (x2, (y1 + y2) // 2),
            "s": ((x1 + x2) // 2, y2),
            "w": (x1, (y1 + y2) // 2)
        }
        
        # Create handle rectangles
        for handle_id, (hx, hy) in handle_positions.items():
            size = self.aoi_handle_size
            handle = self.canvas.create_rectangle(
                hx - size//2, hy - size//2,
                hx + size//2, hy + size//2,
                fill="white", outline="black",
                tags=("handle", handle_id)
            )
            self.aoi_handles.append(handle)
            self.aoi_handle_coords[handle_id] = (hx, hy)
    
    def update_handle_positions(self):
        """Update the positions of AOI adjustment handles"""
        if not self.aoi_handles:
            return
            
        x1, y1, x2, y2 = self.get_adjusted_aoi_coords()
        
        # Update handle positions
        handle_positions = {
            "nw": (x1, y1),
            "ne": (x2, y1),
            "se": (x2, y2),
            "sw": (x1, y2),
            "n": ((x1 + x2) // 2, y1),
            "e": (x2, (y1 + y2) // 2),
            "s": ((x1 + x2) // 2, y2),
            "w": (x1, (y1 + y2) // 2)
        }
        
        # Update handle rectangles
        for i, handle_id in enumerate(["nw", "ne", "se", "sw", "n", "e", "s", "w"]):
            if i < len(self.aoi_handles):
                hx, hy = handle_positions[handle_id]
                size = self.aoi_handle_size
                self.canvas.coords(
                    self.aoi_handles[i],
                    hx - size//2, hy - size//2,
                    hx + size//2, hy + size//2
                )
                self.aoi_handle_coords[handle_id] = (hx, hy)

def main():
    root = tk.Tk()
    app = SimpleToupCamLive(root)
    root.mainloop()

if __name__ == "__main__":
    main()
