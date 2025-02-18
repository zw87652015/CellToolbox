import cv2
import numpy as np
from skimage import filters, morphology, measure, segmentation
import sys
import tkinter as tk
from parameter_control import UnifiedUI
import os

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

def process_frame(frame, params, clahe_clip_limit=2.5, clahe_tile_size=10): 
    """Process a frame to detect and track cells"""
    global previous_cells, cell_lifetimes
    
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_tile_size, clahe_tile_size))
    enhanced_image = clahe.apply(gray)
    
    # Convert to float and apply Gaussian blur
    float_image = enhanced_image.astype(np.float32) / 255.0
    denoised_image = cv2.GaussianBlur(float_image, (3, 3), 2)
    
    # Kirsch operators for edge detection (4 main directions)
    kirsch_kernels = [
        np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float32),  # Vertical
        np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float32),  # Horizontal
        np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float32),  # Diagonal 1
        np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float32)   # Diagonal 2
    ]

    kirsch_outputs = []
    for kernel in kirsch_kernels:
        # Apply Kirsch filter (keeping float32)
        filtered = cv2.filter2D(denoised_image, -1, kernel)
        
        # Convert to absolute values
        filtered = np.abs(filtered)
        
        # Normalize to 0-1 range
        filtered_min = np.min(filtered)
        filtered_max = np.max(filtered)
        if filtered_max > filtered_min:  # Avoid division by zero
            filtered_norm = (filtered - filtered_min) / (filtered_max - filtered_min)
        else:
            filtered_norm = np.zeros_like(filtered)
        
        # Calculate Otsu threshold
        binary = filtered_norm > filters.threshold_otsu(filtered_norm)
        kirsch_outputs.append(binary)

    # Combine all Kirsch outputs
    binary = np.zeros_like(kirsch_outputs[0], dtype=bool)
    for output in kirsch_outputs:
        binary = binary | output
    
    # Convert to uint8 for contour detection
    binary = binary.astype(np.uint8) * 255

    # Remove small areas
    binary = morphology.remove_small_objects(binary.astype(bool), min_size=100)

    # Clean up - using less aggressive thinning
    binary = morphology.thin(binary, max_num_iter=1)

    # Fill small holes in cells to fix gaps
    binary = morphology.remove_small_holes(binary.astype(bool), area_threshold=100)
    binary = binary.astype(np.uint8) * 255

    # Calculate and filter based on more lenient eccentricity
    labeled = measure.label(binary)
    props = measure.regionprops(labeled)
    mask = np.zeros_like(binary, dtype=bool)
    
    for prop in props:
        # More lenient criteria for eccentricity and area
        if (prop.eccentricity < 0.99 and prop.area > 100) or (prop.area > 300):
            mask[labeled == prop.label] = True
    
    binary = mask.astype(np.uint8) * 255

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
    
    # Update final_seg with the binary mask
    final_seg = binary.copy()
    
    return display_frame, white_window, final_seg

def process_frame_debug(frame, output_dir, clahe_clip_limit=2.5, clahe_tile_size=10):
    """Process a frame and save intermediate steps"""
    import os
    
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(os.path.join(output_dir, '1-Grayscale.png'), gray)
    
    # Enhance contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_tile_size, clahe_tile_size))
    enhanced_image = clahe.apply(gray)
    cv2.imwrite(os.path.join(output_dir, '2-EnhancedContrast.png'), enhanced_image)
    
    # Convert to float and apply Gaussian blur
    float_image = enhanced_image.astype(np.float32) / 255.0
    denoised_image = cv2.GaussianBlur(float_image, (3, 3), 2)
    cv2.imwrite(os.path.join(output_dir, '3-GaussianBlur.png'), (denoised_image * 255).astype(np.uint8))
    
    # Kirsch operators for edge detection (4 main directions)
    kirsch_kernels = [
        np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float32),  # Vertical
        np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float32),  # Horizontal
        np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float32),  # Diagonal 1
        np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float32)   # Diagonal 2
    ]

    kirsch_outputs = []
    for i, kernel in enumerate(kirsch_kernels):
        # Apply Kirsch filter (keeping float32)
        filtered = cv2.filter2D(denoised_image, -1, kernel)
        
        # Convert to absolute values
        filtered = np.abs(filtered)
        
        # Normalize to 0-1 range
        filtered_min = np.min(filtered)
        filtered_max = np.max(filtered)
        if filtered_max > filtered_min:  # Avoid division by zero
            filtered_norm = (filtered - filtered_min) / (filtered_max - filtered_min)
        else:
            filtered_norm = np.zeros_like(filtered)
        
        # Calculate Otsu threshold
        binary = filtered_norm > filters.threshold_otsu(filtered_norm)
        kirsch_outputs.append(binary)
        
        # Save each direction's output
        cv2.imwrite(os.path.join(output_dir, f'4-KirschDirection{i+1}.png'), 
                   binary.astype(np.uint8) * 255)

    # Combine all Kirsch outputs
    binary = np.zeros_like(kirsch_outputs[0], dtype=bool)
    for output in kirsch_outputs:
        binary = binary | output
    
    # Convert to uint8 for contour detection
    binary = binary.astype(np.uint8) * 255
    cv2.imwrite(os.path.join(output_dir, '5-KirschCombined.png'), binary)

    # Remove small areas
    binary = morphology.remove_small_objects(binary.astype(bool), min_size=100)
    cv2.imwrite(os.path.join(output_dir, '6-SmallAreasRemoved.png'), 
                binary.astype(np.uint8) * 255)

    # Clean up - using less aggressive thinning
    binary = morphology.thin(binary, max_num_iter=1)
    cv2.imwrite(os.path.join(output_dir, '7-Thinned.png'), 
                binary.astype(np.uint8) * 255)

    # Fill small holes in cells to fix gaps
    binary = morphology.remove_small_holes(binary.astype(bool), area_threshold=100)
    binary = binary.astype(np.uint8) * 255
    cv2.imwrite(os.path.join(output_dir, '8-HolesFilled.png'), binary)

    # Calculate and filter based on more lenient eccentricity
    labeled = measure.label(binary)
    props = measure.regionprops(labeled)
    mask = np.zeros_like(binary, dtype=bool)
    
    for prop in props:
        # More lenient criteria for eccentricity and area
        if (prop.eccentricity < 0.99 and prop.area > 100) or (prop.area > 300):
            mask[labeled == prop.label] = True
    
    binary = mask.astype(np.uint8) * 255
    cv2.imwrite(os.path.join(output_dir, '9-FinalSegmentation.png'), binary)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create visualization windows
    display_frame = frame.copy()
    black_window = np.zeros_like(frame)  # For green contours
    white_window = np.zeros_like(frame)  # For white rectangles
    final_seg = np.zeros_like(frame)
    
    # Process each contour with more lenient criteria
    for contour in contours:
        # Calculate properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # More lenient parameters for debug visualization
        area_min, area_max = 100, 5000  # Reduced minimum area
        perimeter_min, perimeter_max = 30, 1000  # Reduced minimum perimeter
        circularity_min, circularity_max = 0.2, 1.0  # More lenient circularity
        
        # Check if the contour meets the criteria
        if (area_min <= area <= area_max and
            perimeter_min <= perimeter <= perimeter_max and
            circularity_min <= circularity <= circularity_max):
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Draw green contour on black window
            cv2.drawContours(black_window, [contour], -1, (0, 255, 0), 2)
            cv2.drawContours(final_seg, [contour], -1, (0, 255, 0), -1)
            
            # Draw filled white rectangle on white window
            cv2.rectangle(white_window, (x, y), (x + w, y + h), (255, 255, 255), -1)
    
    # Save additional debug images
    cv2.imwrite(os.path.join(output_dir, '10-ContourOutlines.png'), black_window)
    cv2.imwrite(os.path.join(output_dir, '11-BoundingBoxes.png'), white_window)
    cv2.imwrite(os.path.join(output_dir, '12-FinalSegmentationColored.png'), final_seg)

    return binary

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
        
        # Store current frame for snapshot
        ui.set_current_frame(frame)
        
        # Process frame
        display_frame, white_window, _ = process_frame(frame, ui.get_parameters())
        
        # Update UI
        ui.update_video_display(display_frame, white_window)
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
