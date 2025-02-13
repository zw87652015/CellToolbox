import cv2
import numpy as np
from skimage import filters, morphology, measure, segmentation
import matplotlib.pyplot as plt
import os
import time

def process_image(image_path):
    start_time = time.time()  # Start timing
    
    # Create processing folder if it doesn't exist
    processing_folder = 'processing'
    if not os.path.exists(processing_folder):
        os.makedirs(processing_folder)

    # Read original image
    org = cv2.imread(image_path)
    if org is None:
        raise ValueError(f"Could not read image at {image_path}")

    # Convert BGR to RGB (OpenCV uses BGR by default)
    org_rgb = cv2.cvtColor(org, cv2.COLOR_BGR2RGB)

    # Convert to grayscale
    gray_image = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(os.path.join(processing_folder, '1-GrayImage.png'), gray_image)

    # Convert to double (float) and denoise
    double_image = gray_image.astype(np.float32) / 255.0
    denoised_image = cv2.GaussianBlur(double_image, (3, 3), 2)
    cv2.imwrite(os.path.join(processing_folder, '2-DenoisedImage.png'), (denoised_image * 255).astype(np.uint8))

    # Binary image
    _, binary_image = cv2.threshold(org[:,:,2], 0, 255, 
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary_image = ~binary_image
    cv2.imwrite(os.path.join(processing_folder, '3-BinaryImage.png'), binary_image)

    # Edge detection
    edge_canny = cv2.Canny((denoised_image * 255).astype(np.uint8), 30, 150)
    cv2.imwrite(os.path.join(processing_folder, '4-CannyEdgeDetection.png'), edge_canny)

    # Convert to 8-bit for OpenCV edge detection
    img_8bit = (denoised_image * 255).astype(np.uint8)
    
    # Prewitt
    kernelx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
    kernely = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
    img_prewittx = cv2.filter2D(img_8bit, -1, kernelx)
    img_prewitty = cv2.filter2D(img_8bit, -1, kernely)
    edge_prewitt = np.sqrt(img_prewittx**2 + img_prewitty**2)
    edge_prewitt = edge_prewitt > 30  # Adjust threshold as needed
    cv2.imwrite(os.path.join(processing_folder, '5-PrewittEdgeDetection.png'), 
                 edge_prewitt.astype(np.uint8) * 255)

    # Roberts
    roberts_x = np.array([[1, 0], [0, -1]])
    roberts_y = np.array([[0, 1], [-1, 0]])
    img_robertsx = cv2.filter2D(img_8bit, -1, roberts_x)
    img_robertsy = cv2.filter2D(img_8bit, -1, roberts_y)
    edge_roberts = np.sqrt(img_robertsx**2 + img_robertsy**2)
    edge_roberts = edge_roberts > 30  # Adjust threshold as needed
    cv2.imwrite(os.path.join(processing_folder, '6-RobertsEdgeDetection.png'), 
                edge_roberts.astype(np.uint8) * 255)

    # Sobel
    sobelx = cv2.Sobel(img_8bit, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img_8bit, cv2.CV_64F, 0, 1, ksize=3)
    edge_sobel = np.sqrt(sobelx**2 + sobely**2)
    edge_sobel = edge_sobel > 30  # Adjust threshold as needed
    cv2.imwrite(os.path.join(processing_folder, '7-SobelEdgeDetection.png'), 
                edge_sobel.astype(np.uint8) * 255)

    # Edge combination
    roi_edge = edge_canny.astype(bool) | edge_prewitt | edge_roberts | edge_sobel
    cv2.imwrite(os.path.join(processing_folder, '8-EdgeDetectionCombination.png'), 
                roi_edge.astype(np.uint8) * 255)

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
        # Apply Kirsch filter (keeping float32)
        filtered = cv2.filter2D(denoised_image.astype(np.float32), -1, kernel)
        
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

    i9 = np.zeros_like(kirsch_outputs[0], dtype=bool)
    for output in kirsch_outputs:
        i9 = i9 | output

    cv2.imwrite(os.path.join(processing_folder, '9-KirschSegmentation1.png'), 
                i9.astype(np.uint8) * 255)

    # Apply morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    i9 = cv2.erode(i9.astype(np.uint8), kernel, iterations=1)
    i9 = cv2.morphologyEx(i9, cv2.MORPH_CLOSE, kernel)
    
    cv2.imwrite(os.path.join(processing_folder, '10-KirschSegmentation2.png'), 
                i9.astype(np.uint8) * 255)

    # Combine segmentations
    roi_seg = roi_edge | i9.astype(bool) | binary_image.astype(bool)
    cv2.imwrite(os.path.join(processing_folder, '11-ROIedgeORI9ORBinary.png'), 
                roi_seg.astype(np.uint8) * 255)

    # Final processing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    final_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    final_seg = morphology.remove_small_objects(final_seg.astype(bool))
    cv2.imwrite(os.path.join(processing_folder, '12-ClosingAndRemove.png'), 
                final_seg.astype(np.uint8) * 255)

    # Fill holes
    final_seg = morphology.remove_small_holes(final_seg)
    cv2.imwrite(os.path.join(processing_folder, '13-HolesFilled.png'), 
                final_seg.astype(np.uint8) * 255)

    # Remove small areas
    final_seg = morphology.remove_small_objects(final_seg, min_size=100)
    cv2.imwrite(os.path.join(processing_folder, '14-SmallAreaRemoved.png'), 
                final_seg.astype(np.uint8) * 255)

    # Clean up
    final_seg = morphology.thin(final_seg, max_num_iter=3)
    cv2.imwrite(os.path.join(processing_folder, '15-SpursRemoved.png'), 
                final_seg.astype(np.uint8) * 255)

    final_seg = morphology.remove_small_objects(final_seg, min_size=1)
    cv2.imwrite(os.path.join(processing_folder, '16-Cleaned.png'), 
                final_seg.astype(np.uint8) * 255)

    # Label connected components
    labeled_image = measure.label(final_seg)
    rgb_label = segmentation.mark_boundaries(org_rgb, labeled_image)
    # plt.imsave(os.path.join(processing_folder, '17-Labelled.png'), rgb_label)

    cv2.imwrite(os.path.join(processing_folder, '18-L_BW.png'), 
                (labeled_image > 0).astype(np.uint8) * 255)

    # Calculate properties and draw rectangles
    props = measure.regionprops(labeled_image)
    
    plt.figure()
    plt.imshow(cv2.cvtColor(org, cv2.COLOR_BGR2RGB))
    
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
                rect = plt.Rectangle((bbox[1], bbox[0]), width, height,
                                  fill=False, edgecolor='red')
                plt.gca().add_patch(rect)
    
    plt.axis('off')
    plt.savefig(os.path.join(processing_folder, '19-FinalResult.png'))
    plt.close()
    
    end_time = time.time()  # End timing
    processing_time = end_time - start_time
    print(f"Processing time: {processing_time:.2f} seconds")
    
    return processing_time

if __name__ == "__main__":
    # Run multiple times to get average performance
    n_runs = 1
    times = []
    
    for i in range(n_runs):
        print(f"\nRun {i+1}/{n_runs}")
        time_taken = process_image('test4.png')
        times.append(time_taken)
    
    avg_time = sum(times) / len(times)
    std_time = np.std(times)
    print(f"\nAverage processing time over {n_runs} runs: {avg_time:.2f} ± {std_time:.2f} seconds")
