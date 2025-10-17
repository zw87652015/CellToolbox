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
    import cupyx.scipy.ndimage as cp_ndimage
    GPU_AVAILABLE = True
    print("GPU acceleration available with CuPy")
except ImportError:
    import numpy as cp
    import scipy.ndimage as cp_ndimage
    GPU_AVAILABLE = False
    print("GPU acceleration not available, falling back to CPU")

# Try to import NVIDIA monitoring library
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    pynvml = None
    NVML_AVAILABLE = False
    print("NVIDIA monitoring (pynvml) not available, GPU monitoring disabled")

class CellDetectorGPU:
    """GPU-accelerated cell detection class for processing images and detecting cells"""
    
    def __init__(self):
        # Initialize NVML for GPU monitoring if available
        self.handle = None
        if NVML_AVAILABLE and pynvml:
            try:
                pynvml.nvmlInit()
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            except Exception as e:
                print(f"Warning: Could not initialize GPU monitoring: {e}")
                self.handle = None
        
        # Parameters for cell detection (optimized for conservative detection)
        self.clahe_clip_limit = 2.0  # Reduced for less aggressive contrast enhancement
        self.clahe_tile_size = 8     # Smaller tiles for more localized enhancement
        self.min_object_size = 25    # Increased to filter out more noise
        self.eccentricity_threshold = 0.95  # More restrictive for rounder objects
        self.area_threshold_small = 100     # Lower threshold for first stage
        self.area_threshold_large = 300     # Reduced for more conservative filtering
        self.area_min = 150          # Increased minimum area
        self.area_max = 1000         # Increased maximum area for larger cells
        self.min_perimeter = 30      # Reduced minimum perimeter
        self.max_perimeter = 200     # Reduced maximum perimeter
        self.min_circularity = 0.3   # More permissive circularity
        self.max_circularity = 3.0   # More restrictive maximum circularity
        self.aspect_ratio_threshold = 2.0  # More permissive aspect ratio
        
        # Shape quality filters (to reject noise)
        self.min_solidity = 0.7      # Minimum solidity (area/convex_hull_area) - rejects irregular noise
        self.min_extent = 0.3        # Minimum extent (area/bbox_area) - rejects sparse noise
        
        # Edge detection parameters (more conservative)
        self.canny_low = 50          # Higher low threshold
        self.canny_high = 150        # Keep high threshold
        self.edge_threshold = 50     # Higher edge threshold
        
        # Morphology parameters
        self.final_min_size = 100
        self.hole_fill_area = 500  # Area threshold for filling holes in cells
        
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
    
    def get_gpu_utilization(self):
        """Get current GPU utilization percentage"""
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            return util.gpu
        except:
            return 0  # Fallback if monitoring fails
    
    def _to_gpu(self, array):
        """Move array to GPU if available"""
        if self.gpu_available:
            return cp.asarray(array)
        return array
    
    def _to_cpu(self, array):
        """Move array to CPU"""
        if self.gpu_available and hasattr(array, 'get'):
            return array.get()  # Use .get() method for explicit conversion
        elif self.gpu_available and cp.is_cuda_array(array):
            return cp.asnumpy(array)
        return array
    
    def _gpu_gaussian_blur(self, image, kernel_size, sigma):
        """True GPU-accelerated Gaussian blur using CuPy"""
        if self.gpu_available:
            # Perform Gaussian blur entirely on GPU
            gpu_image = cp.asarray(image)
            # Handle kernel_size tuple (convert to single size for square kernel)
            if isinstance(kernel_size, tuple):
                size = kernel_size[0]  # Use first dimension for square kernel
            else:
                size = kernel_size
            # Create Gaussian kernel
            kernel = self._create_gaussian_kernel(size, sigma)
            # Use CuPy's convolution instead of scipy
            if len(gpu_image.shape) == 2:
                # 2D convolution for grayscale images
                result = cp_ndimage.convolve(gpu_image, kernel, mode='reflect')
            else:
                # Apply to each channel separately for color images
                result = cp.zeros_like(gpu_image)
                for i in range(gpu_image.shape[2]):
                    result[:, :, i] = cp_ndimage.convolve(gpu_image[:, :, i], kernel, mode='reflect')
            return result
        else:
            # Convert kernel_size to tuple if it's an integer
            if isinstance(kernel_size, int):
                ksize = (kernel_size, kernel_size)
            else:
                ksize = kernel_size
            return cv2.GaussianBlur(image, ksize, sigma)
            
    def _create_gaussian_kernel(self, size, sigma):
        """Create Gaussian kernel on GPU"""
        kernel = cp.zeros((size, size))
        center = size // 2
        for i in range(size):
            for j in range(size):
                x, y = i - center, j - center
                kernel[i, j] = cp.exp(-(x**2 + y**2)/(2*sigma**2))
        kernel /= kernel.sum()
        return kernel
    
    def _gpu_canny(self, image, low, high):
        """GPU-accelerated Canny edge detection using CuPy"""
        if self.gpu_available:
            gpu_image = cp.asarray(image)
            # Simplified edge detection using Sobel filters
            sobel_x = cp.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
            sobel_y = cp.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
            
            # Apply Sobel filters using CuPy
            grad_x = cp_ndimage.convolve(gpu_image.astype(cp.float32), sobel_x)
            grad_y = cp_ndimage.convolve(gpu_image.astype(cp.float32), sobel_y)
            
            # Calculate gradient magnitude
            magnitude = cp.sqrt(grad_x**2 + grad_y**2)
            
            # Apply thresholding
            edges = cp.zeros_like(magnitude, dtype=cp.uint8)
            edges[magnitude > high] = 255
            edges[(magnitude > low) & (magnitude <= high)] = 128
            
            return edges.astype(cp.uint8)
        else:
            return cv2.Canny(image, low, high)
    
    def _gpu_threshold(self, image, thresh, maxval, type):
        """GPU-accelerated thresholding using CuPy"""
        if self.gpu_available:
            gpu_image = cp.asarray(image)
            
            if type == cv2.THRESH_BINARY:
                result = cp.where(gpu_image > thresh, maxval, 0)
            elif type == cv2.THRESH_BINARY_INV:
                result = cp.where(gpu_image > thresh, 0, maxval)
            elif type == cv2.THRESH_OTSU:
                # Simple Otsu implementation on GPU
                hist = cp.histogram(gpu_image, bins=256, range=(0, 256))[0]
                total = gpu_image.size
                current_max, threshold = 0, 0
                sum_total = cp.sum(cp.arange(256) * hist)
                sum_bg, weight_bg = 0, 0
                
                for i in range(256):
                    weight_bg += hist[i]
                    if weight_bg == 0:
                        continue
                    weight_fg = total - weight_bg
                    if weight_fg == 0:
                        break
                    sum_bg += i * hist[i]
                    mean_bg = sum_bg / weight_bg
                    mean_fg = (sum_total - sum_bg) / weight_fg
                    var_between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
                    if var_between > current_max:
                        current_max = var_between
                        threshold = i
                
                result = cp.where(gpu_image > threshold, maxval, 0)
            else:
                # Fallback to CPU for other threshold types
                _, cpu_result = cv2.threshold(gpu_image.get(), thresh, maxval, type)
                result = cp.asarray(cpu_result)
            
            return result.astype(cp.uint8)
        else:
            _, result = cv2.threshold(image, thresh, maxval, type)
            return result
    
    def _gpu_morphology(self, image, operation, kernel, iterations=1):
        """GPU-accelerated morphological operations using CuPy"""
        if self.gpu_available:
            gpu_image = cp.asarray(image)
            gpu_kernel = cp.asarray(kernel)
            
            for _ in range(iterations):
                if operation == cv2.MORPH_ERODE:
                    # Erosion: minimum filter using CuPy
                    gpu_image = cp_ndimage.minimum_filter(gpu_image, footprint=gpu_kernel)
                elif operation == cv2.MORPH_DILATE:
                    # Dilation: maximum filter using CuPy
                    gpu_image = cp_ndimage.maximum_filter(gpu_image, footprint=gpu_kernel)
                elif operation == cv2.MORPH_OPEN:
                    # Opening: erosion followed by dilation using CuPy
                    gpu_image = cp_ndimage.minimum_filter(gpu_image, footprint=gpu_kernel)
                    gpu_image = cp_ndimage.maximum_filter(gpu_image, footprint=gpu_kernel)
                elif operation == cv2.MORPH_CLOSE:
                    # Closing: dilation followed by erosion using CuPy
                    gpu_image = cp_ndimage.maximum_filter(gpu_image, footprint=gpu_kernel)
                    gpu_image = cp_ndimage.minimum_filter(gpu_image, footprint=gpu_kernel)
                else:
                    # Fallback to CPU for other operations
                    cpu_result = cv2.morphologyEx(gpu_image.get(), operation, gpu_kernel.get())
                    gpu_image = cp.asarray(cpu_result)
            
            return gpu_image.astype(cp.uint8)
        else:
            return cv2.morphologyEx(image, operation, kernel, iterations=iterations)
    
    def _gpu_clahe(self, image, clip_limit=2.0, tile_grid_size=(8, 8)):
        """GPU-accelerated CLAHE using CuPy"""
        if not self.gpu_available:
            # Fallback to CPU CLAHE
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            return clahe.apply(image)
        
        gpu_image = cp.asarray(image, dtype=cp.float32)
        h, w = gpu_image.shape
        tile_h, tile_w = tile_grid_size
        
        # Calculate tile dimensions
        step_h = h // tile_h
        step_w = w // tile_w
        
        # Process each tile
        result = cp.zeros_like(gpu_image)
        
        for i in range(tile_h):
            for j in range(tile_w):
                # Define tile boundaries
                y1 = i * step_h
                y2 = min((i + 1) * step_h, h)
                x1 = j * step_w
                x2 = min((j + 1) * step_w, w)
                
                # Extract tile
                tile = gpu_image[y1:y2, x1:x2]
                
                # Calculate histogram
                hist = cp.histogram(tile, bins=256, range=(0, 256))[0].astype(cp.float32)
                
                # Apply clipping
                clip_val = clip_limit * tile.size / 256
                excess = cp.sum(cp.maximum(hist - clip_val, 0))
                hist = cp.minimum(hist, clip_val)
                
                # Redistribute excess
                if excess > 0:
                    redistrib = excess / 256
                    hist += redistrib
                
                # Calculate CDF
                cdf = cp.cumsum(hist)
                cdf = (cdf / cdf[-1] * 255).astype(cp.uint8)
                
                # Apply histogram equalization to tile
                tile_eq = cdf[tile.astype(cp.int32)]
                result[y1:y2, x1:x2] = tile_eq
        
        return result.astype(cp.uint8)
    
    def _gpu_connected_components(self, binary_image):
        """GPU-accelerated connected components analysis using CuPy"""
        if not self.gpu_available:
            # Fallback to CPU
            from skimage import measure
            labels = measure.label(binary_image)
            return labels, cp.max(labels) if hasattr(labels, 'max') else np.max(labels)
        
        gpu_binary = cp.asarray(binary_image, dtype=cp.uint8)
        
        # Simple connected components using iterative dilation
        # This is a simplified version - for production, consider using cuCIM
        labels = cp.zeros_like(gpu_binary, dtype=cp.int32)
        current_label = 1
        
        # Find all foreground pixels
        foreground = gpu_binary > 0
        
        # Process connected components
        while cp.any(foreground):
            # Find first foreground pixel
            coords = cp.where(foreground)
            if len(coords[0]) == 0:
                break
                
            # Start flood fill from first pixel
            seed_y, seed_x = int(coords[0][0]), int(coords[1][0])
            
            # Create component mask using morphological operations
            component_mask = cp.zeros_like(gpu_binary, dtype=cp.bool_)
            component_mask[seed_y, seed_x] = True
            
            # Iteratively dilate to find connected pixels
            kernel = cp.ones((3, 3), dtype=cp.uint8)
            prev_sum = 0
            
            for _ in range(min(gpu_binary.shape[0], gpu_binary.shape[1])):  # Max iterations
                # Dilate current component
                dilated = cp_ndimage.binary_dilation(component_mask, structure=kernel)
                # Keep only pixels that are also foreground
                component_mask = dilated & foreground
                
                # Check convergence
                current_sum = cp.sum(component_mask)
                if current_sum == prev_sum:
                    break
                prev_sum = current_sum
            
            # Assign label to this component
            labels[component_mask] = current_label
            
            # Remove processed pixels from foreground
            foreground = foreground & ~component_mask
            current_label += 1
            
            # Safety check to prevent infinite loops
            if current_label > 10000:
                break
        
        return labels, current_label - 1
    
    def _gpu_region_properties(self, labels, num_labels):
        """GPU-accelerated region properties calculation using CuPy"""
        if not self.gpu_available or num_labels == 0:
            # Fallback to CPU regionprops
            from skimage import measure
            cpu_labels = labels.get() if hasattr(labels, 'get') else labels
            return measure.regionprops(cpu_labels)
        
        gpu_labels = cp.asarray(labels)
        properties = []
        
        for label_id in range(1, num_labels + 1):
            # Create mask for current region
            mask = gpu_labels == label_id
            
            if not cp.any(mask):
                continue
            
            # Calculate basic properties on GPU
            coords = cp.where(mask)
            y_coords, x_coords = coords[0], coords[1]
            
            # Area
            area = cp.sum(mask)
            
            # Centroid
            centroid_y = cp.mean(y_coords.astype(cp.float32))
            centroid_x = cp.mean(x_coords.astype(cp.float32))
            
            # Bounding box
            min_y, max_y = cp.min(y_coords), cp.max(y_coords)
            min_x, max_x = cp.min(x_coords), cp.max(x_coords)
            
            # Equivalent diameter (approximate)
            equiv_diameter = 2 * cp.sqrt(area / cp.pi)
            
            # Perimeter (approximate using boundary pixels)
            # Dilate and subtract to find boundary
            kernel = cp.ones((3, 3), dtype=cp.uint8)
            dilated = cp_ndimage.binary_dilation(mask, structure=kernel)
            boundary = dilated & ~mask
            perimeter = cp.sum(boundary)
            
            # Eccentricity and other shape properties (simplified)
            # For full implementation, consider using moments
            height = max_y - min_y + 1
            width = max_x - min_x + 1
            aspect_ratio = float(cp.maximum(height, width) / cp.maximum(cp.minimum(height, width), 1))
            
            # Circularity (4π * area / perimeter²)
            circularity = 4 * cp.pi * area / cp.maximum(perimeter * perimeter, 1)
            
            # Create a simplified region object
            class GPURegion:
                def __init__(self):
                    self.area = float(area)
                    self.centroid = (float(centroid_y), float(centroid_x))
                    self.bbox = (int(min_y), int(min_x), int(max_y + 1), int(max_x + 1))
                    self.equivalent_diameter = float(equiv_diameter)
                    self.perimeter = float(perimeter)
                    self.eccentricity = min(0.99, float(1 - 1/aspect_ratio)) if aspect_ratio > 1 else 0.0
                    self.label = label_id
                    
                    # Additional properties for compatibility
                    self.coords = cp.column_stack([y_coords, x_coords]).get()
                    self.circularity = float(circularity)
                    self.aspect_ratio = float(aspect_ratio)
            
            properties.append(GPURegion())
        
        return properties
    
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
                return ([], None) if return_debug else []
            org = org[y1:y2, x1:x2]
        else:
            x1, y1 = 0, 0
        
        # Convert to grayscale and move to GPU immediately
        if len(org.shape) == 3:
            gray_image = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = org.copy()
        
        # Move to GPU for all processing
        if self.gpu_available:
            gpu_gray = cp.asarray(gray_image)
            
            # Fallback to CPU CLAHE - custom GPU implementation too slow
            clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, 
                                   tileGridSize=(self.clahe_tile_size, self.clahe_tile_size))
            enhanced_image = clahe.apply(gray_image)
            gpu_enhanced = cp.asarray(enhanced_image)
            
            # Gaussian denoising on GPU
            gpu_double = gpu_enhanced.astype(cp.float32) / 255.0
            gpu_denoised = self._gpu_gaussian_blur(gpu_double, 3, 2)
            
            # Binary thresholding on GPU
            try:
                gpu_binary = self._gpu_threshold(gpu_enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            except:
                gpu_binary = self._gpu_threshold(gpu_enhanced, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Edge detection on GPU
            gpu_8bit = (gpu_denoised * 255).astype(cp.uint8)
            gpu_edges = self._gpu_canny(gpu_8bit, self.canny_low, self.canny_high)
            
            # Combine binary and edge detection on GPU
            gpu_roi_seg = (gpu_binary > 0) | (gpu_edges > 0)
        else:
            # CPU fallback
            clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, 
                                   tileGridSize=(self.clahe_tile_size, self.clahe_tile_size))
            enhanced_image = clahe.apply(gray_image)
            
            double_image = enhanced_image.astype(np.float32) / 255.0
            denoised_image = self._gpu_gaussian_blur(double_image, 3, 2)
            
            try:
                binary_image = self._gpu_threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            except:
                binary_image = self._gpu_threshold(gray_image, 127, 255, cv2.THRESH_BINARY_INV)
            
            img_8bit = (denoised_image * 255).astype(np.uint8)
            edge_canny = self._gpu_canny(img_8bit, self.canny_low, self.canny_high)
            
            roi_seg = binary_image.astype(bool) | edge_canny.astype(bool)
        
        # Conservative morphological operations
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        if self.gpu_available:
            # Apply morphological operations on GPU
            gpu_roi_seg_uint8 = gpu_roi_seg.astype(cp.uint8)
            gpu_roi_seg = self._gpu_morphology(gpu_roi_seg_uint8, cv2.MORPH_OPEN, kernel_small)
            gpu_roi_seg = self._gpu_morphology(gpu_roi_seg, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
            
            # Keep processing on GPU
            roi_seg_gpu = gpu_roi_seg > 0
        else:
            # Remove noise first
            roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=self.min_object_size)
            
            # GPU-accelerated morphological operations
            roi_seg_uint8 = roi_seg.astype(np.uint8)
            roi_seg = self._gpu_morphology(roi_seg_uint8, cv2.MORPH_OPEN, kernel_small)
            roi_seg = self._gpu_morphology(roi_seg, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
            roi_seg = roi_seg > 0
        
        if self.gpu_available:
            # Convert GPU results to CPU for remaining operations (CPU regionprops is faster)
            roi_seg_cpu = roi_seg_gpu.get()
            
            # Aggressive hole filling to create solid filled cells (not donuts)
            # First pass: fill large holes
            roi_seg = morphology.remove_small_holes(roi_seg_cpu.astype(bool), area_threshold=self.hole_fill_area)
            # Second pass: binary fill to ensure completely filled cells
            roi_seg = ndi.binary_fill_holes(roi_seg)
            
            # Final segmentation with stricter size filtering
            final_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=self.min_object_size * 2)
            
            # Label connected components (CPU is faster for this)
            labeled_image = measure.label(final_seg)
            props = measure.regionprops(labeled_image)
        else:
            # CPU fallback
            # Aggressive hole filling to create solid filled cells (not donuts)
            # First pass: fill large holes
            roi_seg = morphology.remove_small_holes(roi_seg.astype(bool), area_threshold=self.hole_fill_area)
            # Second pass: binary fill to ensure completely filled cells
            roi_seg = ndi.binary_fill_holes(roi_seg)
            
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
            solidity = prop.solidity  # area / convex_hull_area (rejects irregular noise)
            extent = prop.extent      # area / bbox_area (rejects sparse noise)
            
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
            
            # Second filtering step - check area, perimeter, circularity, aspect ratio, AND quality metrics
            # Quality metrics (solidity, extent) help reject noise that has similar size to real cells
            if (self.area_min * 0.8 < area < self.area_max * 1.2 and 
                self.min_perimeter * 0.7 < perimeter < self.max_perimeter * 1.3 and 
                self.min_circularity * 0.8 < circularity < self.max_circularity * 1.2 and
                aspect_ratio_condition and
                solidity >= self.min_solidity and  # Reject irregular/fragmented noise
                extent >= self.min_extent):         # Reject sparse noise
                    
                    # Calculate centroid (keep in AOI/cropped image space)
                    y, x = prop.centroid
                    
                    # Convert bbox from (min_row, min_col, max_row, max_col) to (x1, y1, x2, y2)
                    # Keep coordinates in AOI/cropped image space - don't adjust back to original
                    cell_bbox = (bbox[1], bbox[0], bbox[3], bbox[2])
                    
                    detected_cells.append({
                        'centroid': (x, y),
                        'area': area,
                        'bbox': cell_bbox,
                        'perimeter': perimeter,
                        'circularity': circularity,
                        'eccentricity': eccentricity,
                        'solidity': solidity,
                        'extent': extent,
                        'aoi_offset': (x1, y1) if aoi_coords else (0, 0)  # Store AOI offset for later use
                    })
        
        # Store results
        self.detected_cells = detected_cells
        
        # Calculate processing time
        processing_time = time.time() - start_time
        gpu_utilization = self.get_gpu_utilization()
        print(f"GPU detection time: {processing_time:.3f}s, GPU utilization: {gpu_utilization}%, Found {len(detected_cells)} cells")
        
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
