import cv2
import cupy as cp
from cupyx.scipy.signal import correlate2d
import numpy as np
from skimage import filters, morphology, measure, segmentation
import time

def process_frame(frame):
    """Process a single frame to detect cells using GPU acceleration with CuPy."""
    # Make a copy of the frame to avoid modifying the original
    display_frame = frame.copy()
    
    try:
        # Convert BGR to grayscale
        gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Move data to GPU using CuPy
        gpu_gray = cp.asarray(gray_image)
        
        # Convert to double and denoise
        gpu_double = (gpu_gray.astype(cp.float32) / 255.0)
        gpu_denoised = cp.array(cv2.GaussianBlur((gpu_double.get() * 255).astype(np.uint8), (3, 3), 2))
        denoised_image = gpu_denoised.get()
        
        # Binary image
        _, binary_image = cv2.threshold(gray_image, 0, 255, 
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary_image = ~binary_image
        
        # Edge detection using CuPy
        gpu_uint8 = cp.asarray(denoised_image)
        
        # Sobel edge detection on GPU
        kernel_x = cp.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=cp.float32)
        kernel_y = cp.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=cp.float32)
        
        sobelx = correlate2d(gpu_uint8, kernel_x, mode='same')
        sobely = correlate2d(gpu_uint8, kernel_y, mode='same')
        
        edge_sobel = cp.sqrt(sobelx**2 + sobely**2)
        edge_sobel = (edge_sobel > 30).get()
        
        # Canny edge detection (using CPU as it's more complex)
        edge_canny = cv2.Canny((denoised_image * 255).astype(np.uint8), 30, 150)
        
        # Edge combination
        roi_seg = edge_canny.astype(bool) | edge_sobel | binary_image.astype(bool)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
        final_seg = morphology.remove_small_objects(final_seg.astype(bool))
        
        # Fill holes and remove small areas
        final_seg = morphology.remove_small_holes(final_seg)
        final_seg = morphology.remove_small_objects(final_seg, min_size=100)
        
        # Label connected components
        labeled_image = measure.label(final_seg)
        
        # Calculate properties and draw rectangles
        props = measure.regionprops(labeled_image)
        
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
                    # Draw rectangle on the display frame
                    cv2.rectangle(display_frame, 
                                (bbox[1], bbox[0]), 
                                (bbox[3], bbox[2]), 
                                (0, 255, 0), 2)
    except Exception as e:
        print(f"Error in GPU processing: {str(e)}")
        # Fall back to CPU processing if GPU fails
        return frame
        
    return display_frame

def main():
    # Check if CuPy can access the GPU
    try:
        mempool = cp.get_default_memory_pool()
        pinned_mempool = cp.get_default_pinned_memory_pool()
        print(f"CuPy is using GPU: {cp.cuda.runtime.getDeviceCount()} device(s) available")
    except Exception as e:
        print(f"Error initializing CuPy: {str(e)}")
        return
    
    # Open camera 0 (usually the first USB camera)
    cap = cv2.VideoCapture(0)
    
    # Set resolution to 1280x720 (HD)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Verify the resolution was set correctly
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera resolution set to: {actual_width}x{actual_height}")
    
    # Create a resizable window
    cv2.namedWindow('Cell Detection', cv2.WINDOW_NORMAL)
    
    print("Press 'q' to quit")
    
    try:
        while cap.isOpened():
            # Read a frame
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Process frame and detect cells
            processed_frame = process_frame(frame)
            
            # Display the frame
            cv2.imshow('Cell Detection', processed_frame)
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except Exception as e:
        print(f"Error in main loop: {str(e)}")
    
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        # Clean up GPU memory
        mempool.free_all_blocks()
        pinned_mempool.free_all_blocks()

if __name__ == "__main__":
    main()
