import tkinter as tk
import subprocess
import sys
import os

class ShapesUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Manual Shapes Launcher")
        self.root.geometry("400x600")
        self.root.resizable(True, True)
        
        # Create frame for buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=50)
        
        # Create title
        title_label = tk.Label(self.button_frame, text="Manual Shapes Toolkit", font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Create buttons
        self.rectangle_button = tk.Button(
            self.button_frame, 
            text="Manual Rectangle", 
            command=self.launch_rectangle,
            width=20,
            height=2,
            font=("Arial", 12)
        )
        self.rectangle_button.pack(pady=10)
        
        self.donut_button = tk.Button(
            self.button_frame, 
            text="Manual Donut", 
            command=self.launch_donut,
            width=20,
            height=2,
            font=("Arial", 12)
        )
        self.donut_button.pack(pady=10)
        
        self.ushape_button = tk.Button(
            self.button_frame, 
            text="Manual U-Shape", 
            command=self.launch_ushape,
            width=20,
            height=2,
            font=("Arial", 12)
        )
        self.ushape_button.pack(pady=10)
        
        self.disk_button = tk.Button(
            self.button_frame, 
            text="Manual Disk", 
            command=self.launch_disk,
            width=20,
            height=2,
            font=("Arial", 12)
        )
        self.disk_button.pack(pady=10)
        
        # Create exit button
        self.exit_button = tk.Button(
            self.root, 
            text="Exit", 
            command=self.root.destroy,
            width=10,
            font=("Arial", 10)
        )
        self.exit_button.pack(side=tk.BOTTOM, pady=20)
    
    def launch_rectangle(self):
        """Launch the manual rectangle tool"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        rectangle_script = os.path.join(script_dir, "Manual_rectangles.py")
        subprocess.Popen([sys.executable, rectangle_script])
    
    def launch_donut(self):
        """Launch the manual donut tool"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        donut_script = os.path.join(script_dir, "Manual_donut.py")
        subprocess.Popen([sys.executable, donut_script])
    
    def launch_ushape(self):
        """Launch the manual U-shape tool"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ushape_script = os.path.join(script_dir, "Manual_u_shape.py")
        subprocess.Popen([sys.executable, ushape_script])
    
    def launch_disk(self):
        """Launch the manual disk tool"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        disk_script = os.path.join(script_dir, "Manual_disks.py")
        subprocess.Popen([sys.executable, disk_script])

def main():
    root = tk.Tk()
    app = ShapesUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
