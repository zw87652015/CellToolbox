"""
Camera Manager Module
This module handles USB camera initialization, capture, and management.
"""

import cv2
import threading
import time
import numpy as np

class CameraManager:
    """Manages USB camera operations including initialization, capture, and reconnection"""
    
    def __init__(self, camera_index=0, target_fps=30):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.cap = None
        self.frame_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        self.running = False
        self.capture_thread = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.new_frame_available = False
        
        # Camera properties
        self.actual_fps = 0
        self.camera_info = "Not connected"
    
    def start_camera(self):
        """Initialize and start the USB camera"""
        try:
            # Release any existing camera
            if self.cap is not None:
                self.cap.release()
            
            # Open the camera
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                raise Exception(f"Failed to open camera at index {self.camera_index}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for lower latency
            
            # Try to set a reasonable resolution if possible
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Get actual camera properties
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            # Update camera info
            self.camera_info = f"Resolution: {self.frame_width}x{self.frame_height} @ {self.actual_fps:.1f}fps"
            
            # Set running flag
            self.running = True
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.capture_thread.start()
            
            return True, f"Camera {self.camera_index} started successfully"
            
        except Exception as e:
            return False, f"Error starting camera: {str(e)}"
    
    def _capture_frames(self):
        """Capture frames from the camera in a separate thread"""
        frame_interval = 1.0 / self.target_fps
        last_frame_time = time.time()
        
        while self.running and self.cap is not None:
            try:
                current_time = time.time()
                
                # Only capture if enough time has passed
                if current_time - last_frame_time >= frame_interval:
                    ret, frame = self.cap.read()
                    if ret:
                        with self.frame_lock:
                            self.frame_buffer = frame.copy()
                            self.new_frame_available = True
                            self.frame_count += 1
                        last_frame_time = current_time
                    else:
                        # If frame reading fails, wait a bit
                        time.sleep(0.05)
                        continue
                else:
                    # Sleep for a short time if we're ahead of schedule
                    time.sleep(0.005)
                    
            except Exception as e:
                print(f"Error capturing frame: {e}")
                time.sleep(0.1)
    
    def get_frame(self):
        """
        Get the latest frame from the camera
        
        Returns:
            tuple: (success, frame) where success is bool and frame is numpy array
        """
        if not self.running or self.frame_buffer is None:
            return False, None
        
        try:
            with self.frame_lock:
                if self.new_frame_available:
                    frame = self.frame_buffer.copy()
                    self.new_frame_available = False
                    return True, frame
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
        
        if self.capture_thread is not None:
            self.capture_thread.join(timeout=1.0)
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        self.frame_buffer = None
        self.new_frame_available = False
    
    def get_camera_info(self):
        """Get camera information string"""
        return self.camera_info
    
    def get_frame_dimensions(self):
        """Get camera frame dimensions"""
        return self.frame_width, self.frame_height
    
    def is_running(self):
        """Check if camera is running"""
        return self.running and self.cap is not None and self.cap.isOpened()
    
    def get_available_cameras(self, max_cameras=10):
        """
        Get list of available camera indices
        
        Args:
            max_cameras: Maximum number of cameras to check
            
        Returns:
            list: List of available camera indices
        """
        available_cameras = []
        
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        return available_cameras
