"""
Exposure Control Panel - Standalone Window
This module provides a standalone window for controlling ToupCam exposure settings.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

class ExposureControlPanel:
    """Standalone exposure control panel for ToupCam"""
    
    def __init__(self, camera_manager, parent=None):
        self.camera_manager = camera_manager
        self.parent = parent
        self.window = None
        self.is_open = False
        
        # Control variables
        self.exposure_time_var = tk.IntVar()
        self.exposure_gain_var = tk.IntVar()
        self.auto_exposure_var = tk.BooleanVar()
        
        # Update thread control
        self.update_running = False
        self.update_thread = None
        
        # Get camera ranges
        self.exposure_time_range = (1, 1000000)  # Default range
        self.exposure_gain_range = (100, 1600)   # Default range
        
    def open_panel(self):
        """Open the exposure control panel window"""
        if self.is_open and self.window and self.window.winfo_exists():
            # Window already open, bring to front
            self.window.lift()
            self.window.focus_force()
            return
        
        # Create new window
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("ToupCam Exposure Control")
        self.window.geometry("400x500")
        self.window.resizable(True, True)
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_panel)
        
        self.is_open = True
        
        # Get current camera ranges and values
        self.update_camera_ranges()
        self.update_current_values()
        
        # Create UI
        self.create_ui()
        
        # Start update thread
        self.start_update_thread()
        
    def close_panel(self):
        """Close the exposure control panel"""
        self.is_open = False
        self.stop_update_thread()
        
        if self.window:
            self.window.destroy()
            self.window = None
    
    def update_camera_ranges(self):
        """Update the exposure ranges from camera"""
        if self.camera_manager and self.camera_manager.is_running():
            try:
                self.exposure_time_range = self.camera_manager.get_exposure_time_range()
                self.exposure_gain_range = self.camera_manager.get_exposure_gain_range()
            except:
                pass  # Use default ranges
    
    def update_current_values(self):
        """Update current values from camera"""
        if self.camera_manager and self.camera_manager.is_running():
            try:
                current_exposure = self.camera_manager.get_exposure_time()
                current_gain = self.camera_manager.get_exposure_gain()
                
                self.exposure_time_var.set(current_exposure)
                self.exposure_gain_var.set(current_gain)
            except:
                pass  # Use default values
    
    def create_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="ToupCam Exposure Control", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Auto exposure control
        auto_frame = ttk.LabelFrame(main_frame, text="Auto Exposure", padding="5")
        auto_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_exposure_checkbox = ttk.Checkbutton(
            auto_frame, 
            text="Enable Auto Exposure",
            variable=self.auto_exposure_var,
            command=self.on_auto_exposure_changed
        )
        self.auto_exposure_checkbox.pack(anchor=tk.W)
        
        # Exposure time control
        time_frame = ttk.LabelFrame(main_frame, text="Exposure Time", padding="5")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Exposure time info
        time_info_frame = ttk.Frame(time_frame)
        time_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(time_info_frame, text="Range:").pack(side=tk.LEFT)
        self.time_range_label = ttk.Label(time_info_frame, 
                                         text=f"{self.exposure_time_range[0]} - {self.exposure_time_range[1]} μs")
        self.time_range_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Current exposure time
        current_time_frame = ttk.Frame(time_frame)
        current_time_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(current_time_frame, text="Current:").pack(side=tk.LEFT)
        self.current_time_label = ttk.Label(current_time_frame, text="8333 μs")
        self.current_time_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Exposure time slider
        self.exposure_time_scale = ttk.Scale(
            time_frame,
            from_=self.exposure_time_range[0],
            to=self.exposure_time_range[1],
            orient=tk.HORIZONTAL,
            variable=self.exposure_time_var,
            command=self.on_exposure_time_changed
        )
        self.exposure_time_scale.pack(fill=tk.X, pady=(0, 5))
        
        # Preset exposure time buttons
        preset_time_frame = ttk.Frame(time_frame)
        preset_time_frame.pack(fill=tk.X)
        
        preset_times = [
            ("1ms", 1000),
            ("8.3ms", 8333),
            ("16.7ms", 16667),
            ("33ms", 33333),
            ("100ms", 100000)
        ]
        
        for label, value in preset_times:
            btn = ttk.Button(preset_time_frame, text=label, width=8,
                           command=lambda v=value: self.set_exposure_time_preset(v))
            btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Exposure gain control
        gain_frame = ttk.LabelFrame(main_frame, text="Exposure Gain", padding="5")
        gain_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Gain info
        gain_info_frame = ttk.Frame(gain_frame)
        gain_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(gain_info_frame, text="Range:").pack(side=tk.LEFT)
        self.gain_range_label = ttk.Label(gain_info_frame, 
                                         text=f"{self.exposure_gain_range[0]} - {self.exposure_gain_range[1]}")
        self.gain_range_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Current gain
        current_gain_frame = ttk.Frame(gain_frame)
        current_gain_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(current_gain_frame, text="Current:").pack(side=tk.LEFT)
        self.current_gain_label = ttk.Label(current_gain_frame, text="100")
        self.current_gain_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Gain slider
        self.exposure_gain_scale = ttk.Scale(
            gain_frame,
            from_=self.exposure_gain_range[0],
            to=self.exposure_gain_range[1],
            orient=tk.HORIZONTAL,
            variable=self.exposure_gain_var,
            command=self.on_exposure_gain_changed
        )
        self.exposure_gain_scale.pack(fill=tk.X, pady=(0, 5))
        
        # Preset gain buttons
        preset_gain_frame = ttk.Frame(gain_frame)
        preset_gain_frame.pack(fill=tk.X)
        
        preset_gains = [
            ("1x", 100),
            ("2x", 200),
            ("4x", 400),
            ("8x", 800),
            ("16x", 1600)
        ]
        
        for label, value in preset_gains:
            btn = ttk.Button(preset_gain_frame, text=label, width=8,
                           command=lambda v=value: self.set_exposure_gain_preset(v))
            btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Reset to Default", 
                  command=self.reset_to_default).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Close", 
                  command=self.close_panel).pack(side=tk.RIGHT)
    
    def on_auto_exposure_changed(self):
        """Handle auto exposure checkbox change"""
        if self.camera_manager and self.camera_manager.is_running():
            enabled = self.auto_exposure_var.get()
            self.camera_manager.set_auto_exposure(enabled)
            
            # Enable/disable manual controls
            state = tk.DISABLED if enabled else tk.NORMAL
            self.exposure_time_scale.configure(state=state)
            self.exposure_gain_scale.configure(state=state)
    
    def on_exposure_time_changed(self, value):
        """Handle exposure time slider change"""
        if self.camera_manager and self.camera_manager.is_running():
            exposure_time = int(float(value))
            self.camera_manager.set_exposure_time(exposure_time)
            self.current_time_label.configure(text=f"{exposure_time} μs")
    
    def on_exposure_gain_changed(self, value):
        """Handle exposure gain slider change"""
        if self.camera_manager and self.camera_manager.is_running():
            gain = int(float(value))
            self.camera_manager.set_exposure_gain(gain)
            self.current_gain_label.configure(text=str(gain))
    
    def set_exposure_time_preset(self, value):
        """Set exposure time to preset value"""
        self.exposure_time_var.set(value)
        self.on_exposure_time_changed(value)
    
    def set_exposure_gain_preset(self, value):
        """Set exposure gain to preset value"""
        self.exposure_gain_var.set(value)
        self.on_exposure_gain_changed(value)
    
    def reset_to_default(self):
        """Reset exposure settings to default values"""
        self.auto_exposure_var.set(False)
        self.exposure_time_var.set(8333)  # 8.333ms
        self.exposure_gain_var.set(100)   # 1x gain
        
        if self.camera_manager and self.camera_manager.is_running():
            self.camera_manager.set_auto_exposure(False)
            self.camera_manager.set_exposure_time(8333)
            self.camera_manager.set_exposure_gain(100)
        
        self.on_auto_exposure_changed()
    
    def start_update_thread(self):
        """Start the update thread to sync with camera"""
        if not self.update_running:
            self.update_running = True
            self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
            self.update_thread.start()
    
    def stop_update_thread(self):
        """Stop the update thread"""
        self.update_running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def update_loop(self):
        """Update loop to sync display with camera values"""
        while self.update_running and self.is_open:
            try:
                if self.camera_manager and self.camera_manager.is_running():
                    # Update current values display
                    current_time = self.camera_manager.get_exposure_time()
                    current_gain = self.camera_manager.get_exposure_gain()
                    
                    if self.window and self.window.winfo_exists():
                        self.window.after(0, lambda: self.current_time_label.configure(text=f"{current_time} μs"))
                        self.window.after(0, lambda: self.current_gain_label.configure(text=str(current_gain)))
                
                time.sleep(0.5)  # Update every 500ms
                
            except Exception as e:
                print(f"Error in exposure control update loop: {e}")
                time.sleep(1.0)
