"""
ToupCam Path Checker
This script checks if the ToupCam SDK paths are correct and if the DLL can be loaded.
"""

import os
import sys
import ctypes

def check_paths():
    print("Checking ToupCam SDK paths...")
    
    # Check SDK path
    sdk_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'toupcamsdk.20241216', 'python')
    print(f"SDK path: {sdk_path}")
    print(f"SDK path exists: {os.path.exists(sdk_path)}")
    
    # Check DLL path
    dll_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'toupcamsdk.20241216', 'win', 'x64')
    print(f"DLL path: {dll_path}")
    print(f"DLL path exists: {os.path.exists(dll_path)}")
    
    # Check DLL file
    toupcam_dll_path = os.path.join(dll_path, 'toupcam.dll')
    print(f"DLL file: {toupcam_dll_path}")
    print(f"DLL file exists: {os.path.exists(toupcam_dll_path)}")
    
    # Try to load the DLL
    if os.path.exists(toupcam_dll_path):
        try:
            toupcam_dll = ctypes.WinDLL(toupcam_dll_path)
            print(f"Successfully loaded ToupCam DLL from: {toupcam_dll_path}")
        except Exception as e:
            print(f"Error loading ToupCam DLL: {e}")
    else:
        print(f"ToupCam DLL not found at: {toupcam_dll_path}")
    
    # Check if toupcam module can be imported
    sys.path.append(sdk_path)
    try:
        import toupcam
        print(f"Successfully imported toupcam module from: {sdk_path}")
    except ImportError as e:
        print(f"Error importing toupcam module: {e}")
    
    # List all files in the SDK directory
    if os.path.exists(sdk_path):
        print("\nFiles in SDK directory:")
        for file in os.listdir(sdk_path):
            print(f"  - {file}")
    
    # List all files in the DLL directory
    if os.path.exists(dll_path):
        print("\nFiles in DLL directory:")
        for file in os.listdir(dll_path):
            print(f"  - {file}")
    
    # Check if the toupcam module is in the correct location
    toupcam_py_path = os.path.join(sdk_path, 'toupcam.py')
    print(f"\nToupcam.py exists: {os.path.exists(toupcam_py_path)}")

if __name__ == "__main__":
    check_paths()
