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
                for widget in child.winfo_descendants():
                    if widget != self.connect_btn and not isinstance(widget, ttk.Label):
                        try:
                            widget.config(state=state)
                        except:
                            pass
    
    def toggle_connection(self):
        """Connect to or disconnect from the controller."""
        if not self.connected:
            try:
                # Create controller instance if it doesn't exist
                if self.controller is None:
                    self.controller = PriorStageController()
                
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
                    self.status.set(f"Failed to connect to COM{port}")
            except ValueError:
                self.status.set("Invalid COM port number")
            except Exception as e:
                self.status.set(f"Error: {str(e)}")
        else:
            # Stop position updates
            self.position_update_running = False
            if self.update_thread:
                self.update_thread.join(timeout=1.0)
            
            # Disconnect
            if self.controller:
                self.controller.disconnect()
            
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
                pos = self.controller.get_position()
                if pos:
                    x, y = pos
                    self.x_pos.set(f"{x:.1f}")
                    self.y_pos.set(f"{y:.1f}")
                    self.position_display.set(f"X: {x:.1f}, Y: {y:.1f}")
                    self.status.set(f"Current position: X={x:.1f}, Y={y:.1f}")
                else:
                    self.status.set("Failed to get position")
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
            info = self.controller.get_controller_info()
            if info:
                self.info_text.insert(tk.END, f"Controller Info:\n{info}\n")
            else:
                self.info_text.insert(tk.END, "Failed to get controller information.\n")
            
            self.info_text.config(state=tk.DISABLED)
        except Exception as e:
            self.status.set(f"Error: {str(e)}")
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Error: {str(e)}")
            self.info_text.config(state=tk.DISABLED)
    
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
