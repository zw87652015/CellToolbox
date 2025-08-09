"""
Cell Detection Module
This module contains the CellDetector class for processing images and detecting cells.
"""

import numpy as np
import cv2
from skimage import filters, morphology, measure, segmentation
import scipy.ndimage as ndi

class CellDetector:
    """Cell detection class for processing images and detecting cells"""
    
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
        
        # Watershed segmentation parameters
        self.use_watershed = True
        self.watershed_distance_threshold = 10
        self.watershed_footprint_size = 3
        self.watershed_compactness = 0.5
        self.watershed_min_area = 500
        
        # For backward compatibility
        self.min_area = self.area_min
        self.max_area = self.area_max
        
        self.detected_cells = []
        self.processing = False
    
    def detect_cells(self, frame, aoi_coords=None, return_debug=False):
        """Process image and detect cells, optionally within an AOI"""
        # Make a copy of the image to avoid modifying the original
        org = frame.copy()
        
        # If AOI is provided, crop the image to the AOI
        if aoi_coords and all(coord != 0 for coord in aoi_coords):
            x1, y1, x2, y2 = aoi_coords
            # Ensure x1 < x2 and y1 < y2
            if x1 > x2: x1, x2 = x2, x1
            if y1 > y2: y1, y2 = y2, y1
            
            # Crop the image to the AOI
            org = org[y1:y2, x1:x2]
            
            # If the cropped image is too small, return empty results
            if org.shape[0] < 10 or org.shape[1] < 10:
                return [] if not return_debug else ([], None)
        
        # Convert BGR to RGB for display
        org_rgb = cv2.cvtColor(org, cv2.COLOR_BGR2RGB)
        
        # Convert to grayscale
        gray_image = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, 
                              tileGridSize=(self.clahe_tile_size, self.clahe_tile_size))
        enhanced_image = clahe.apply(gray_image)
        
        # Convert to float and denoise
        double_image = enhanced_image.astype(np.float32) / 255.0
        denoised_image = cv2.GaussianBlur(double_image, (3, 3), 2)
        
        # Conservative binary thresholding - use Otsu for cleaner segmentation
        try:
            # Use Otsu thresholding for better automatic threshold selection
            _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        except:
            # Fallback to simple thresholding
            _, binary_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Conservative edge detection - use only Canny for clean edges
        img_8bit = (denoised_image * 255).astype(np.uint8)
        edge_canny = cv2.Canny(img_8bit, self.canny_low, self.canny_high)
        
        # Combine binary and edge detection (more conservative approach)
        roi_seg = binary_image.astype(bool) | edge_canny.astype(bool)
        
        # Conservative morphological operations
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # Remove noise first
        roi_seg = morphology.remove_small_objects(roi_seg.astype(bool), min_size=self.min_object_size)
        
        # Light morphological operations to preserve cell boundaries
        roi_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_OPEN, kernel_small)
        roi_seg = cv2.morphologyEx(roi_seg.astype(np.uint8), cv2.MORPH_CLOSE, kernel_medium, iterations=1)
        
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
                # This helps identify separate cells even when they're touching
                distance_peaks = distance > self.watershed_distance_threshold
                
                # Clean up the peaks to get better markers
                distance_peaks = morphology.remove_small_objects(distance_peaks, min_size=2)
                
                # Label the peaks as markers
                markers = measure.label(distance_peaks)
                
                # Apply watershed segmentation to large objects only
                # Use the negative distance as the input for watershed
                watershed_labels = segmentation.watershed(-distance, markers, mask=large_objects_mask, 
                                                        compactness=self.watershed_compactness)
                
                # Combine the watershed segmentation of large objects with the small objects
                # First, get the maximum label from watershed_labels
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
            
            # Calculate aspect ratio condition using parameter from visualization UI
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
                    
                    # If using AOI, adjust the coordinates back to the original image
                    if aoi_coords and all(coord != 0 for coord in aoi_coords):
                        x1_aoi, y1_aoi = aoi_coords[0], aoi_coords[1]
                        adjusted_bbox = (
                            bbox[1] + x1_aoi,  # x1 (min_col + x_offset)
                            bbox[0] + y1_aoi,  # y1 (min_row + y_offset)
                            bbox[3] + x1_aoi,  # x2 (max_col + x_offset)
                            bbox[2] + y1_aoi   # y2 (max_row + y_offset)
                        )
                        detected_cells.append({
                            'bbox': adjusted_bbox,
                            'area': area,
                            'perimeter': perimeter,
                            'circularity': circularity,
                            'eccentricity': eccentricity,
                            'centroid': (x + x1_aoi, y + y1_aoi)  # (x, y) format
                        })
                    else:
                        # Add cell to the list
                        detected_cells.append({
                            'bbox': (bbox[1], bbox[0], bbox[3], bbox[2]),  # Convert to (x1, y1, x2, y2)
                            'centroid': (x, y),  # (x, y) format
                            'area': area,
                            'perimeter': perimeter,
                            'circularity': circularity,
                            'eccentricity': eccentricity
                        })
        
        self.detected_cells = detected_cells
        
        # Return debug information if requested
        if return_debug:
            # Convert final_seg to 8-bit for visualization (white = detected objects)
            debug_image = (final_seg * 255).astype(np.uint8)
            return detected_cells, debug_image
        else:
            return detected_cells
    
    def visualize_cells(self, image, cells, aoi_coords=None):
        """
        Create a visualization of the detected cells
        
        Args:
            image: Original image
            cells: List of detected cells
            aoi_coords: Optional AOI coordinates
            
        Returns:
            numpy.ndarray: Visualization image
        """
        # Create a copy of the image for visualization
        vis_image = image.copy()
        
        # Draw detected cells
        for cell in cells:
            centroid = cell['centroid']
            bbox = cell['bbox']
            
            # Draw centroid
            cv2.circle(vis_image, (int(centroid[0]), int(centroid[1])), 3, (0, 255, 0), -1)
            
            # Draw bounding box
            cv2.rectangle(vis_image, 
                         (int(bbox[0]), int(bbox[1])), 
                         (int(bbox[2]), int(bbox[3])), 
                         (255, 0, 0), 2)
        
        # Draw AOI if specified
        if aoi_coords is not None:
            x1, y1, x2, y2 = aoi_coords
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        return vis_image
