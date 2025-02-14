import cv2
import numpy as np
from skimage import filters, morphology, measure, segmentation
import sys
import tkinter as tk
from parameter_control import UnifiedUI

# Global variables for cell tracking and persistence
CAMERASELECTED = 0  # 0~infinity for USB camera index
previous_cells = []  # List to store bounding boxes of previously detected cells
cell_lifetimes = []  # List to track the remaining frames each cell will be displayed
CELL_MEMORY_FRAMES = 5  # Number of frames to keep tracking a cell after it disappears
MAX_MOVEMENT = 200  # Maximum allowed pixel distance for cell movement between frames
DISTANCE_THRESHOLD = 50  # Maximum distance threshold for cell identity matching

def calculate_iou(box1, box2):
    """Calculate Intersection over Union (IoU) between two bounding boxes.
    Args:
        box1, box2: Bounding boxes in format (y1, x1, y2, x2)
    Returns:
        float: IoU score between 0 and 1, where 1 indicates perfect overlap
    """
    x1 = max(box1[1], box2[1])
    y1 = max(box1[0], box2[0])
    x2 = min(box1[3], box2[3])
    y2 = min(box1[2], box2[2])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[3] - box1[1]) * (box1[2] - box1[0])
    area2 = (box2[3] - box2[1]) * (box2[2] - box2[0])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0

def calculate_center_distance(box1, box2):
    """Calculate Euclidean distance between centers of two bounding boxes.
    Args:
        box1, box2: Bounding boxes in format (y1, x1, y2, x2)
    Returns:
        float: Pixel distance between box centers
    """
    center1_x = (box1[1] + box1[3]) / 2
    center1_y = (box1[0] + box1[2]) / 2
    center2_x = (box2[1] + box2[3]) / 2
    center2_y = (box2[0] + box2[2]) / 2
    
    return np.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)

def non_max_suppression(boxes, scores, iou_threshold=0.2):
    """Apply Non-Maximum Suppression to remove redundant overlapping cell detections.
    Args:
        boxes: List of bounding boxes in format (y1, x1, y2, x2)
        scores: List of confidence scores for each box
        iou_threshold: IoU threshold to determine box overlap (default: 0.2)
    Returns:
        list: Filtered list of non-overlapping bounding boxes
    """
    if not boxes:
        return []
        
    # Convert to numpy array if not already
    boxes = np.array(boxes)
    
    # Get indices of boxes sorted by scores
    indices = np.argsort(scores)[::-1]
    
    keep = []
    while indices.size > 0:
        # Pick the box with highest score
        current = indices[0]
        keep.append(current)
        
        # Calculate IOU with rest of boxes
        ious = np.array([calculate_iou(boxes[current], boxes[i]) for i in indices[1:]])
        
        # Keep boxes with IOU less than threshold
        indices = indices[1:][ious < iou_threshold]
    
    return [boxes[i] for i in keep]

def process_frame(frame, params=None):
    """Process a video frame to detect and track cells.
    
    This function performs the following steps:
    1. Image preprocessing (grayscale conversion, denoising)
    2. Cell detection using multiple edge detection methods
    3. Morphological operations to refine cell regions
    4. Cell tracking using IoU and distance-based matching
    5. Visualization of detected cells
    
    Args:
        frame: Input BGR frame from video stream
        params: Dictionary of parameters for cell detection (optional)
    Returns:
        tuple: (frame with green rectangles, frame with white rectangles)
    """
    global previous_cells, cell_lifetimes
    
    if params is None:
        params = {
            'area': (50, 4000),
            'perimeter': (50, 300),
            'circularity': (0.8, 1.8),
            'cell_memory_frames': 5,
            'max_movement': 200,
            'distance_threshold': 50
        }
    
    # Make a copy of the frame to avoid modifying the original
    display_frame = frame.copy()
    
    # Create a black window for white rectangles
    black_window = np.zeros_like(frame)
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detect edges using multiple methods
    edges_canny = cv2.Canny(blurred, 50, 150)
    edges_sobel = filters.sobel(blurred)
    edges_combined = cv2.bitwise_or(edges_canny.astype(np.uint8), 
                                  (edges_sobel * 255).astype(np.uint8))
    
    # Threshold the combined edges
    _, binary = cv2.threshold(edges_combined, 25, 255, cv2.THRESH_BINARY)
    
    # Apply morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Label connected components
    label_image = measure.label(binary)
    
    # Measure properties of labeled regions
    current_cells = []
    for prop in measure.regionprops(label_image):
        area = prop.area
        perimeter = prop.perimeter
        circularity = (perimeter * perimeter) / (4 * np.pi * area)
        
        if (params['area'][0] < area < params['area'][1] and 
            params['perimeter'][0] < perimeter < params['perimeter'][1] and 
            params['circularity'][0] < circularity < params['circularity'][1]):
            
            bbox = prop.bbox
            height = bbox[2] - bbox[0]
            width = bbox[3] - bbox[1]
            
            if ((height > width and 1.5 * width > height) or 
                (width > height and 1.5 * height > width)):
                
                current_cells.append(bbox)
                
                # Draw rectangle on display frame
                cv2.rectangle(display_frame,
                            (bbox[1], bbox[0]),
                            (bbox[3], bbox[2]),
                            (0, 255, 0), 2)
                
                # Draw white rectangle on black window
                cv2.rectangle(black_window,
                            (bbox[1], bbox[0]),
                            (bbox[3], bbox[2]),
                            (255, 255, 255), -1)
    
    # Track cells between frames
    if previous_cells:
        # Update lifetimes for previous cells
        cell_lifetimes = [t - 1 for t in cell_lifetimes]
        
        # Match current cells with previous cells
        matched_prev_indices = set()
        matched_curr_indices = set()
        
        for i, prev_box in enumerate(previous_cells):
            if cell_lifetimes[i] <= 0:
                continue
                
            prev_center = ((prev_box[0] + prev_box[2]) / 2,
                          (prev_box[1] + prev_box[3]) / 2)
            
            min_dist = float('inf')
            best_match = -1
            
            for j, curr_box in enumerate(current_cells):
                if j in matched_curr_indices:
                    continue
                    
                curr_center = ((curr_box[0] + curr_box[2]) / 2,
                              (curr_box[1] + curr_box[3]) / 2)
                
                # Calculate distance between cell centers
                dist = np.sqrt((prev_center[0] - curr_center[0])**2 +
                             (prev_center[1] - curr_center[1])**2)
                
                if dist < min_dist and dist < params['max_movement']:
                    min_dist = dist
                    best_match = j
            
            if best_match >= 0 and min_dist < params['distance_threshold']:
                matched_prev_indices.add(i)
                matched_curr_indices.add(best_match)
                
                # Draw tracking line on display frame
                cv2.line(display_frame,
                        (int((previous_cells[i][1] + previous_cells[i][3]) / 2),
                         int((previous_cells[i][0] + previous_cells[i][2]) / 2)),
                        (int((current_cells[best_match][1] + current_cells[best_match][3]) / 2),
                         int((current_cells[best_match][0] + current_cells[best_match][2]) / 2)),
                        (255, 0, 0), 1)
        
        # Draw rectangles for unmatched previous cells with remaining lifetime
        for i, prev_box in enumerate(previous_cells):
            if i not in matched_prev_indices and cell_lifetimes[i] > 0:
                cv2.rectangle(black_window,
                            (prev_box[1], prev_box[0]),
                            (prev_box[3], prev_box[2]),
                            (255, 255, 255), -1)
    
    # Update previous cells and initialize lifetimes for new cells
    previous_cells = current_cells.copy()
    cell_lifetimes = [params['cell_memory_frames']] * len(current_cells)
    
    return display_frame, black_window

def main():
    """Main function to run the cell detection and tracking system.
    
    Sets up video capture, creates display windows, and runs the main
    processing loop. The program can be exited by:
    - Pressing 'q'
    - Clicking the Quit button
    - Closing the window
    """
    # Create unified UI
    ui = UnifiedUI()
    
    # Initialize video capture
    cap = cv2.VideoCapture(CAMERASELECTED)
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Get actual resolution
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera resolution set to: {actual_width}x{actual_height}")
    
    print("Press 'q' to quit")
    
    try:
        while not ui.quit_flag:
            # Update tkinter window
            ui.update()
            
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Get current parameters
            params = ui.parameters
            
            # Process frame and detect cells
            display_frame, black_window = process_frame(frame, params)
            
            # Update the UI frames
            ui.update_frame(display_frame, ui.cell_detection_canvas, "cell_detection")
            ui.update_frame(black_window, ui.white_rectangles_canvas, "white_rectangles")
            
            # Check for 'q' key press (wait for 1ms)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except tk.TkinterError:
        print("UI window was closed")
    finally:
        # Clean up
        cap.release()
        ui.root.destroy()

if __name__ == "__main__":
    main()
