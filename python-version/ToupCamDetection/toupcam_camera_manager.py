"""
ToupCam Camera Manager Module
This module handles ToupCam initialization, capture, and management.
Replaces the USB camera manager with ToupCam SDK integration.
"""

import sys
import os
import ctypes
import threading
import time
import numpy as np

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

class ToupCamCameraManager:
    """Manages ToupCam operations including initialization, capture, and reconnection"""
    
    def __init__(self, camera_index=0, target_fps=30):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.hcam = None
        self.cam_buffer = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.running = False
        self.capture_thread = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.start_time = time.time()
        self.last_frame_time = time.time()
        self.frame_times = []
        self.new_frame_available = False
        
        # Camera properties
        self.actual_fps = 0
        self.camera_info = "Not connected"
        
        # ToupCam specific settings
        self.exposure_time = 8333  # 8.333ms in microseconds (same as simple_toupcam_live.py)
        self.devices = []
        
    def start_camera(self):
        """Initialize and start the ToupCam camera"""
        try:
            # Release any existing camera
            if self.hcam is not None:
                self.hcam.Close()
                self.hcam = None
            
            # Enumerate ToupCam devices
            self.devices = toupcam.Toupcam.EnumV2()
            if len(self.devices) == 0:
                raise Exception("No ToupCam devices found")
            
            if self.camera_index >= len(self.devices):
                raise Exception(f"Camera index {self.camera_index} not available. Found {len(self.devices)} cameras.")
            
            # Open the camera - use None for first camera or device ID for specific camera
            if self.camera_index == 0:
                self.hcam = toupcam.Toupcam.Open(None)  # Open first available camera
            else:
                self.hcam = toupcam.Toupcam.Open(self.devices[self.camera_index].id)
            
            if self.hcam is None:
                raise Exception(f"Failed to open ToupCam at index {self.camera_index}")
            
            # Get camera resolution
            self.frame_width, self.frame_height = self.hcam.get_Size()
            print(f"Camera resolution: {self.frame_width}x{self.frame_height}")
            
            # Set camera properties for optimal performance (same as working implementation)
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BYTEORDER, 0)  # RGB
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_UPSIDE_DOWN, 0)  # Normal orientation
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)  # Minimize frame queue
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_CALLBACK_THREAD, 1)  # Enable dedicated callback thread
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_THREAD_PRIORITY, 2)  # Set high thread priority
            
            # Disable auto exposure
            self.hcam.put_AutoExpoEnable(False)
            
            # Set anti-flicker to 60Hz (for 16.67ms exposure)
            self.hcam.put_HZ(2)  # 2 = 60Hz
            
            # Set exposure time (same as simple_toupcam_live.py)
            self.hcam.put_ExpoTime(self.exposure_time)
            
            # Set other camera options
            self.hcam.put_Brightness(0)
            self.hcam.put_Contrast(0)
            self.hcam.put_Gamma(100)  # 1.0
            
            # Set white balance
            self.hcam.put_TempTint(4796, 1153)  # Temperature 4796, Tint 1153
            
            # Allocate buffer for image data (same as working implementation)
            buffer_size = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(buffer_size)
            
            # Pre-allocate numpy array shape for zero-copy processing
            self.frame_buffer_shape = (self.frame_height, toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3, 3)
            
            # Update camera info
            device_info = self.devices[self.camera_index]
            self.camera_info = f"ToupCam {device_info.displayname} - Resolution: {self.frame_width}x{self.frame_height}"
            
            # Register callback (same as working implementation)
            self.hcam.StartPullModeWithCallback(self._frame_callback, self)
            
            # Set running flag
            self.running = True
            
            return True, f"ToupCam {self.camera_index} started successfully"
            
        except Exception as e:
            return False, f"Error starting ToupCam: {str(e)}"
    
    @staticmethod
    def _frame_callback(nEvent, ctx):
        """Callback function for ToupCam frame events"""
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            current_time = time.time()
            # Calculate latency
            latency = (current_time - ctx.last_frame_time) * 1000  # ms
            ctx.frame_times.append(latency)
            ctx.last_frame_time = current_time
            
            # Calculate FPS every 30 frames (silently - displayed in UI)
            ctx.frame_count += 1
            if ctx.frame_count % 30 == 0:
                elapsed = time.time() - ctx.start_time
                fps = ctx.frame_count / elapsed
                # FPS is displayed in UI, no need to print
                ctx.frame_count = 0
                ctx.start_time = time.time()
                ctx.frame_times = []
            ctx._on_frame_received()
    
    def _on_frame_received(self):
        """Handle frame received from ToupCam - Optimized for minimal latency"""
        if not self.running or self.hcam is None:
            return
        
        try:
            # Pull image from camera (exactly like working implementation)
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            
            # Zero-copy frame processing - use pre-allocated buffer shape
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8).reshape(self.frame_buffer_shape)
            
            # Crop to actual frame width (zero-copy slice)
            frame = frame[:, :self.frame_width, :]
            
            # Minimal locking - just swap buffer pointers
            with self.frame_lock:
                self.frame_buffer = frame  # No copy, just reference
                self.new_frame_available = True
                self.frame_count += 1
                
        except toupcam.HRESULTException as ex:
            print(f"Error pulling image: 0x{ex.hr & 0xffffffff:x}")
        except Exception as e:
            print(f"Error processing ToupCam frame: {e}")
    
    def get_frame(self):
        """
        Get the latest frame from the camera with optimized color conversion
        
        Returns:
            tuple: (success, frame) where success is bool and frame is numpy array
        """
        if not self.running or self.frame_buffer is None:
            return False, None
        
        try:
            with self.frame_lock:
                if self.new_frame_available:
                    # Zero-copy reference to frame buffer
                    frame = self.frame_buffer
                    self.new_frame_available = False
                    
                    # Convert BGR to RGB efficiently (only when frame is actually used)
                    if frame is not None:
                        # Use cv2 for optimized color conversion instead of array slicing
                        import cv2
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        return True, frame_rgb
                    else:
                        return False, None
                else:
                    return False, None
        except Exception as e:
            print(f"Error getting frame: {e}")
            return False, None
    
    def reconnect_camera(self, new_camera_index=None):
        """
        Reconnect to the camera with the specified index
        
        Args:
            new_camera_index: New camera index to connect to (optional)
            
        Returns:
            tuple: (success, message)
        """
        if new_camera_index is not None:
            self.camera_index = new_camera_index
        
        # Stop current camera
        self.stop_camera()
        
        # Wait a moment for cleanup
        time.sleep(0.5)
        
        # Start new camera
        return self.start_camera()
    
    def stop_camera(self):
        """Stop the camera and cleanup resources"""
        self.running = False
        
        if self.hcam is not None:
            try:
                self.hcam.Close()
            except:
                pass
            self.hcam = None
        
        self.frame_buffer = None
        self.new_frame_available = False
        self.cam_buffer = None
    
    def get_camera_info(self):
        """Get camera information string"""
        return self.camera_info
    
    def get_frame_dimensions(self):
        """Get camera frame dimensions"""
        return self.frame_width, self.frame_height
    
    def is_running(self):
        """Check if camera is running"""
        return self.running and self.hcam is not None
    
    def get_available_cameras(self, max_cameras=10):
        """
        Get list of available camera indices
        
        Args:
            max_cameras: Maximum number of cameras to check (ignored for ToupCam)
            
        Returns:
            list: List of available camera indices
        """
        try:
            devices = toupcam.Toupcam.EnumV2()
            return list(range(len(devices)))
        except:
            return []
    
    def get_camera_list(self):
        """
        Get list of available ToupCam devices with their names
        
        Returns:
            list: List of tuples (index, display_name)
        """
        try:
            devices = toupcam.Toupcam.EnumV2()
            return [(i, device.displayname) for i, device in enumerate(devices)]
        except:
            return []
    
    def set_exposure_time(self, exposure_time_us):
        """
        Set camera exposure time
        
        Args:
            exposure_time_us: Exposure time in microseconds
        """
        if self.hcam is not None:
            try:
                self.hcam.put_ExpoTime(exposure_time_us)
                self.exposure_time = exposure_time_us
                return True
            except Exception as e:
                print(f"Error setting exposure time: {e}")
                return False
        return False
    
    def get_exposure_time(self):
        """Get current exposure time in microseconds"""
        if self.hcam is not None:
            try:
                return self.hcam.get_ExpoTime()
            except:
                pass
        return self.exposure_time
    
    def set_auto_exposure(self, enabled):
        """
        Enable or disable auto exposure
        
        Args:
            enabled: True to enable auto exposure, False to disable
        """
        if self.hcam is not None:
            try:
                self.hcam.put_AutoExpoEnable(enabled)
                return True
            except Exception as e:
                print(f"Error setting auto exposure: {e}")
                return False
        return False
    
    def set_exposure_gain(self, gain):
        """
        Set camera exposure gain
        
        Args:
            gain: Gain value (typically 100-1600, where 100 = 1x gain)
        """
        if self.hcam is not None:
            try:
                self.hcam.put_ExpoAGain(gain)
                return True
            except Exception as e:
                print(f"Error setting exposure gain: {e}")
                return False
        return False
    
    def get_exposure_gain(self):
        """Get current exposure gain"""
        if self.hcam is not None:
            try:
                return self.hcam.get_ExpoAGain()
            except:
                pass
        return 100  # Default gain
    
    def get_exposure_gain_range(self):
        """Get the range of supported exposure gain values"""
        if self.hcam is not None:
            try:
                return self.hcam.get_ExpoAGainRange()
            except:
                pass
        return (100, 1600)  # Default range
    
    def get_exposure_time_range(self):
        """Get the range of supported exposure time values in microseconds"""
        if self.hcam is not None:
            try:
                return self.hcam.get_ExpTimeRange()
            except:
                pass
        return (1, 1000000)  # Default range: 1us to 1s
