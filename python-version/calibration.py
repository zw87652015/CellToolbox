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
        
        # Store screen circle parameters
        scale_x = self.projector_width / 2560
        scale_y = self.projector_height / 1600
        self.screen_circle_x = int(1000 * scale_x)
        self.screen_circle_y = int(1200 * scale_y)
        self.screen_circle_radius = int(80 * min(scale_x, scale_y))
        
        # Initialize calibration parameters
        self.calibration_scale = None
        self.calibration_offset_x = None
        self.calibration_offset_y = None
        self.fov_screen_corners = None
        
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
            # if center and radius:
            #     print(f"Camera circle detected - Center: {center}, Radius: {radius}")
            cv2.imshow("Camera View", marked_frame)
            cv2.waitKey(1)
        
        # Schedule next update
        self.root.after(30, self.update_camera_view)
        
    def start_calibration(self):
        """Triggered when calibration button is clicked"""
        ret, frame = self.cap.read()
        if ret:
            marked_frame, center, radius = self.detect_circle(frame)
            if center and radius:
                print("\nCalibration circle recorded:")
                print(f"  Camera circle - Center: {center}, Radius: {radius}")
                print(f"  Screen circle - Center: ({self.screen_circle_x}, {self.screen_circle_y}), Radius: {self.screen_circle_radius}")
                
                # Calculate scale factor (screen/camera)
                self.calibration_scale = self.screen_circle_radius / radius
                
                # Calculate offset between screen and camera centers
                self.calibration_offset_x = self.screen_circle_x - center[0] * self.calibration_scale
                self.calibration_offset_y = self.screen_circle_y - center[1] * self.calibration_scale
                
                # Calculate FOV corners in camera coordinates
                camera_corners = [
                    (0, 0),  # Top-left
                    (self.camera_width, 0),  # Top-right
                    (self.camera_width, self.camera_height),  # Bottom-right
                    (0, self.camera_height)  # Bottom-left
                ]
                
                # Transform corners to screen coordinates
                self.fov_screen_corners = []
                for cx, cy in camera_corners:
                    screen_x = int(cx * self.calibration_scale + self.calibration_offset_x)
                    screen_y = int(cy * self.calibration_scale + self.calibration_offset_y)
                    self.fov_screen_corners.append((screen_x, screen_y))
                
                # Clear previous FOV outline if any
                self.canvas.delete("fov")
                
                # Draw FOV outline on screen
                for i in range(len(self.fov_screen_corners)):
                    start = self.fov_screen_corners[i]
                    end = self.fov_screen_corners[(i + 1) % len(self.fov_screen_corners)]
                    self.canvas.create_line(start[0], start[1], end[0], end[1],
                                         fill='red', width=2, tags="fov")
                
                print("\nCamera-Screen Transformation Parameters:")
                print(f"  Scale factor: {self.calibration_scale:.3f}")
                print(f"  Offset X: {self.calibration_offset_x:.1f} pixels")
                print(f"  Offset Y: {self.calibration_offset_y:.1f} pixels")
                print("\nField of View on Screen:")
                print(f"  Top-left: {self.fov_screen_corners[0]}")
                print(f"  Top-right: {self.fov_screen_corners[1]}")
                print(f"  Bottom-right: {self.fov_screen_corners[2]}")
                print(f"  Bottom-left: {self.fov_screen_corners[3]}")
            else:
                print("\nNo circle detected during calibration")
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
