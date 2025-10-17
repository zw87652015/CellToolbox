#!/usr/bin/env python3
"""
Rigol DG2052 Signal Source Controller
Python implementation matching MATLAB UI functionality
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Menu
import pyvisa
import threading
import time
from datetime import datetime
import os


class SignalSourceController:
    """
    GUI Controller for Rigol DG2052 Signal Generator
    Implements same functionality as MATLAB version
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Signal Source Controller")
        self.root.geometry("400x600")
        
        # Application version
        self.current_app_version = "v1.2"
        
        # Connection properties
        self.dg2052 = None
        self.is_connected = False
        self.rm = None
        
        # Timer properties
        self.output_timer = None
        self.countdown_timer = None
        self.remaining_time = 0.0
        self.timer_running = False
        
        # Log storage
        self.log = ""
        
        # Create menu bar
        self.create_menu()
        
        # Create UI components
        self.create_widgets()
        
        # Initialize button states
        self.initialize_ui_state()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_menu(self):
        """Create menu bar"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # Log menu
        log_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Log", menu=log_menu)
        log_menu.add_command(label="About", command=self.show_about)
        log_menu.add_command(label="Clear log", command=self.clear_log)
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        row = 0
        
        # Connect/Disconnect buttons
        button_frame1 = ttk.Frame(main_frame)
        button_frame1.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        button_frame1.columnconfigure(0, weight=1)
        button_frame1.columnconfigure(1, weight=1)
        
        self.connect_button = ttk.Button(button_frame1, text="Connect", 
                                        command=self.connect_device)
        self.connect_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 2))
        
        self.disconnect_button = ttk.Button(button_frame1, text="Disconnect", 
                                           command=self.disconnect_device)
        self.disconnect_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(2, 0))
        
        row += 1
        
        # Output ON/OFF buttons
        button_frame2 = ttk.Frame(main_frame)
        button_frame2.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        button_frame2.columnconfigure(0, weight=1)
        button_frame2.columnconfigure(1, weight=1)
        
        self.output_on_button = ttk.Button(button_frame2, text="Output 1 on", 
                                          command=self.output_on)
        self.output_on_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 2))
        
        self.output_off_button = ttk.Button(button_frame2, text="Output 1 off", 
                                           command=self.output_off)
        self.output_off_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(2, 0))
        
        row += 1
        
        # Lasting input
        lasting_frame = ttk.Frame(main_frame)
        lasting_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        lasting_frame.columnconfigure(1, weight=1)
        
        ttk.Label(lasting_frame, text="Lasting:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.lasting_entry = ttk.Entry(lasting_frame)
        self.lasting_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.lasting_entry.insert(0, "0")
        self.lasting_entry.bind('<FocusOut>', self.validate_lasting)
        self.lasting_entry.bind('<Return>', self.validate_lasting)
        ttk.Label(lasting_frame, text="s").grid(row=0, column=2, sticky=tk.W)
        
        row += 1
        
        # Timer display (read-only)
        timer_frame = ttk.Frame(main_frame)
        timer_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        timer_frame.columnconfigure(1, weight=1)
        
        ttk.Label(timer_frame, text="Timer:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.timer_entry = ttk.Entry(timer_frame, state='readonly')
        self.timer_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Label(timer_frame, text="s").grid(row=0, column=2, sticky=tk.W)
        
        # Set timer value
        self.timer_var = tk.StringVar(value="0")
        self.timer_entry.config(textvariable=self.timer_var)
        
        row += 1
        
        # Pulses input
        pulses_frame = ttk.Frame(main_frame)
        pulses_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        pulses_frame.columnconfigure(1, weight=1)
        
        ttk.Label(pulses_frame, text="Pulses:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.pulses_entry = ttk.Entry(pulses_frame)
        self.pulses_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.pulses_entry.insert(0, "1")
        self.pulses_entry.bind('<FocusOut>', self.validate_pulses)
        self.pulses_entry.bind('<Return>', self.validate_pulses)
        ttk.Label(pulses_frame, text="pulse(s)").grid(row=0, column=2, sticky=tk.W)
        
        row += 1
        
        # Set/Read buttons
        button_frame3 = ttk.Frame(main_frame)
        button_frame3.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        button_frame3.columnconfigure(0, weight=1)
        button_frame3.columnconfigure(1, weight=1)
        
        self.set_button = ttk.Button(button_frame3, text="Set", 
                                    command=self.set_parameters)
        self.set_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 2))
        
        self.read_button = ttk.Button(button_frame3, text="Read", 
                                     command=self.read_parameters)
        self.read_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(2, 0))
        
        row += 1
        
        # Save log button
        self.save_log_button = ttk.Button(main_frame, text="Save log", 
                                         command=self.save_log)
        self.save_log_button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        
        row += 1
        
        # Log text area
        ttk.Label(main_frame, text="Log").grid(row=row, column=0, sticky=tk.W, pady=(5, 2))
        row += 1
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=45, 
                                                  state='disabled', wrap=tk.WORD)
        self.log_text.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        main_frame.rowconfigure(row, weight=1)
    
    def initialize_ui_state(self):
        """Initialize button states on startup"""
        self.connect_button.config(state='normal')
        self.disconnect_button.config(state='disabled')
        self.output_on_button.config(state='disabled')
        self.output_off_button.config(state='disabled')
        self.timer_var.set("0")
    
    def disp_log_info(self, message):
        """Display log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] -> {message}\n"
        self.log += log_message
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def show_about(self):
        """Show about dialog"""
        self.disp_log_info(self.current_app_version)
    
    def clear_log(self):
        """Clear log content"""
        self.log = ""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def validate_lasting(self, event=None):
        """Validate lasting time input"""
        try:
            value = float(self.lasting_entry.get())
            if value < 0:
                self.lasting_entry.delete(0, tk.END)
                self.lasting_entry.insert(0, "0")
                self.disp_log_info("Invalid lasting time. Reset to 0.")
            else:
                self.lasting_entry.delete(0, tk.END)
                self.lasting_entry.insert(0, f"{value:.1f}")
        except ValueError:
            self.lasting_entry.delete(0, tk.END)
            self.lasting_entry.insert(0, "0")
            self.disp_log_info("Invalid lasting time. Reset to 0.")
    
    def validate_pulses(self, event=None):
        """Validate pulses input and auto-update lasting time"""
        try:
            value = float(self.pulses_entry.get())
            if value <= 0:
                self.pulses_entry.delete(0, tk.END)
                self.pulses_entry.insert(0, "1")
                self.disp_log_info("Invalid pulses value. Reset to 1.")
                value = 1
            else:
                value = round(value)
                self.pulses_entry.delete(0, tk.END)
                self.pulses_entry.insert(0, f"{int(value)}")
            
            # Auto-update Lasting time (Pulses + 0.3 seconds)
            lasting_time = value + 0.3
            self.lasting_entry.delete(0, tk.END)
            self.lasting_entry.insert(0, f"{lasting_time:.1f}")
            
        except ValueError:
            self.pulses_entry.delete(0, tk.END)
            self.pulses_entry.insert(0, "1")
            self.disp_log_info("Invalid pulses value. Reset to 1.")
    
    def connect_device(self):
        """Connect to DG2052 device"""
        if self.is_connected:
            self.disp_log_info("DG2052 is already connected.")
            return
        
        try:
            self.disp_log_info("Searching for DG2052 device...")
            
            # Initialize PyVISA resource manager
            self.rm = pyvisa.ResourceManager()
            
            # List available resources
            resources = self.rm.list_resources()
            self.disp_log_info(f"Available resources: {', '.join(resources) if resources else 'None'}")
            
            # Connection strings to try
            connection_strings = [
                'USB0::0x1AB1::0x0644::DG2P232400656::0::INSTR',
                'USB0::0x1AB1::0x0644::DG2P232400656::INSTR',
                'USB::0x1AB1::0x0644::DG2P232400656::0::INSTR',
                'USB::0x1AB1::0x0644::DG2P232400656::INSTR'
            ]
            
            # Also try any USB resources found
            usb_resources = [r for r in resources if 'USB' in r.upper()]
            connection_strings.extend(usb_resources)
            
            connected = False
            for conn_str in connection_strings:
                try:
                    self.disp_log_info(f"Trying connection: {conn_str}")
                    self.dg2052 = self.rm.open_resource(conn_str)
                    self.dg2052.timeout = 5000  # 5 second timeout
                    
                    # Test connection by querying device ID
                    idn = self.dg2052.query('*IDN?')
                    self.disp_log_info(f"Device identified: {idn.strip()}")
                    
                    connected = True
                    self.disp_log_info(f"Connected using: {conn_str}")
                    break
                except Exception as e:
                    if self.dg2052:
                        try:
                            self.dg2052.close()
                        except:
                            pass
                        self.dg2052 = None
                    continue
            
            if connected:
                self.is_connected = True
                self.connect_button.config(state='disabled')
                self.disconnect_button.config(state='normal')
                self.output_on_button.config(state='normal')
                self.output_off_button.config(state='disabled')
                self.disp_log_info("DG2052 connected successfully.")
            else:
                raise Exception("Could not connect with any of the attempted connection strings")
                
        except Exception as e:
            self.disp_log_info(f"Failed to connect to DG2052: {str(e)}")
            self.disp_log_info("Please check: 1) Device is connected via USB, 2) Device is powered on, 3) No other software is using the device")
            self.is_connected = False
            if self.dg2052:
                try:
                    self.dg2052.close()
                except:
                    pass
                self.dg2052 = None
    
    def disconnect_device(self):
        """Disconnect from DG2052 device"""
        try:
            if self.is_connected and self.dg2052:
                # Turn off output before disconnecting
                try:
                    self.dg2052.write(':OUTP1 OFF')
                except:
                    pass
                
                self.dg2052.close()
                self.dg2052 = None
                self.is_connected = False
                
                # Update button states
                self.connect_button.config(state='normal')
                self.disconnect_button.config(state='disabled')
                self.output_on_button.config(state='disabled')
                self.output_off_button.config(state='disabled')
                
                # Clean up timers
                self.stop_countdown_display()
                if self.output_timer:
                    self.output_timer.cancel()
                    self.output_timer = None
                
                self.disp_log_info("DG2052 disconnected and cleared.")
            else:
                self.disp_log_info("DG2052 is not connected.")
        except Exception as e:
            self.disp_log_info(f"Error during disconnect: {str(e)}")
            self.is_connected = False
            self.connect_button.config(state='normal')
            self.disconnect_button.config(state='disabled')
    
    def output_on(self):
        """Turn on output 1"""
        if not self.is_connected or not self.dg2052:
            self.disp_log_info("Error: DG2052 not connected. Please connect first.")
            return
        
        try:
            self.disp_log_info("Output 1 ON.")
            self.output_on_button.config(state='disabled')
            self.output_off_button.config(state='normal')
            
            # Turn on the signal source
            self.dg2052.write(':OUTP1 ON')
            
            # Check if we need to set up an automatic turn-off timer
            try:
                lasting_time = float(self.lasting_entry.get())
                
                if lasting_time > 0:
                    # Clean up any existing timer
                    if self.output_timer:
                        self.output_timer.cancel()
                    
                    # Create and start the auto turn-off timer
                    self.output_timer = threading.Timer(lasting_time, self.auto_turn_off_output)
                    self.output_timer.daemon = True
                    self.output_timer.start()
                    
                    # Start countdown display
                    self.remaining_time = lasting_time
                    self.start_countdown_display()
                    
                    self.disp_log_info(f"Auto turn-off timer set for {lasting_time:.1f} seconds.")
            except ValueError:
                self.disp_log_info("Warning: Invalid lasting time value. Timer not set.")
                
        except Exception as e:
            self.disp_log_info(f"Error turning on output: {str(e)}")
            self.output_on_button.config(state='normal')
            self.output_off_button.config(state='disabled')
    
    def output_off(self):
        """Turn off output 1"""
        if not self.is_connected or not self.dg2052:
            self.disp_log_info("Error: DG2052 not connected. Please connect first.")
            return
        
        try:
            self.disp_log_info("Output 1 OFF.")
            self.output_on_button.config(state='normal')
            self.output_off_button.config(state='disabled')
            
            # Clean up any active timers
            if self.output_timer:
                self.output_timer.cancel()
                self.output_timer = None
            
            self.stop_countdown_display()
            
            # Turn off the signal source
            self.dg2052.write(':OUTP1 OFF')
            
        except Exception as e:
            self.disp_log_info(f"Error turning off output: {str(e)}")
    
    def auto_turn_off_output(self):
        """Automatically turn off the output when timer expires"""
        if not self.is_connected or not self.dg2052:
            self.disp_log_info("Error: DG2052 not connected during auto turn-off.")
            return
        
        try:
            self.disp_log_info("Output 1 OFF (auto).")
            
            # Update UI in main thread
            self.root.after(0, lambda: self.output_on_button.config(state='normal'))
            self.root.after(0, lambda: self.output_off_button.config(state='disabled'))
            
            # Clean up timers
            if self.output_timer:
                self.output_timer = None
            
            self.root.after(0, self.stop_countdown_display)
            
            # Turn off the signal source
            self.dg2052.write(':OUTP1 OFF')
            
        except Exception as e:
            self.disp_log_info(f"Error during auto turn-off: {str(e)}")
    
    def start_countdown_display(self):
        """Start the countdown timer that updates every 0.1 seconds"""
        self.timer_running = True
        self.update_countdown_display()
    
    def update_countdown_display(self):
        """Update the countdown display"""
        if not self.timer_running:
            return
        
        if self.remaining_time > 0:
            self.timer_var.set(f"{self.remaining_time:.1f}")
            self.remaining_time -= 0.1
            # Schedule next update in 100ms
            self.countdown_timer = self.root.after(100, self.update_countdown_display)
        else:
            self.timer_var.set("0")
            self.stop_countdown_display()
    
    def stop_countdown_display(self):
        """Stop and clean up the countdown timer"""
        self.timer_running = False
        if self.countdown_timer:
            self.root.after_cancel(self.countdown_timer)
            self.countdown_timer = None
        self.timer_var.set("0")
        self.remaining_time = 0.0
    
    def set_parameters(self):
        """Set DG2052 parameters"""
        try:
            # Get values from inputs
            pulses_str = self.pulses_entry.get()
            
            # Validate and convert values
            pulses = float(pulses_str)
            
            if pulses <= 0:
                self.disp_log_info("Error: Pulses value must be a positive number.")
                return
            
            # Calculate lasting time = pulses + 0.3 seconds
            lasting_time = pulses + 0.3
            
            # Update the Lasting entry
            self.lasting_entry.delete(0, tk.END)
            self.lasting_entry.insert(0, f"{lasting_time:.1f}")
            
            self.disp_log_info(f"Parameters set - Pulses: {int(pulses)}, Lasting: {lasting_time:.1f}s")
            
        except ValueError:
            self.disp_log_info("Error: Invalid input values. Please check Pulses.")
        except Exception as e:
            self.disp_log_info(f"Error setting DG2052 parameters: {str(e)}")
    
    def read_parameters(self):
        """Read current DG2052 settings"""
        if not self.is_connected or not self.dg2052:
            self.disp_log_info("Error: DG2052 not connected. Please connect first.")
            return
        
        try:
            self.disp_log_info("Reading DG2052 current settings...")
            
            # Read waveform type
            waveform = self.dg2052.query(':SOUR1:FUNC?').strip()
            
            # Read high level voltage
            high_volt = float(self.dg2052.query(':SOUR1:VOLT:HIGH?'))
            
            # Read low level voltage
            low_volt = float(self.dg2052.query(':SOUR1:VOLT:LOW?'))
            
            # Read frequency
            frequency = float(self.dg2052.query(':SOUR1:FREQ?'))
            
            # Read pulse width
            pulse_width = float(self.dg2052.query(':SOUR1:PULS:WIDT?'))
            
            # Read output status
            output_status = int(self.dg2052.query(':OUTP1?'))
            
            # Convert width from seconds to microseconds for display
            width_us = pulse_width * 1e6
            
            # Display current settings in log
            self.disp_log_info("=== Current DG2052 Settings ===")
            self.disp_log_info(f"Waveform: {waveform}")
            self.disp_log_info(f"High Level: {high_volt:.3f} V")
            self.disp_log_info(f"Low Level: {low_volt:.3f} V")
            self.disp_log_info(f"Frequency: {frequency:.1f} Hz")
            self.disp_log_info(f"Pulse Width: {width_us:.1f} us")
            status_str = "ON" if output_status == 1 else "OFF"
            self.disp_log_info(f"Output Status: {status_str}")
            self.disp_log_info("===============================")
            
        except Exception as e:
            self.disp_log_info(f"Error reading DG2052 settings: {str(e)}")
    
    def save_log(self):
        """Save log content to file"""
        try:
            # Generate timestamp for filename
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f'log_{timestamp}.txt'
            
            # Get current working directory
            current_dir = os.getcwd()
            full_path = os.path.join(current_dir, filename)
            
            # Write log content to file
            if self.log:
                with open(full_path, 'w') as f:
                    f.write(self.log)
                
                self.disp_log_info(f"Log saved to: {full_path}")
            else:
                self.disp_log_info("No log content to save.")
                
        except Exception as e:
            self.disp_log_info(f"Error saving log: {str(e)}")
    
    def on_closing(self):
        """Handle window close event"""
        # Disconnect device if connected
        if self.is_connected:
            self.disconnect_device()
        
        # Close resource manager
        if self.rm:
            try:
                self.rm.close()
            except:
                pass
        
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = SignalSourceController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
