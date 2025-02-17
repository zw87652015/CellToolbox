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

def process_frame(frame, params):
    """Process a frame to detect and track cells"""
    global previous_cells, cell_lifetimes
    
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create visualization windows
    display_frame = frame.copy()
    black_window = np.zeros_like(frame)  # For green contours
    white_window = np.zeros_like(frame)  # For white rectangles
    final_seg = np.zeros_like(frame)
    
    # Get parameters
    area_min, area_max = params['area']
    perimeter_min, perimeter_max = params['perimeter']
    circularity_min, circularity_max = params['circularity']
    max_movement = params['max_movement']
    cell_memory_frames = params['cell_memory_frames']
    
    # Process each contour
    current_cells = []
    for contour in contours:
        # Calculate properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Check if the contour meets the criteria
        if (area_min <= area <= area_max and
            perimeter_min <= perimeter <= perimeter_max and
            circularity_min <= circularity <= circularity_max):
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            current_cells.append((y, x, y + h, x + w))
            
            # Draw green contour on black window
            cv2.drawContours(black_window, [contour], -1, (0, 255, 0), 2)
            cv2.drawContours(final_seg, [contour], -1, (0, 255, 0), -1)
            
            # Draw filled white rectangle on white window
            cv2.rectangle(white_window, (x, y), (x + w, y + h), (255, 255, 255), -1)
            
            # Draw green rectangle on display frame
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # Track cells between frames
    matched_prev_indices = set()
    matched_curr_indices = set()
    new_cell_lifetimes = [cell_memory_frames] * len(current_cells)
    
    if previous_cells:
        # Update tracking as before...
        if len(cell_lifetimes) < len(previous_cells):
            cell_lifetimes.extend([cell_memory_frames] * (len(previous_cells) - len(cell_lifetimes)))
        
        # Process unmatched previous cells
        for i, prev_box in enumerate(previous_cells):
            if i in matched_prev_indices:
                continue
            
            # Find best match among current cells
            best_match = -1
            best_score = float('inf')
            
            for j, curr_box in enumerate(current_cells):
                if j in matched_curr_indices:
                    continue
                
                # Calculate distance between box centers
                distance = calculate_center_distance(prev_box, curr_box)
                
                if distance < max_movement and distance < best_score:
                    best_score = distance
                    best_match = j
            
            if best_match >= 0:
                matched_prev_indices.add(i)
                matched_curr_indices.add(best_match)
                cell_lifetimes[i] = cell_memory_frames
                new_cell_lifetimes[best_match] = cell_lifetimes[i]
    
    # Update global tracking variables
    previous_cells = current_cells.copy()
    cell_lifetimes = new_cell_lifetimes
    
    return display_frame, white_window, final_seg

def main():
    """Main function to run the cell detection and tracking system."""
    # Initialize video capture
    cap = cv2.VideoCapture(CAMERASELECTED)
    if not cap.isOpened():
        print(f"Error: Could not open camera {CAMERASELECTED}")
        return
    
    # Initialize UI
    ui = UnifiedUI()
    
    while not ui.quit_flag:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Process frame
        display_frame, white_window, _ = process_frame(frame, ui.get_parameters())
        
        # Update UI
        ui.update_video_display(display_frame, white_window)
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
