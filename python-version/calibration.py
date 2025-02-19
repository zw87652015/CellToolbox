import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import time

class ProjectorCameraCalibration:
    def __init__(self):
        self.projector_width = 1920
        self.projector_height = 1080
        self.camera_width = 1200
        self.camera_height = 675
        
        # Initialize camera
        self.cap = cv2.VideoCapture(1)
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
            
        # Detect pattern and analyze line distances
        camera_pattern = self.detect_pattern_in_camera(frame)
        if camera_pattern is None:
            print("Failed to detect pattern")
            self.calibrate_button.config(state='normal')
            return
            
        # Find pattern location
        self.fov_corners = self.find_pattern_location(camera_pattern)
        if self.fov_corners is not None:
            self.draw_fov()
            print("\nCamera FOV corners in screen coordinates:")
            print(self.fov_corners)
        else:
            print("Failed to locate pattern")
        
        self.calibrate_button.config(state='normal')
        
    def detect_pattern_in_camera(self, frame):
        """Detect the calibration pattern in camera view and analyze line distances"""
        # Flip frame horizontally
        frame = cv2.flip(frame, 1)
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Use a gentle Gaussian blur
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # Simple thresholding with high value to get just the bright lines
        _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)
        
        # Clean up noise with a small closing operation
        kernel = np.ones((3,3), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find lines using Hough transform
        lines = cv2.HoughLinesP(cleaned, 1, np.pi/180, 
                               threshold=50,
                               minLineLength=40, 
                               maxLineGap=10)
        
        if lines is None:
            return None
            
        # Separate horizontal and vertical lines
        horizontal_lines = []
        vertical_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.arctan2(y2 - y1, x2 - x1))
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            
            # Use stricter angle criteria and minimum length
            if angle < np.pi/6 or angle > 5*np.pi/6:  # Horizontal (±30°)
                y_avg = (y1 + y2) / 2  # Use average y-coordinate
                x_min, x_max = min(x1, x2), max(x1, x2)
                if length > 30:  # Minimum length threshold
                    horizontal_lines.append((y_avg, (x_min, x_max)))
            elif np.pi/3 <= angle <= 2*np.pi/3:  # Vertical (±30° from vertical)
                x_avg = (x1 + x2) / 2  # Use average x-coordinate
                y_min, y_max = min(y1, y2), max(y1, y2)
                if length > 30:  # Minimum length threshold
                    vertical_lines.append((x_avg, (y_min, y_max)))
        
        # Remove duplicate lines (lines that are very close to each other)
        def merge_close_lines(lines, threshold=10):
            if not lines:
                return []
            lines.sort()  # Sort by position
            merged = []
            current = lines[0]
            
            for line in lines[1:]:
                if abs(line[0] - current[0]) < threshold:
                    # Merge lines by averaging position and extending range
                    pos = (current[0] + line[0]) / 2
                    range_min = min(current[1][0], line[1][0])
                    range_max = max(current[1][1], line[1][1])
                    current = (pos, (range_min, range_max))
                else:
                    merged.append(current)
                    current = line
            merged.append(current)
            return merged
        
        horizontal_lines = merge_close_lines(horizontal_lines)
        vertical_lines = merge_close_lines(vertical_lines)
        
        # Calculate distances between adjacent lines
        h_distances = []
        v_distances = []
        
        for i in range(1, len(horizontal_lines)):
            dist = horizontal_lines[i][0] - horizontal_lines[i-1][0]
            h_distances.append(dist)
            
        for i in range(1, len(vertical_lines)):
            dist = vertical_lines[i][0] - vertical_lines[i-1][0]
            v_distances.append(dist)
        
        # Show intermediate results for debugging
        debug_frame = frame.copy()
        
        # Draw horizontal lines in blue
        for y, (x1, x2) in horizontal_lines:
            cv2.line(debug_frame, (int(x1), int(y)), (int(x2), int(y)), (255, 0, 0), 2)
            
        # Draw vertical lines in green
        for x, (y1, y2) in vertical_lines:
            cv2.line(debug_frame, (int(x), int(y1)), (int(x), int(y2)), (0, 255, 0), 2)
        
        # Draw distances
        for i, dist in enumerate(h_distances):
            y = (horizontal_lines[i][0] + horizontal_lines[i+1][0]) // 2
            x = min(horizontal_lines[i][1][0], horizontal_lines[i+1][1][0])
            cv2.putText(debug_frame, f"{dist:.1f}", (int(x), int(y)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
        for i, dist in enumerate(v_distances):
            x = (vertical_lines[i][0] + vertical_lines[i+1][0]) // 2
            y = min(vertical_lines[i][1][0], vertical_lines[i+1][1][0])
            cv2.putText(debug_frame, f"{dist:.1f}", (int(x), int(y)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Show all processing steps
        debug_images = np.hstack([
            cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
        ])
        cv2.imshow("Processing Steps", debug_images)
        cv2.imshow("Detected Pattern", debug_frame)
        
        return {
            'horizontal_lines': horizontal_lines,
            'vertical_lines': vertical_lines,
            'h_distances': h_distances,
            'v_distances': v_distances
        }
        
    def find_pattern_location(self, camera_pattern):
        """Find where in the screen pattern the camera pattern matches"""
        if camera_pattern is None:
            return None
            
        # Get screen pattern properties
        cell_size = 100  # Size of each grid cell in screen coordinates
        screen_margin = 40  # Screen pattern margin
        
        # Calculate the average cell size in camera pixels
        avg_h_dist = np.mean(camera_pattern['h_distances']) if camera_pattern['h_distances'] else 0
        avg_v_dist = np.mean(camera_pattern['v_distances']) if camera_pattern['v_distances'] else 0
        
        if avg_h_dist == 0 or avg_v_dist == 0:
            print("Failed to calculate average distances")
            return None
            
        # Calculate number of cells visible in camera view
        h_cells = len(camera_pattern['h_distances']) + 1
        v_cells = len(camera_pattern['v_distances']) + 1
        
        print("\nDebug Info:")
        print(f"Average horizontal distance in camera pixels: {avg_h_dist:.1f}")
        print(f"Average vertical distance in camera pixels: {avg_v_dist:.1f}")
        print(f"Number of cells: {h_cells} rows x {v_cells} columns")
        
        # Get the bounds of detected pattern in camera view
        left = min(x for x, _ in camera_pattern['vertical_lines'])
        right = max(x for x, _ in camera_pattern['vertical_lines'])
        top = min(y for y, _ in camera_pattern['horizontal_lines'])
        bottom = max(y for y, _ in camera_pattern['horizontal_lines'])
        
        # Calculate pattern width and height in camera pixels
        pattern_width_cam = right - left
        pattern_height_cam = bottom - top
        
        # Calculate pattern width and height in screen pixels
        pattern_width_screen = v_cells * cell_size
        pattern_height_screen = h_cells * cell_size
        
        # Calculate scale factors
        scale_x = pattern_width_screen / pattern_width_cam
        scale_y = pattern_height_screen / pattern_height_cam
        
        print(f"Pattern size in camera: {pattern_width_cam:.1f} x {pattern_height_cam:.1f} pixels")
        print(f"Pattern size in screen: {pattern_width_screen} x {pattern_height_screen} pixels")
        print(f"Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
        
        # Find leftmost visible cell in screen coordinates
        leftmost_cell = round((left - screen_margin) / avg_v_dist)
        topmost_cell = round((top - screen_margin) / avg_h_dist)
        
        # Convert camera coordinates to screen coordinates
        screen_left = screen_margin + leftmost_cell * cell_size
        screen_right = screen_left + pattern_width_screen
        screen_top = screen_margin + topmost_cell * cell_size
        screen_bottom = screen_top + pattern_height_screen
        
        print(f"Screen coordinates: left={screen_left}, right={screen_right}, top={screen_top}, bottom={screen_bottom}")
        
        # Create corner points for FOV
        return np.array([
            [screen_left, screen_top],
            [screen_right, screen_top],
            [screen_right, screen_bottom],
            [screen_left, screen_bottom]
        ], dtype=np.int32)
        
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
