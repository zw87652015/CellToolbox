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
        
        self.camera_width = 1024
        self.camera_height = 576
        
        # Initialize camera
        self.cap = cv2.VideoCapture(1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        
        # Get actual camera settings
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Camera resolution: {actual_width}x{actual_height}")
        
        # Store screen circle parameters
        scale_x = self.projector_width / 2560
        scale_y = self.projector_height / 1600
        
        # First circle (larger)
        self.screen_circle1_x = int(1000 * scale_x)
        self.screen_circle1_y = int(1200 * scale_y)
        self.screen_circle1_radius = int(80 * min(scale_x, scale_y))
        
        # Second circle (smaller)
        self.screen_circle2_x = int((1000 + 200) * scale_x)  # 200 pixels to the right
        self.screen_circle2_y = int(1200 * scale_y)  # Same y coordinate
        self.screen_circle2_radius = int(40 * min(scale_x, scale_y))
        
        # Initialize calibration parameters
        self.calibration_scale = None
        self.calibration_offset_x = None
        self.calibration_offset_y = None
        self.calibration_rotation = None
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
        
        # Draw first black circle (larger)
        self.canvas.create_oval(
            self.screen_circle1_x - self.screen_circle1_radius,
            self.screen_circle1_y - self.screen_circle1_radius,
            self.screen_circle1_x + self.screen_circle1_radius,
            self.screen_circle1_y + self.screen_circle1_radius,
            fill='black', outline='black'
        )
        
        # Draw second black circle (smaller)
        self.canvas.create_oval(
            self.screen_circle2_x - self.screen_circle2_radius,
            self.screen_circle2_y - self.screen_circle2_radius,
            self.screen_circle2_x + self.screen_circle2_radius,
            self.screen_circle2_y + self.screen_circle2_radius,
            fill='black', outline='black'
        )
        
        # Add rotation indicator line
        line_length = scaled_radius * 0.8
        self.canvas.create_line(scaled_x, scaled_y,
                              scaled_x + line_length, scaled_y,
                              fill='white', width=2)
        
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
        """Detect two black circles in the camera frame"""
        # Flip the frame horizontally
        frame = cv2.flip(frame, 1)
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("1. Grayscale", gray)
        
        # Use adaptive thresholding instead of Otsu's
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            21,  # Block size
            5    # C constant
        )
        
        # Optional: Add morphological operations to clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        cv2.imshow("2. Binary", binary)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        result = frame.copy()
        circles_found = []
        
        # Try to find two circles
        for contour in contours[:4]:  # Look at the four largest contours
            area = cv2.contourArea(contour)
            if area > 50:  # Lower minimum area threshold
                # Fit circle to contour
                (x, y), radius = cv2.minEnclosingCircle(contour)
                center = (int(x), int(y))
                radius = int(radius)
                
                # Calculate circularity
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                # Only accept if the shape is reasonably circular
                if circularity > 0.6:  # Slightly relaxed circularity threshold
                    # Calculate contour solidity
                    hull = cv2.convexHull(contour)
                    hull_area = cv2.contourArea(hull)
                    solidity = float(area) / hull_area
                    
                    # Additional check for solidity
                    if solidity > 0.8:
                        # Draw the circle and its center
                        cv2.circle(result, center, radius, (0, 255, 0), 2)
                        cv2.circle(result, center, 2, (0, 0, 255), 3)
                        circles_found.append((center, radius))
        
        if len(circles_found) == 2:
            # Sort circles by x-coordinate
            circles_found.sort(key=lambda x: x[0][0])
            return result, circles_found[0][0], circles_found[0][1], circles_found[1][0], circles_found[1][1]
        
        return result, None, None, None, None
        
    def update_camera_view(self):
        """Update camera view continuously"""
        ret, frame = self.cap.read()
        if ret:
            # Detect and mark circles
            marked_frame, center1, radius1, center2, radius2 = self.detect_circle(frame)
            cv2.imshow("Camera View", marked_frame)
            cv2.waitKey(1)
        
        # Schedule next update
        self.root.after(30, self.update_camera_view)
        
    def start_calibration(self):
        """Triggered when calibration button is clicked"""
        ret, frame = self.cap.read()
        if ret:
            marked_frame, center1, radius1, center2, radius2 = self.detect_circle(frame)
            if center1 and center2:
                print("\nCalibration circles recorded:")
                print(f"Circle 1 (larger) - Center: {center1}, Radius: {radius1}")
                print(f"Circle 2 (smaller) - Center: {center2}, Radius: {radius2}")
                print(f"Screen circles - Large: ({self.screen_circle1_x}, {self.screen_circle1_y}), R={self.screen_circle1_radius}")
                print(f"              - Small: ({self.screen_circle2_x}, {self.screen_circle2_y}), R={self.screen_circle2_radius}")
                
                # Calculate scale factor using the distance between circles
                camera_distance = np.sqrt((center2[0] - center1[0])**2 + (center2[1] - center1[1])**2)
                screen_distance = np.sqrt((self.screen_circle2_x - self.screen_circle1_x)**2 + 
                                       (self.screen_circle2_y - self.screen_circle1_y)**2)
                self.calibration_scale = screen_distance / camera_distance
                
                # Calculate rotation angle
                camera_angle = np.arctan2(center2[1] - center1[1], center2[0] - center1[0])
                screen_angle = np.arctan2(self.screen_circle2_y - self.screen_circle1_y,
                                        self.screen_circle2_x - self.screen_circle1_x)
                self.calibration_rotation = screen_angle - camera_angle
                
                # Calculate offset
                self.calibration_offset_x = self.screen_circle1_x - center1[0] * self.calibration_scale
                self.calibration_offset_y = self.screen_circle1_y - center1[1] * self.calibration_scale

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
                    # First apply scale and rotation
                    dx = cx - center1[0]
                    dy = cy - center1[1]
                    
                    # Rotate
                    rx = dx * np.cos(self.calibration_rotation) - dy * np.sin(self.calibration_rotation)
                    ry = dx * np.sin(self.calibration_rotation) + dy * np.cos(self.calibration_rotation)
                    
                    # Scale and translate
                    screen_x = int(rx * self.calibration_scale + self.screen_circle1_x)
                    screen_y = int(ry * self.calibration_scale + self.screen_circle1_y)
                    self.fov_screen_corners.append((screen_x, screen_y))
                
                # Clear previous FOV outline
                self.canvas.delete("fov")
                
                # Draw new FOV outline on screen
                for i in range(len(self.fov_screen_corners)):
                    start = self.fov_screen_corners[i]
                    end = self.fov_screen_corners[(i + 1) % len(self.fov_screen_corners)]
                    self.canvas.create_line(start[0], start[1], end[0], end[1],
                                         fill='red', width=2, tags="fov")
                
                # Save calibration data to file
                calibration_data = {
                    'scale': float(self.calibration_scale),
                    'rotation': float(self.calibration_rotation),
                    'offset_x': float(self.calibration_offset_x),
                    'offset_y': float(self.calibration_offset_y),
                    'camera_resolution': {
                        'width': self.camera_width,
                        'height': self.camera_height
                    },
                    'projector_resolution': {
                        'width': self.projector_width,
                        'height': self.projector_height
                    },
                    'fov_corners': self.fov_screen_corners,
                    'calibration_time': self.get_current_time()
                }
                
                self.save_calibration_data(calibration_data)
                
                print("\nCamera-Screen Transformation Parameters:")
                print(f"  Scale factor: {self.calibration_scale:.3f}")
                print(f"  Offset X: {self.calibration_offset_x:.1f} pixels")
                print(f"  Offset Y: {self.calibration_offset_y:.1f} pixels")
                print(f"  Rotation angle: {np.degrees(self.calibration_rotation):.1f}°")
                print("\nField of View on Screen:")
                print(f"  Top-left: {self.fov_screen_corners[0]}")
                print(f"  Top-right: {self.fov_screen_corners[1]}")
                print(f"  Bottom-right: {self.fov_screen_corners[2]}")
                print(f"  Bottom-left: {self.fov_screen_corners[3]}")
                
                print("\nCalibration data saved successfully!")
            else:
                print("Could not detect both calibration circles clearly. Please adjust the camera or lighting.")
            cv2.imshow("Camera View", marked_frame)
            cv2.waitKey(1)
        
    def get_current_time(self):
        """Get current time in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_calibration_data(self, data):
        """Save calibration data to a JSON file"""
        import json
        import os
        
        # Create calibration directory if it doesn't exist
        os.makedirs('calibration', exist_ok=True)
        
        # Save to a timestamped file
        filename = os.path.join('calibration', f'calibration_{data["calibration_time"].replace(":", "-")}.json')
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            
        # Also save to a 'latest' file
        latest_file = os.path.join('calibration', 'latest_calibration.json')
        with open(latest_file, 'w') as f:
            json.dump(data, f, indent=4)
            
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
