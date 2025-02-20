import cv2
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk

class ProjectorCameraCalibration:
    def __init__(self):
        # Get the screen resolution
        root = tk.Tk()
        self.projector_width = root.winfo_screenwidth()
        self.projector_height = root.winfo_screenheight()
        root.destroy()
        
        print(f"Screen resolution: {self.projector_width}x{self.projector_height}")
        
        self.camera_width = 800
        self.camera_height = 600
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        
        # Get actual camera settings
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Camera resolution: {actual_width}x{actual_height}")
        
        self.create_windows()
        
    def create_windows(self):
        # Create pattern window
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        
        # Calculate scaling factors to map from 2560x1600 to actual screen resolution
        scale_x = self.projector_width / 2560
        scale_y = self.projector_height / 1600
        
        # Scale the circle position and size
        original_x, original_y = 1000, 1200  # Original coordinates in 2560x1600
        original_radius = 80  # Original radius reduced to 80
        
        # Scale to actual screen resolution
        scaled_x = int(original_x * scale_x)
        scaled_y = int(original_y * scale_y)
        scaled_radius = int(original_radius * min(scale_x, scale_y))  # Use minimum scale to keep circle round
        
        # Create canvas with white background
        self.canvas = tk.Canvas(self.root, 
                              width=self.projector_width,
                              height=self.projector_height,
                              bg='white',
                              highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Draw black circle at scaled coordinates
        self.canvas.create_oval(scaled_x - scaled_radius, scaled_y - scaled_radius,
                              scaled_x + scaled_radius, scaled_y + scaled_radius,
                              fill='black', outline='black')
        
        # Create camera window
        cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera View", self.camera_width, self.camera_height)
        
        # Create control window
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Calibration Control")
        self.control_window.geometry("200x150")  
        
        # Add calibrate button
        self.calibrate_button = ttk.Button(
            self.control_window, 
            text="Start Calibration", 
            command=self.start_calibration
        )
        self.calibrate_button.pack(pady=10)
        
        # Add close button
        self.close_button = ttk.Button(
            self.control_window, 
            text="Close Program", 
            command=self.cleanup_and_close,
            style='Accent.TButton'
        )
        self.close_button.pack(pady=10)
        
        # Create accent style for close button
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='red')
        
    def detect_circle(self, frame):
        """Detect black circle in the camera frame"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest contour
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # If contour is large enough and roughly circular
            if area > 100:
                # Fit circle to contour
                (x, y), radius = cv2.minEnclosingCircle(largest_contour)
                center = (int(x), int(y))
                radius = int(radius)
                
                # Draw the circle
                result = frame.copy()
                cv2.circle(result, center, radius, (0, 255, 0), 2)
                cv2.circle(result, center, 2, (0, 0, 255), 3)
                return result, center, radius
                
        return frame, None, None
        
    def update_camera_view(self):
        """Update camera view continuously"""
        ret, frame = self.cap.read()
        if ret:
            # Detect and mark circle
            marked_frame, center, radius = self.detect_circle(frame)
            if center and radius:
                print(f"Camera circle detected - Center: {center}, Radius: {radius}")
            cv2.imshow("Camera View", marked_frame)
            cv2.waitKey(1)
        
        # Schedule next update
        self.root.after(30, self.update_camera_view)
        
    def start_calibration(self):
        """Triggered when calibration button is clicked"""
        ret, frame = self.cap.read()
        if ret:
            marked_frame, center, radius = self.detect_circle(frame)
            cv2.imshow("Camera View", marked_frame)
            cv2.waitKey(1)
        
    def cleanup_and_close(self):
        """Clean up resources and close the application"""
        self.cleanup()
        self.root.quit()
        
    def cleanup(self):
        """Clean up resources"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        
    def run(self):
        """Main loop to run the calibration system"""
        self.update_camera_view()
        self.root.mainloop()
        self.cleanup()

def main():
    calibration = ProjectorCameraCalibration()
    calibration.run()

if __name__ == "__main__":
    main()
