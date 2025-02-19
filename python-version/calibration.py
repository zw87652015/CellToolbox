import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import time

class ProjectorCameraCalibration:
    def __init__(self):
        self.projector_width = 1920
        self.projector_height = 1080
        self.camera_width = 640
        self.camera_height = 480
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        print(f"Camera resolution: {self.camera_width}x{self.camera_height}")
        
        # Create calibration pattern
        self.pattern_spacing = 200  
        self.dot_size = 8  
        self.fov_corners = None  
        self.create_windows()
        
    def create_windows(self):
        # Create pattern window
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        
        # Get actual screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        self.canvas = tk.Canvas(self.root, 
                              width=self.screen_width, 
                              height=self.screen_height, 
                              bg='black',
                              highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Create camera window
        cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera View", self.camera_width, self.camera_height)
        
        # Create calibration button window
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Calibration Control")
        self.control_window.geometry("200x150")  # Made taller for two buttons
        
        # Add calibrate button
        self.calibrate_button = tk.Button(self.control_window, 
                                        text="Start Calibration", 
                                        command=self.start_calibration)
        self.calibrate_button.pack(pady=10)
        
        # Add close button
        self.close_button = tk.Button(self.control_window, 
                                    text="Close Program", 
                                    command=self.cleanup_and_close,
                                    bg='red', fg='white')
        self.close_button.pack(pady=10)
        
        # Draw initial pattern
        self.draw_calibration_pattern()
        
    def update_camera_view(self):
        """Update camera view continuously"""
        ret, frame = self.cap.read()
        if ret:
            cv2.imshow("Camera View", frame)
            cv2.waitKey(1)
        
        # Schedule next update
        self.root.after(30, self.update_camera_view)  
        
    def start_calibration(self):
        """Triggered when calibration button is clicked"""
        self.calibrate_button.config(state='disabled')
        
        # Capture current frame
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame")
            self.calibrate_button.config(state='normal')
            return
            
        # Detect pattern points in the captured frame
        camera_points = self.detect_pattern_in_camera(frame)
        if len(camera_points) < 4:
            print("Not enough pattern points detected")
            self.calibrate_button.config(state='normal')
            return
        
        # Convert points to numpy arrays
        camera_points = np.array(camera_points, dtype=np.float32)
        
        # Create corresponding screen points based on grid
        screen_points = []
        cell_size = 100
        margin = 40
        
        for cam_pt in camera_points:
            # Estimate grid position based on point location
            grid_x = round((cam_pt[0] - margin) / cell_size)
            grid_y = round((cam_pt[1] - margin) / cell_size)
            
            # Convert grid position to screen coordinates
            screen_x = margin + grid_x * cell_size
            screen_y = margin + grid_y * cell_size
            screen_points.append([screen_x, screen_y])
        
        screen_points = np.array(screen_points, dtype=np.float32)
        
        # Debug: Show point correspondences
        debug_correspondences = np.zeros((max(frame.shape[0], self.screen_height), 
                                        frame.shape[1] + self.screen_width, 3), 
                                       dtype=np.uint8)
        # Draw camera view
        debug_correspondences[0:frame.shape[0], 0:frame.shape[1]] = frame
        
        # Draw screen pattern
        pattern_img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        for i in range(0, len(screen_points)):
            cv2.circle(pattern_img, 
                      (int(screen_points[i][0]), int(screen_points[i][1])), 
                      3, (0, 255, 0), -1)
            
        debug_correspondences[0:self.screen_height, 
                            frame.shape[1]:frame.shape[1]+self.screen_width] = pattern_img
        
        # Draw correspondence lines
        for i in range(len(camera_points)):
            pt1 = (int(camera_points[i][0]), int(camera_points[i][1]))
            pt2 = (int(screen_points[i][0]) + frame.shape[1], int(screen_points[i][1]))
            cv2.line(debug_correspondences, pt1, pt2, (0, 255, 255), 1)
            # Number the points
            cv2.putText(debug_correspondences, str(i), pt1, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            cv2.putText(debug_correspondences, str(i), pt2, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        cv2.imshow("Point Correspondences", debug_correspondences)
        
        # Calculate homography
        H, mask = cv2.findHomography(camera_points, screen_points, cv2.RANSAC, 5.0)
        print("\nHomography matrix:")
        print(H)
        print("\nRANSAC mask (1 = inlier, 0 = outlier):")
        print(mask.ravel())
        
        # Map camera corners to screen space
        camera_corners = np.array([
            [0, 0],
            [self.camera_width, 0],
            [self.camera_width, self.camera_height],
            [0, self.camera_height]
        ], dtype=np.float32)
        
        camera_corners_homog = np.ones((4, 3))
        camera_corners_homog[:, :2] = camera_corners
        screen_corners = np.dot(H, camera_corners_homog.T).T
        screen_corners = screen_corners[:, :2] / screen_corners[:, 2:]
        
        self.fov_corners = screen_corners.astype(np.int32)
        self.draw_fov()
        print("\nCamera FOV corners in screen coordinates:")
        print(self.fov_corners)
        
        # Debug: Draw the mapped FOV on camera view
        debug_fov = frame.copy()
        for i in range(4):
            pt1 = (int(camera_corners[i][0]), int(camera_corners[i][1]))
            pt2 = (int(camera_corners[(i+1)%4][0]), int(camera_corners[(i+1)%4][1]))
            cv2.line(debug_fov, pt1, pt2, (0, 0, 255), 2)
        cv2.imshow("Camera FOV", debug_fov)
        
        self.calibrate_button.config(state='normal')
        
    def detect_pattern_in_camera(self, frame):
        """Detect the calibration pattern in camera view"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        # Threshold to get bright lines
        _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY)
        
        # Find lines using Hough transform
        lines = cv2.HoughLinesP(thresh, 1, np.pi/180, 50, 
                               minLineLength=30, maxLineGap=10)
        
        if lines is None:
            return []
            
        # Separate horizontal and vertical lines
        horizontal_lines = []
        vertical_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.arctan2(y2 - y1, x2 - x1))
            
            # Classify lines as horizontal or vertical based on angle
            if angle < np.pi/4 or angle > 3*np.pi/4:  # Horizontal
                horizontal_lines.append(line[0])
            else:  # Vertical
                vertical_lines.append(line[0])
        
        # Find intersection points
        intersection_points = []
        for h_line in horizontal_lines:
            for v_line in vertical_lines:
                h_x1, h_y1, h_x2, h_y2 = h_line
                v_x1, v_y1, v_x2, v_y2 = v_line
                
                # Line equations
                A = np.array([
                    [h_y2 - h_y1, h_x1 - h_x2],
                    [v_y2 - v_y1, v_x1 - v_x2]
                ])
                b = np.array([
                    [h_y2*h_x1 - h_y1*h_x2],
                    [v_y2*v_x1 - v_y1*v_x2]
                ])
                
                try:
                    x, y = np.linalg.solve(A, b)
                    # Check if intersection is within line segments
                    if (min(h_x1, h_x2) <= x[0] <= max(h_x1, h_x2) and
                        min(v_x1, v_x2) <= x[0] <= max(v_x1, v_x2) and
                        min(h_y1, h_y2) <= y[0] <= max(h_y1, h_y2) and
                        min(v_y1, v_y2) <= y[0] <= max(v_y1, v_y2)):
                        intersection_points.append((int(x[0]), int(y[0])))
                except np.linalg.LinAlgError:
                    continue
        
        # Show intermediate results for debugging
        debug_frame = frame.copy()
        
        # Draw horizontal lines in blue
        for line in horizontal_lines:
            x1, y1, x2, y2 = line
            cv2.line(debug_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # Draw vertical lines in green
        for line in vertical_lines:
            x1, y1, x2, y2 = line
            cv2.line(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw intersection points in red
        for pt in intersection_points:
            cv2.circle(debug_frame, pt, 5, (0, 0, 255), -1)
        
        debug_images = np.hstack([gray, enhanced, thresh])
        cv2.imshow("Processing Steps", debug_images)
        cv2.imshow("Detected Pattern", debug_frame)
        
        return intersection_points
        
    def draw_fov(self):
        """Draw FOV rectangle on the pattern window"""
        if self.fov_corners is not None:
            # Clear previous FOV rectangle
            self.draw_calibration_pattern()  # Redraw pattern
            
            # Draw FOV rectangle
            points = self.fov_corners.reshape((-1, 2))
            for i in range(4):
                start = tuple(points[i])
                end = tuple(points[(i + 1) % 4])
                self.canvas.create_line(start[0], start[1], 
                                     end[0], end[1], 
                                     fill='red', width=4)
                # Draw corner points
                self.canvas.create_oval(start[0]-5, start[1]-5,
                                     start[0]+5, start[1]+5,
                                     fill='red', outline='red')
            
            # Draw corner labels
            labels = ['Top-Left', 'Top-Right', 'Bottom-Right', 'Bottom-Left']
            for i, label in enumerate(labels):
                self.canvas.create_text(points[i][0], points[i][1]-15,
                                     text=label, fill='red',
                                     font=('Arial', 12, 'bold'))
            
            self.root.update()
        
    def draw_calibration_pattern(self):
        """Draw a grid pattern with unique features for calibration"""
        self.canvas.delete("all")
        
        # Calculate safe margins
        margin = 40
        usable_width = self.screen_width - 2*margin
        usable_height = self.screen_height - 2*margin
        
        # Create position-encoding pattern
        cell_size = 100  
        num_cols = usable_width // cell_size
        num_rows = usable_height // cell_size
        
        print(f"Screen dimensions: {self.screen_width}x{self.screen_height}")
        print(f"Usable area: {usable_width}x{usable_height}")
        print(f"Cell size: {cell_size} pixels")
        print(f"Grid size: {num_cols}x{num_rows} cells")
        
        # Draw position-encoding cells
        for i in range(num_cols):
            for j in range(num_rows):
                x = margin + (i * cell_size)
                y = margin + (j * cell_size)
                
                if x < self.screen_width - cell_size and y < self.screen_height - cell_size:
                    # Draw cell border for visibility
                    self.canvas.create_rectangle(x, y, x + cell_size, y + cell_size, 
                                              outline='gray')
                    
                    # Encode X position (vertical lines)
                    x_code = format(i, '04b')  
                    for bit_idx, bit in enumerate(x_code):
                        if bit == '1':
                            line_x = x + (bit_idx + 1) * cell_size/6
                            self.canvas.create_line(line_x, y, line_x, y + cell_size, 
                                                 fill='white', width=3)
                    
                    # Encode Y position (horizontal lines)
                    y_code = format(j, '04b')  
                    for bit_idx, bit in enumerate(y_code):
                        if bit == '1':
                            line_y = y + (bit_idx + 1) * cell_size/6
                            self.canvas.create_line(x, line_y, x + cell_size, line_y, 
                                                 fill='white', width=3)
        
        self.root.update()
        
    def run(self):
        """Main loop to run the calibration system"""
        self.update_camera_view()  
        self.root.mainloop()
        
    def cleanup_and_close(self):
        """Clean up resources and close the application"""
        # Release camera
        if hasattr(self, 'cap'):
            self.cap.release()
        
        # Close all opencv windows
        cv2.destroyAllWindows()
        
        # Close main window
        self.root.quit()
        self.root.destroy()
        
    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    calibrator = ProjectorCameraCalibration()
    try:
        calibrator.run()
    finally:
        calibrator.cleanup()

if __name__ == "__main__":
    main()
