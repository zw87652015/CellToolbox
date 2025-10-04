#!/usr/bin/env python3
"""
ImageProcessor Main Entry Point
Launches the GUI application for Bayer RAW cell detection
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_app import MainApplication
except ImportError as e:
    print(f"Error importing GUI application: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def check_dependencies():
    """Check if required dependencies are available"""
    required_modules = [
        'numpy', 'opencv-python', 'scikit-image', 
        'matplotlib', 'Pillow', 'PyYAML'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'opencv-python':
                import cv2
            elif module == 'scikit-image':
                import skimage
            elif module == 'Pillow':
                import PIL
            elif module == 'PyYAML':
                import yaml
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"Missing required modules: {', '.join(missing_modules)}\n"
        error_msg += "Please install them using:\n"
        error_msg += "pip install -r requirements.txt"
        
        # Try to show GUI error if tkinter is available
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            messagebox.showerror("Missing Dependencies", error_msg)
            root.destroy()
        except:
            print(error_msg)
        
        return False
    
    return True


def main():
    """Main entry point"""
    print("ImageProcessor - Bayer RAW Cell Detection")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Create and run GUI application
        app = MainApplication()
        print("Starting GUI application...")
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        error_msg = f"Error starting application: {str(e)}"
        print(error_msg)
        
        # Try to show GUI error
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Application Error", error_msg)
            root.destroy()
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
