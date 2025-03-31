"""
ToupCam Simple Connection Test
This script tests the connection to a ToupCam camera and displays basic information.
"""

import sys
import os
import ctypes
import time

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

def list_cameras():
    """List all available ToupCam cameras and their details"""
    devices = toupcam.Toupcam.EnumV2()
    if not devices:
        print("No ToupCam cameras found")
        return []
    
    print(f"\nFound {len(devices)} ToupCam camera(s):")
    for i, dev in enumerate(devices):
        print(f"\nCamera {i+1}: {dev.displayname}")
        print(f"  Model: {dev.model.name}")
        print(f"  ID: {dev.id}")
        print(f"  Flag: 0x{dev.model.flag:x}")
        
        # Print camera capabilities
        flags = []
        if dev.model.flag & toupcam.TOUPCAM_FLAG_USB30:
            flags.append("USB 3.0")
        if dev.model.flag & toupcam.TOUPCAM_FLAG_USB30_OVER_USB20:
            flags.append("USB 3.0 over USB 2.0")
        if dev.model.flag & toupcam.TOUPCAM_FLAG_MONO:
            flags.append("Monochrome")
        if dev.model.flag & toupcam.TOUPCAM_FLAG_CMOS:
            flags.append("CMOS Sensor")
        if dev.model.flag & toupcam.TOUPCAM_FLAG_CCD_PROGRESSIVE:
            flags.append("Progressive CCD")
        if dev.model.flag & toupcam.TOUPCAM_FLAG_CCD_INTERLACED:
            flags.append("Interlaced CCD")
        
        print(f"  Capabilities: {', '.join(flags) if flags else 'None'}")
        print(f"  Max Speed: {dev.model.maxspeed}")
        print(f"  Preview Resolutions: {dev.model.preview}")
        print(f"  Still Resolutions: {dev.model.still}")
        print(f"  Pixel Size: {dev.model.xpixsz}x{dev.model.ypixsz} um")
        
        print("  Available Resolutions:")
        for j in range(dev.model.preview):
            res = dev.model.res[j]
            print(f"    {j+1}: {res.width} x {res.height}")
    
    return devices

def test_camera_connection(device_index=0):
    """Test connection to a camera without starting image streaming"""
    devices = toupcam.Toupcam.EnumV2()
    if not devices:
        print("No ToupCam cameras found")
        return False
    
    if device_index >= len(devices):
        print(f"Invalid device index {device_index}, only {len(devices)} camera(s) available")
        return False
    
    device = devices[device_index]
    print(f"\nTesting connection to {device.displayname}...")
    
    # Try to open the camera
    hcam = None
    try:
        hcam = toupcam.Toupcam.Open(device.id)
        if not hcam:
            print("Failed to open camera")
            return False
        
        print("Successfully opened camera connection")
        
        # Get camera properties
        try:
            width, height = hcam.get_Size()
            print(f"Current resolution: {width} x {height}")
            
            # Get exposure range - handle different return value formats
            try:
                exp_range = hcam.get_ExpTimeRange()
                if isinstance(exp_range, tuple):
                    if len(exp_range) >= 2:
                        print(f"Exposure time range: {exp_range[0]} - {exp_range[1]} us")
                    else:
                        print(f"Exposure time range: {exp_range}")
                else:
                    print(f"Exposure time range: {exp_range}")
            except toupcam.HRESULTException as ex:
                print(f"Could not get exposure range: 0x{ex.hr & 0xffffffff:x}")
            
            # Get gain range - handle different return value formats
            try:
                gain_range = hcam.get_ExpoAGainRange()
                if isinstance(gain_range, tuple):
                    if len(gain_range) >= 2:
                        print(f"Gain range: {gain_range[0]} - {gain_range[1]}")
                    else:
                        print(f"Gain range: {gain_range}")
                else:
                    print(f"Gain range: {gain_range}")
            except toupcam.HRESULTException as ex:
                print(f"Could not get gain range: 0x{ex.hr & 0xffffffff:x}")
            
            # Get current exposure
            try:
                auto_expo = hcam.get_AutoExpoEnable()
                print(f"Auto exposure: {'Enabled' if auto_expo else 'Disabled'}")
                
                if not auto_expo:
                    expo_time = hcam.get_ExpoTime()
                    print(f"Current exposure time: {expo_time} us")
            except toupcam.HRESULTException as ex:
                print(f"Could not get exposure settings: 0x{ex.hr & 0xffffffff:x}")
            
            # Get current gain
            try:
                gain = hcam.get_ExpoAGain()
                print(f"Current gain: {gain}")
            except toupcam.HRESULTException as ex:
                print(f"Could not get gain: 0x{ex.hr & 0xffffffff:x}")
            
            # Try to get temperature (if supported)
            try:
                temp = hcam.get_Temperature()
                print(f"Sensor temperature: {temp/10.0} C")
            except toupcam.HRESULTException:
                print("Temperature reading not supported by this camera")
            
            # Try to get some basic options
            print("\nTesting basic camera options:")
            try:
                # Test a few options that are likely to be available
                for option_id in range(0x01, 0x10):  # Test options 1-15
                    try:
                        value = hcam.get_Option(option_id)
                        print(f"  Option 0x{option_id:02x}: {value}")
                    except toupcam.HRESULTException:
                        pass  # Skip options that aren't supported
            except Exception as e:
                print(f"Error testing options: {e}")
            
            return True
            
        except toupcam.HRESULTException as ex:
            print(f"Error getting camera properties: 0x{ex.hr & 0xffffffff:x}")
            return False
            
    except toupcam.HRESULTException as ex:
        print(f"Error opening camera: 0x{ex.hr & 0xffffffff:x}")
        return False
        
    finally:
        # Close the camera
        if hcam:
            hcam.Close()
            print("Camera connection closed")

def main():
    print("ToupCam Simple Connection Test")
    print("==============================")
    print(f"SDK Version: {toupcam.Toupcam.Version()}")
    
    # List available cameras
    devices = list_cameras()
    if not devices:
        return
    
    # Test connection to the first camera
    test_camera_connection(0)
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
