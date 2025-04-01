"""
ToupCam Live Control Launcher with Binning Support
This script launches the ToupCam binning launcher, which allows users to select
binning parameters before starting the main ToupCam live control application.
"""

import sys
import os
import subprocess

def main():
    # Get the path to the binning launcher
    launcher_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toupcam_binning_launcher.py")
    
    # Check if the launcher exists
    if not os.path.exists(launcher_path):
        print(f"Error: Binning launcher not found at {launcher_path}")
        return
    
    # Start the binning launcher
    print("Starting ToupCam binning launcher...")
    subprocess.Popen([sys.executable, launcher_path])

if __name__ == "__main__":
    main()
