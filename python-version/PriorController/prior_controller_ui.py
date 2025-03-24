"""
Prior Controller UI
------------------
A user-friendly interface for controlling Prior Scientific motorized stages.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import threading
import time

# Add parent directory to path to find prior_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PriorController.prior_controller import PriorStageController

class PriorControllerUI:
    """User interface for controlling Prior Scientific motorized stages."""
    
    def __init__(self, root):
        """
        Initialize the UI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Prior Stage Controller")
        self.root.geometry("600x500")
        self.root.minsize(600, 500)
        
        # Set style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        self.style.configure("TLabel", padding=3)
        self.style.configure("TFrame", padding=5)
        
        # Controller instance (will be created when connecting)
        self.controller = None
        self.connected = False
        
        # Variables for UI elements
        self.com_port = StringVar(value="3")
        self.x_pos = StringVar(value="0.0")
        self.y_pos = StringVar(value="0.0")
        self.step_size = StringVar(value="100.0")
        self.speed = StringVar(value="50")
        self.accel = StringVar(value="50")
        self.status = StringVar(value="Not connected")
        self.position_display = StringVar(value="X: 0.0, Y: 0.0")
        
        # Create the UI elements
        self.create_ui()
        
        # Update position display periodically when connected
        self.position_update_running = False
        self.update_thread = None
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        """Create the UI elements."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection")
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(conn_frame, textvariable=self.com_port, width=5).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Add initialization button
        self.init_btn = ttk.Button(conn_frame, text="Initialize Stage", command=self.initialize_stage)
        self.init_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.status).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(status_frame, text="Position:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.position_display).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Position control tab
        pos_frame = ttk.Frame(notebook)
        notebook.add(pos_frame, text="Position Control")
        
        # Absolute position control
        abs_frame = ttk.LabelFrame(pos_frame, text="Absolute Position")
        abs_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(abs_frame, text="X (µm):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.x_entry = ttk.Entry(abs_frame, textvariable=self.x_pos, width=10)
        self.x_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(abs_frame, text="Y (µm):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.y_entry = ttk.Entry(abs_frame, textvariable=self.y_pos, width=10)
        self.y_entry.grid(row=0, column=3, padx=5, pady=5)
        
        btn_frame = ttk.Frame(abs_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Move To", command=self.move_to).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Get Position", command=self.get_pos).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Set As Origin", command=self.set_origin).pack(side=tk.LEFT, padx=5)
        
        # Relative movement
        rel_frame = ttk.LabelFrame(pos_frame, text="Relative Movement")
        rel_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Step size control
        step_frame = ttk.Frame(rel_frame)
        step_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(step_frame, text="Step Size (µm):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(step_frame, textvariable=self.step_size, width=10).pack(side=tk.LEFT, padx=5)
        
        # Movement buttons in a grid
        move_frame = ttk.Frame(rel_frame)
        move_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a 3x3 grid of buttons
        # Top row
        ttk.Button(move_frame, text="↖", command=lambda: self.move_rel(-1, 1)).grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Button(move_frame, text="↑", command=lambda: self.move_rel(0, 1)).grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ttk.Button(move_frame, text="↗", command=lambda: self.move_rel(1, 1)).grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        # Middle row
        ttk.Button(move_frame, text="←", command=lambda: self.move_rel(-1, 0)).grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Button(move_frame, text="■", command=self.stop_movement).grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        ttk.Button(move_frame, text="→", command=lambda: self.move_rel(1, 0)).grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        
        # Bottom row
        ttk.Button(move_frame, text="↙", command=lambda: self.move_rel(-1, -1)).grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Button(move_frame, text="↓", command=lambda: self.move_rel(0, -1)).grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
        ttk.Button(move_frame, text="↘", command=lambda: self.move_rel(1, -1)).grid(row=2, column=2, padx=5, pady=5, sticky="nsew")
        
        # Configure grid to expand with window
        for i in range(3):
            move_frame.columnconfigure(i, weight=1)
            move_frame.rowconfigure(i, weight=1)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # Speed and acceleration settings
        speed_frame = ttk.LabelFrame(settings_frame, text="Speed & Acceleration")
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(speed_frame, text="Speed (%):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(speed_frame, textvariable=self.speed, width=5).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(speed_frame, text="Set Speed", command=self.set_speed).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(speed_frame, text="Get Speed", command=self.get_speed).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(speed_frame, text="Acceleration (%):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(speed_frame, textvariable=self.accel, width=5).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(speed_frame, text="Set Accel", command=self.set_accel).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(speed_frame, text="Get Accel", command=self.get_accel).grid(row=1, column=3, padx=5, pady=5)
        
        # Controller information
        info_frame = ttk.LabelFrame(settings_frame, text="Controller Information")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = tk.Text(info_frame, height=10, width=50, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.info_text.insert(tk.END, "Connect to controller to see information.")
        self.info_text.config(state=tk.DISABLED)
        
        ttk.Button(info_frame, text="Get Controller Info", command=self.get_controller_info).pack(padx=5, pady=5)
        
        # Initialize UI state
        self.update_ui_state()
    
    def update_ui_state(self):
        """Update UI elements based on connection state."""
        state = "normal" if self.connected else "disabled"
        
        # Update button text
        self.connect_btn.config(text="Disconnect" if self.connected else "Connect")
        
        # Update all widgets in notebook
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                self._update_widget_state(child, state)
    
    def _update_widget_state(self, parent, state):
        """Recursively update widget states."""
        for child in parent.winfo_children():
            # Keep the COM port entry field enabled
            is_com_port_entry = (hasattr(child, 'cget') and 
                                isinstance(parent, ttk.LabelFrame) and 
                                parent.cget('text') == "Connection" and
                                child.winfo_class() == "TEntry")
            
            if child != self.connect_btn and not isinstance(child, ttk.Label) and not is_com_port_entry:
                try:
                    child.config(state=state)
                except:
                    pass
            if hasattr(child, 'winfo_children') and callable(child.winfo_children):
                self._update_widget_state(child, state)
    
    def toggle_connection(self):
        """Connect to or disconnect from the controller."""
        if not self.connected:
            try:
                # Create controller instance if it doesn't exist
                if self.controller is None:
                    self.controller = PriorStageController()
                    # Show the DLL path in the status
                    self.status.set(f"Using DLL: {self.controller.dll_path}")
                    self.root.update_idletasks()
                    time.sleep(1)  # Give user time to see the DLL path
                
                port = int(self.com_port.get())
                self.status.set(f"Connecting to COM{port}...")
                self.root.update_idletasks()
                
                if self.controller.connect(port):
                    self.connected = True
                    self.status.set(f"Connected to COM{port}")
                    
                    # Start position update thread
                    self.position_update_running = True
                    self.update_thread = threading.Thread(target=self.update_position_thread, daemon=True)
                    self.update_thread.start()
                    
                    # Get initial position
                    self.get_pos()
                    
                    # Get controller info
                    self.get_controller_info()
                else:
                    # Show more detailed error information
                    self.status.set(f"Failed to connect to COM{port} - Check console for details")
                    # Update info text with troubleshooting tips
                    self.info_text.config(state=tk.NORMAL)
                    self.info_text.delete(1.0, tk.END)
                    self.info_text.insert(tk.END, "Connection Troubleshooting Tips:\n\n")
                    self.info_text.insert(tk.END, "1. Verify the Prior controller is powered on\n")
                    self.info_text.insert(tk.END, "2. Check that the USB cable is connected\n")
                    self.info_text.insert(tk.END, "3. Confirm the correct COM port in Device Manager\n")
                    self.info_text.insert(tk.END, "4. Try a different COM port number\n")
                    self.info_text.insert(tk.END, "5. Check if Prior SDK drivers are installed\n")
                    self.info_text.insert(tk.END, f"\nDLL Path: {self.controller.dll_path}\n")
                    self.info_text.config(state=tk.DISABLED)
            except ValueError:
                self.status.set("Invalid COM port number")
            except Exception as e:
                self.status.set(f"Error: {str(e)}")
                # Show detailed error in info text
                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, f"Error Details:\n\n{str(e)}\n\n")
                self.info_text.insert(tk.END, "Please check if:\n")
                self.info_text.insert(tk.END, "- The Prior SDK is properly installed\n")
                self.info_text.insert(tk.END, "- The DLL file exists at the expected location\n")
                self.info_text.config(state=tk.DISABLED)
        else:
            # Stop position updates
            self.position_update_running = False
            if self.update_thread:
                self.update_thread.join(timeout=1.0)
            
            # Disconnect
            if self.controller:
                try:
                    self.controller.disconnect()
                    self.controller.close()
                except:
                    pass
            
            self.connected = False
            self.status.set("Disconnected")
        
        self.update_ui_state()
    
    def update_position_thread(self):
        """Thread function to update position display."""
        while self.position_update_running:
            try:
                if self.connected and self.controller:
                    pos = self.controller.get_position()
                    if pos:
                        x, y = pos
                        self.position_display.set(f"X: {x:.1f}, Y: {y:.1f}")
            except:
                pass
            time.sleep(0.5)  # Update every 500ms
    
    def get_pos(self):
        """Get and display current position."""
        try:
            if self.controller:
                self.status.set("Requesting position...")
                self.root.update_idletasks()
                
                pos = self.controller.get_position()
                if pos:
                    x, y = pos
                    self.x_pos.set(f"{x:.1f}")
                    self.y_pos.set(f"{y:.1f}")
                    self.position_display.set(f"X: {x:.1f}, Y: {y:.1f}")
                    self.status.set(f"Current position: X={x:.1f}, Y={y:.1f}")
                else:
                    self.status.set("Failed to get position - check console for details")
                    # Show troubleshooting info
                    self.info_text.config(state=tk.NORMAL)
                    self.info_text.delete(1.0, tk.END)
                    self.info_text.insert(tk.END, "Position Request Troubleshooting:\n\n")
                    self.info_text.insert(tk.END, "1. Verify the stage is properly connected\n")
                    self.info_text.insert(tk.END, "2. Check if the stage is powered on\n")
                    self.info_text.insert(tk.END, "3. The stage might not support position commands\n")
                    self.info_text.insert(tk.END, "4. Try disconnecting and reconnecting\n")
                    self.info_text.insert(tk.END, "5. Check if Prior SDK drivers are installed\n")
                    self.info_text.config(state=tk.DISABLED)
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def set_origin(self):
        """Set current position as origin (0,0)."""
        try:
            if self.controller and self.controller.set_position(0, 0):
                self.x_pos.set("0.0")
                self.y_pos.set("0.0")
                self.position_display.set("X: 0.0, Y: 0.0")
                self.status.set("Origin set to current position")
            else:
                self.status.set("Failed to set origin")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def move_to(self):
        """Move to absolute position."""
        try:
            x = float(self.x_pos.get())
            y = float(self.y_pos.get())
            self.status.set(f"Moving to X={x:.1f}, Y={y:.1f}...")
            
            if self.controller and self.controller.move_to(x, y):
                # Position will be updated by the update thread
                pass
            else:
                self.status.set("Movement failed")
        except ValueError:
            self.status.set("Invalid position values")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def move_rel(self, dx, dy):
        """Move by relative amount."""
        try:
            step = float(self.step_size.get())
            dx = dx * step
            dy = dy * step
            self.status.set(f"Moving by dX={dx:.1f}, dY={dy:.1f}...")
            
            if self.controller and self.controller.move_relative(dx, dy):
                # Position will be updated by the update thread
                pass
            else:
                self.status.set("Relative movement failed")
        except ValueError:
            self.status.set("Invalid step size")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def stop_movement(self):
        """Stop all movement."""
        try:
            if self.controller and self.controller.stop():
                self.status.set("Movement stopped")
            else:
                self.status.set("Failed to stop movement")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def set_speed(self):
        """Set speed percentage."""
        try:
            speed = int(self.speed.get())
            if 0 <= speed <= 100:
                if self.controller and self.controller.set_speed(speed):
                    self.status.set(f"Speed set to {speed}%")
                else:
                    self.status.set("Failed to set speed")
            else:
                self.status.set("Speed must be between 0-100%")
        except ValueError:
            self.status.set("Invalid speed value")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def get_speed(self):
        """Get current speed setting."""
        try:
            if self.controller:
                speed = self.controller.get_speed()
                if speed is not None:
                    self.speed.set(str(speed))
                    self.status.set(f"Current speed: {speed}%")
                else:
                    self.status.set("Failed to get speed")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def set_accel(self):
        """Set acceleration percentage."""
        try:
            accel = int(self.accel.get())
            if 0 <= accel <= 100:
                if self.controller and self.controller.set_acceleration(accel):
                    self.status.set(f"Acceleration set to {accel}%")
                else:
                    self.status.set("Failed to set acceleration")
            else:
                self.status.set("Acceleration must be between 0-100%")
        except ValueError:
            self.status.set("Invalid acceleration value")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def get_accel(self):
        """Get current acceleration setting."""
        try:
            if self.controller:
                accel = self.controller.get_acceleration()
                if accel is not None:
                    self.accel.set(str(accel))
                    self.status.set(f"Current acceleration: {accel}%")
                else:
                    self.status.set("Failed to get acceleration")
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
    
    def get_controller_info(self):
        """Get and display controller information."""
        try:
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            
            if not self.connected:
                self.info_text.insert(tk.END, "Not connected to controller.")
                self.info_text.config(state=tk.DISABLED)
                return
            
            # Get SDK version
            self.info_text.insert(tk.END, f"SDK Version: {self.controller.sdk_version}\n\n")
            
            # Get controller info
            self.status.set("Requesting controller information...")
            self.root.update_idletasks()
            
            info = self.controller.get_controller_info()
            if info:
                self.info_text.insert(tk.END, f"Controller Info:\n{info}\n")
                self.status.set("Controller information retrieved")
            else:
                self.info_text.insert(tk.END, "Failed to get controller information.\n\n")
                self.info_text.insert(tk.END, "Troubleshooting:\n")
                self.info_text.insert(tk.END, "1. Your controller model might not support the info command\n")
                self.info_text.insert(tk.END, "2. Check if the controller is properly connected\n")
                self.info_text.insert(tk.END, "3. Try disconnecting and reconnecting\n")
                self.info_text.insert(tk.END, "\nSee console for detailed command responses\n")
                self.status.set("Failed to get controller information")
            
            self.info_text.config(state=tk.DISABLED)
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Error: {str(e)}\n\n")
            self.info_text.insert(tk.END, "Check console for more details")
            self.info_text.config(state=tk.DISABLED)
    
    def initialize_stage(self):
        """Initialize the stage by finding limits and moving to center."""
        if not self.connected or not self.controller:
            self.status.set("Connect to controller first")
            return
        
        # Update status
        self.status.set("Initializing stage...")
        self.root.update_idletasks()
        
        # Create a progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Stage Initialization")
        progress_window.geometry("500x300")
        progress_window.transient(self.root)
        
        # Progress message
        progress_label = ttk.Label(progress_window, text="Stage Initialization")
        progress_label.pack(pady=10)
        
        # Log text
        log_text = tk.Text(progress_window, height=10, width=60)
        log_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar to log text
        scrollbar = ttk.Scrollbar(log_text, command=log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.config(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(progress_window)
        buttons_frame.pack(pady=10, fill=tk.X)
        
        # Update function for the log
        def update_log(message):
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, message + "\n")
            log_text.see(tk.END)
            log_text.config(state=tk.DISABLED)
            progress_window.update_idletasks()
        
        # Automatic initialization function
        def auto_init():
            update_log("Starting automatic initialization...")
            
            # Disable all buttons during initialization
            for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                btn.config(state=tk.DISABLED)
            
            try:
                # Create a progress bar for automatic initialization
                progress = ttk.Progressbar(progress_window, mode="determinate", length=300)
                progress.pack(before=buttons_frame, pady=10)
                progress.config(value=0, maximum=100)
                
                # Get current position as starting point
                update_log("Getting current position...")
                start_pos = self.controller.get_position()
                if not start_pos:
                    update_log("Failed to get current position")
                    progress.destroy()
                    for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                        btn.config(state=tk.NORMAL)
                    return
                
                update_log(f"Starting position: X={start_pos[0]:.1f}, Y={start_pos[1]:.1f}")
                
                # Set a slow speed for safety
                original_speed = self.controller.get_speed()
                self.controller.set_speed(20)  # 20% speed for safety
                
                # Define step size for incremental movement
                step_size = 5000  # 5mm steps
                
                # Find X minimum (left limit)
                update_log("Finding left limit (X minimum)...")
                progress.config(value=10)
                x_min = find_limit_in_direction('left', start_pos, step_size, update_log)
                if x_min is None:
                    update_log("Failed to find left limit")
                    progress.destroy()
                    if original_speed is not None:
                        self.controller.set_speed(original_speed)
                    self.controller.move_to(start_pos[0], start_pos[1])
                    for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                        btn.config(state=tk.NORMAL)
                    return
                
                # Return to starting position
                update_log("Returning to starting position...")
                progress.config(value=20)
                self.controller.move_to(start_pos[0], start_pos[1])
                time.sleep(2)  # Wait for movement to complete
                
                # Find X maximum (right limit)
                update_log("Finding right limit (X maximum)...")
                progress.config(value=30)
                x_max = find_limit_in_direction('right', start_pos, step_size, update_log)
                if x_max is None:
                    update_log("Failed to find right limit")
                    progress.destroy()
                    if original_speed is not None:
                        self.controller.set_speed(original_speed)
                    self.controller.move_to(start_pos[0], start_pos[1])
                    for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                        btn.config(state=tk.NORMAL)
                    return
                
                # Return to starting position
                update_log("Returning to starting position...")
                progress.config(value=40)
                self.controller.move_to(start_pos[0], start_pos[1])
                time.sleep(2)  # Wait for movement to complete
                
                # Find Y minimum (bottom limit)
                update_log("Finding bottom limit (Y minimum)...")
                progress.config(value=50)
                y_min = find_limit_in_direction('bottom', start_pos, step_size, update_log)
                if y_min is None:
                    update_log("Failed to find bottom limit")
                    progress.destroy()
                    if original_speed is not None:
                        self.controller.set_speed(original_speed)
                    self.controller.move_to(start_pos[0], start_pos[1])
                    for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                        btn.config(state=tk.NORMAL)
                    return
                
                # Return to starting position
                update_log("Returning to starting position...")
                progress.config(value=60)
                self.controller.move_to(start_pos[0], start_pos[1])
                time.sleep(2)  # Wait for movement to complete
                
                # Find Y maximum (top limit)
                update_log("Finding top limit (Y maximum)...")
                progress.config(value=70)
                y_max = find_limit_in_direction('top', start_pos, step_size, update_log)
                if y_max is None:
                    update_log("Failed to find top limit")
                    progress.destroy()
                    if original_speed is not None:
                        self.controller.set_speed(original_speed)
                    self.controller.move_to(start_pos[0], start_pos[1])
                    for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                        btn.config(state=tk.NORMAL)
                    return
                
                # Calculate center position
                update_log("Calculating center position...")
                progress.config(value=80)
                x_center = (x_min + x_max) / 2
                y_center = (y_min + y_max) / 2
                
                update_log(f"Found limits: X: {x_min:.1f} to {x_max:.1f}, Y: {y_min:.1f} to {y_max:.1f}")
                update_log(f"Center position: X={x_center:.1f}, Y={y_center:.1f}")
                
                # Move to center position
                update_log("Moving to center position...")
                progress.config(value=90)
                self.controller.move_to(x_center, y_center)
                time.sleep(2)  # Wait for movement to complete
                
                # Set as origin
                update_log("Setting center as new origin (0,0)...")
                progress.config(value=95)
                success = self.controller.set_position(0, 0)
                
                # Restore original speed
                if original_speed is not None:
                    self.controller.set_speed(original_speed)
                
                if success:
                    update_log("Initialization complete!")
                    self.x_pos.set("0.0")
                    self.y_pos.set("0.0")
                    self.position_display.set("X: 0.0, Y: 0.0")
                    self.status.set("Stage initialized and centered")
                else:
                    update_log("Failed to set origin")
                    self.status.set("Failed to set origin")
                
                progress.config(value=100)
                
            except Exception as e:
                update_log(f"Error during initialization: {str(e)}")
                self.status.set(f"Initialization error: {str(e)}")
            finally:
                # Re-enable buttons
                for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                    btn.config(state=tk.NORMAL)
        
        # Helper function to find limit in a direction
        def find_limit_in_direction(direction, start_pos, step_size, log_func):
            """Find limit in a specific direction by making incremental moves."""
            # Get starting position
            x, y = start_pos
            
            # Track the last successful position
            last_pos = (x, y)
            
            # Maximum steps to try
            max_steps = 100
            
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
                    log_func(f"Invalid direction: {direction}")
                    return None
                
                # Try to move to new position
                log_func(f"Step {step+1}: Moving to X={new_x:.1f}, Y={new_y:.1f}")
                success = self.controller.move_to(new_x, new_y)
                
                # Wait for movement to complete
                time.sleep(1)
                
                # Get current position
                current_pos = self.controller.get_position()
                if current_pos is None:
                    log_func("Could not get current position")
                    return None
                
                log_func(f"Current position: X={current_pos[0]:.1f}, Y={current_pos[1]:.1f}")
                
                # Check if we've hit a limit
                if direction == 'left' or direction == 'right':
                    # Check if X position hasn't changed much
                    if abs(current_pos[0] - last_pos[0]) < (step_size * 0.5):
                        log_func(f"Hit limit in {direction} direction at X={current_pos[0]:.1f}")
                        return current_pos[0]
                else:
                    # Check if Y position hasn't changed much
                    if abs(current_pos[1] - last_pos[1]) < (step_size * 0.5):
                        log_func(f"Hit limit in {direction} direction at Y={current_pos[1]:.1f}")
                        return current_pos[1]
                
                # Update last successful position
                last_pos = current_pos
                
                # Update x, y for next iteration
                x, y = current_pos
            
            # If we've reached max steps without finding a limit, use the last position
            log_func(f"Reached maximum steps without finding limit in {direction} direction")
            if direction == 'left' or direction == 'right':
                return last_pos[0]
            else:
                return last_pos[1]
        
        # Manual initialization functions
        def manual_init():
            update_log("Starting manual initialization...")
            
            # Disable all buttons during initialization
            for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                btn.config(state=tk.DISABLED)
            
            try:
                # Get current position
                update_log("Getting current position...")
                pos = self.controller.get_position()
                if pos:
                    update_log(f"Current position: X={pos[0]:.1f}, Y={pos[1]:.1f}")
                else:
                    update_log("Failed to get current position")
                    
                # Ask user to manually move to limits
                update_log("\nMANUAL INITIALIZATION INSTRUCTIONS:")
                update_log("1. Use the arrow buttons in the main window to move the stage")
                update_log("2. Move to each limit (left, right, top, bottom) to find the stage boundaries")
                update_log("3. Move to what you consider the center position")
                update_log("4. Click 'Set as Center' when positioned at the center")
                update_log("5. Click 'Set as Origin (0,0)' to define this as the new origin")
                
            except Exception as e:
                update_log(f"Error: {str(e)}")
            finally:
                # Re-enable buttons
                for btn in [auto_init_btn, manual_init_btn, set_center_btn, set_origin_btn, close_btn]:
                    btn.config(state=tk.NORMAL)
        
        def set_as_center():
            try:
                pos = self.controller.get_position()
                if pos:
                    update_log(f"Setting current position as center: X={pos[0]:.1f}, Y={pos[1]:.1f}")
                    self.center_position = pos
                    update_log("Center position set. You can now click 'Set as Origin (0,0)'")
                else:
                    update_log("Failed to get current position")
            except Exception as e:
                update_log(f"Error: {str(e)}")
        
        def set_as_origin():
            try:
                pos = self.controller.get_position()
                if pos:
                    update_log(f"Setting current position as origin (0,0): X={pos[0]:.1f}, Y={pos[1]:.1f}")
                    success = self.controller.set_position(0, 0)
                    if success:
                        update_log("Origin set successfully!")
                        self.x_pos.set("0.0")
                        self.y_pos.set("0.0")
                        self.position_display.set("X: 0.0, Y: 0.0")
                        self.status.set("Stage initialized with new origin")
                    else:
                        update_log("Failed to set origin")
                else:
                    update_log("Failed to get current position")
            except Exception as e:
                update_log(f"Error: {str(e)}")
        
        # Add buttons for initialization options
        auto_init_btn = ttk.Button(buttons_frame, text="Auto Initialize", command=auto_init)
        auto_init_btn.pack(side=tk.LEFT, padx=5)
        
        manual_init_btn = ttk.Button(buttons_frame, text="Manual Init", command=manual_init)
        manual_init_btn.pack(side=tk.LEFT, padx=5)
        
        set_center_btn = ttk.Button(buttons_frame, text="Set as Center", command=set_as_center)
        set_center_btn.pack(side=tk.LEFT, padx=5)
        
        set_origin_btn = ttk.Button(buttons_frame, text="Set as Origin (0,0)", command=set_as_origin)
        set_origin_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = ttk.Button(buttons_frame, text="Close", command=progress_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Start with instructions
        update_log("STAGE INITIALIZATION")
        update_log("====================")
        update_log("This tool helps you initialize the stage by finding limits and setting the center as origin (0,0).")
        update_log("")
        update_log("Choose an initialization method:")
        update_log("1. Auto Initialize - Automatically find limits and center")
        update_log("2. Manual Init - Manually move to limits and center")
    
    def on_close(self):
        """Handle window close event."""
        # Stop position updates
        self.position_update_running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
        
        # Disconnect and clean up
        if self.controller:
            try:
                self.controller.disconnect()
                self.controller.close()
            except:
                pass
        
        self.root.destroy()


def main():
    """Main function to start the application."""
    root = tk.Tk()
    app = PriorControllerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
