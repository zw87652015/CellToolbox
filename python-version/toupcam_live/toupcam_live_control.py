"""
ToupCam Live Stream with Manual Controls
This script provides a live stream from a ToupCam camera with manual exposure controls
and light source frequency selection.
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

class ToupCamLiveControl:
    def __init__(self, root):
        self.root = root
        self.root.title("ToupCam Live Control")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Camera variables
        self.hcam = None
        self.cam_buffer = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.running = False
        self.auto_exposure = True
        self.exposure_time = 10000  # Default exposure time in microseconds
        self.gain = 100  # Default gain
        self.light_source = 0  # 0: DC, 1: 50Hz, 2: 60Hz
        
        # Exposure range
        self.exposure_min = 10
        self.exposure_max = 15000000
        self.gain_min = 100
        self.gain_max = 5000
        
        # UI update variables
        self.last_update_time = 0
        self.update_interval = 16  # milliseconds (60+ fps)
        self.photo_image = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
        # Create UI
        self.create_ui()
        
        # Start camera
        self.start_camera()
    
    def create_ui(self):
        # Main frame layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for video display
        self.video_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Video canvas with fixed size
        self.canvas = tk.Canvas(self.video_frame, bg="black", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # FPS counter
        self.fps_label = ttk.Label(self.video_frame, text="FPS: 0")
        self.fps_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # Right panel for controls
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Camera info section
        info_frame = ttk.LabelFrame(control_frame, text="Camera Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.camera_info_label = ttk.Label(info_frame, text="No camera connected")
        self.camera_info_label.pack(padx=5, pady=5)
        
        self.resolution_label = ttk.Label(info_frame, text="Resolution: -")
        self.resolution_label.pack(padx=5, pady=5)
        
        # Exposure control section
        exposure_frame = ttk.LabelFrame(control_frame, text="Exposure Control")
        exposure_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Auto exposure checkbox
        self.auto_exposure_var = tk.BooleanVar(value=True)
        self.auto_exposure_check = ttk.Checkbutton(
            exposure_frame, 
            text="Auto Exposure", 
            variable=self.auto_exposure_var,
            command=self.toggle_auto_exposure
        )
        self.auto_exposure_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # Exposure time control
        exposure_control_frame = ttk.Frame(exposure_frame)
        exposure_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(exposure_control_frame, text="Exposure Time (ms):").pack(side=tk.LEFT)
        
        self.exposure_value_label = ttk.Label(exposure_control_frame, text="10.0")
        self.exposure_value_label.pack(side=tk.RIGHT)
        
        self.exposure_scale = ttk.Scale(
            exposure_frame, 
            from_=0, 
            to=100,
            orient=tk.HORIZONTAL,
            command=self.update_exposure_time
        )
        self.exposure_scale.set(50)  # Set to middle initially
        self.exposure_scale.pack(fill=tk.X, padx=5, pady=5)
        
        # Gain control
        gain_control_frame = ttk.Frame(exposure_frame)
        gain_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(gain_control_frame, text="Gain:").pack(side=tk.LEFT)
        
        self.gain_value_label = ttk.Label(gain_control_frame, text="100")
        self.gain_value_label.pack(side=tk.RIGHT)
        
        self.gain_scale = ttk.Scale(
            exposure_frame, 
            from_=0, 
            to=100,
            orient=tk.HORIZONTAL,
            command=self.update_gain
        )
        self.gain_scale.set(0)  # Set to minimum initially
        self.gain_scale.pack(fill=tk.X, padx=5, pady=5)
        
        # Light source frequency selection
        light_source_frame = ttk.LabelFrame(control_frame, text="Light Source Frequency")
        light_source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.light_source_var = tk.IntVar(value=0)
        
        ttk.Radiobutton(
            light_source_frame, 
            text="DC (No Flicker)", 
            variable=self.light_source_var, 
            value=0,
            command=self.set_light_source
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(
            light_source_frame, 
            text="50 Hz (Europe/Asia)", 
            variable=self.light_source_var, 
            value=1,
            command=self.set_light_source
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(
            light_source_frame, 
            text="60 Hz (North America)", 
            variable=self.light_source_var, 
            value=2,
            command=self.set_light_source
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Snapshot button
        snapshot_frame = ttk.Frame(control_frame)
        snapshot_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.snapshot_button = ttk.Button(
            snapshot_frame, 
            text="Take Snapshot", 
            command=self.take_snapshot
        )
        self.snapshot_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Disable manual controls initially
        self.exposure_scale.configure(state=tk.DISABLED)
        self.gain_scale.configure(state=tk.DISABLED)
    
    def start_camera(self):
        """Initialize and start the camera"""
        devices = toupcam.Toupcam.EnumV2()
        if not devices:
            self.status_var.set("No ToupCam cameras found")
            return
        
        device = devices[0]  # Use the first camera
        
        # Update camera info
        self.camera_info_label.configure(text=f"Camera: {device.displayname}")
        
        # Try to open the camera
        try:
            self.hcam = toupcam.Toupcam.Open(device.id)
            if not self.hcam:
                self.status_var.set("Failed to open camera")
                return
            
            # Get camera properties
            self.frame_width, self.frame_height = self.hcam.get_Size()
            self.resolution_label.configure(text=f"Resolution: {self.frame_width} x {self.frame_height}")
            
            # Calculate buffer size
            bufsize = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(bufsize)
            
            # Create frame buffer for OpenCV
            self.frame_buffer = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
            
            # Get exposure range
            try:
                exp_range = self.hcam.get_ExpTimeRange()
                if isinstance(exp_range, tuple) and len(exp_range) >= 2:
                    self.exposure_min = exp_range[0]
                    self.exposure_max = exp_range[1]
                    print(f"Exposure range: {self.exposure_min} - {self.exposure_max} us")
            except toupcam.HRESULTException as ex:
                print(f"Could not get exposure range: 0x{ex.hr & 0xffffffff:x}")
            
            # Get gain range
            try:
                gain_range = self.hcam.get_ExpoAGainRange()
                if isinstance(gain_range, tuple) and len(gain_range) >= 2:
                    self.gain_min = gain_range[0]
                    self.gain_max = gain_range[1]
                    print(f"Gain range: {self.gain_min} - {self.gain_max}")
            except toupcam.HRESULTException as ex:
                print(f"Could not get gain range: 0x{ex.hr & 0xffffffff:x}")
            
            # Set initial auto exposure
            try:
                self.hcam.put_AutoExpoEnable(self.auto_exposure)
            except toupcam.HRESULTException as ex:
                print(f"Could not set auto exposure: 0x{ex.hr & 0xffffffff:x}")
            
            # Set camera options for low latency
            try:
                # Set low latency mode if available
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_NOPACKET_TIMEOUT, 0)  # Disable packet timeout
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimum frame buffer
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_PROCESSMODE, 0)  # Raw mode for lower latency
                self.hcam.put_RealTime(True)  # Enable real-time mode
            except toupcam.HRESULTException as ex:
                print(f"Could not set low latency options: 0x{ex.hr & 0xffffffff:x}")
            
            # Start the camera with callback
            self.running = True
            self.hcam.StartPullModeWithCallback(self.camera_callback, self)
            
            # Start the UI update thread
            self.update_thread = threading.Thread(target=self.update_ui)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            # Schedule FPS update
            self.root.after(1000, self.update_fps)
            
            self.status_var.set("Camera started successfully")
            
        except toupcam.HRESULTException as ex:
            self.status_var.set(f"Error initializing camera: 0x{ex.hr & 0xffffffff:x}")
    
    @staticmethod
    def camera_callback(nEvent, ctx):
        """Static callback function for the camera events"""
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            ctx.process_image()
        elif nEvent == toupcam.TOUPCAM_EVENT_EXPOSURE:
            ctx.status_var.set("Auto exposure adjustment in progress")
        elif nEvent == toupcam.TOUPCAM_EVENT_TEMPTINT:
            ctx.status_var.set("White balance adjustment in progress")
        elif nEvent == toupcam.TOUPCAM_EVENT_ERROR:
            ctx.status_var.set("Camera error occurred")
        elif nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
            ctx.status_var.set("Camera disconnected")
    
    def process_image(self):
        """Process the image received from the camera"""
        if not self.running or not self.hcam:
            return
        
        try:
            # Pull the image from the camera with minimal processing
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Convert the raw buffer to a numpy array (optimized)
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8)
            
            # Reshape the array to an image format
            frame = frame.reshape((self.frame_height, toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3, 3))
            frame = frame[:, :self.frame_width, :]
            
            # Convert BGR to RGB (ToupCam provides BGR by default)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Store the frame (no copy to reduce latency)
            self.frame_buffer = frame
            
            # Count frames for FPS calculation
            self.frame_count += 1
            
            # Schedule UI update immediately
            self.root.after_idle(self.update_frame)
            
        except toupcam.HRESULTException as ex:
            print(f"Error pulling image: 0x{ex.hr & 0xffffffff:x}")
    
    def update_frame(self):
        """Update the UI with the latest frame (called on the main thread)"""
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
            
            # Resize the frame (use NEAREST for speed)
            display_frame = cv2.resize(self.frame_buffer, (display_width, display_height), 
                                      interpolation=cv2.INTER_NEAREST)
            
            # Convert to PhotoImage
            img = Image.fromarray(display_frame)
            self.photo_image = ImageTk.PhotoImage(image=img)
            
            # If this is the first frame, create the image on the canvas
            if not self.canvas.find_withtag("video"):
                self.canvas.create_image(
                    canvas_width//2, 
                    canvas_height//2, 
                    anchor=tk.CENTER, 
                    image=self.photo_image,
                    tags=("video",)
                )
            else:
                # Update the existing image
                self.canvas.itemconfig("video", image=self.photo_image)
    
    def update_ui(self):
        """Background thread for periodic UI updates"""
        while self.running:
            # Sleep to prevent high CPU usage
            time.sleep(0.1)
    
    def toggle_auto_exposure(self):
        """Toggle between auto and manual exposure"""
        if not self.hcam:
            return
        
        self.auto_exposure = self.auto_exposure_var.get()
        
        try:
            self.hcam.put_AutoExpoEnable(self.auto_exposure)
            
            if self.auto_exposure:
                # Disable manual controls
                self.exposure_scale.configure(state=tk.DISABLED)
                self.gain_scale.configure(state=tk.DISABLED)
                self.status_var.set("Auto exposure enabled")
            else:
                # Enable manual controls
                self.exposure_scale.configure(state=tk.NORMAL)
                self.gain_scale.configure(state=tk.NORMAL)
                
                # Get current exposure and gain
                try:
                    self.exposure_time = self.hcam.get_ExpoTime()
                    self.gain = self.hcam.get_ExpoAGain()
                    
                    # Update sliders
                    self.update_exposure_slider()
                    self.update_gain_slider()
                    
                    self.status_var.set("Manual exposure enabled")
                except toupcam.HRESULTException as ex:
                    print(f"Error getting exposure settings: 0x{ex.hr & 0xffffffff:x}")
        
        except toupcam.HRESULTException as ex:
            print(f"Error setting auto exposure: 0x{ex.hr & 0xffffffff:x}")
    
    def update_exposure_time(self, value):
        """Update the exposure time based on slider value"""
        if not self.hcam or self.auto_exposure:
            return
        
        # Convert slider value (0-100) to exposure time in logarithmic scale
        normalized = float(value) / 100.0
        log_range = np.log10(self.exposure_max) - np.log10(self.exposure_min)
        log_value = np.log10(self.exposure_min) + normalized * log_range
        self.exposure_time = int(10 ** log_value)
        
        # Ensure within range
        self.exposure_time = max(self.exposure_min, min(self.exposure_max, self.exposure_time))
        
        # Update label (convert to ms for display)
        self.exposure_value_label.configure(text=f"{self.exposure_time / 1000:.1f}")
        
        try:
            self.hcam.put_ExpoTime(self.exposure_time)
            self.status_var.set(f"Exposure time set to {self.exposure_time / 1000:.1f} ms")
        except toupcam.HRESULTException as ex:
            print(f"Error setting exposure time: 0x{ex.hr & 0xffffffff:x}")
    
    def update_gain(self, value):
        """Update the gain based on slider value"""
        if not self.hcam or self.auto_exposure:
            return
        
        # Convert slider value (0-100) to gain
        normalized = float(value) / 100.0
        gain_range = self.gain_max - self.gain_min
        self.gain = int(self.gain_min + normalized * gain_range)
        
        # Ensure within range
        self.gain = max(self.gain_min, min(self.gain_max, self.gain))
        
        # Update label
        self.gain_value_label.configure(text=str(self.gain))
        
        try:
            self.hcam.put_ExpoAGain(self.gain)
            self.status_var.set(f"Gain set to {self.gain}")
        except toupcam.HRESULTException as ex:
            print(f"Error setting gain: 0x{ex.hr & 0xffffffff:x}")
    
    def update_exposure_slider(self):
        """Update the exposure slider to match the current exposure time"""
        if self.exposure_min <= self.exposure_time <= self.exposure_max:
            # Convert exposure time to slider value (0-100) in logarithmic scale
            log_range = np.log10(self.exposure_max) - np.log10(self.exposure_min)
            log_current = np.log10(self.exposure_time) - np.log10(self.exposure_min)
            normalized = log_current / log_range
            slider_value = normalized * 100.0
            
            self.exposure_scale.set(slider_value)
            self.exposure_value_label.configure(text=f"{self.exposure_time / 1000:.1f}")
    
    def update_gain_slider(self):
        """Update the gain slider to match the current gain"""
        if self.gain_min <= self.gain <= self.gain_max:
            # Convert gain to slider value (0-100)
            gain_range = self.gain_max - self.gain_min
            normalized = (self.gain - self.gain_min) / gain_range
            slider_value = normalized * 100.0
            
            self.gain_scale.set(slider_value)
            self.gain_value_label.configure(text=str(self.gain))
    
    def set_light_source(self, event=None):
        """Set the light source frequency (anti-flicker)"""
        if not self.hcam:
            return
        
        self.light_source = self.light_source_var.get()
        
        try:
            # The correct method is put_HZ, not put_Option with TOUPCAM_OPTION_LIGHTSOURCE
            # 0 = DC, 1 = 50Hz, 2 = 60Hz
            self.hcam.put_HZ(self.light_source)
            
            # Set optimal exposure time based on light source frequency
            if self.light_source == 1:  # 50Hz
                # Set exposure time to 20ms (1000/50) for 50Hz
                optimal_exposure = 20000  # 20ms in microseconds
                try:
                    # Disable auto exposure if it's enabled
                    if self.auto_exposure:
                        self.auto_exposure = False
                        self.hcam.put_AutoExpoEnable(False)
                        self.auto_exposure_var.set(0)
                    
                    # Set the optimal exposure time
                    self.hcam.put_ExpoTime(optimal_exposure)
                    self.exposure_time = optimal_exposure
                    self.update_exposure_slider()
                    print(f"Set optimal exposure time for 50Hz: {optimal_exposure/1000:.2f}ms")
                except toupcam.HRESULTException as ex:
                    print(f"Error setting optimal exposure time: 0x{ex.hr & 0xffffffff:x}")
            elif self.light_source == 2:  # 60Hz
                # Set exposure time to 16.67ms (1000/60) for 60Hz
                optimal_exposure = 16667  # 16.667ms in microseconds
                try:
                    # Disable auto exposure if it's enabled
                    if self.auto_exposure:
                        self.auto_exposure = False
                        self.hcam.put_AutoExpoEnable(False)
                        self.auto_exposure_var.set(0)
                    
                    # Set the optimal exposure time
                    self.hcam.put_ExpoTime(optimal_exposure)
                    self.exposure_time = optimal_exposure
                    self.update_exposure_slider()
                    print(f"Set optimal exposure time for 60Hz: {optimal_exposure/1000:.2f}ms")
                except toupcam.HRESULTException as ex:
                    print(f"Error setting optimal exposure time: 0x{ex.hr & 0xffffffff:x}")
            
            light_source_names = ["DC (No Flicker)", "50 Hz", "60 Hz"]
            self.status_var.set(f"Light source set to {light_source_names[self.light_source]}")
            print(f"Light source set to {light_source_names[self.light_source]} (value: {self.light_source})")
        except toupcam.HRESULTException as ex:
            error_code = ex.hr & 0xffffffff
            print(f"Error setting light source with put_HZ: 0x{error_code:x}")
            self.status_var.set(f"Failed to set light source frequency")
    
    def take_snapshot(self):
        """Take a snapshot and save it to disk"""
        if self.frame_buffer is None:
            self.status_var.set("No frame available for snapshot")
            return
        
        # Create snapshots directory if it doesn't exist
        snapshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots")
        os.makedirs(snapshots_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(snapshots_dir, f"toupcam_snapshot_{timestamp}.png")
        
        # Save the image
        cv2.imwrite(filename, cv2.cvtColor(self.frame_buffer, cv2.COLOR_RGB2BGR))
        
        self.status_var.set(f"Snapshot saved to {filename}")
    
    def update_fps(self):
        """Update the FPS counter"""
        if self.running:
            current_time = time.time()
            time_diff = current_time - self.last_fps_time
            
            if time_diff > 0:
                self.fps = self.frame_count / time_diff
                self.fps_label.config(text=f"FPS: {self.fps:.1f}")
                
                # Reset counters
                self.frame_count = 0
                self.last_fps_time = current_time
            
            # Schedule next update
            self.root.after(1000, self.update_fps)
    
    def on_closing(self):
        """Clean up resources when closing the application"""
        print("Closing application and cleaning up resources...")
        
        # Set running flag to False first to stop any ongoing operations
        self.running = False
        
        # Give a short time for threads to stop
        time.sleep(0.1)
        
        # Handle camera with extreme caution - both Stop and Close can hang
        if self.hcam:
            camera_ref = self.hcam
            self.hcam = None  # Immediately set to None so we don't try to access it again
            
            try:
                # Create a thread to handle camera cleanup with timeout
                def cleanup_camera():
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
                        print(f"Fatal error in camera cleanup: {e}")
                
                # Start camera cleanup in a separate thread
                cleanup_thread = threading.Thread(target=cleanup_camera)
                cleanup_thread.daemon = True  # Make thread a daemon so it won't block program exit
                cleanup_thread.start()
                
                # Only wait a very short time - don't let it block the application exit
                print("Waiting briefly for camera cleanup...")
                cleanup_thread.join(timeout=0.5)  # Wait max 0.5 second for entire cleanup
                
                if cleanup_thread.is_alive():
                    print("WARNING: Camera cleanup timed out, abandoning camera resources")
            except Exception as e:
                print(f"Error setting up camera cleanup: {e}")
        
        print("Shutting down application...")
        # Use after_idle to ensure this runs in the main thread after current processing
        self.root.after_idle(self._force_quit)
    
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
        
def main():
    root = tk.Tk()
    app = ToupCamLiveControl(root)
    root.mainloop()

if __name__ == "__main__":
    main()
