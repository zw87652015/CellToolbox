"""
ToupCam Live Stream - Main Application
This is the main entry point for the ToupCam live stream application.
"""

import sys
import os
import tkinter as tk
from toupcam_live import ToupCameraLive
from monitor_utils import get_monitor_info

def main():
    """Main function to start the ToupCam live stream application"""
    # Get monitor information
    monitors = get_monitor_info()
    
    # Create the root window
    root = tk.Tk()
    
    # Position the window on the secondary monitor if available, otherwise on the primary
    if len(monitors) > 1:
        # Find the secondary monitor (first non-primary monitor)
        secondary_monitor = None
        for monitor in monitors:
            if not monitor['is_primary']:
                secondary_monitor = monitor
                break
        
        if secondary_monitor:
            print("Positioning application on secondary monitor")
            # Position the window on the secondary monitor
            x = secondary_monitor.get('work_left', secondary_monitor['left'])
            y = secondary_monitor.get('work_top', secondary_monitor['top'])
            root.geometry(f"+{x}+{y}")
    else:
        print("Only one monitor detected, using primary monitor")
    
    # Create and run the application
    try:
        app = ToupCameraLive(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
