"""
ToupCam Digital Binning Launcher
This script provides a launcher to select digital binning parameters before starting the ToupCam live control.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import ctypes

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
    sys.exit(1)

class BinningLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("ToupCam Digital Binning")
        self.root.geometry("400x550")  # Increased height from 500 to 550
        self.root.resizable(False, False)
        
        # Set icon if available
        try:
            self.root.iconbitmap("camera.ico")
        except:
            pass
        
        # Binning options
        self.binning_options = [
            ("No Binning (1×1)", 0x0001),
            ("2×2 Average", 0x0002),
            ("3×3 Average", 0x0004),
            ("4×4 Average", 0x0008),
            ("2×2 Add", 0x0082),
            ("3×3 Add", 0x0084),
            ("4×4 Add", 0x0088)
        ]
        
        # Default to no binning
        self.binning_var = tk.IntVar(value=0x0001)
        
        # Create UI
        self.create_ui()
        
        # Check for camera
        self.root.after(100, self.check_camera)
    
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="ToupCam Digital Binning Settings", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = (
            "Select the digital binning mode for the camera. Digital binning combines adjacent pixels "
            "in software to improve sensitivity at the cost of resolution.\n\n"
            "Regular binning averages pixels, while 'Add' mode sums them for "
            "better low-light performance."
        )
        desc_label = ttk.Label(
            main_frame, 
            text=desc_text,
            wraplength=360,
            justify="left"
        )
        desc_label.pack(pady=(0, 20), anchor="w")
        
        # Binning support warning (initially hidden)
        self.binning_warning_var = tk.StringVar(value="")
        self.binning_warning_label = ttk.Label(
            main_frame,
            textvariable=self.binning_warning_var,
            foreground="red",
            wraplength=360,
            justify="left"
        )
        self.binning_warning_label.pack(pady=(0, 10), fill="x")
        
        # Binning options frame
        binning_frame = ttk.LabelFrame(main_frame, text="Binning Mode")
        binning_frame.pack(fill="x", pady=(0, 20))
        
        # Binning radio buttons
        self.binning_buttons = []
        for i, (text, value) in enumerate(self.binning_options):
            rb = ttk.Radiobutton(
                binning_frame,
                text=text,
                value=value,
                variable=self.binning_var
            )
            rb.pack(anchor="w", padx=20, pady=3)
            self.binning_buttons.append(rb)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Start button
        start_button = ttk.Button(
            button_frame,
            text="Start Camera",
            command=self.start_camera,
            style="Accent.TButton"
        )
        start_button.pack(side="right", padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.root.destroy
        )
        cancel_button.pack(side="right", padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create a custom style for the accent button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
    def check_camera(self):
        """Check if any ToupCam cameras are available"""
        try:
            print("Checking for ToupCam cameras...")
            
            # Verify DLL is loaded
            if not os.path.exists(toupcam_dll_path):
                error_msg = f"ToupCam DLL not found at: {toupcam_dll_path}"
                print(error_msg)
                self.status_var.set(error_msg)
                messagebox.showerror("DLL Error", error_msg)
                return False
                
            # Try to enumerate cameras
            try:
                devices = toupcam.Toupcam.EnumV2()
                print(f"Found {len(devices) if devices else 0} ToupCam devices")
                
                if not devices:
                    self.status_var.set("No ToupCam cameras found")
                    messagebox.showerror(
                        "Camera Error", 
                        "No ToupCam cameras found. Please connect a camera and restart the application."
                    )
                    return False
                
                # Check camera details
                device = devices[0]  # Use the first camera
                print(f"Camera model: {device.displayname}")
                print(f"Camera flags: 0x{device.model.flag:x}")
                print(f"SDK reports binning supported: {bool(device.model.flag & toupcam.TOUPCAM_FLAG_BINSKIP_SUPPORTED)}")
                
                # Even if the SDK doesn't report binning support, we'll enable it
                # since the official program shows it's supported
                self.status_var.set(f"Camera found: {device.displayname}")
                
                # Add a note if the SDK doesn't report binning support
                if not (device.model.flag & toupcam.TOUPCAM_FLAG_BINSKIP_SUPPORTED):
                    self.binning_warning_var.set(
                        "Note: The SDK reports that this camera doesn't support binning, but "
                        "the official program shows it does. All binning options are enabled."
                    )
                else:
                    self.binning_warning_var.set("")
                
                return True
            except Exception as e:
                error_msg = f"Error enumerating cameras: {str(e)}"
                print(error_msg)
                self.status_var.set(error_msg)
                messagebox.showerror("Camera Error", error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error checking camera: {str(e)}"
            print(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("Camera Error", error_msg)
            return False
    
    def start_camera(self):
        """Start the ToupCam live control with the selected binning mode"""
        binning_mode = self.binning_var.get()
        
        # Save the binning setting to a temporary file
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "binning_settings.txt")
        with open(settings_path, "w") as f:
            f.write(str(binning_mode))
        
        # Start the main application
        self.status_var.set(f"Starting camera with binning mode: {binning_mode}")
        
        # Close this window
        self.root.destroy()
        
        # Start the main application
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toupcam_live_control.py")
        subprocess.Popen([sys.executable, script_path])

def main():
    root = tk.Tk()
    app = BinningLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
