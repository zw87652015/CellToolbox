"""
GPU-accelerated Cell Detection Module
This module provides GPU-accelerated cell detection using CUDA and CuPy for improved performance.
"""

import cv2
import numpy as np
from skimage import measure, morphology, filters, segmentation
from scipy import ndimage as ndi
import time

# Try to import GPU libraries
try:
    import cupy as cp
    GPU_AVAILABLE = True
    print("GPU acceleration available with CuPy")
except ImportError:
    import numpy as cp  # Fallback to numpy if CuPy not available
    GPU_AVAILABLE = False
    print("GPU acceleration not available, falling back to CPU")

class CellDetectorGPU:
    """GPU-accelerated cell detection class for processing images and detecting cells"""
    
    def __init__(self):
        # Parameters for cell detection (optimized for conservative detection)
        self.clahe_clip_limit = 2.0  # Reduced for less aggressive contrast enhancement
        self.clahe_tile_size = 8     # Smaller tiles for more localized enhancement
        self.min_object_size = 25    # Increased to filter out more noise
        self.eccentricity_threshold = 0.95  # More restrictive for rounder objects
        self.area_threshold_small = 100     # Lower threshold for first stage
        self.area_threshold_large = 300     # Reduced for more conservative filtering
        self.area_min = 80           # Increased minimum area
        self.area_max = 500          # Increased maximum area for larger cells
        self.min_perimeter = 30      # Reduced minimum perimeter
        self.max_perimeter = 200     # Reduced maximum perimeter
        self.min_circularity = 0.3   # More permissive circularity
        self.max_circularity = 3.0   # More restrictive maximum circularity
        self.aspect_ratio_threshold = 2.0  # More permissive aspect ratio
        
        # Edge detection parameters (more conservative)
        self.canny_low = 50          # Higher low threshold
        self.canny_high = 150        # Keep high threshold
        self.edge_threshold = 50     # Higher edge threshold
        
        # Morphology parameters
        self.final_min_size = 100
        
        # Watershed parameters
        self.use_watershed = True
        self.watershed_distance_threshold = 10
        self.watershed_footprint_size = 3
        self.watershed_compactness = 0.5
        self.watershed_min_area = 500
        
        # Additional parameters
        self.min_area = self.area_min
        self.max_area = self.area_max
        
        # Detection results
        self.detected_cells = []
        self.processing = False
        
        # GPU context
        self.gpu_available = GPU_AVAILABLE
        if self.gpu_available:
            try:
                # Test GPU functionality
                test_array = cp.array([1, 2, 3])
                _ = cp.asnumpy(test_array)
                print("GPU context initialized successfully")
            except Exception as e:
                print(f"GPU initialization failed: {e}")
                self.gpu_available = False
    
    def _to_gpu(self, array):
        """Move array to GPU if available"""
        if self.gpu_available:
            return cp.asarray(array)
        return array
    
    def _to_cpu(self, array):
        """Move array to CPU"""
        if self.gpu_available and hasattr(array, 'get'):
            return cp.asnumpy(array)
        return array
    
    def _gpu_gaussian_blur(self, image, kernel_size, sigma):
        """GPU-accelerated Gaussian blur"""
        if self.gpu_available:
            # Use CuPy for GPU operations
            gpu_image = self._to_gpu(image)
            # CuPy doesn't have direct Gaussian blur, so we'll use CPU for this
            cpu_result = cv2.GaussianBlur(self._to_cpu(gpu_image), kernel_size, sigma)
            return self._to_gpu(cpu_result)
        else:
            return cv2.GaussianBlur(image, kernel_size, sigma)
    
    def _gpu_canny(self, image, low, high):
        """GPU-accelerated Canny edge detection"""
        if self.gpu_available:
            # OpenCV with CUDA support
            try:
                gpu_mat = cv2.cuda_GpuMat()
                gpu_mat.upload(image)
                gpu_canny = cv2.cuda.Canny(gpu_mat, low, high)
                result = gpu_canny.download()
                return result
            except:
                # Fallback to CPU if GPU Canny fails
                return cv2.Canny(image, low, high)
        else:
            return cv2.Canny(image, low, high)
    
    def _gpu_threshold(self, image, thresh, maxval, type):
        """GPU-accelerated thresholding"""
        if self.gpu_available:
            try:
                gpu_mat = cv2.cuda_GpuMat()
                gpu_mat.upload(image)
                _, gpu_result = cv2.cuda.threshold(gpu_mat, thresh, maxval, type)
                result = gpu_result.download()
                return result
            except:
                # Fallback to CPU
                _, result = cv2.threshold(image, thresh, maxval, type)
                return result
        else:
            _, result = cv2.threshold(image, thresh, maxval, type)
            return result
    
    def _gpu_morphology(self, image, operation, kernel, iterations=1):
        """GPU-accelerated morphological operations"""
        if self.gpu_available:
            try:
                gpu_mat = cv2.cuda_GpuMat()
                gpu_mat.upload(image)
                
                # Create morphology filter
                morph_filter = cv2.cuda.createMorphologyFilter(operation, image.dtype, kernel)
                gpu_result = cv2.cuda_GpuMat()
                
                for _ in range(iterations):
                    morph_filter.apply(gpu_mat, gpu_result)
                    gpu_mat = gpu_result.clone()
                
                result = gpu_result.download()
                return result
            except:
                # Fallback to CPU
                return cv2.morphologyEx(image, operation, kernel, iterations=iterations)
        else:
            return cv2.morphologyEx(image, operation, kernel, iterations=iterations)
    
    def detect_cells(self, frame, aoi_coords=None, return_debug=False):
        """
        GPU-accelerated cell detection method
        """
        start_time = time.time()
        
        # Make a copy of the image to avoid modifying the original
        org = frame.copy()
        
        # Handle AOI cropping
        if aoi_coords is not None:
            x1, y1, x2, y2 = aoi_coords
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(org.shape[1], x2), min(org.shape[0], y2)
            if x2 <= x1 or y2 <= y1:
                return [], None if return_debug else []
            org = org[y1:y2, x1:x2]
        else:
            x1, y1 = 0, 0
        
        # Convert to grayscale
        if len(org.shape) == 3:
            gray_image = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = org.copy()
        
        # CLAHE enhancement
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, 
                               tileGridSize=(self.clahe_tile_size, self.clahe_tile_size))
        enhanced_image = clahe.apply(gray_image)
        
        # Gaussian denoising
        double_image = enhanced_image.astype(np.float32) / 255.0
        denoised_image = self._gpu_gaussian_blur(double_image, (3, 3), 2)
        denoised_image = self._to_cpu(denoised_image)  # Ensure CPU for subsequent operations
        
        # Conservative binary thresholding - use Otsu for cleaner segmentation
        try:
            # Use GPU-accelerated Otsu thresholding
            binary_image = self._gpu_threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        except:
            # Fallback to simple thresholding
            binary_image = self._gpu_threshold(gray_image, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Conservative edge detection - use GPU-accelerated Canny
        img_8bit = (denoised_image * 255).astype(np.uint8)
        edge_canny = self._gpu_canny(img_8bit, self.canny_low, self.canny_high)
        
        # Combine binary and edge detection (more conservative approach)
        roi_seg = binary_image.astype(bool) | edge_canny.astype(bool)
        
        # Conservative morphological operations
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # Remove noise first
        roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=self.min_object_size)
        
        # GPU-accelerated morphological operations
        roi_seg_uint8 = roi_seg.astype(np.uint8)
        roi_seg = self._gpu_morphology(roi_seg_uint8, cv2.MORPH_OPEN, kernel_small)
        roi_seg = self._gpu_morphology(roi_seg, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
        
        # Fill small holes only
        roi_seg = morphology.remove_small_holes(roi_seg.astype(bool), area_threshold=50)
        
        # Final segmentation with stricter size filtering
        final_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=self.min_object_size * 2)
        
        # Label connected components
        labeled_image = measure.label(final_seg)
        props = measure.regionprops(labeled_image)
        
        # First filtering step - more permissive to improve recall
        # Allow objects that meet basic size criteria to pass to second filter
        mask = np.zeros_like(final_seg, dtype=bool)
        for prop in props:
            # More permissive first filter - let second filter do the detailed work
            if (prop.area > self.area_min/2):  # Allow smaller objects to pass through
                mask[labeled_image == prop.label] = True
        
        # Update final segmentation with the mask
        final_seg = mask
        
        # Apply watershed segmentation to separate touching cells if enabled
        if self.use_watershed:
            # First, get the original labeled image and region properties
            original_labeled = measure.label(final_seg)
            original_props = measure.regionprops(original_labeled)
            
            # Create a mask for large objects that need watershed segmentation
            large_objects_mask = np.zeros_like(final_seg, dtype=bool)
            for prop in original_props:
                if prop.area > self.watershed_min_area:
                    large_objects_mask[original_labeled == prop.label] = True
            
            # Create a mask for small objects that don't need watershed segmentation
            small_objects_mask = final_seg & ~large_objects_mask
            
            # Only apply watershed to large objects
            if np.any(large_objects_mask):
                # Distance transform on large objects only
                distance = ndi.distance_transform_edt(large_objects_mask)
                
                # Apply threshold to distance map to find markers
                distance_peaks = distance > self.watershed_distance_threshold
                
                # Clean up the peaks to get better markers
                distance_peaks = morphology.remove_small_objects(distance_peaks, min_size=2)
                
                # Label the peaks as markers
                markers = measure.label(distance_peaks)
                
                # Apply watershed segmentation to large objects only
                watershed_labels = segmentation.watershed(-distance, markers, mask=large_objects_mask, 
                                                        compactness=self.watershed_compactness)
                
                # Combine the watershed segmentation of large objects with the small objects
                max_watershed_label = np.max(watershed_labels) if np.any(watershed_labels) else 0
                
                # Label the small objects starting from max_watershed_label + 1
                small_objects_labeled = measure.label(small_objects_mask)
                small_objects_labeled[small_objects_labeled > 0] += max_watershed_label
                
                # Combine the two labeled images
                combined_labels = watershed_labels.copy()
                combined_labels[small_objects_mask] = small_objects_labeled[small_objects_mask]
                
                # Final labeled image
                labeled_image = combined_labels
            else:
                # If no large objects, just use the original labeling
                labeled_image = original_labeled
        else:
            # Re-label after filtering without watershed
            labeled_image = measure.label(final_seg)
        
        # Get updated region properties after watershed segmentation
        props = measure.regionprops(labeled_image)
        
        # Filter cells based on properties
        detected_cells = []
        for prop in props:
            area = prop.area
            perimeter = prop.perimeter
            circularity = (perimeter * perimeter) / (4 * np.pi * area)
            eccentricity = prop.eccentricity
            
            # Get bounding box for aspect ratio calculation
            bbox = prop.bbox
            height = bbox[2] - bbox[0]
            width = bbox[3] - bbox[1]
            
            # Calculate aspect ratio condition
            aspect_ratio_condition = (
                (height > width and self.aspect_ratio_threshold * width > height) or
                (width > height and self.aspect_ratio_threshold * height > width) or
                (height == width)
            )
            
            # Second filtering step - check area, perimeter, circularity and aspect ratio
            # Slightly more permissive to improve recall
            if (self.area_min * 0.8 < area < self.area_max * 1.2 and 
                self.min_perimeter * 0.7 < perimeter < self.max_perimeter * 1.3 and 
                self.min_circularity * 0.8 < circularity < self.max_circularity * 1.2 and
                aspect_ratio_condition):
                    
                    # Calculate centroid
                    y, x = prop.centroid
                    
                    # Adjust coordinates back to original image space if AOI was used
                    adjusted_centroid = (x + x1, y + y1)
                    
                    # Convert bbox from (min_row, min_col, max_row, max_col) to (x1, y1, x2, y2)
                    adjusted_bbox = (bbox[1] + x1, bbox[0] + y1, bbox[3] + x1, bbox[2] + y1)
                    
                    detected_cells.append({
                        'centroid': adjusted_centroid,
                        'area': area,
                        'bbox': adjusted_bbox,
                        'perimeter': perimeter,
                        'circularity': circularity,
                        'eccentricity': eccentricity
                    })
        
        # Store results
        self.detected_cells = detected_cells
        
        # Calculate processing time
        processing_time = time.time() - start_time
        print(f"GPU detection time: {processing_time:.3f}s, Found {len(detected_cells)} cells")
        
        if return_debug:
            # Create debug image showing the binary segmentation
            debug_image = (final_seg * 255).astype(np.uint8)
            return detected_cells, debug_image
        
        return detected_cells

    def update_parameters(self, **kwargs):
        """Update detection parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
