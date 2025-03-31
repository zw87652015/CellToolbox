"""
ToupCam Integration for CellToolbox
This script provides integration between ToupCam cameras and the CellToolbox project.
It includes parameter control UI similar to other CellToolbox components.
"""

import sys
import os
import time
import numpy as np
import cv2
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import threading

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
except ImportError:
    print(f"Error: Could not import toupcam module. Check if the path is correct: {sdk_path}")
    print("Make sure the toupcam.py file exists in the SDK path.")
    sys.exit(1)

class ToupCamCellToolbox:
    def __init__(self, root=None):
        self.hcam = None
        self.buf = None
        self.total = 0
        self.width = 0
        self.height = 0
        self.running = False
        self.current_frame = None
        self.snapshot_count = 0
        self.calibration_data = None
        
        # Create UI if root is provided
        self.root = root
        if self.root:
            self.create_ui()
        
        # Camera parameters with default values
        self.params = {
            'exposure': 10000,  # in microseconds
            'gain': 100,        # 100 = 1.0x gain
            'auto_exposure': True,
            'white_balance': True,
            'resolution_index': 0,
            'color_temp': 6500,  # in Kelvin
            'contrast': 0,       # -100 to 100
            'saturation': 0,     # -100 to 100
            'gamma': 100,        # 20 to 180
            'frame_rate': 30     # frames per second
        }
        
    def create_ui(self):
        """Create the user interface for camera control"""
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Camera selection frame
        camera_frame = ttk.LabelFrame(self.main_frame, text="Camera Control", padding="10")
        camera_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Camera selection
        ttk.Label(camera_frame, text="Camera:").grid(row=0, column=0, sticky=tk.W)
        self.camera_var = tk.StringVar()
        self.camera_combo = ttk.Combobox(camera_frame, textvariable=self.camera_var, state="readonly")
        self.camera_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Connect/Disconnect buttons
        self.connect_btn = ttk.Button(camera_frame, text="Connect", command=self.connect_selected_camera)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.disconnect_btn = ttk.Button(camera_frame, text="Disconnect", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Refresh camera list button
        self.refresh_btn = ttk.Button(camera_frame, text="Refresh List", command=self.refresh_camera_list)
        self.refresh_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Resolution selection
        ttk.Label(camera_frame, text="Resolution:").grid(row=1, column=0, sticky=tk.W)
        self.resolution_var = tk.StringVar()
        self.resolution_combo = ttk.Combobox(camera_frame, textvariable=self.resolution_var, state="readonly")
        self.resolution_combo.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.resolution_combo.bind("<<ComboboxSelected>>", self.on_resolution_change)
        
        # Parameter control frame
        param_frame = ttk.LabelFrame(self.main_frame, text="Camera Parameters", padding="10")
        param_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Auto exposure checkbox
        self.auto_exposure_var = tk.BooleanVar(value=self.params['auto_exposure'])
        self.auto_exposure_check = ttk.Checkbutton(
            param_frame, text="Auto Exposure", variable=self.auto_exposure_var,
            command=self.on_auto_exposure_change
        )
        self.auto_exposure_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Exposure control
        ttk.Label(param_frame, text="Exposure (µs):").grid(row=1, column=0, sticky=tk.W)
        self.exposure_var = tk.IntVar(value=self.params['exposure'])
        self.exposure_scale = ttk.Scale(
            param_frame, from_=1000, to=1000000, variable=self.exposure_var,
            command=lambda _: self.on_exposure_change()
        )
        self.exposure_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.exposure_entry = ttk.Entry(param_frame, width=10, textvariable=self.exposure_var)
        self.exposure_entry.grid(row=1, column=2, padx=5, pady=5)
        self.exposure_entry.bind("<Return>", lambda _: self.on_exposure_change())
        
        # Gain control
        ttk.Label(param_frame, text="Gain:").grid(row=2, column=0, sticky=tk.W)
        self.gain_var = tk.IntVar(value=self.params['gain'])
        self.gain_scale = ttk.Scale(
            param_frame, from_=0, to=400, variable=self.gain_var,
            command=lambda _: self.on_gain_change()
        )
        self.gain_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.gain_entry = ttk.Entry(param_frame, width=10, textvariable=self.gain_var)
        self.gain_entry.grid(row=2, column=2, padx=5, pady=5)
        self.gain_entry.bind("<Return>", lambda _: self.on_gain_change())
        
        # White balance checkbox and button
        self.wb_var = tk.BooleanVar(value=self.params['white_balance'])
        self.wb_check = ttk.Checkbutton(
            param_frame, text="Auto White Balance", variable=self.wb_var,
            command=self.on_white_balance_change
        )
        self.wb_check.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.wb_once_btn = ttk.Button(param_frame, text="WB Once", command=self.white_balance_once)
        self.wb_once_btn.grid(row=3, column=1, padx=5, pady=5)
        
        # Snapshot frame
        snapshot_frame = ttk.LabelFrame(self.main_frame, text="Snapshot Control", padding="10")
        snapshot_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Snapshot button
        self.snapshot_btn = ttk.Button(snapshot_frame, text="Take Snapshot", command=self.take_snapshot)
        self.snapshot_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Snapshot directory
        ttk.Label(snapshot_frame, text="Save Directory:").grid(row=0, column=1, sticky=tk.W, padx=5)
        self.snapshot_dir_var = tk.StringVar(value=os.getcwd())
        self.snapshot_dir_entry = ttk.Entry(snapshot_frame, width=30, textvariable=self.snapshot_dir_var)
        self.snapshot_dir_entry.grid(row=0, column=2, padx=5, pady=5)
        
        self.browse_btn = ttk.Button(snapshot_frame, text="Browse", command=self.browse_snapshot_dir)
        self.browse_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Video frame (placeholder)
        self.video_frame = ttk.LabelFrame(self.root, text="Camera Feed", padding="10")
        self.video_frame.grid(row=0, column=1, rowspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.video_canvas = tk.Canvas(self.video_frame, width=640, height=480, bg="black")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Initialize camera list
        self.refresh_camera_list()
        
    def refresh_camera_list(self):
        """Refresh the list of available cameras"""
        devices = toupcam.Toupcam.EnumV2()
        self.cameras = devices
        
        # Update camera combobox
        camera_names = [f"{i+1}: {dev.displayname}" for i, dev in enumerate(devices)]
        if not camera_names:
            camera_names = ["No cameras found"]
            self.connect_btn.configure(state=tk.DISABLED)
        else:
            self.connect_btn.configure(state=tk.NORMAL)
            
        self.camera_combo['values'] = camera_names
        if camera_names:
            self.camera_combo.current(0)
            
        self.update_status(f"Found {len(devices)} camera(s)")
        
    def connect_selected_camera(self):
        """Connect to the selected camera from the dropdown"""
        if not self.cameras:
            self.update_status("No cameras available")
            return
            
        # Get selected camera index
        selected = self.camera_combo.current()
        if selected < 0 or selected >= len(self.cameras):
            self.update_status("Invalid camera selection")
            return
            
        # Connect to camera
        self.connect(selected)
        
    def on_resolution_change(self, event=None):
        """Handle resolution change"""
        if not self.hcam:
            return
            
        selected = self.resolution_combo.current()
        if selected < 0:
            return
            
        try:
            # Set the resolution
            self.hcam.Stop()
            self.hcam.put_eSize(selected)
            
            # Update width and height
            self.width, self.height = self.hcam.get_Size()
            
            # Reallocate buffer
            bufsize = toupcam.TDIBWIDTHBYTES(self.width * 24) * self.height
            self.buf = bytes(bufsize)
            
            # Restart the camera
            self.hcam.StartPullModeWithCallback(self.camera_callback, self)
            self.update_status(f"Resolution changed to {self.width}x{self.height}")
            
        except toupcam.HRESULTException as ex:
            self.update_status(f"Failed to change resolution: 0x{ex.hr & 0xffffffff:x}")
        
    def on_auto_exposure_change(self):
        """Handle auto exposure checkbox change"""
        if not self.hcam:
            return
            
        auto_expo = self.auto_exposure_var.get()
        try:
            self.hcam.put_AutoExpoEnable(auto_expo)
            self.params['auto_exposure'] = auto_expo
            
            # Enable/disable manual exposure controls
            state = tk.DISABLED if auto_expo else tk.NORMAL
            self.exposure_scale.configure(state=state)
            self.exposure_entry.configure(state=state)
            
            self.update_status(f"Auto exposure {'enabled' if auto_expo else 'disabled'}")
            
        except toupcam.HRESULTException as ex:
            self.update_status(f"Failed to set auto exposure: 0x{ex.hr & 0xffffffff:x}")
        
    def on_exposure_change(self):
        """Handle exposure slider or entry change"""
        if not self.hcam or self.auto_exposure_var.get():
            return
            
        exposure = self.exposure_var.get()
        try:
            self.hcam.put_ExpoTime(exposure)
            self.params['exposure'] = exposure
            self.update_status(f"Exposure set to {exposure} µs")
            
        except toupcam.HRESULTException as ex:
            self.update_status(f"Failed to set exposure: 0x{ex.hr & 0xffffffff:x}")
        
    def on_gain_change(self):
        """Handle gain slider or entry change"""
        if not self.hcam:
            return
            
        gain = self.gain_var.get()
        try:
            self.hcam.put_ExpoAGain(gain)
            self.params['gain'] = gain
            self.update_status(f"Gain set to {gain/100:.2f}x")
            
        except toupcam.HRESULTException as ex:
            self.update_status(f"Failed to set gain: 0x{ex.hr & 0xffffffff:x}")
        
    def on_white_balance_change(self):
        """Handle white balance checkbox change"""
        if not self.hcam:
            return
            
        wb_auto = self.wb_var.get()
        try:
            self.hcam.put_TempTint(6500, 1000)  # Default temp and tint
            self.hcam.put_AWBAuxRect(0, 0, self.width, self.height)  # Use full frame for AWB
            self.hcam.put_AutoWB(wb_auto)
            self.params['white_balance'] = wb_auto
            self.update_status(f"Auto white balance {'enabled' if wb_auto else 'disabled'}")
            
        except toupcam.HRESULTException as ex:
            self.update_status(f"Failed to set white balance: 0x{ex.hr & 0xffffffff:x}")
        
    def white_balance_once(self):
        """Perform one-time white balance adjustment"""
        if not self.hcam:
            return
            
        try:
            self.hcam.AwbOnce()
            self.update_status("White balance adjusted")
            
        except toupcam.HRESULTException as ex:
            self.update_status(f"Failed to adjust white balance: 0x{ex.hr & 0xffffffff:x}")
        
    def take_snapshot(self):
        """Take a snapshot and save it to the specified directory"""
        if not self.hcam or self.current_frame is None:
            self.update_status("No camera or no frame available")
            return
            
        # Get save directory
        save_dir = self.snapshot_dir_var.get()
        if not os.path.isdir(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                self.update_status(f"Failed to create directory: {e}")
                return
                
        # Generate filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"toupcam_snapshot_{timestamp}_{self.snapshot_count:03d}.png")
        self.snapshot_count += 1
        
        # Save the image
        try:
            cv2.imwrite(filename, self.current_frame)
            self.update_status(f"Snapshot saved as {os.path.basename(filename)}")
            
        except Exception as e:
            self.update_status(f"Failed to save snapshot: {e}")
        
    def browse_snapshot_dir(self):
        """Open a directory browser to select snapshot save location"""
        directory = filedialog.askdirectory(
            initialdir=self.snapshot_dir_var.get(),
            title="Select Snapshot Save Directory"
        )
        if directory:
            self.snapshot_dir_var.set(directory)
        
    def update_status(self, message):
        """Update the status bar with a message"""
        self.status_var.set(message)
        print(message)
        
    def update_ui_state(self, connected):
        """Update UI elements based on connection state"""
        if not self.root:
            return
            
        state_connected = tk.NORMAL if connected else tk.DISABLED
        state_disconnected = tk.DISABLED if connected else tk.NORMAL
        
        # Update button states
        self.connect_btn.configure(state=state_disconnected)
        self.disconnect_btn.configure(state=state_connected)
        self.camera_combo.configure(state="readonly" if not connected else tk.DISABLED)
        self.resolution_combo.configure(state="readonly" if connected else tk.DISABLED)
        
        # Update parameter controls
        self.auto_exposure_check.configure(state=state_connected)
        self.wb_check.configure(state=state_connected)
        self.wb_once_btn.configure(state=state_connected)
        self.snapshot_btn.configure(state=state_connected)
        
        # Update exposure controls based on auto exposure setting
        expo_state = tk.DISABLED if connected and self.auto_exposure_var.get() else state_connected
        self.exposure_scale.configure(state=expo_state)
        self.exposure_entry.configure(state=expo_state)
        
        # Always enable gain control
        self.gain_scale.configure(state=state_connected)
        self.gain_entry.configure(state=state_connected)
        
    # Camera callback function
    @staticmethod
    def camera_callback(nEvent, ctx):
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            ctx.process_image(nEvent)
        elif nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
            ctx.update_status("Camera disconnected")
            ctx.disconnect()
            
    def process_image(self, nEvent):
        """Process image data from camera"""
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            try:
                # Pull the image from the camera
                self.hcam.PullImageV4(self.buf, 0, 24, 0, None)
                self.total += 1
                
                # Convert the raw buffer to a numpy array
                frame = np.frombuffer(self.buf, dtype=np.uint8)
                frame = frame.reshape((self.height, self.width, 3))
                
                # Store the current frame (BGR format for OpenCV)
                self.current_frame = frame
                
                # Convert to RGB for display in Tkinter
                if self.root:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.update_video_canvas(frame_rgb)
                    
            except toupcam.HRESULTException as ex:
                self.update_status(f'Pull image failed, hr=0x{ex.hr & 0xffffffff:x}')
        else:
            self.update_status(f'Event callback: {nEvent}')
            
    def update_video_canvas(self, frame):
        """Update the video canvas with the current frame"""
        if not self.root:
            return
            
        # Resize the frame to fit the canvas while maintaining aspect ratio
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet properly sized, use default size
            canvas_width = 640
            canvas_height = 480
            
        # Calculate scaling factor to fit the canvas
        scale_width = canvas_width / frame.shape[1]
        scale_height = canvas_height / frame.shape[0]
        scale = min(scale_width, scale_height)
        
        # Resize the frame
        if scale < 1:
            new_width = int(frame.shape[1] * scale)
            new_height = int(frame.shape[0] * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
        # Convert to PIL Image and then to PhotoImage
        img = Image.fromarray(frame)
        img_tk = ImageTk.PhotoImage(image=img)
        
        # Update canvas
        self.video_canvas.config(width=frame.shape[1], height=frame.shape[0])
        self.video_canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=img_tk)
        self.video_canvas.image = img_tk  # Keep a reference to prevent garbage collection
        
    def list_cameras(self):
        """List all available ToupCam cameras"""
        devices = toupcam.Toupcam.EnumV2()
        if not devices:
            print("No ToupCam cameras found")
            return []
        
        print(f"Found {len(devices)} ToupCam camera(s):")
        for i, dev in enumerate(devices):
            print(f"  {i+1}. {dev.displayname} (Model: {dev.model.name})")
        
        return devices
    
    def connect(self, device_index=0):
        """Connect to a ToupCam camera by index"""
        devices = toupcam.Toupcam.EnumV2()
        if not devices:
            self.update_status("No ToupCam cameras found")
            return False
        
        if device_index >= len(devices):
            self.update_status(f"Invalid device index {device_index}, only {len(devices)} camera(s) available")
            return False
        
        device = devices[device_index]
        self.update_status(f"Connecting to {device.displayname}...")
        
        # Open the camera
        self.hcam = toupcam.Toupcam.Open(device.id)
        if not self.hcam:
            self.update_status("Failed to open camera")
            return False
        
        # Get available resolutions
        if self.root:
            resolutions = []
            for i in range(device.model.preview):
                res = device.model.res[i]
                resolutions.append(f"{res.width} x {res.height}")
                
            self.resolution_combo['values'] = resolutions
            self.resolution_combo.current(0)
        
        # Get camera resolution
        self.width, self.height = self.hcam.get_Size()
        self.update_status(f"Camera resolution: {self.width} x {self.height}")
        
        # Allocate buffer for image data
        bufsize = toupcam.TDIBWIDTHBYTES(self.width * 24) * self.height
        self.update_status(f"Buffer size: {bufsize} bytes")
        self.buf = bytes(bufsize)
        
        # Set some camera parameters for better image quality
        try:
            # Set auto exposure
            self.hcam.put_AutoExpoEnable(self.params['auto_exposure'])
            
            # Set white balance
            self.hcam.put_TempTint(6500, 1000)  # Default temp and tint
            self.hcam.put_AWBAuxRect(0, 0, self.width, self.height)  # Use full frame for AWB
            self.hcam.put_AutoWB(self.params['white_balance'])
            
            # Set gain
            self.hcam.put_ExpoAGain(self.params['gain'])
            
            # Start the camera with callback
            self.hcam.StartPullModeWithCallback(self.camera_callback, self)
            self.running = True
            self.update_status("Camera started successfully")
            
            # Update UI state
            self.update_ui_state(True)
            
            return True
            
        except toupcam.HRESULTException as ex:
            self.update_status(f"Failed to start camera: 0x{ex.hr & 0xffffffff:x}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from the camera"""
        if self.hcam:
            self.hcam.Close()
            self.hcam = None
            self.buf = None
            self.running = False
            self.update_status("Camera disconnected")
            
            # Update UI state
            self.update_ui_state(False)
    
    def run_standalone(self):
        """Run as a standalone application with OpenCV window"""
        if not self.root:  # Only use OpenCV window if not running in Tkinter
            # Create an OpenCV window
            window_name = "ToupCam Live Stream"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            
            print("Press 'q' to quit, 's' to save a snapshot")
            
            try:
                while self.running:
                    if self.current_frame is not None:
                        # Display the frame
                        cv2.imshow(window_name, self.current_frame)
                    
                    key = cv2.waitKey(30) & 0xFF
                    
                    # Check for key presses
                    if key == ord('q'):
                        print("Quitting...")
                        break
                    elif key == ord('s'):
                        # Save a snapshot
                        if self.current_frame is not None:
                            filename = f"toupcam_snapshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
                            cv2.imwrite(filename, self.current_frame)
                            print(f"Snapshot saved as {filename}")
                    
                    # Check if window was closed
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        break
                        
            finally:
                self.disconnect()
                cv2.destroyAllWindows()
    
    def load_calibration(self, calibration_file):
        """Load camera calibration data from a file"""
        try:
            # This is a placeholder for actual calibration loading code
            # In a real implementation, you would load the calibration data
            # from the file and store it in self.calibration_data
            self.update_status(f"Loaded calibration from {calibration_file}")
            return True
        except Exception as e:
            self.update_status(f"Failed to load calibration: {e}")
            return False
    
    def apply_calibration(self, frame):
        """Apply calibration to a frame"""
        if self.calibration_data is None:
            return frame
            
        # This is a placeholder for actual calibration application code
        # In a real implementation, you would apply the calibration data
        # to the frame and return the calibrated frame
        return frame

def main():
    # Create Tkinter root window
    root = tk.Tk()
    root.title("ToupCam CellToolbox Integration")
    root.geometry("1200x700")
    
    # Create the application
    app = ToupCamCellToolbox(root)
    
    # List available cameras
    devices = app.list_cameras()
    if not devices:
        app.update_status("No cameras found. Please connect a camera and restart the application.")
    
    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
