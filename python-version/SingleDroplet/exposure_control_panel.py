"""
Standalone Exposure Control Panel for ToupCam SingleDroplet Application
Provides real-time exposure time and gain control with preset buttons
"""

import tkinter as tk
from tkinter import ttk
import threading
import time


class ExposureControlPanel:
    """Standalone window for controlling camera exposure parameters"""
    
    def __init__(self, camera_manager):
        """
        Initialize exposure control panel
        
        Args:
            camera_manager: Camera manager instance with exposure control methods
        """
        self.camera_manager = camera_manager
        self.window = None
        self.exposure_var = tk.IntVar()
        self.gain_var = tk.IntVar()
        self.auto_exposure_var = tk.BooleanVar()
        self.update_thread = None
        self.running = False
        
        # Cache for camera ranges
        self.exposure_range = None
        self.gain_range = None
        
    def open_panel(self):
        """Open the exposure control panel window"""
        if self.window and self.window.winfo_exists():
            # Window already exists, just bring it to front
            self.window.lift()
            self.window.focus_force()
            return
            
        # Create new window
        self.window = tk.Toplevel()
        self.window.title("Exposure Control Panel")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        
        # Keep window on top
        self.window.attributes('-topmost', True)
        
        # Setup UI
        self._setup_ui()
        
        # Get camera ranges
        self._get_camera_ranges()
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close_panel)
        
    def close_panel(self):
        """Close the exposure control panel"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
        if self.window:
            self.window.destroy()
            self.window = None
            
    def _setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Auto Exposure Section
        auto_frame = ttk.LabelFrame(main_frame, text="Auto Exposure", padding="5")
        auto_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.auto_checkbox = ttk.Checkbutton(
            auto_frame, 
            text="Enable Auto Exposure",
            variable=self.auto_exposure_var,
            command=self._on_auto_exposure_changed
        )
        self.auto_checkbox.grid(row=0, column=0, sticky=tk.W)
        
        # Exposure Time Section
        exposure_frame = ttk.LabelFrame(main_frame, text="Exposure Time", padding="5")
        exposure_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Exposure time display
        ttk.Label(exposure_frame, text="Current:").grid(row=0, column=0, sticky=tk.W)
        self.exposure_label = ttk.Label(exposure_frame, text="0 μs")
        self.exposure_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Exposure range display
        self.exposure_range_label = ttk.Label(exposure_frame, text="Range: N/A")
        self.exposure_range_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Exposure slider
        self.exposure_scale = ttk.Scale(
            exposure_frame,
            from_=1,
            to=1000000,
            orient=tk.HORIZONTAL,
            variable=self.exposure_var,
            command=self._on_exposure_changed
        )
        self.exposure_scale.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Exposure preset buttons
        preset_frame = ttk.Frame(exposure_frame)
        preset_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Common exposure time presets (in microseconds)
        presets = [
            ("1ms", 1000),
            ("8.3ms", 8333),
            ("16.7ms", 16667),
            ("33ms", 33333),
            ("100ms", 100000)
        ]
        
        for i, (label, value) in enumerate(presets):
            btn = ttk.Button(
                preset_frame,
                text=label,
                command=lambda v=value: self._set_exposure_preset(v),
                width=8
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2)
        
        # Exposure Gain Section
        gain_frame = ttk.LabelFrame(main_frame, text="Exposure Gain", padding="5")
        gain_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Gain display
        ttk.Label(gain_frame, text="Current:").grid(row=0, column=0, sticky=tk.W)
        self.gain_label = ttk.Label(gain_frame, text="100")
        self.gain_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Gain range display
        self.gain_range_label = ttk.Label(gain_frame, text="Range: N/A")
        self.gain_range_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Gain slider
        self.gain_scale = ttk.Scale(
            gain_frame,
            from_=100,
            to=1600,
            orient=tk.HORIZONTAL,
            variable=self.gain_var,
            command=self._on_gain_changed
        )
        self.gain_scale.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Gain preset buttons
        gain_preset_frame = ttk.Frame(gain_frame)
        gain_preset_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Common gain presets
        gain_presets = [
            ("1x", 100),
            ("2x", 200),
            ("4x", 400),
            ("8x", 800),
            ("16x", 1600)
        ]
        
        for i, (label, value) in enumerate(gain_presets):
            btn = ttk.Button(
                gain_preset_frame,
                text=label,
                command=lambda v=value: self._set_gain_preset(v),
                width=8
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text="Initializing...")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Configure column weights
        main_frame.columnconfigure(0, weight=1)
        exposure_frame.columnconfigure(1, weight=1)
        gain_frame.columnconfigure(1, weight=1)
        
    def _get_camera_ranges(self):
        """Get camera exposure and gain ranges"""
        try:
            if hasattr(self.camera_manager, 'get_exposure_time_range'):
                self.exposure_range = self.camera_manager.get_exposure_time_range()
                if self.exposure_range:
                    min_exp, max_exp = self.exposure_range
                    self.exposure_scale.configure(from_=min_exp, to=max_exp)
                    self.exposure_range_label.configure(text=f"Range: {min_exp} - {max_exp} μs")
                    
            if hasattr(self.camera_manager, 'get_exposure_gain_range'):
                self.gain_range = self.camera_manager.get_exposure_gain_range()
                if self.gain_range:
                    min_gain, max_gain = self.gain_range
                    self.gain_scale.configure(from_=min_gain, to=max_gain)
                    self.gain_range_label.configure(text=f"Range: {min_gain} - {max_gain}")
                    
        except Exception as e:
            print(f"Error getting camera ranges: {e}")
            
    def _on_auto_exposure_changed(self):
        """Handle auto exposure checkbox change"""
        try:
            auto_enabled = self.auto_exposure_var.get()
            if hasattr(self.camera_manager, 'hcam') and self.camera_manager.hcam:
                self.camera_manager.hcam.put_AutoExpoEnable(auto_enabled)
                
                # Enable/disable manual controls
                state = 'disabled' if auto_enabled else 'normal'
                self.exposure_scale.configure(state=state)
                self.gain_scale.configure(state=state)
                
                self.status_label.configure(text=f"Auto exposure: {'Enabled' if auto_enabled else 'Disabled'}")
                
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")
            
    def _on_exposure_changed(self, value):
        """Handle exposure time slider change"""
        try:
            exposure_time = int(float(value))
            if hasattr(self.camera_manager, 'hcam') and self.camera_manager.hcam:
                self.camera_manager.hcam.put_ExpoTime(exposure_time)
                self.exposure_label.configure(text=f"{exposure_time} μs")
                self.status_label.configure(text=f"Exposure set to {exposure_time} μs")
                
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")
            
    def _on_gain_changed(self, value):
        """Handle gain slider change"""
        try:
            gain_value = int(float(value))
            if hasattr(self.camera_manager, 'hcam') and self.camera_manager.hcam:
                if hasattr(self.camera_manager.hcam, 'put_ExpoAGain'):
                    self.camera_manager.hcam.put_ExpoAGain(gain_value)
                    self.gain_label.configure(text=str(gain_value))
                    self.status_label.configure(text=f"Gain set to {gain_value}")
                    
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")
            
    def _set_exposure_preset(self, exposure_time):
        """Set exposure time to preset value"""
        self.exposure_var.set(exposure_time)
        self._on_exposure_changed(exposure_time)
        
    def _set_gain_preset(self, gain_value):
        """Set gain to preset value"""
        self.gain_var.set(gain_value)
        self._on_gain_changed(gain_value)
        
    def _update_loop(self):
        """Background thread to sync display with camera values"""
        while self.running:
            try:
                if self.window and self.window.winfo_exists():
                    # Update current values from camera
                    if hasattr(self.camera_manager, 'hcam') and self.camera_manager.hcam:
                        # Get current exposure time
                        try:
                            current_exposure = self.camera_manager.hcam.get_ExpoTime()
                            self.window.after_idle(lambda: self._update_exposure_display(current_exposure))
                        except:
                            pass
                            
                        # Get current auto exposure state
                        try:
                            auto_enabled = self.camera_manager.hcam.get_AutoExpoEnable()
                            self.window.after_idle(lambda: self._update_auto_exposure_display(auto_enabled))
                        except:
                            pass
                            
                        # Get current gain
                        try:
                            if hasattr(self.camera_manager.hcam, 'get_ExpoAGain'):
                                current_gain = self.camera_manager.hcam.get_ExpoAGain()
                                self.window.after_idle(lambda: self._update_gain_display(current_gain))
                        except:
                            pass
                            
                time.sleep(0.5)  # Update every 500ms
                
            except Exception as e:
                print(f"Error in exposure control update loop: {e}")
                break
                
    def _update_exposure_display(self, exposure_time):
        """Update exposure time display (called from main thread)"""
        if self.window and self.window.winfo_exists():
            self.exposure_var.set(exposure_time)
            self.exposure_label.configure(text=f"{exposure_time} μs")
            
    def _update_auto_exposure_display(self, auto_enabled):
        """Update auto exposure display (called from main thread)"""
        if self.window and self.window.winfo_exists():
            self.auto_exposure_var.set(auto_enabled)
            state = 'disabled' if auto_enabled else 'normal'
            self.exposure_scale.configure(state=state)
            self.gain_scale.configure(state=state)
            
    def _update_gain_display(self, gain_value):
        """Update gain display (called from main thread)"""
        if self.window and self.window.winfo_exists():
            self.gain_var.set(gain_value)
            self.gain_label.configure(text=str(gain_value))
