
import pygame
import pygame.gfxdraw
import tkinter as tk
from tkinter import ttk
import math
import sys
import threading
import time
from multiprocessing import Process, Value
import numpy as np
import os
import ctypes

# Initialize screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
RED = (255, 0, 0)

# Default parameters
DEFAULT_R1 = 30
DEFAULT_H = 100

# Function to ensure window stays in foreground (Windows OS)
def stay_on_top(window_name):
    try:
        # Get window handle
        hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
        if hwnd:
            # Set window to topmost
            ctypes.windll.user32.SetWindowPos(
                hwnd, -1, 0, 0, 0, 0, 
                0x0001 | 0x0002 | 0x0010
            )
            # Force update
            ctypes.windll.user32.BringWindowToTop(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW = 5
            return True
    except Exception as e:
        print(f"Error setting window on top: {e}")
    return False

# Parameter Control Panel class using multiprocessing for thread safety
class ParameterControlPanel:
    def __init__(self):
        # Use shared memory for communication between processes
        self._r1 = Value('i', DEFAULT_R1)  # Radius of the center disk
        self._h = Value('i', DEFAULT_H)    # Height of the vertical line
        self._panel_active = Value('i', 0)  # 0 = inactive, 1 = active
        self.process = None
    
    @property
    def r1(self):
        return self._r1.value
    
    @property
    def h(self):
        return self._h.value
    
    @property
    def panel_active(self):
        return self._panel_active.value
    
    def create_panel(self):
        if self.process is None or not self.process.is_alive():
            self.process = Process(target=self._run_panel, 
                                  args=(self._r1, self._h, self._panel_active))
            self.process.daemon = True
            self.process.start()
            self._panel_active.value = 1
    
    def _run_panel(self, r1, h, panel_active):
        # Create Tk root window
        root = tk.Tk()
        root.title("Parameter Control Panel")
        root.geometry("300x250")
        root.protocol("WM_DELETE_WINDOW", lambda: on_close())
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # R1 control
        r1_frame = ttk.LabelFrame(main_frame, text="R1 (Center Disk Radius)")
        r1_frame.pack(fill=tk.X, pady=5)
        
        r1_scale = ttk.Scale(
            r1_frame, 
            from_=10, 
            to=100, 
            orient=tk.HORIZONTAL,
            length=200, 
            value=r1.value,
            command=lambda v: update_r1(int(float(v)))
        )
        r1_scale.pack(side=tk.LEFT, padx=5, pady=5)
        
        r1_label = ttk.Label(r1_frame, text=str(r1.value))
        r1_label.pack(side=tk.LEFT, padx=5)
        
        # H control
        h_frame = ttk.LabelFrame(main_frame, text="H (Vertical Line Length)")
        h_frame.pack(fill=tk.X, pady=5)
        
        h_scale = ttk.Scale(
            h_frame, 
            from_=50, 
            to=200, 
            orient=tk.HORIZONTAL,
            length=200, 
            value=h.value,
            command=lambda v: update_h(int(float(v)))
        )
        h_scale.pack(side=tk.LEFT, padx=5, pady=5)
        
        h_label = ttk.Label(h_frame, text=str(h.value))
        h_label.pack(side=tk.LEFT, padx=5)
        
        # R2 value display (calculated)
        r2_frame = ttk.LabelFrame(main_frame, text="R2 (Circle Radius)")
        r2_frame.pack(fill=tk.X, pady=5)
        
        r2_value = calculate_r2(r1.value, h.value)
        r2_label = ttk.Label(r2_frame, text=f"R2 = {r2_value:.2f} pixels")
        r2_label.pack(padx=5, pady=5)
        
        # Update functions
        def update_r1(value):
            r1.value = value
            r1_label.config(text=str(value))
            r2_value = calculate_r2(r1.value, h.value)
            r2_label.config(text=f"R2 = {r2_value:.2f} pixels")
        
        def update_h(value):
            h.value = value
            h_label.config(text=str(value))
            r2_value = calculate_r2(r1.value, h.value)
            r2_label.config(text=f"R2 = {r2_value:.2f} pixels")
        
        def on_close():
            panel_active.value = 0
            root.destroy()
            sys.exit()  # Exit the process
        
        # Function to keep the window in foreground
        def keep_on_top():
            while panel_active.value == 1:
                try:
                    stay_on_top("Parameter Control Panel")
                    time.sleep(0.5)  # Check every half second
                except:
                    break
        
        # Start a thread to keep the window on top
        top_thread = threading.Thread(target=keep_on_top)
        top_thread.daemon = True
        top_thread.start()
        
        # Start Tk main loop
        root.mainloop()
    
    def on_close(self):
        if self.process and self.process.is_alive():
            self._panel_active.value = 0
            self.process.terminate()
            self.process.join()
            self.process = None

# Function to calculate R2 based on mathematical relationship H^2+R2^2=(R1+R2)^2
def calculate_r2(r1, h):
    # Solve H^2+R2^2=(R1+R2)^2
    # H^2+R2^2=R1^2+2*R1*R2+R2^2
    # H^2=R1^2+2*R1*R2
    # R2=H^2/(2*R1) - R1/2
    return h**2/(2*r1) - r1/2

# Main function
def main():
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Geometric Drawing")
    
    # Initialize parameter panel
    param_panel = ParameterControlPanel()
    param_panel.create_panel()
    
    # Font for displaying values
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 16)
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Clear the screen with grey
        screen.fill(GREY)
        
        # Get current parameter values
        r1 = param_panel.r1
        h = param_panel.h
        r2 = calculate_r2(r1, h)
        
        # Calculate positions
        p1 = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)  # Center point, shifted up a bit
        p2 = (p1[0], p1[1] + h)  # Point below P1
        a1 = (p2[0] - r2, p2[1])  # Left point
        a2 = (p2[0] + r2, p2[1])  # Right point
        
        # Draw P1 (center point)
        pygame.draw.circle(screen, RED, p1, 3)
        text = font.render("P1", True, RED)
        screen.blit(text, (p1[0] + 5, p1[1] - 20))
        
        # Draw white disk around P1 with radius R1
        pygame.draw.circle(screen, WHITE, p1, r1)
        
        # Draw vertical white line from P1 to P2
        pygame.draw.line(screen, WHITE, p1, p2, 1)
        
        # Draw horizontal black lines from P2 to A1 and A2
        pygame.draw.line(screen, BLACK, p2, a1, 1)
        pygame.draw.line(screen, BLACK, p2, a2, 1)
        
        # Draw P2 point
        pygame.draw.circle(screen, RED, p2, 3)
        text = font.render("P2", True, RED)
        screen.blit(text, (p2[0] + 5, p2[1] + 5))
        
        # Draw A1 and A2 points
        pygame.draw.circle(screen, RED, a1, 3)
        text = font.render("A1", True, RED)
        screen.blit(text, (a1[0] - 20, a1[1] + 5))
        
        pygame.draw.circle(screen, RED, a2, 3)
        text = font.render("A2", True, RED)
        screen.blit(text, (a2[0] + 5, a2[1] + 5))
        
        # Create a surface for the triangle minus circles
        mask_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Draw the white filled triangle
        pygame.draw.polygon(mask_surface, WHITE, (p1, a1, a2))
        
        # Subtract the grey circles at A1 and A2
        pygame.draw.circle(mask_surface, (0, 0, 0, 0), a1, int(r2))
        pygame.draw.circle(mask_surface, (0, 0, 0, 0), a2, int(r2))
        
        # Blit the mask to the screen
        screen.blit(mask_surface, (0, 0))
        
        # Display parameter values
        r1_text = font.render(f"R1 = {r1}", True, WHITE)
        h_text = font.render(f"H = {h}", True, WHITE)
        r2_text = font.render(f"R2 = {r2:.2f}", True, WHITE)
        
        screen.blit(r1_text, (10, 10))
        screen.blit(h_text, (10, 30))
        screen.blit(r2_text, (10, 50))
        
        # Update the display
        pygame.display.flip()
        clock.tick(60)
    
    # Clean up
    param_panel.on_close()
    pygame.quit()

if __name__ == "__main__":
    main()