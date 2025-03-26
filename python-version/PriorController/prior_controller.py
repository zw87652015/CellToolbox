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
        print(f"Attempting to connect to COM{com_port} using DLL: {self.dll_path}")
        ret, response = self.cmd(f"controller.connect {com_port}")
        print(f"Connection response: ret={ret}, response='{response}'")
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
        print("Attempting to get position...")
        ret, response = self.cmd("controller.stage.position.get")
        print(f"Position response: ret={ret}, response='{response}'")
        if ret == 0:
            try:
                # Handle different formats of position data
                # First try to split by space (standard format)
                parts = response.split()
                
                if len(parts) == 2:
                    # Try to parse as standard format with periods as decimal separators
                    try:
                        x, y = map(float, parts)
                        return x, y
                    except ValueError:
                        # If that fails, try to handle comma as decimal separator
                        x = float(parts[0].replace(',', '.'))
                        y = float(parts[1].replace(',', '.'))
                        return x, y
                else:
                    # Try to handle single string with comma as value separator
                    parts = response.split(',')
                    if len(parts) == 2:
                        x = float(parts[0].replace(',', '.'))
                        y = float(parts[1].replace(',', '.'))
                        return x, y
                
                # If we get here, we couldn't parse the position
                print(f"Could not parse position from: '{response}'")
                return None
            except Exception as e:
                print(f"Error parsing position: {str(e)}")
                return None
        return None
    
    def set_position(self, x, y):
        """
        Set the current position as the specified coordinates.
        This essentially redefines the origin of the coordinate system.
        
        Args:
            x (float): X coordinate to set as current position
            y (float): Y coordinate to set as current position
            
        Returns:
            bool: True if command was sent successfully
        """
        print(f"Setting current position as: X={x}, Y={y}")
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
    
    def set_max_speed(self, x_max, y_max):
        """
        Set maximum speed values for X and Y axes in microns/second.
        This is crucial for controlling the actual movement speed.
        
        Args:
            x_max (int): Maximum X speed in microns/second
            y_max (int): Maximum Y speed in microns/second
            
        Returns:
            bool: True if command was sent successfully
        """
        ret, _ = self.cmd(f"controller.stage.maxspeed.set {x_max} {y_max}")
        return ret == 0
    
    def get_max_speed(self):
        """
        Get current maximum speed settings.
        
        Returns:
            tuple: (x_max, y_max) speeds in microns/second or None if error
        """
        ret, response = self.cmd("controller.stage.maxspeed.get")
        
        if ret == 0:
            try:
                parts = response.split()
                if len(parts) == 2:
                    x_max = int(float(parts[0].replace(',', '.')))
                    y_max = int(float(parts[1].replace(',', '.')))
                    return x_max, y_max
                else:
                    # Try comma-separated format
                    parts = response.split(',')
                    if len(parts) == 2:
                        x_max = int(float(parts[0].replace(',', '.')))
                        y_max = int(float(parts[1].replace(',', '.')))
                        return x_max, y_max
            except Exception as e:
                print(f"Error parsing max speed: {str(e)}")
        
        return None
    
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
        print("Attempting to get speed...")
        ret, response = self.cmd("controller.stage.speed.get")
        print(f"Speed response: ret={ret}, response='{response}'")
        
        if ret == 0:
            try:
                # Try to parse as integer
                return int(response)
            except ValueError:
                # Try to handle comma as decimal separator
                try:
                    return int(float(response.replace(',', '.')))
                except ValueError:
                    # Try alternative formats
                    try:
                        # Some controllers return "Speed=X" format
                        if "=" in response:
                            value = response.split("=")[1].strip()
                            return int(float(value.replace(',', '.')))
                    except:
                        pass
                    print(f"Could not parse speed from: '{response}'")
                    return None
        
        # If standard command fails, try alternative commands
        if ret != 0:
            print("Standard speed command failed, trying alternatives...")
            # Try controller.stage.get-speed (used in some Prior models)
            ret, response = self.cmd("controller.stage.get-speed")
            print(f"Alternative speed command response: ret={ret}, response='{response}'")
            
            if ret == 0:
                try:
                    return int(float(response.replace(',', '.')))
                except:
                    pass
        
        return None
    
    def get_acceleration(self):
        """
        Get current acceleration setting.
        
        Returns:
            int: Acceleration percentage or None if error
        """
        print("Attempting to get acceleration...")
        ret, response = self.cmd("controller.stage.accel.get")
        print(f"Acceleration response: ret={ret}, response='{response}'")
        
        if ret == 0:
            try:
                # Try to parse as integer
                return int(response)
            except ValueError:
                # Try to handle comma as decimal separator
                try:
                    return int(float(response.replace(',', '.')))
                except ValueError:
                    # Try alternative formats
                    try:
                        # Some controllers return "Accel=X" format
                        if "=" in response:
                            value = response.split("=")[1].strip()
                            return int(float(value.replace(',', '.')))
                    except:
                        pass
                    print(f"Could not parse acceleration from: '{response}'")
                    return None
        
        # If standard command fails, try alternative commands
        if ret != 0:
            print("Standard acceleration command failed, trying alternatives...")
            # Try controller.stage.get-accel (used in some Prior models)
            ret, response = self.cmd("controller.stage.get-accel")
            print(f"Alternative acceleration command response: ret={ret}, response='{response}'")
            
            if ret == 0:
                try:
                    return int(float(response.replace(',', '.')))
                except:
                    pass
        
        return None
    
    def get_controller_info(self):
        """
        Get controller information.
        
        Returns:
            dict: Controller information or None if error
        """
        print("Attempting to get controller info...")
        ret, response = self.cmd("controller.info.get")
        print(f"Controller info response: ret={ret}, response='{response}'")
        
        # If the standard command fails, try alternative commands
        if ret != 0:
            print("Standard info command failed, trying alternatives...")
            # Try controller.get-info (used in some Prior models)
            ret, response = self.cmd("controller.get-info")
            print(f"Alternative info command response: ret={ret}, response='{response}'")
            
            if ret != 0:
                # Try controller.version.get
                ret, response = self.cmd("controller.version.get")
                print(f"Version command response: ret={ret}, response='{response}'")
        
        if ret == 0:
            return response
        return None
    
    def find_limits(self):
        """
        Find the limits of the stage by moving to the limits in each direction.
        
        Returns:
            tuple: ((x_min, x_max), (y_min, y_max)) or None if error
        """
        print("Starting limit finding process...")
        
        # Check if we're connected
        if not self.connected:
            print("Not connected to controller")
            return None
        
        try:
            # First, try to get the limits directly from the controller
            print("Attempting to get limits directly...")
            ret, response = self.cmd("controller.stage.limits.get")
            print(f"Limits response: ret={ret}, response='{response}'")
            
            if ret == 0:
                try:
                    # Parse the response - format might vary by controller
                    parts = response.split()
                    if len(parts) >= 4:
                        x_min = float(parts[0].replace(',', '.'))
                        x_max = float(parts[1].replace(',', '.'))
                        y_min = float(parts[2].replace(',', '.'))
                        y_max = float(parts[3].replace(',', '.'))
                        return ((x_min, x_max), (y_min, y_max))
                except Exception as e:
                    print(f"Error parsing limits: {str(e)}")
            
            # If direct method fails, try to find limits by movement
            print("Direct limit detection failed, attempting to find limits by movement...")
            
            # Store original position to return to
            original_pos = self.get_position()
            if original_pos is None:
                print("Could not get current position")
                return None
            
            # Set a slow speed for safety
            original_speed = self.get_speed()
            self.set_speed(20)  # 20% speed for safety
            
            # Get current position as a starting reference
            current_pos = self.get_position()
            if current_pos is None:
                print("Could not get current position")
                return None
            
            print(f"Starting position: X={current_pos[0]}, Y={current_pos[1]}")
            
            # Try a simpler approach - make small movements in each direction
            # and see how far we can go before hitting limits
            
            # Define step size and max steps
            STEP_SIZE = 1000  # 1mm steps
            MAX_STEPS = 100   # Maximum 100 steps (10cm) in each direction
            
            # Find X minimum (left limit)
            print("Finding X minimum (left limit)...")
            x_min = self.find_limit_in_direction('left', current_pos, STEP_SIZE, MAX_STEPS)
            if x_min is None:
                print("Could not find X minimum")
                # Restore original speed and position
                if original_speed is not None:
                    self.set_speed(original_speed)
                self.move_to(original_pos[0], original_pos[1])
                return None
            
            # Find X maximum (right limit)
            print("Finding X maximum (right limit)...")
            x_max = self.find_limit_in_direction('right', current_pos, STEP_SIZE, MAX_STEPS)
            if x_max is None:
                print("Could not find X maximum")
                # Restore original speed and position
                if original_speed is not None:
                    self.set_speed(original_speed)
                self.move_to(original_pos[0], original_pos[1])
                return None
            
            # Find Y minimum (bottom limit)
            print("Finding Y minimum (bottom limit)...")
            y_min = self.find_limit_in_direction('bottom', current_pos, STEP_SIZE, MAX_STEPS)
            if y_min is None:
                print("Could not find Y minimum")
                # Restore original speed and position
                if original_speed is not None:
                    self.set_speed(original_speed)
                self.move_to(original_pos[0], original_pos[1])
                return None
            
            # Find Y maximum (top limit)
            print("Finding Y maximum (top limit)...")
            y_max = self.find_limit_in_direction('top', current_pos, STEP_SIZE, MAX_STEPS)
            if y_max is None:
                print("Could not find Y maximum")
                # Restore original speed and position
                if original_speed is not None:
                    self.set_speed(original_speed)
                self.move_to(original_pos[0], original_pos[1])
                return None
            
            # Restore original speed
            if original_speed is not None:
                self.set_speed(original_speed)
            
            # Return to original position
            self.move_to(original_pos[0], original_pos[1])
            
            print(f"Found limits: X: {x_min} to {x_max}, Y: {y_min} to {y_max}")
            return ((x_min, x_max), (y_min, y_max))
            
        except Exception as e:
            print(f"Error finding limits: {str(e)}")
            return None
    
    def find_limit_in_direction(self, direction, start_pos, step_size, max_steps):
        """
        Find limit in a specific direction by making incremental moves.
        
        Args:
            direction (str): One of 'left', 'right', 'top', 'bottom'
            start_pos (tuple): Starting position (x, y)
            step_size (float): Step size in microns
            max_steps (int): Maximum number of steps to try
            
        Returns:
            float: Limit position or None if error
        """
        print(f"Finding limit in {direction} direction...")
        
        # Get starting position
        x, y = start_pos
        
        # Track the last successful position
        last_pos = (x, y)
        
        for step in range(max_steps):
            # Calculate new position based on direction
            if direction == 'left':
                new_x = x - step_size
                new_y = y
            elif direction == 'right':
                new_x = x + step_size
                new_y = y
            elif direction == 'top':
                new_x = x
                new_y = y + step_size
            elif direction == 'bottom':
                new_x = x
                new_y = y - step_size
            else:
                print(f"Invalid direction: {direction}")
                return None
            
            # Try to move to new position
            print(f"Step {step+1}: Moving to X={new_x}, Y={new_y}")
            success = self.move_to(new_x, new_y)
            
            # Wait for movement to complete
            time.sleep(0.5)
            
            # Get current position
            current_pos = self.get_position()
            if current_pos is None:
                print("Could not get current position")
                return None
            
            print(f"Current position: X={current_pos[0]}, Y={current_pos[1]}")
            
            # Check if we've hit a limit
            if direction == 'left' or direction == 'right':
                # Check if X position hasn't changed much
                if abs(current_pos[0] - last_pos[0]) < (step_size * 0.5):
                    print(f"Hit limit in {direction} direction at X={current_pos[0]}")
                    return current_pos[0]
            else:
                # Check if Y position hasn't changed much
                if abs(current_pos[1] - last_pos[1]) < (step_size * 0.5):
                    print(f"Hit limit in {direction} direction at Y={current_pos[1]}")
                    return current_pos[1]
            
            # Update last successful position
            last_pos = current_pos
            
            # Update x, y for next iteration
            x, y = current_pos
        
        # If we've reached max steps without finding a limit, use the last position
        print(f"Reached maximum steps without finding limit in {direction} direction")
        if direction == 'left' or direction == 'right':
            return last_pos[0]
        else:
            return last_pos[1]
    
    def move_to_limit(self, direction):
        """
        Move to a limit in the specified direction.
        
        Args:
            direction (str): One of 'left', 'right', 'top', 'bottom'
            
        Returns:
            bool: True if command was sent successfully
        """
        print(f"Moving to {direction} limit...")
        
        # Instead of using specialized limit commands, use large movements
        # in the specified direction that will reach the limit
        
        # First get current position
        current_pos = self.get_position()
        if current_pos is None:
            print("Could not get current position")
            return False
        
        # Use large values that will exceed the stage limits
        # The stage will stop automatically at the physical limit
        LARGE_MOVE = 1000000  # 1 million microns = 1 meter (should exceed any stage limit)
        
        direction = direction.lower()
        if direction == 'left':
            # Move far to the left (negative X)
            ret = self.move_to(current_pos[0] - LARGE_MOVE, current_pos[1])
        elif direction == 'right':
            # Move far to the right (positive X)
            ret = self.move_to(current_pos[0] + LARGE_MOVE, current_pos[1])
        elif direction == 'top':
            # Move far to the top (positive Y)
            ret = self.move_to(current_pos[0], current_pos[1] + LARGE_MOVE)
        elif direction == 'bottom':
            # Move far to the bottom (negative Y)
            ret = self.move_to(current_pos[0], current_pos[1] - LARGE_MOVE)
        else:
            print(f"Invalid direction: {direction}")
            return False
        
        # Wait for movement to complete
        time.sleep(5)  # Give more time for the stage to reach the limit
        
        return ret
    
    def move_to_center(self):
        """
        Move to the center of the stage based on the limits.
        
        Returns:
            bool: True if successful
        """
        limits = self.find_limits()
        if limits is None:
            print("Could not find limits")
            return False
        
        (x_min, x_max), (y_min, y_max) = limits
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        print(f"Moving to center position: X={x_center}, Y={y_center}")
        return self.move_to(x_center, y_center)
    
    def initialize(self):
        """
        Initialize the stage by finding limits and moving to center.
        
        Returns:
            tuple: ((x_min, x_max), (y_min, y_max)) or None if error
        """
        if not self.connected:
            print("Not connected to controller")
            return None
        
        # Find limits
        limits = self.find_limits()
        if limits is None:
            return None
        
        # Move to center
        self.move_to_center()
        
        return limits
    
    def __del__(self):
        """Clean up resources when object is deleted."""
        try:
            self.close()
        except:
            pass
