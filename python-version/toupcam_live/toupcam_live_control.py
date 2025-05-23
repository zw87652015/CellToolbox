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
from tkinter import messagebox

# Win32 constants for window management
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SW_SHOW = 5
SWP_SHOWWINDOW = 0x0040

# Win32 API functions
SetWindowPos = ctypes.windll.user32.SetWindowPos
ShowWindow = ctypes.windll.user32.ShowWindow
BringWindowToTop = ctypes.windll.user32.BringWindowToTop
AttachThreadInput = ctypes.windll.user32.AttachThreadInput
GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
GetCurrentThreadId = ctypes.windll.kernel32.GetCurrentThreadId

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
        self.binning_mode = 0x01  # Default: No binning
        
        # Load binning settings if available
        self.binning_mode = self.load_binning_settings()
        
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
        
        # Window focus maintenance
        self.focus_thread = None
        self.focus_running = False
        
        # Rendering thread
        self.render_thread = None
        self.render_running = False
        self.new_frame_available = False
        self.frame_lock = threading.Lock()
        
        # Create UI
        self.create_ui()
        
        # Start camera
        self.start_camera()
        
        # Start window focus maintenance
        self.start_focus_maintenance()
        
        # Start rendering thread
        self.start_render_thread()
    
    def load_binning_settings(self):
        """Load binning settings from file"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "binning_settings.txt")
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    binning_mode = int(f.read().strip())
                print(f"Loaded digital binning mode: {hex(binning_mode)}")
                return binning_mode
        except Exception as e:
            print(f"Error loading binning settings: {str(e)}")
        return 0x0001  # Default: No binning
    
    def create_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Exposure controls
        exposure_frame = ttk.LabelFrame(control_frame, text="Exposure")
        exposure_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Exposure time slider
        ttk.Label(exposure_frame, text="Time (ms):").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.exposure_scale = ttk.Scale(
            exposure_frame, 
            from_=1, 
            to=100, 
            orient=tk.HORIZONTAL, 
            length=150,
            command=self.on_exposure_change
        )
        self.exposure_scale.set(16.67)  # Default: 16.67ms
        self.exposure_scale.grid(row=0, column=1, padx=5, pady=2)
        self.exposure_value = ttk.Label(exposure_frame, text="16.67")
        self.exposure_value.grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        
        # Gain slider
        ttk.Label(exposure_frame, text="Gain:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.gain_scale = ttk.Scale(
            exposure_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL, 
            length=150,
            command=self.on_gain_change
        )
        self.gain_scale.set(0)  # Default: 0
        self.gain_scale.grid(row=1, column=1, padx=5, pady=2)
        self.gain_value = ttk.Label(exposure_frame, text="0")
        self.gain_value.grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)
        
        # Auto exposure checkbox
        self.auto_exposure_var = tk.BooleanVar(value=False)
        auto_exposure_cb = ttk.Checkbutton(
            exposure_frame, 
            text="Auto Exposure", 
            variable=self.auto_exposure_var,
            command=self.on_auto_exposure_change
        )
        auto_exposure_cb.grid(row=2, column=0, columnspan=3, padx=5, pady=2, sticky=tk.W)
        
        # Binning label
        self.binning_label = ttk.Label(control_frame, text="Digital Binning: Not Set")
        self.binning_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Left panel for video display
        self.video_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Video canvas with fixed size
        self.canvas = tk.Canvas(self.video_frame, bg="black", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # FPS counter
        self.fps_label = ttk.Label(self.video_frame, text="FPS: 0")
        self.fps_label.pack(anchor=tk.NW, padx=5, pady=5)
        
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
            
            # Set digital binning mode regardless of whether the camera reports supporting it
            try:
                # Set the binning mode
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BINNING, self.binning_mode)
                
                # Update the binning mode label
                binning_text = self.get_binning_text(self.binning_mode)
                self.binning_label.configure(text=f"Digital Binning: {binning_text}")
                print(f"Set digital binning mode to: {binning_text}")
            except toupcam.HRESULTException as ex:
                print(f"Could not set binning mode: 0x{ex.hr & 0xffffffff:x}")
            
            # Get camera properties
            self.frame_width, self.frame_height = self.hcam.get_Size()
            print(f"Camera resolution: {self.frame_width}x{self.frame_height}")
            
            # Set camera properties for optimal performance
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BYTEORDER, 0)  # RGB
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_UPSIDE_DOWN, 0)  # Normal orientation
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimize frame queue
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_CALLBACK_THREAD, 1)  # Enable dedicated callback thread
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_THREAD_PRIORITY, 2)  # Set high thread priority
            self.hcam.put_AutoExpoEnable(False)
            
            # Set anti-flicker to 60Hz (for 16.67ms exposure)
            self.hcam.put_HZ(2)
            
            # Set exposure time (in microseconds)
            self.hcam.put_ExpoTime(16670)  # 16.67ms
            
            # Set other camera options
            self.hcam.put_Brightness(0)
            self.hcam.put_Contrast(0)
            self.hcam.put_Gamma(100)  # 1.0
            
            # Allocate buffer for image data (pre-allocate to avoid reallocations)
            buffer_size = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(buffer_size)
            
            # Pre-allocate numpy array for frame buffer to avoid memory allocations
            self.frame_buffer_shape = (self.frame_height, toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3, 3)
            
            # Initialize frame timing variables
            self.last_frame_time = time.time()
            self.frame_interval = 1.0 / 60.0  # Target 60 FPS
            
            # Register callback
            self.hcam.StartPullModeWithCallback(self.on_frame, self)
            
            # Set running flag to True to enable image processing
            self.running = True
            
            self.status_var.set(f"Camera started: {device.displayname}")
            
        except Exception as e:
            self.status_var.set(f"Error starting camera: {str(e)}")
            messagebox.showerror("Camera Error", f"Error starting camera: {str(e)}")
    
    def get_binning_text(self, binning_mode):
        """Convert binning mode value to descriptive text"""
        binning_map = {
            0x0001: "None (1×1)",
            0x0002: "2×2 Average",
            0x0004: "3×3 Average",
            0x0008: "4×4 Average",
            0x0082: "2×2 Add",
            0x0084: "3×3 Add",
            0x0088: "4×4 Add"
        }
        return binning_map.get(binning_mode, f"Unknown ({hex(binning_mode)})")
    
    def on_frame(self, nEvent, ctx):
        try:
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
        except Exception as e:
            print(f"[ERROR] Exception in on_frame: {e}")
    
    def process_image(self):
        if not self.running or not self.hcam:
            return
            
        # Track frame timing for FPS calculation
        current_time = time.time()
        self.last_frame_time = current_time
            
        try:
            # Pull the image from the camera with minimal processing
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Convert the raw buffer to a numpy array without copying data
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8).reshape(self.frame_buffer_shape)
            frame = frame[:, :self.frame_width, :]
            
            # Store the frame (no copy to reduce latency)
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
                
            # No need to schedule UI updates here - the render thread handles that
        except toupcam.HRESULTException as ex:
            print(f"[ERROR] Error pulling image: 0x{ex.hr & 0xffffffff:x}")
        except Exception as e:
            print(f"[ERROR] process_image exception: {e}")
    
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
            
            # Convert BGR to RGB for display
            rgb_frame = cv2.cvtColor(self.frame_buffer, cv2.COLOR_BGR2RGB)
            
            # Resize the frame
            display_frame = cv2.resize(rgb_frame, (display_width, display_height), 
                                      interpolation=cv2.INTER_LINEAR)
            
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
    
    def on_exposure_change(self, value):
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
        self.exposure_value.configure(text=f"{self.exposure_time / 1000:.1f}")
        
        try:
            self.hcam.put_ExpoTime(self.exposure_time)
            self.status_var.set(f"Exposure time set to {self.exposure_time / 1000:.1f} ms")
        except toupcam.HRESULTException as ex:
            print(f"Error setting exposure time: 0x{ex.hr & 0xffffffff:x}")
    
    def on_gain_change(self, value):
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
        self.gain_value.configure(text=str(self.gain))
        
        try:
            self.hcam.put_ExpoAGain(self.gain)
            self.status_var.set(f"Gain set to {self.gain}")
        except toupcam.HRESULTException as ex:
            print(f"Error setting gain: 0x{ex.hr & 0xffffffff:x}")
    
    def on_auto_exposure_change(self):
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
    
    def update_exposure_slider(self):
        """Update the exposure slider to match the current exposure time"""
        if self.exposure_min <= self.exposure_time <= self.exposure_max:
            # Convert exposure time to slider value (0-100) in logarithmic scale
            log_range = np.log10(self.exposure_max) - np.log10(self.exposure_min)
            log_current = np.log10(self.exposure_time) - np.log10(self.exposure_min)
            normalized = log_current / log_range
            slider_value = normalized * 100.0
            
            self.exposure_scale.set(slider_value)
            self.exposure_value.configure(text=f"{self.exposure_time / 1000:.1f}")
    
    def update_gain_slider(self):
        """Update the gain slider to match the current gain"""
        if self.gain_min <= self.gain <= self.gain_max:
            # Convert gain to slider value (0-100)
            gain_range = self.gain_max - self.gain_min
            normalized = (self.gain - self.gain_min) / gain_range
            slider_value = normalized * 100.0
            
            self.gain_scale.set(slider_value)
            self.gain_value.configure(text=str(self.gain))
    
    def start_focus_maintenance(self):
        """Start a thread to maintain window focus and ensure consistent frame updates"""
        self.focus_running = True
        self.focus_thread = threading.Thread(target=self.maintain_window_focus)
        self.focus_thread.daemon = True
        self.focus_thread.start()
        print("Window focus maintenance thread started")
    
    def maintain_window_focus(self):
        """Maintain window focus to ensure consistent frame updates"""
        try:
            # Get the window handle from Tkinter
            hwnd = int(self.root.winfo_id())
            print(f"Focus thread got window handle: {hwnd}")
            
            # Initial window setup - make it visible but not forcing foreground
            ShowWindow(hwnd, SW_SHOW)
            SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            print("Window visibility set up")
            
            # Periodically ensure window is visible
            while self.focus_running:
                # Just ensure the window is visible, don't force it to foreground
                ShowWindow(hwnd, SW_SHOW)
                
                # Sleep to avoid excessive CPU usage
                time.sleep(0.2)  # Check every 200ms
        except Exception as e:
            print(f"Error in window focus maintenance: {str(e)}")
        
        print("Window focus maintenance thread exiting")
    
    def start_render_thread(self):
        """Start a dedicated thread for rendering frames"""
        self.render_running = True
        self.render_thread = threading.Thread(target=self.render_loop)
        self.render_thread.daemon = True
        self.render_thread.start()
        print("Render thread started")
    
    def render_loop(self):
        """Continuously render frames at a high rate regardless of UI focus"""
        try:
            while self.render_running:
                if self.running and self.frame_buffer is not None:
                    # Use tkinter's thread-safe after method to update UI
                    self.root.after_idle(self.update_frame)
                    
                # Sleep briefly to avoid excessive CPU usage
                # Short enough to maintain high frame rates
                time.sleep(0.01)  # 10ms = potential for 100fps
        except Exception as e:
            print(f"Error in render loop: {str(e)}")
        
        print("Render thread exiting")
    
    def on_closing(self):
        """Clean up resources when closing the application"""
        print("Closing application and cleaning up resources...")
        
        # Stop focus maintenance thread
        self.focus_running = False
        if self.focus_thread:
            self.focus_thread.join(timeout=1.0)
        
        # Stop render thread
        self.render_running = False
        if self.render_thread:
            self.render_thread.join(timeout=1.0)
            
        # Stop camera
        self.cleanup_camera()
        
        # Force quit the application
        self._force_quit()
    
    def cleanup_camera(self):
        """Clean up camera resources"""
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
