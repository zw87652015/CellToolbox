"""
SingleDroplet Launcher
---------------------
Simple launcher for the SingleDroplet cell detection application.
"""

import os
import sys
import subprocess

def main():
    """Launch the SingleDroplet application"""
    # Get the path to the single_droplet_detection.py script
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              "single_droplet_detection.py")
    
    # Check if the script exists
    if not os.path.exists(script_path):
        print(f"Error: Could not find {script_path}")
        return
    
    # Launch the script
    print("Starting SingleDroplet cell detection application...")
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running SingleDroplet application: {e}")
    except KeyboardInterrupt:
        print("Application terminated by user")

if __name__ == "__main__":
    main()
