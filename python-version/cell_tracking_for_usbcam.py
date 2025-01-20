import cv2
import numpy as np
from skimage import filters, morphology, measure, segmentation
import sys

# Global variables for tracking
previous_cells = []  # List to store previous cell positions
cell_lifetimes = []  # List to store how long each cell has been detected
CELL_MEMORY_FRAMES = 4  # Reduced from 10 to 5 frames
MAX_MOVEMENT = 80  # Maximum pixels a cell can move between frames
DISTANCE_THRESHOLD = 50  # Maximum distance to consider it's the same cell

def calculate_iou(box1, box2):
    """Calculate Intersection over Union between two bounding boxes."""
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
    """Calculate the distance between centers of two bounding boxes."""
    center1_x = (box1[1] + box1[3]) / 2
    center1_y = (box1[0] + box1[2]) / 2
    center2_x = (box2[1] + box2[3]) / 2
    center2_y = (box2[0] + box2[2]) / 2
    
    return np.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)

def non_max_suppression(boxes, scores, iou_threshold=0.2):
    """Apply Non-Maximum Suppression to remove overlapping detections."""
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

def process_frame(frame):
    """Process a single frame to detect cells."""
    global previous_cells, cell_lifetimes
    
    # Make a copy of the frame to avoid modifying the original
    display_frame = frame.copy()
    
    # Convert BGR to grayscale
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Convert to double and denoise
    double_image = gray_image.astype(np.float32) / 255.0
    denoised_image = cv2.GaussianBlur(double_image, (3, 3), 2)
    
    # Binary image
    _, binary_image = cv2.threshold(gray_image, 0, 255, 
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary_image = ~binary_image
    
    # Edge detection
    edge_canny = cv2.Canny((denoised_image * 255).astype(np.uint8), 30, 150)
    
    # Convert to 8-bit
    img_8bit = (denoised_image * 255).astype(np.uint8)
    
    # Edge detection using various methods
    sobelx = cv2.Sobel(img_8bit, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img_8bit, cv2.CV_64F, 0, 1, ksize=3)
    edge_sobel = np.sqrt(sobelx**2 + sobely**2)
    edge_sobel = edge_sobel > 30
    
    # Edge combination
    roi_seg = edge_canny.astype(bool) | edge_sobel | binary_image.astype(bool)
    
    # Final processing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    final_seg = morphology.remove_small_objects(final_seg.astype(bool))
    
    # Fill holes and remove small areas
    final_seg = morphology.remove_small_holes(final_seg)
    final_seg = morphology.remove_small_objects(final_seg, min_size=100)
    
    # Label connected components
    labeled_image = measure.label(final_seg)
    
    # Create a black background window with fixed resolution
    black_window = np.zeros((768, 1024, 3), dtype=np.uint8)
    
    # Calculate properties and draw rectangles
    props = measure.regionprops(labeled_image)
    
    # Current frame detections
    current_cells = []
    detection_scores = []
    
    for prop in props:
        area = prop.area
        perimeter = prop.perimeter
        circularity = (perimeter * perimeter) / (4 * np.pi * area)
        
        if (50 < area < 4000 and 
            50 < perimeter < 300 and 
            0.8 < circularity < 1.8):
            
            bbox = prop.bbox
            height = bbox[2] - bbox[0]
            width = bbox[3] - bbox[1]
            
            if ((height > width and 1.5 * width > height) or 
                (width > height and 1.5 * height > width) or 
                (height == width)):
                # Calculate detection score based on circularity (closer to 1 is better)
                score = 1 - abs(1 - circularity)
                current_cells.append(bbox)
                detection_scores.append(score)
    
    # Apply Non-Maximum Suppression
    if current_cells:
        current_cells = non_max_suppression(current_cells, detection_scores)
    
    # Match current detections with previous ones
    matched_previous = set()
    matched_current = set()
    
    # Update existing cells
    new_previous_cells = []
    new_cell_lifetimes = []
    
    # Match current detections with previous ones
    for i, prev_bbox in enumerate(previous_cells):
        best_match = None
        best_score = float('inf')  # Lower is better
        
        for j, curr_bbox in enumerate(current_cells):
            if j in matched_current:
                continue
            
            # Calculate both IOU and distance
            iou = calculate_iou(prev_bbox, curr_bbox)
            distance = calculate_center_distance(prev_bbox, curr_bbox)
            
            # Skip if the cell has moved too far
            if distance > MAX_MOVEMENT:
                continue
            
            # Combined score (lower is better)
            # We want high IOU (closer to 1) and low distance
            score = distance * (1 - iou)
            
            if score < best_score:
                best_match = j
                best_score = score
        
        if best_match is not None and best_score < MAX_MOVEMENT:
            # Update the position with the new detection
            new_previous_cells.append(current_cells[best_match])
            new_cell_lifetimes.append(CELL_MEMORY_FRAMES)  # Reset lifetime
            matched_current.add(best_match)
            matched_previous.add(i)
        elif cell_lifetimes[i] > 0:
            # Keep the cell if it still has lifetime and hasn't moved too far
            new_previous_cells.append(prev_bbox)
            new_cell_lifetimes.append(cell_lifetimes[i] - 1)
    
    # Add new detections
    for i, curr_bbox in enumerate(current_cells):
        if i not in matched_current:
            new_previous_cells.append(curr_bbox)
            new_cell_lifetimes.append(CELL_MEMORY_FRAMES)
    
    # Update global tracking variables
    previous_cells = new_previous_cells
    cell_lifetimes = new_cell_lifetimes
    
    # Draw all active cells
    for bbox in previous_cells:
        # Draw rectangle on the display frame
        cv2.rectangle(display_frame, 
                    (bbox[1], bbox[0]), 
                    (bbox[3], bbox[2]), 
                    (0, 255, 0), 2)
        
        # Calculate scaled coordinates for the fixed resolution window
        scale_x = 1024 / frame.shape[1]
        scale_y = 768 / frame.shape[0]
        x1 = int(bbox[1] * scale_x)
        y1 = int(bbox[0] * scale_y)
        x2 = int(bbox[3] * scale_x)
        y2 = int(bbox[2] * scale_y)
        
        # Draw white filled rectangle on black window
        cv2.rectangle(black_window,
                    (x1, y1),
                    (x2, y2),
                    (255, 255, 255), -1)
    
    # Show both windows
    cv2.imshow('Cell Detection', display_frame)
    cv2.imshow('White Rectangles', black_window)
    
    return display_frame

def on_window_close(event, x, y, flags, param):
    """Handle window close event"""
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.destroyAllWindows()
        sys.exit(0)

def main():
    # Initialize video capture
    cap = cv2.VideoCapture(0)
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Get actual resolution
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera resolution set to: {actual_width}x{actual_height}")
    
    # Create windows and set up close handlers
    cv2.namedWindow('Cell Detection', cv2.WINDOW_NORMAL)
    cv2.namedWindow('White Rectangles', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('White Rectangles', 1024, 768)
    
    # Set up window close handlers
    cv2.setMouseCallback('Cell Detection', on_window_close)
    cv2.setMouseCallback('White Rectangles', on_window_close)
    
    print("Press 'q' to quit")
    
    try:
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            
            if not ret:
                print("Failed to grab frame")
                break
                
            # Process frame and detect cells
            processed_frame = process_frame(frame)
            
            # Check for 'q' key press (wait for 1ms)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            # Check if windows were closed
            if cv2.getWindowProperty('Cell Detection', cv2.WND_PROP_VISIBLE) < 1 or \
               cv2.getWindowProperty('White Rectangles', cv2.WND_PROP_VISIBLE) < 1:
                break
    
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        # Force exit to ensure all windows and resources are released
        sys.exit(0)

if __name__ == "__main__":
    main()
