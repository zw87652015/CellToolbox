import cv2
import numpy as np
from skimage import filters, morphology, measure, segmentation
import sys
import tkinter as tk
from parameter_control import UnifiedUI

# Global variables for cell tracking and persistence
CAMERASELECTED = 1  # 0~infinity for USB camera index
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
    """Process a video frame to detect and track cells using advanced detection methods.
    
    This function performs the following steps:
    1. Image preprocessing (grayscale conversion, denoising)
    2. Cell detection using multiple edge detection methods (Canny, Prewitt, Roberts, Sobel, Kirsch)
    3. Advanced binary processing with adaptive thresholding
    4. Morphological operations to refine cell regions
    5. Cell tracking using IoU and distance-based matching
    6. Visualization of detected cells
    
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
    
    # Make copies of the frame
    display_frame = frame.copy()
    black_window = np.zeros_like(frame)
    
    # Convert to grayscale and denoise
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    denoised = cv2.GaussianBlur(gray.astype(np.float32) / 255.0, (3, 3), 2)
    img_8bit = (denoised * 255).astype(np.uint8)

    # 1. Binary image using adaptive thresholding
    binary_image1 = cv2.adaptiveThreshold(frame[:,:,2], 255, 
                                       cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
    binary_image2 = cv2.adaptiveThreshold(frame[:,:,2], 255, 
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
    binary_image = binary_image1 | binary_image2
    binary_image = ~binary_image

    # 2. Multiple edge detection methods
    # Canny
    edge_canny = cv2.Canny(img_8bit, 30, 150)
    
    # Prewitt
    kernelx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
    kernely = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
    img_prewittx = cv2.filter2D(img_8bit, -1, kernelx)
    img_prewitty = cv2.filter2D(img_8bit, -1, kernely)
    edge_prewitt = np.sqrt(img_prewittx**2 + img_prewitty**2)
    edge_prewitt = edge_prewitt > 30
    
    # Roberts
    roberts_x = np.array([[1, 0], [0, -1]])
    roberts_y = np.array([[0, 1], [-1, 0]])
    img_robertsx = cv2.filter2D(img_8bit, -1, roberts_x)
    img_robertsy = cv2.filter2D(img_8bit, -1, roberts_y)
    edge_roberts = np.sqrt(img_robertsx**2 + img_robertsy**2)
    edge_roberts = edge_roberts > 30
    
    # Sobel
    sobelx = cv2.Sobel(img_8bit, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img_8bit, cv2.CV_64F, 0, 1, ksize=3)
    edge_sobel = np.sqrt(sobelx**2 + sobely**2)
    edge_sobel = edge_sobel > 30

    # Kirsch operators
    kirsch_kernels = [
        np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float32),
        np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float32),
        np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float32),
        np.array([[-3, -3, -3], [5, 0, -3], [5, 5, -3]], dtype=np.float32),
        np.array([[-3, -3, -3], [-3, 0, -3], [5, 5, 5]], dtype=np.float32),
        np.array([[-3, -3, -3], [-3, 0, 5], [-3, 5, 5]], dtype=np.float32),
        np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float32),
        np.array([[-3, 5, 5], [-3, 0, 5], [-3, -3, -3]], dtype=np.float32)
    ]

    kirsch_outputs = []
    for kernel in kirsch_kernels:
        filtered = cv2.filter2D(denoised.astype(np.float32), -1, kernel)
        filtered = np.abs(filtered)
        filtered_min = np.min(filtered)
        filtered_max = np.max(filtered)
        if filtered_max > filtered_min:
            filtered_norm = (filtered - filtered_min) / (filtered_max - filtered_min)
        else:
            filtered_norm = np.zeros_like(filtered)
        binary = filtered_norm > filters.threshold_otsu(filtered_norm)
        kirsch_outputs.append(binary)

    kirsch_result = np.zeros_like(kirsch_outputs[0], dtype=bool)
    for output in kirsch_outputs:
        kirsch_result = kirsch_result | output

    # Apply morphological operations to Kirsch result
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kirsch_result = cv2.erode(kirsch_result.astype(np.uint8), kernel, iterations=1)
    kirsch_result = cv2.morphologyEx(kirsch_result, cv2.MORPH_CLOSE, kernel)

    # 3. Combine all edge detection results
    roi_edge = (edge_canny.astype(bool) | edge_prewitt | 
               edge_roberts | edge_sobel)
    roi_seg = roi_edge | kirsch_result | binary_image.astype(bool)

    # 4. Pre-processing to reduce noise
    # Remove small objects first
    roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=15)
    
    # Use a small kernel to clean up noise
    small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    roi_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, small_kernel)

    # Final processing with adjusted parameters
    # Use moderate kernel for closing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Remove small objects with moderate threshold
    final_seg = morphology.remove_small_objects(final_seg.astype(bool), min_size=20)
    
    # Fill holes
    final_seg = morphology.remove_small_holes(final_seg)
    
    # Remove small areas
    final_seg = morphology.remove_small_objects(final_seg, min_size=100)
    
    # Clean up
    final_seg = morphology.thin(final_seg, max_num_iter=3)

    # Additional cleaning steps to remove spider-web like noise
    # 1. Use area opening to remove small objects
    final_seg = morphology.remove_small_objects(final_seg, min_size=20)
    
    # 2. Remove thin connections using area closing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    final_seg = cv2.morphologyEx(final_seg.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    
    # 3. Calculate and filter based on eccentricity to remove elongated objects
    labeled = measure.label(final_seg)
    props = measure.regionprops(labeled)
    mask = np.zeros_like(final_seg, dtype=bool)
    
    for prop in props:
        # Filter based on eccentricity and area
        if prop.eccentricity < 0.95 and prop.area > 300:  # Less elongated objects
            mask[labeled == prop.label] = True
    
    final_seg = mask

    # 5. Advanced cell filtering
    labeled = measure.label(final_seg)
    current_cells = []
    
    for prop in measure.regionprops(labeled):
        # Filter based on area and eccentricity
        if prop.area > 300 and prop.eccentricity < 0.95:
            bbox = prop.bbox
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

    # 6. Track cells between frames
    matched_prev_indices = set()
    matched_curr_indices = set()
    new_cell_lifetimes = [params['cell_memory_frames']] * len(current_cells)

    if previous_cells:
        # Ensure cell_lifetimes has the same length as previous_cells
        while len(cell_lifetimes) < len(previous_cells):
            cell_lifetimes.append(params['cell_memory_frames'])
        
        # Update lifetimes
        cell_lifetimes = cell_lifetimes[:len(previous_cells)]  # Trim any extra lifetimes
        cell_lifetimes = [t - 1 for t in cell_lifetimes]
        
        # Only process cells with positive lifetime
        valid_prev_indices = [i for i, lifetime in enumerate(cell_lifetimes) if lifetime > 0]
        
        for i in valid_prev_indices:
            min_dist = float('inf')
            best_match = -1
            
            for j, curr_box in enumerate(current_cells):
                if j in matched_curr_indices:
                    continue
                
                # Calculate both IoU and center distance
                iou = calculate_iou(previous_cells[i], curr_box)
                dist = calculate_center_distance(previous_cells[i], curr_box)
                
                # Use combined metric for matching
                if (iou > 0.3 or dist < params['distance_threshold']) and dist < min_dist:
                    min_dist = dist
                    best_match = j
            
            if best_match >= 0:
                matched_prev_indices.add(i)
                matched_curr_indices.add(best_match)
                cell_lifetimes[i] = params['cell_memory_frames']
                # Transfer the lifetime to the matched current cell
                new_cell_lifetimes[best_match] = cell_lifetimes[i]
    
    # Update cell tracking state
    previous_cells = current_cells.copy()  # Make a copy to avoid reference issues
    cell_lifetimes = new_cell_lifetimes
    
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
    
    except tk.TclError:
        print("UI window was closed")
    finally:
        # Clean up
        cap.release()
        ui.root.destroy()

if __name__ == "__main__":
    main()
