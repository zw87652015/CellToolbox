"""
Prior Controller Module
----------------------
This module provides a Python interface to the Prior Scientific SDK for controlling
motorized stages and platforms.
"""

import os
import sys
import time
from ctypes import WinDLL, create_string_buffer

class PriorStageController:
    """
    Class for controlling Prior Scientific motorized stages through the SDK.
    """
    def __init__(self, dll_path=None):
        """
        Initialize the Prior Stage Controller.
        
        Args:
            dll_path: Path to the PriorScientificSDK.dll file
        """
        # Find DLL
        if dll_path is None:
            # Try to find DLL in common locations
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x64", "PriorScientificSDK.dll")
            
            if not os.path.exists(dll_path):
                # Try x86 folder if x64 doesn't exist
                dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x86", "PriorScientificSDK.dll")
            
            # Additional fallback paths
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "DisTab", "PriorSDK 1.9.2", "PriorScientificSDK.dll")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    dll_path = path
                    break
            
            if not os.path.exists(dll_path):
                raise RuntimeError("Could not find PriorScientificSDK.dll. Please specify the path.")
        
        # Load DLL
        if os.path.exists(dll_path):
            self.sdk = WinDLL(dll_path)
            self.dll_path = dll_path
        else:
            raise RuntimeError(f"DLL could not be loaded from {dll_path}")
        
        # Initialize
        self.rx = create_string_buffer(1000)
        ret = self.sdk.PriorScientificSDK_Initialise()
        if ret:
            raise RuntimeError(f"Error initialising SDK: {ret}")
        
        # Create session
        self.session_id = self.sdk.PriorScientificSDK_OpenNewSession()
        if self.session_id < 0:
            raise RuntimeError(f"Error creating session: {self.session_id}")
        
        self.connected = False
        
        # Get SDK version
        ret = self.sdk.PriorScientificSDK_Version(self.rx)
        self.sdk_version = self.rx.value.decode() if ret == 0 else "Unknown"
    
    def cmd(self, msg):
        """
        Send a command to the controller and get the response.
        
        Args:
            msg (str): Command to send
            
        Returns:
            tuple: (return code, response string)
        """
        ret = self.sdk.PriorScientificSDK_cmd(
            self.session_id, create_string_buffer(msg.encode()), self.rx
        )
        response = self.rx.value.decode()
        return ret, response
    
    def connect(self, com_port):
        """
        Connect to the controller.
        
        Args:
            com_port (int): COM port number
            
        Returns:
            bool: True if connection successful
        """
        ret, response = self.cmd(f"controller.connect {com_port}")
        if ret == 0:
            self.connected = True
            return True
        return False
    
    def disconnect(self):
        """
        Disconnect from the controller.
        
        Returns:
            bool: True if disconnection successful
        """
        if self.connected:
            ret, _ = self.cmd("controller.disconnect")
            self.connected = False
            return ret == 0
        return True
    
    def close(self):
        """
        Close the session and clean up resources.
        """
        if self.connected:
            self.disconnect()
        self.sdk.PriorScientificSDK_CloseSession(self.session_id)
    
    def get_position(self):
        """
        Get current XY position.
        
        Returns:
            tuple: (x, y) position in microns or None if error
        """
        ret, response = self.cmd("controller.stage.position.get")
        if ret == 0:
            try:
                x, y = map(float, response.split())
                return x, y
            except:
                return None
        return None
    
    def set_position(self, x, y):
        """
        Set current position as x, y.
        
        Args:
            x (float): X position in microns
            y (float): Y position in microns
            
        Returns:
            bool: True if successful
        """
        ret, _ = self.cmd(f"controller.stage.position.set {x} {y}")
        return ret == 0
    
    def move_to(self, x, y):
        """
        Move to absolute position.
        
        Args:
            x (float): X position in microns
            y (float): Y position in microns
            
        Returns:
            bool: True if command was sent successfully
        """
        ret, _ = self.cmd(f"controller.stage.goto-position {x} {y}")
        return ret == 0
    
    def move_relative(self, dx, dy):
        """
        Move by relative amount.
        
        Args:
            dx (float): X displacement in microns
            dy (float): Y displacement in microns
            
        Returns:
            bool: True if command was sent successfully
        """
        ret, _ = self.cmd(f"controller.stage.move-relative {dx} {dy}")
        return ret == 0
    
    def set_velocity(self, vx, vy):
        """
        Set velocity for movement.
        
        Args:
            vx (float): X velocity in microns/second
            vy (float): Y velocity in microns/second
            
        Returns:
            bool: True if command was sent successfully
        """
        ret, _ = self.cmd(f"controller.stage.move-at-velocity {vx} {vy}")
        return ret == 0
    
    def stop(self):
        """
        Stop all movement.
        
        Returns:
            bool: True if stop command was sent successfully
        """
        return self.set_velocity(0, 0)
    
    def is_busy(self):
        """
        Check if stage is busy.
        
        Returns:
            bool: True if stage is busy
        """
        ret, response = self.cmd("controller.stage.busy.get")
        return ret == 0 and response == "1"
    
    def wait_until_idle(self, timeout=30, check_interval=0.1):
        """
        Wait until stage stops moving.
        
        Args:
            timeout (float): Maximum time to wait in seconds
            check_interval (float): Time between checks in seconds
            
        Returns:
            bool: True if stage became idle within timeout
        """
        start_time = time.time()
        while self.is_busy():
            time.sleep(check_interval)
            if time.time() - start_time > timeout:
                return False
        return True
    
    def set_speed(self, speed_percent):
        """
        Set speed as percentage of maximum.
        
        Args:
            speed_percent (int): Speed percentage (0-100)
            
        Returns:
            bool: True if command was sent successfully
        """
        ret, _ = self.cmd(f"controller.stage.speed.set {speed_percent}")
        return ret == 0
    
    def set_acceleration(self, accel_percent):
        """
        Set acceleration as percentage of maximum.
        
        Args:
            accel_percent (int): Acceleration percentage (0-100)
            
        Returns:
            bool: True if command was sent successfully
        """
        ret, _ = self.cmd(f"controller.stage.accel.set {accel_percent}")
        return ret == 0
    
    def get_speed(self):
        """
        Get current speed setting.
        
        Returns:
            int: Speed percentage or None if error
        """
        ret, response = self.cmd("controller.stage.speed.get")
        if ret == 0:
            try:
                return int(response)
            except:
                return None
        return None
    
    def get_acceleration(self):
        """
        Get current acceleration setting.
        
        Returns:
            int: Acceleration percentage or None if error
        """
        ret, response = self.cmd("controller.stage.accel.get")
        if ret == 0:
            try:
                return int(response)
            except:
                return None
        return None
    
    def get_controller_info(self):
        """
        Get controller information.
        
        Returns:
            dict: Controller information or None if error
        """
        ret, response = self.cmd("controller.info.get")
        if ret == 0:
            return response
        return None
    
    def __del__(self):
        """Clean up resources when object is deleted."""
        try:
            self.close()
        except:
            pass
