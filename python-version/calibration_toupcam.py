"""
ToupCam Projector-Camera Calibration
This script provides calibration functionality for the ToupCam camera with a projector.
It displays calibration patterns on the projector and detects them with the camera
to establish a coordinate transformation between camera and projector space.
"""

import sys
import os
import ctypes
import time
import threading
import json
import cv2
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime

# Add the toupcam SDK path to the Python path
sdk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'toupcamsdk.20241216', 'python')
sys.path.append(sdk_path)

# Add the DLL directory to the PATH environment variable
dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'toupcamsdk.20241216', 'win', 'x64')
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

class ToupCamProjectorCalibration:
    def __init__(self):
        # Get the screen resolution
        root = tk.Tk()
        self.projector_width = root.winfo_screenwidth()
        self.projector_height = root.winfo_screenheight()
        root.destroy()
        
        print(f"Screen resolution: {self.projector_width}x{self.projector_height}")
        
        # ToupCam camera resolution
        self.camera_width = 2688
        self.camera_height = 1520
        
        # Camera variables
        self.hcam = None
        self.cam_buffer = None
        self.frame_buffer = None
        self.running = False
        
        # Color inversion state
        self.inverted_colors = False
        
        # Camera exposure settings
        self.exposure_time = 8333  # Default: 8.333ms in microseconds
        self.min_exposure = 1000   # 1ms
        self.max_exposure = 100000 # 100ms
        
        # Store screen circle parameters
        scale_x = self.projector_width / 2560
        scale_y = self.projector_height / 1600
        
        # First circle (larger)
        self.screen_circle1_x = int(1000 * scale_x)
        self.screen_circle1_y = int(1200 * scale_y)
        self.screen_circle1_radius = int(80 * min(scale_x, scale_y))
        
        # Second circle (smaller)
        self.screen_circle2_x = int((1000 + 200) * scale_x)  # 200 pixels to the right
        self.screen_circle2_y = int(1200 * scale_y)  # Same y coordinate
        self.screen_circle2_radius = int(40 * min(scale_x, scale_y))
        
        # Initialize calibration parameters
        self.calibration_scale = None
        self.calibration_offset_x = None
        self.calibration_offset_y = None
        self.calibration_rotation = None
        self.fov_screen_corners = None
        
        # Initialize camera
        self.initialize_camera()
        
        # Create UI windows
        self.create_windows()
        
    def initialize_camera(self):
        """Initialize the ToupCam camera"""
        devices = toupcam.Toupcam.EnumV2()
        if not devices:
            print("No ToupCam cameras found")
            sys.exit(1)
        
        device = devices[0]  # Use the first camera
        print(f"Found camera: {device.displayname}")
        
        # Try to open the camera
        try:
            self.hcam = toupcam.Toupcam.Open(device.id)
            if not self.hcam:
                print("Failed to open camera")
                sys.exit(1)
            
            # Get camera properties and verify resolution
            width, height = self.hcam.get_Size()
            print(f"Camera resolution: {width} x {height}")
            
            # Update resolution if different from expected
            if width != self.camera_width or height != self.camera_height:
                print(f"Updating camera resolution from {width}x{height} to {self.camera_width}x{self.camera_height}")
                self.camera_width = width
                self.camera_height = height
            
            # Calculate buffer size
            bufsize = toupcam.TDIBWIDTHBYTES(self.camera_width * 24) * self.camera_height
            self.cam_buffer = bytes(bufsize)
            
            # Create frame buffer for OpenCV
            self.frame_buffer = np.zeros((self.camera_height, self.camera_width, 3), dtype=np.uint8)
            
            # Set camera options for low latency
            try:
                # Set anti-flicker to 60Hz (North America)
                self.hcam.put_HZ(2)  # 0: DC, 1: 50Hz, 2: 60Hz
                
                # Set exposure time to 8.333ms (optimal for 60Hz)
                self.hcam.put_AutoExpoEnable(False)  # Disable auto exposure
                self.hcam.put_ExpoTime(self.exposure_time)  # Use the exposure time variable
                
                # Set other options for low latency
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_NOPACKET_TIMEOUT, 0)  # Disable packet timeout
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimum frame buffer
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_PROCESSMODE, 0)  # Raw mode for lower latency
                self.hcam.put_RealTime(True)  # Enable real-time mode
            except toupcam.HRESULTException as ex:
                print(f"Could not set camera options: 0x{ex.hr & 0xffffffff:x}")
            
            # Start the camera with callback
            self.running = True
            self.hcam.StartPullModeWithCallback(self.camera_callback, self)
            
        except toupcam.HRESULTException as ex:
            print(f"Error initializing camera: 0x{ex.hr & 0xffffffff:x}")
            sys.exit(1)
        
    @staticmethod
    def camera_callback(nEvent, ctx):
        """Static callback function for the camera events"""
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            ctx.process_image()
        elif nEvent == toupcam.TOUPCAM_EVENT_ERROR:
            print("Camera error occurred")
        elif nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
            print("Camera disconnected")
    
    def process_image(self):
        """Process the image received from the camera"""
        if not self.running or not self.hcam:
            return
        
        try:
            # Pull the image from the camera with minimal processing
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Convert the raw buffer to a numpy array
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8)
            
            # Reshape the array to an image format
            frame = frame.reshape((self.camera_height, toupcam.TDIBWIDTHBYTES(self.camera_width * 24) // 3, 3))
            frame = frame[:, :self.camera_width, :]
            
            # Convert BGR to RGB (ToupCam provides BGR by default)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Store the frame
            self.frame_buffer = frame.copy()
            
        except toupcam.HRESULTException as ex:
            print(f"Error pulling image: 0x{ex.hr & 0xffffffff:x}")
        
    def create_windows(self):
        # Create pattern window
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        
        # Create canvas with black background
        self.canvas = tk.Canvas(self.root, 
                              width=self.projector_width,
                              height=self.projector_height,
                              bg='black',
                              highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Draw calibration pattern
        self.draw_calibration_pattern()
        
        # Bind key events for color inversion
        self.root.bind('<KeyPress>', self.handle_key_press)
        
        # Create camera window - sized appropriately for the high resolution
        cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)
        # Scale down for display (1/3 of original size)
        display_width = self.camera_width // 3
        display_height = self.camera_height // 3
        cv2.resizeWindow("Camera View", display_width, display_height)
        
        # Create control window
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Calibration Control")
        self.control_window.geometry("300x350")  # Increased height for exposure controls
        
        # Add exposure control frame
        exposure_frame = ttk.LabelFrame(self.control_window, text="Exposure Control")
        exposure_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Add exposure value label
        self.exposure_value_var = tk.StringVar(value=f"Exposure: {self.exposure_time/1000:.2f} ms")
        exposure_label = ttk.Label(
            exposure_frame,
            textvariable=self.exposure_value_var
        )
        exposure_label.pack(pady=(5,0), padx=5)
        
        # Add exposure slider
        self.exposure_slider = ttk.Scale(
            exposure_frame,
            from_=self.min_exposure,
            to=self.max_exposure,
            orient=tk.HORIZONTAL,
            value=self.exposure_time,
            command=self.update_exposure
        )
        self.exposure_slider.pack(pady=5, padx=5, fill=tk.X)
        
        # Add min/max labels
        exposure_range_frame = ttk.Frame(exposure_frame)
        exposure_range_frame.pack(fill=tk.X, padx=5)
        
        ttk.Label(exposure_range_frame, text=f"{self.min_exposure/1000:.1f} ms").pack(side=tk.LEFT)
        ttk.Label(exposure_range_frame, text=f"{self.max_exposure/1000:.1f} ms").pack(side=tk.RIGHT)
        
        # Add calibrate button
        self.calibrate_button = ttk.Button(
            self.control_window, 
            text="Start Calibration", 
            command=self.start_calibration
        )
        self.calibrate_button.pack(pady=10, padx=10, fill=tk.X)
        
        # Add status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.control_window,
            textvariable=self.status_var,
            wraplength=230
        )
        self.status_label.pack(pady=10, padx=10, fill=tk.X)
        
        # Add close button
        self.close_button = ttk.Button(
            self.control_window, 
            text="Close Program", 
            command=self.cleanup_and_close,
            style='Accent.TButton'
        )
        self.close_button.pack(pady=10, padx=10, fill=tk.X)
        
        # Create accent style for close button
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='red')
        
    def draw_calibration_pattern(self):
        """Draw the calibration pattern with current color settings"""
        # Clear previous pattern
        self.canvas.delete("all")
        
        # Set colors based on inversion state
        bg_color = 'white' if self.inverted_colors else 'black'
        fg_color = 'black' if self.inverted_colors else 'white'
        line_color = 'white' if self.inverted_colors else 'black'
        
        # Set canvas background
        self.canvas.configure(bg=bg_color)
        
        # Draw first circle (larger)
        self.canvas.create_oval(
            self.screen_circle1_x - self.screen_circle1_radius,
            self.screen_circle1_y - self.screen_circle1_radius,
            self.screen_circle1_x + self.screen_circle1_radius,
            self.screen_circle1_y + self.screen_circle1_radius,
            fill=fg_color, outline=fg_color
        )
        
        # Draw second circle (smaller)
        self.canvas.create_oval(
            self.screen_circle2_x - self.screen_circle2_radius,
            self.screen_circle2_y - self.screen_circle2_radius,
            self.screen_circle2_x + self.screen_circle2_radius,
            self.screen_circle2_y + self.screen_circle2_radius,
            fill=fg_color, outline=fg_color
        )
        
        # Add rotation indicator line
        line_length = self.screen_circle1_radius * 0.8
        self.canvas.create_line(
            self.screen_circle1_x, 
            self.screen_circle1_y,
            self.screen_circle1_x + line_length, 
            self.screen_circle1_y,
            fill=line_color, width=2
        )
        
        # Redraw FOV outline if it exists
        if hasattr(self, 'fov_screen_corners') and self.fov_screen_corners:
            for i in range(len(self.fov_screen_corners)):
                start = self.fov_screen_corners[i]
                end = self.fov_screen_corners[(i + 1) % len(self.fov_screen_corners)]
                self.canvas.create_line(start[0], start[1], end[0], end[1],
                                     fill='red', width=2, tags="fov")
    
    def handle_key_press(self, event):
        """Handle key press events"""
        if event.char.upper() == 'C':
            # Toggle color inversion
            self.inverted_colors = not self.inverted_colors
            print(f"Colors {'inverted' if self.inverted_colors else 'reset to default'}")
            
            # Redraw the calibration pattern with new colors
            self.draw_calibration_pattern()
            
            # Update status
            self.status_var.set(f"Colors {'inverted' if self.inverted_colors else 'reset to default'}")
    
    def update_exposure(self, value):
        """Update the camera exposure time"""
        if not self.hcam:
            return
            
        # Convert to integer
        exposure = int(float(value))
        self.exposure_time = exposure
        
        # Update the display
        self.exposure_value_var.set(f"Exposure: {exposure/1000:.2f} ms")
        
        try:
            # Update camera exposure
            self.hcam.put_ExpoTime(exposure)
            print(f"Exposure time set to {exposure/1000:.2f} ms")
        except toupcam.HRESULTException as ex:
            print(f"Error setting exposure: 0x{ex.hr & 0xffffffff:x}")
            
    def detect_circle(self, frame):
        """Detect two white circles in the camera frame"""
        # Flip the frame both horizontally and vertically to correct orientation
        frame = cv2.flip(frame, -1)  # -1 flips both horizontally and vertically
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Resize for display in debug window
        debug_scale = 0.25  # Show at 1/4 size
        debug_width = int(self.camera_width * debug_scale)
        debug_height = int(self.camera_height * debug_scale)
        
        gray_small = cv2.resize(gray, (debug_width, debug_height))
        cv2.imshow("1. Grayscale", gray_small)
        cv2.resizeWindow("1. Grayscale", debug_width, debug_height)
        
        # Try multiple thresholding approaches
        
        # 1. Lower threshold value for simple thresholding
        _, binary1 = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        
        # 2. Adaptive thresholding
        binary2 = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            51,  # Larger block size for high resolution
            -5   # Negative C value to better detect white objects
        )
        
        # Combine both methods
        binary = cv2.bitwise_or(binary1, binary2)
        
        # Optional: Add morphological operations to clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Show all thresholding results for debugging
        binary1_small = cv2.resize(binary1, (debug_width, debug_height))
        cv2.imshow("2a. Simple Threshold", binary1_small)
        cv2.resizeWindow("2a. Simple Threshold", debug_width, debug_height)
        
        binary2_small = cv2.resize(binary2, (debug_width, debug_height))
        cv2.imshow("2b. Adaptive Threshold", binary2_small)
        cv2.resizeWindow("2b. Adaptive Threshold", debug_width, debug_height)
        
        binary_small = cv2.resize(binary, (debug_width, debug_height))
        cv2.imshow("2c. Combined Binary", binary_small)
        cv2.resizeWindow("2c. Combined Binary", debug_width, debug_height)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        result = frame.copy()
        circles_found = []
        
        # Simply use the two largest contours
        for i, contour in enumerate(contours[:2]):
            area = cv2.contourArea(contour)
            
            # Fit circle to contour
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            # Draw the circle and its center
            cv2.circle(result, center, radius, (0, 255, 0), 3)  # Thicker line for visibility
            cv2.circle(result, center, 5, (0, 0, 255), 5)  # Larger center point
            circles_found.append((center, radius))
            
            # Print debug info
            print(f"Circle {i+1}: center={center}, radius={radius}, area={area}")
        
        if len(circles_found) == 2:
            # Sort circles by x-coordinate
            circles_found.sort(key=lambda x: x[0][0])
            return result, circles_found[0][0], circles_found[0][1], circles_found[1][0], circles_found[1][1]
        else:
            print(f"Found {len(circles_found)} circles, need exactly 2")
        
        return result, None, None, None, None
        
    def update_camera_view(self):
        """Update camera view continuously"""
        if self.frame_buffer is not None:
            # Make a copy of the frame buffer to avoid race conditions
            frame = self.frame_buffer.copy()
            
            # Convert RGB to BGR for OpenCV display
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Detect and mark circles
            marked_frame, center1, radius1, center2, radius2 = self.detect_circle(frame)
            
            # Resize for display if needed
            display_frame = cv2.resize(marked_frame, (self.camera_width // 3, self.camera_height // 3))
            cv2.imshow("Camera View", display_frame)
            cv2.waitKey(1)
        
        # Schedule next update
        self.root.after(30, self.update_camera_view)
        
    def start_calibration(self):
        """Triggered when calibration button is clicked"""
        if self.frame_buffer is None:
            self.status_var.set("No camera frame available")
            return
            
        # Make a copy of the frame buffer
        frame = self.frame_buffer.copy()
        
        # Convert RGB to BGR for OpenCV processing
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        marked_frame, center1, radius1, center2, radius2 = self.detect_circle(frame)
        if center1 and center2:
            print("\nCalibration circles recorded:")
            print(f"Circle 1 (larger) - Center: {center1}, Radius: {radius1}")
            print(f"Circle 2 (smaller) - Center: {center2}, Radius: {radius2}")
            print(f"Screen circles - Large: ({self.screen_circle1_x}, {self.screen_circle1_y}), R={self.screen_circle1_radius}")
            print(f"              - Small: ({self.screen_circle2_x}, {self.screen_circle2_y}), R={self.screen_circle2_radius}")
            
            # Calculate scale factor using the distance between circles
            camera_distance = np.sqrt((center2[0] - center1[0])**2 + (center2[1] - center1[1])**2)
            screen_distance = np.sqrt((self.screen_circle2_x - self.screen_circle1_x)**2 + 
                                   (self.screen_circle2_y - self.screen_circle1_y)**2)
            self.calibration_scale = screen_distance / camera_distance
            
            # Calculate rotation angle
            camera_angle = np.arctan2(center2[1] - center1[1], center2[0] - center1[0])
            screen_angle = np.arctan2(self.screen_circle2_y - self.screen_circle1_y,
                                    self.screen_circle2_x - self.screen_circle1_x)
            self.calibration_rotation = screen_angle - camera_angle
            
            # Calculate offset
            self.calibration_offset_x = self.screen_circle1_x - center1[0] * self.calibration_scale
            self.calibration_offset_y = self.screen_circle1_y - center1[1] * self.calibration_scale

            # Calculate FOV corners in camera coordinates
            camera_corners = [
                (0, 0),  # Top-left
                (self.camera_width, 0),  # Top-right
                (self.camera_width, self.camera_height),  # Bottom-right
                (0, self.camera_height)  # Bottom-left
            ]
            
            # Transform corners to screen coordinates
            self.fov_screen_corners = []
            for cx, cy in camera_corners:
                # First apply scale and rotation
                dx = cx - center1[0]
                dy = cy - center1[1]
                
                # Rotate
                rx = dx * np.cos(self.calibration_rotation) - dy * np.sin(self.calibration_rotation)
                ry = dx * np.sin(self.calibration_rotation) + dy * np.cos(self.calibration_rotation)
                
                # Scale and translate
                screen_x = int(rx * self.calibration_scale + self.screen_circle1_x)
                screen_y = int(ry * self.calibration_scale + self.screen_circle1_y)
                self.fov_screen_corners.append((screen_x, screen_y))
            
            # Clear previous FOV outline
            self.canvas.delete("fov")
            
            # Draw new FOV outline on screen
            for i in range(len(self.fov_screen_corners)):
                start = self.fov_screen_corners[i]
                end = self.fov_screen_corners[(i + 1) % len(self.fov_screen_corners)]
                self.canvas.create_line(start[0], start[1], end[0], end[1],
                                     fill='red', width=2, tags="fov")
            
            # Save calibration data to file
            calibration_data = {
                'scale': float(self.calibration_scale),
                'rotation': float(self.calibration_rotation),
                'offset_x': float(self.calibration_offset_x),
                'offset_y': float(self.calibration_offset_y),
                'camera_resolution': {
                    'width': self.camera_width,
                    'height': self.camera_height
                },
                'projector_resolution': {
                    'width': self.projector_width,
                    'height': self.projector_height
                },
                'fov_corners': self.fov_screen_corners,
                'calibration_time': self.get_current_time()
            }
            
            self.save_calibration_data(calibration_data)
            
            print("\nCamera-Screen Transformation Parameters:")
            print(f"  Scale factor: {self.calibration_scale:.3f}")
            print(f"  Offset X: {self.calibration_offset_x:.1f} pixels")
            print(f"  Offset Y: {self.calibration_offset_y:.1f} pixels")
            print(f"  Rotation angle: {np.degrees(self.calibration_rotation):.1f}°")
            print("\nField of View on Screen:")
            print(f"  Top-left: {self.fov_screen_corners[0]}")
            print(f"  Top-right: {self.fov_screen_corners[1]}")
            print(f"  Bottom-right: {self.fov_screen_corners[2]}")
            print(f"  Bottom-left: {self.fov_screen_corners[3]}")
            
            self.status_var.set("Calibration completed successfully!")
            print("\nCalibration data saved successfully!")
        else:
            self.status_var.set("Could not detect both calibration circles clearly. Please adjust the camera or lighting.")
            print("Could not detect both calibration circles clearly. Please adjust the camera or lighting.")
        
        cv2.imshow("Camera View", marked_frame)
        cv2.waitKey(1)
    
    def get_current_time(self):
        """Get current time in ISO format"""
        return datetime.now().isoformat()
    
    def save_calibration_data(self, data):
        """Save calibration data to a JSON file"""
        # Create calibration directory if it doesn't exist
        os.makedirs('calibration', exist_ok=True)
        
        # Save to a timestamped file
        filename = os.path.join('calibration', f'calibration_{data["calibration_time"].replace(":", "-")}.json')
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            
        # Also save to a 'latest' file
        latest_file = os.path.join('calibration', 'latest_calibration.json')
        with open(latest_file, 'w') as f:
            json.dump(data, f, indent=4)
            
    def cleanup_and_close(self):
        """Clean up resources and close the application"""
        self.cleanup()
        self.root.quit()
        
    def cleanup(self):
        """Clean up resources"""
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
        
        cv2.destroyAllWindows()
        
    def run(self):
        """Main loop to run the calibration system"""
        self.update_camera_view()
        self.root.mainloop()
        self.cleanup()

def main():
    calibration = ToupCamProjectorCalibration()
    calibration.run()

if __name__ == "__main__":
    main()
