"""
ImageProcessor: Bayer RAW Image Cell Detection and Analysis
Processes 16-bit single-channel TIFF images from RawDigger RGGB Bayer RAW export
"""

import os
import sys
import logging
import yaml
import numpy as np
import cv2
from skimage import filters, morphology, measure
from skimage.segmentation import clear_border
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from typing import List, Tuple, Optional, Dict, Any


class ImageProcessor:
    """Main image processing class for Bayer RAW cell detection"""
    
    def __init__(self, config_path: str = None):
        """Initialize ImageProcessor with configuration"""
        if config_path is None:
            # Use config.yaml in the same directory as this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "config.yaml")
        
        self.config = self.load_config(config_path)
        self.setup_logging()
        
        # Image data storage
        self.raw_image = None
        self.r_raw = None
        self.r_flu = None
        self.r_gau = None
        self.r_bin = None
        self.dark_field = None
        
        # Processing results
        self.contours = []
        self.cell_data = []
        
        # File paths
        self.main_image_path = None
        self.dark_field_path = None
        self.output_dir = None
        
        self.logger.info("ImageProcessor initialized")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Warning: Config file {config_path} not found, using defaults")
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        default_config = {
            'contrast_enhancement': {
                'enabled': True,
                'clahe_clip_limit': 3.0,
                'clahe_tile_size': 8,
                'gamma': 0.7
            },
            'gaussian': {'sigma': 0.8},
            'thresholding': {'algorithm': 'otsu', 'min_area': 200},
            'morphology': {'closing_radius': 3},
            'dark_field': {'corner_size': 50},
            'output': {
                'overlay_colormap': 'red',
                'contour_color': [0, 255, 0],
                'text_color': [255, 255, 255]
            },
            'logging': {'level': 'DEBUG'}
        }
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config['logging']['level'])
        
        # Create log file in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(script_dir, 'image_processor.log')
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_image_unicode_safe(self, image_path: str) -> np.ndarray:
        """Load image with Unicode path support"""
        self.logger.debug(f"Attempting to load image: {image_path}")
        
        try:
            # Method 1: Try standard OpenCV method (works for ASCII paths)
            self.logger.debug("Trying cv2.imread...")
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if image is not None:
                self.logger.debug(f"cv2.imread successful: shape={image.shape}, dtype={image.dtype}")
                return image
            else:
                self.logger.debug("cv2.imread returned None, trying alternative methods...")
            
        except Exception as e1:
            self.logger.debug(f"cv2.imread failed: {str(e1)}")
        
        try:
            # Method 2: Try numpy + cv2.imdecode for Unicode paths
            self.logger.debug("Trying binary read + cv2.imdecode...")
            
            # Read file as binary data
            with open(image_path, 'rb') as f:
                file_bytes = f.read()
            
            self.logger.debug(f"Read {len(file_bytes)} bytes from file")
            
            # Convert to numpy array
            file_array = np.frombuffer(file_bytes, dtype=np.uint8)
            
            # Decode using OpenCV
            image = cv2.imdecode(file_array, cv2.IMREAD_UNCHANGED)
            
            if image is not None:
                self.logger.debug(f"cv2.imdecode successful: shape={image.shape}, dtype={image.dtype}")
                return image
            else:
                self.logger.debug("cv2.imdecode returned None")
                
        except Exception as e2:
            self.logger.debug(f"Binary read + cv2.imdecode failed: {str(e2)}")
        
        try:
            # Method 3: Try PIL as fallback for TIFF files
            self.logger.debug("Trying PIL...")
            from PIL import Image as PILImage
            
            pil_image = PILImage.open(image_path)
            self.logger.debug(f"PIL opened image: mode={pil_image.mode}, size={pil_image.size}")
            
            # Convert PIL image to numpy array
            if pil_image.mode == 'I;16':  # 16-bit grayscale
                image = np.array(pil_image, dtype=np.uint16)
            elif pil_image.mode == 'L':   # 8-bit grayscale
                image = np.array(pil_image, dtype=np.uint8)
            elif pil_image.mode == 'I':   # 32-bit integer
                image = np.array(pil_image, dtype=np.uint32)
            else:
                # Convert to grayscale if needed
                pil_image = pil_image.convert('L')
                image = np.array(pil_image, dtype=np.uint8)
            
            self.logger.debug(f"PIL conversion successful: shape={image.shape}, dtype={image.dtype}")
            return image
            
        except Exception as e3:
            self.logger.debug(f"PIL method failed: {str(e3)}")
        
        # All methods failed
        self.logger.error(f"All image loading methods failed for {image_path}")
        self.logger.error("This is likely due to Unicode characters in the file path or corrupted file")
        return None
    
    def load_image(self, image_path: str) -> np.ndarray:
        """Load 16-bit TIFF image and validate dimensions"""
        try:
            # Normalize path separators for Windows
            normalized_path = os.path.normpath(image_path)
            
            # Check if file exists before attempting to load
            if not os.path.exists(normalized_path):
                raise ValueError(f"File not found: {normalized_path}")
            
            # Load image using method that handles Unicode paths
            image = self._load_image_unicode_safe(normalized_path)
            
            if image is None:
                raise ValueError(f"Failed to load image: {normalized_path}")
            
            # Ensure 16-bit depth
            if image.dtype != np.uint16:
                self.logger.warning(f"Image is not 16-bit, converting from {image.dtype}")
                if image.dtype == np.uint8:
                    image = image.astype(np.uint16) * 256
                else:
                    image = image.astype(np.uint16)
            
            # Check if single channel
            if len(image.shape) != 2:
                raise ValueError("Image must be single channel (grayscale)")
            
            # Validate Bayer dimensions (must be even)
            height, width = image.shape
            if height % 2 != 0 or width % 2 != 0:
                raise ValueError("Bayer 尺寸非法: Image dimensions must be even for Bayer pattern")
            
            self.logger.info(f"Loaded image: {width}x{height}, dtype: {image.dtype}")
            return image
            
        except Exception as e:
            self.logger.error(f"Error loading image {normalized_path}: {str(e)}")
            raise
    
    def split_bayer_rggb(self, raw_image: np.ndarray) -> Dict[str, np.ndarray]:
        """Split RGGB Bayer pattern into separate channels"""
        try:
            height, width = raw_image.shape
            
            # Extract RGGB channels
            r_channel = raw_image[0::2, 0::2].astype(np.float32)  # Even rows, even cols
            g1_channel = raw_image[0::2, 1::2].astype(np.float32)  # Even rows, odd cols
            g2_channel = raw_image[1::2, 0::2].astype(np.float32)  # Odd rows, even cols
            b_channel = raw_image[1::2, 1::2].astype(np.float32)  # Odd rows, odd cols
            
            channels = {
                'R': r_channel,
                'G1': g1_channel,
                'G2': g2_channel,
                'B': b_channel
            }
            
            self.logger.info(f"Bayer split completed: R shape {r_channel.shape}")
            return channels
            
        except Exception as e:
            self.logger.error(f"Error splitting Bayer pattern: {str(e)}")
            raise
    
    def calculate_dark_field(self, r_raw: np.ndarray, dark_field_path: Optional[str] = None) -> np.ndarray:
        """Calculate dark field from separate image or corner regions"""
        try:
            if dark_field_path and os.path.exists(dark_field_path):
                self.logger.info(f"Loading dark field image from: {dark_field_path}")
                
                # Load dark field image with enhanced error handling
                try:
                    dark_image = self.load_image(dark_field_path)
                    if dark_image is None:
                        raise ValueError("Dark field image could not be loaded")
                    
                    dark_channels = self.split_bayer_rggb(dark_image)
                    dark_field = dark_channels['R']
                    self.logger.info(f"Using provided dark field image{dark_field.shape}")
                    
                except Exception as dark_load_error:
                    self.logger.warning(f"Failed to load dark field image: {str(dark_load_error)}")
                    self.logger.warning("Falling back to corner-based dark field calculation")
                    
                    # Fall back to corner calculation
                    corner_size = self.config['dark_field']['corner_size']
                    height, width = r_raw.shape
                    
                    # Extract four corners
                    corners = [
                        r_raw[:corner_size, :corner_size],  # Top-left
                        r_raw[:corner_size, -corner_size:],  # Top-right
                        r_raw[-corner_size:, :corner_size],  # Bottom-left
                        r_raw[-corner_size:, -corner_size:]  # Bottom-right
                    ]
                    
                    # Calculate median of all corner pixels
                    all_corner_pixels = np.concatenate([corner.flatten() for corner in corners])
                    dark_value = np.median(all_corner_pixels)
                    dark_field = np.full_like(r_raw, dark_value, dtype=np.float32)
                    
                    self.logger.info(f"Calculated dark field from corners: median = {dark_value:.2f}")
            else:
                # Use corner regions of main image
                corner_size = self.config['dark_field']['corner_size']
                height, width = r_raw.shape
                
                # Extract four corners
                corners = [
                    r_raw[:corner_size, :corner_size],  # Top-left
                    r_raw[:corner_size, -corner_size:],  # Top-right
                    r_raw[-corner_size:, :corner_size],  # Bottom-left
                    r_raw[-corner_size:, -corner_size:]  # Bottom-right
                ]
                
                # Calculate median of all corner pixels
                all_corner_pixels = np.concatenate([corner.flatten() for corner in corners])
                dark_value = np.median(all_corner_pixels)
                dark_field = np.full_like(r_raw, dark_value, dtype=np.float32)
                
                self.logger.info(f"Calculated dark field from corners: median = {dark_value:.2f}")
            
            return dark_field
            
        except Exception as e:
            self.logger.error(f"Error calculating dark field: {str(e)}")
            raise
    
    def subtract_dark_field(self, r_raw: np.ndarray, dark_field: np.ndarray) -> np.ndarray:
        """Subtract dark field and clip negative values"""
        try:
            r_flu = r_raw - dark_field
            r_flu = np.clip(r_flu, 0, None)  # Clip negative values to 0
            
            self.logger.info(f"Dark field subtraction completed: range [{r_flu.min():.2f}, {r_flu.max():.2f}]")
            return r_flu
            
        except Exception as e:
            self.logger.error(f"Error subtracting dark field: {str(e)}")
            raise
    
    def enhance_contrast_for_detection(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast for better cell detection without affecting measurements"""
        try:
            # Check if enhancement is enabled
            if not self.config.get('contrast_enhancement', {}).get('enabled', True):
                return image.astype(np.float32)
            
            # Get parameters from config
            clahe_clip_limit = self.config.get('contrast_enhancement', {}).get('clahe_clip_limit', 3.0)
            clahe_tile_size = self.config.get('contrast_enhancement', {}).get('clahe_tile_size', 8)
            gamma = self.config.get('contrast_enhancement', {}).get('gamma', 0.7)
            
            # Create enhanced version for detection only
            enhanced = image.copy()
            
            # Method 1: Percentile-based contrast stretching
            p1, p99 = np.percentile(enhanced, [1, 99])
            if p99 > p1:  # Avoid division by zero
                enhanced = np.clip((enhanced - p1) / (p99 - p1), 0, 1)
                enhanced = enhanced * (image.max() - image.min()) + image.min()
            
            # Method 2: Adaptive histogram equalization (CLAHE) for local contrast
            # Convert to 16-bit for CLAHE
            img_16bit = (enhanced / enhanced.max() * 65535).astype(np.uint16)
            
            # Apply CLAHE with configurable parameters
            clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_tile_size, clahe_tile_size))
            enhanced_16bit = clahe.apply(img_16bit)
            
            # Convert back to original range
            enhanced = enhanced_16bit.astype(np.float32) / 65535.0 * enhanced.max()
            
            # Method 3: Gamma correction for mid-tone enhancement
            enhanced = np.power(enhanced / enhanced.max(), gamma) * enhanced.max()
            
            self.logger.info(f"Contrast enhancement applied: CLAHE(clip={clahe_clip_limit}, tile={clahe_tile_size}), gamma={gamma}")
            self.logger.info(f"Enhanced range: [{enhanced.min():.2f}, {enhanced.max():.2f}]")
            return enhanced.astype(np.float32)
            
        except Exception as e:
            self.logger.warning(f"Contrast enhancement failed, using original: {str(e)}")
            return image.astype(np.float32)
    
    def apply_gaussian_filter(self, image: np.ndarray) -> np.ndarray:
        """Apply Gaussian blur for noise reduction while preserving edges"""
        try:
            sigma = self.config['gaussian']['sigma']
            
            # Apply Gaussian filter
            filtered = filters.gaussian(image, sigma=sigma, preserve_range=True)
            
            self.logger.info(f"Gaussian filtering applied: sigma = {sigma}")
            return filtered.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"Error applying Gaussian filter: {str(e)}")
            raise
    
    def apply_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply automatic thresholding (Otsu or Triangle)"""
        try:
            algorithm = self.config['thresholding']['algorithm']
            
            # Convert to uint8 for thresholding
            image_8bit = ((image - image.min()) / (image.max() - image.min()) * 255).astype(np.uint8)
            
            if algorithm.lower() == 'otsu':
                threshold = filters.threshold_otsu(image_8bit)
            elif algorithm.lower() == 'triangle':
                threshold = filters.threshold_triangle(image_8bit)
            else:
                self.logger.warning(f"Unknown algorithm {algorithm}, using Otsu")
                threshold = filters.threshold_otsu(image_8bit)
            
            # Apply threshold
            binary = image_8bit > threshold
            
            self.logger.info(f"Thresholding applied: {algorithm}, threshold = {threshold}")
            return binary.astype(np.uint8)
            
        except Exception as e:
            self.logger.error(f"Error applying threshold: {str(e)}")
            raise
    
    def post_process_binary(self, binary: np.ndarray) -> np.ndarray:
        """Post-process binary image: remove small objects and apply morphological closing"""
        try:
            min_area = self.config['thresholding']['min_area']
            closing_radius = self.config['morphology']['closing_radius']
            
            # Remove small objects
            cleaned = morphology.remove_small_objects(
                binary.astype(bool), min_size=min_area
            )
            
            # Apply morphological closing
            selem = morphology.disk(closing_radius)
            closed = morphology.binary_closing(cleaned, selem)
            
            self.logger.info(f"Post-processing: removed objects < {min_area} pixels, closing radius = {closing_radius}")
            return closed.astype(np.uint8)
            
        except Exception as e:
            self.logger.error(f"Error in post-processing: {str(e)}")
            raise
    
    def find_contours(self, binary: np.ndarray) -> List[np.ndarray]:
        """Find contours using OpenCV"""
        try:
            # Find contours
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Convert to list of numpy arrays
            contour_list = [contour.squeeze() for contour in contours if len(contour) > 2]
            
            self.logger.info(f"Found {len(contour_list)} contours")
            return contour_list
            
        except Exception as e:
            self.logger.error(f"Error finding contours: {str(e)}")
            raise
    
    def measure_intensity(self, r_flu: np.ndarray, contours: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Measure intensity for each cell contour"""
        try:
            cell_data = []
            height, width = r_flu.shape
            
            for i, contour in enumerate(contours):
                # Create mask for this contour
                mask = np.zeros((height, width), dtype=np.uint8)
                cv2.fillPoly(mask, [contour], 1)
                
                # Calculate measurements
                area = np.sum(mask)
                if area == 0:
                    continue
                
                total_intensity = np.sum(r_flu * mask)
                mean_intensity = total_intensity / area
                
                # Convert contour to string format
                contour_str = '|'.join([f"{int(pt[0])}:{int(pt[1])}" for pt in contour])
                
                cell_info = {
                    'label': i + 1,
                    'area_pixel': int(area),
                    'mean_intensity': float(mean_intensity),
                    'total_intensity': float(total_intensity),
                    'contour_csv': contour_str,
                    'contour_points': contour
                }
                
                cell_data.append(cell_info)
            
            self.logger.info(f"Measured intensity for {len(cell_data)} cells")
            return cell_data
            
        except Exception as e:
            self.logger.error(f"Error measuring intensity: {str(e)}")
            raise
    
    def save_csv(self, cell_data: List[Dict[str, Any]], output_path: str):
        """Save cell data to CSV file"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if not cell_data:
                    # Write empty file with headers only
                    fieldnames = ['label', 'area_pixel', 'mean_intensity', 'total_intensity', 'contour_csv']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    self.logger.warning("No cells detected, saved empty CSV with headers")
                else:
                    fieldnames = ['label', 'area_pixel', 'mean_intensity', 'total_intensity', 'contour_csv']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for cell in cell_data:
                        writer.writerow({
                            'label': cell['label'],
                            'area_pixel': cell['area_pixel'],
                            'mean_intensity': cell['mean_intensity'],
                            'total_intensity': cell['total_intensity'],
                            'contour_csv': cell['contour_csv']
                        })
                    
                    self.logger.info(f"Saved {len(cell_data)} cells to CSV: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving CSV: {str(e)}")
            raise
    
    def create_overlay_image(self, r_flu: np.ndarray, contours: List[np.ndarray], 
                           cell_data: List[Dict[str, Any]], output_path: str):
        """Create quality control overlay image"""
        try:
            self.logger.info(f"Creating overlay image with {len(contours)} contours")
            self.logger.info(f"Image shape: {r_flu.shape}, dtype: {r_flu.dtype}")
            self.logger.info(f"Image range: {r_flu.min()} to {r_flu.max()}")
            
            # Normalize to 8-bit for display
            if r_flu.max() == r_flu.min():
                # Handle case where image has no variation
                r_flu_norm = np.zeros_like(r_flu, dtype=np.uint8)
                self.logger.warning("Image has no intensity variation, creating blank overlay")
            else:
                r_flu_norm = ((r_flu - r_flu.min()) / (r_flu.max() - r_flu.min()) * 255).astype(np.uint8)
            
            # Apply red colormap for R channel visualization
            colormap = self.config['output']['overlay_colormap']
            if colormap == 'red' or colormap == 'r_channel':
                # Create red colormap for R channel
                colored = np.zeros((r_flu_norm.shape[0], r_flu_norm.shape[1], 3), dtype=np.uint8)
                colored[:, :, 2] = r_flu_norm  # Red channel (BGR format)
            elif colormap == 'jet':
                colored = cv2.applyColorMap(r_flu_norm, cv2.COLORMAP_JET)
            elif colormap == 'magma':
                # Use matplotlib for magma colormap
                cmap = cm.get_cmap('magma')
                colored = (cmap(r_flu_norm / 255.0)[:, :, :3] * 255).astype(np.uint8)
                colored = cv2.cvtColor(colored, cv2.COLOR_RGB2BGR)
            else:
                # Default to red colormap for R channel
                colored = np.zeros((r_flu_norm.shape[0], r_flu_norm.shape[1], 3), dtype=np.uint8)
                colored[:, :, 2] = r_flu_norm  # Red channel (BGR format)
            
            # Draw contours and labels
            contour_color = tuple(self.config['output']['contour_color'])
            for i, (contour, cell) in enumerate(zip(contours, cell_data)):
                # Draw contour
                cv2.drawContours(colored, [contour], -1, contour_color, 2)
                
                # Find top-left point of contour for label placement
                x, y, w, h = cv2.boundingRect(contour)
                
                # Create labels for area, mean intensity, and integrated intensity
                area_text = f"A:{cell['area_pixel']}"
                mean_intensity_text = f"Mean:{cell['mean_intensity']:.1f}"
                total_intensity_text = f"Total:{cell['total_intensity']:.0f}"
                
                # Draw labels with proper spacing
                cv2.putText(colored, area_text, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, contour_color, 1)
                cv2.putText(colored, mean_intensity_text, (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
                cv2.putText(colored, total_intensity_text, (x, y-35), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
            
            # Add metadata text
            height, width = colored.shape[:2]
            text_color = tuple(self.config['output']['text_color'])
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 1
            
            # Calculate statistics
            mean_intensities = [cell['mean_intensity'] for cell in cell_data] if cell_data else [0]
            total_intensities = [cell['total_intensity'] for cell in cell_data] if cell_data else [0]
            avg_mean_intensity = np.mean(mean_intensities)
            avg_total_intensity = np.mean(total_intensities)
            sum_integrated = np.sum(total_intensities)
            
            # Prepare text lines
            text_lines = [
                f"Cells: {len(cell_data)}",
                f"Avg Mean: {avg_mean_intensity:.1f}",
                f"Avg Total: {avg_total_intensity:.0f}",
                f"Sum Integrated: {sum_integrated:.0f}",
                f"Algorithm: {self.config['thresholding']['algorithm']}",
                f"Min Area: {self.config['thresholding']['min_area']}"
            ]
            
            # Draw text in bottom-right corner
            y_offset = height - 20
            for line in reversed(text_lines):
                text_size = cv2.getTextSize(line, font, font_scale, thickness)[0]
                x_pos = width - text_size[0] - 10
                cv2.putText(colored, line, (x_pos, y_offset), font, font_scale, text_color, thickness)
                y_offset -= 25
            
            # Save as TIFF - handle Unicode paths
            self.logger.info(f"Saving overlay image to: {output_path}")
            
            try:
                # Method 1: Try direct cv2.imwrite first
                success = cv2.imwrite(output_path, colored)
                if success:
                    self.logger.info(f"Successfully saved overlay image: {output_path}")
                else:
                    raise RuntimeError("cv2.imwrite returned False")
                    
            except Exception as e1:
                self.logger.warning(f"cv2.imwrite failed, trying alternative method: {str(e1)}")
                
                try:
                    # Method 2: Use PIL for Unicode path support
                    from PIL import Image
                    
                    # Convert BGR to RGB for PIL
                    colored_rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
                    
                    # Create PIL image and save
                    pil_image = Image.fromarray(colored_rgb)
                    pil_image.save(output_path, format='TIFF', compression='lzw')
                    
                    self.logger.info(f"Successfully saved overlay image using PIL: {output_path}")
                    
                except Exception as e2:
                    self.logger.warning(f"PIL method failed, trying encoded path: {str(e2)}")
                    
                    try:
                        # Method 3: Use cv2.imencode and write binary
                        
                        # Encode image to memory
                        success, encoded_img = cv2.imencode('.tiff', colored)
                        if not success:
                            raise RuntimeError("cv2.imencode failed")
                        
                        # Write binary data to file
                        with open(output_path, 'wb') as f:
                            f.write(encoded_img.tobytes())
                        
                        self.logger.info(f"Successfully saved overlay image using binary write: {output_path}")
                        
                    except Exception as e3:
                        self.logger.error(f"All save methods failed: cv2.imwrite={str(e1)}, PIL={str(e2)}, binary={str(e3)}")
                        
                        # Final fallback: try saving to a simple ASCII path first, then copy
                        try:
                            import tempfile
                            import shutil
                            
                            # Create temporary file with ASCII name
                            with tempfile.NamedTemporaryFile(suffix='.tiff', delete=False) as tmp_file:
                                temp_path = tmp_file.name
                            
                            # Save to temp path
                            success = cv2.imwrite(temp_path, colored)
                            if success:
                                # Copy to final destination
                                shutil.copy2(temp_path, output_path)
                                os.unlink(temp_path)  # Clean up temp file
                                self.logger.info(f"Successfully saved overlay image using temp file method: {output_path}")
                            else:
                                raise RuntimeError("Even temp file method failed")
                                
                        except Exception as e4:
                            self.logger.error(f"All save methods failed including temp file: {str(e4)}")
                            raise RuntimeError(f"Unable to save overlay image to {output_path}. All methods failed.")
            
        except Exception as e:
            self.logger.error(f"Error creating overlay image: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def process_image(self, main_image_path: str, dark_field_path: Optional[str] = None) -> Dict[str, Any]:
        """Complete image processing pipeline"""
        try:
            self.logger.info(f"Starting processing pipeline for: {main_image_path}")
            
            # Step 1: Load main image
            self.raw_image = self.load_image(main_image_path)
            self.main_image_path = main_image_path
            
            # Step 2: Split Bayer pattern
            channels = self.split_bayer_rggb(self.raw_image)
            self.r_raw = channels['R']
            
            # Step 3: Dark field subtraction
            self.dark_field = self.calculate_dark_field(self.r_raw, dark_field_path)
            self.r_flu = self.subtract_dark_field(self.r_raw, self.dark_field)
            
            # Step 4: Enhance contrast for better detection (separate from measurement)
            self.r_enhanced = self.enhance_contrast_for_detection(self.r_flu)
            
            # Step 5: Gaussian filtering on enhanced image for detection
            self.r_gau = self.apply_gaussian_filter(self.r_enhanced)
            
            # Step 6: Thresholding on enhanced/filtered image
            binary = self.apply_threshold(self.r_gau)
            self.r_bin = self.post_process_binary(binary)
            
            # Step 7: Contour detection on binary image
            self.contours = self.find_contours(self.r_bin)
            
            # Step 8: Intensity measurement on ORIGINAL r_flu (not enhanced)
            # This preserves quantitative accuracy for measurements
            self.cell_data = self.measure_intensity(self.r_flu, self.contours)
            
            # Prepare results
            results = {
                'cell_count': len(self.cell_data),
                'cell_data': self.cell_data,
                'contours': self.contours,
                'processed_images': {
                    'raw': self.raw_image,
                    'r_raw': self.r_raw,
                    'r_flu': self.r_flu,
                    'r_enhanced': self.r_enhanced,  # Enhanced version for display
                    'r_gau': self.r_gau,
                    'r_bin': self.r_bin
                }
            }
            
            if len(self.cell_data) == 0:
                self.logger.warning("No cells detected in the image")
            else:
                avg_intensity = np.mean([cell['mean_intensity'] for cell in self.cell_data])
                self.logger.info(f"Processing completed: {len(self.cell_data)} cells, avg intensity: {avg_intensity:.2f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in processing pipeline: {str(e)}")
            raise
    
    def save_results(self, output_dir: str, base_filename: str):
        """Save CSV and overlay image results"""
        try:
            if not self.cell_data:
                self.logger.warning("No cell data to save")
                return
            
            if not hasattr(self, 'contours') or not self.contours:
                self.logger.warning("No contours available for overlay image")
                return
            
            if not hasattr(self, 'r_flu') or self.r_flu is None:
                self.logger.warning("No fluorescence image available for overlay")
                return
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            self.logger.info(f"Saving results to directory: {output_dir}")
            
            # Save CSV
            csv_path = os.path.join(output_dir, f"{base_filename}-cells.csv")
            self.logger.info(f"Saving CSV to: {csv_path}")
            self.save_csv(self.cell_data, csv_path)
            
            # Verify CSV was created
            if os.path.exists(csv_path):
                self.logger.info(f"CSV file created successfully: {csv_path}")
            else:
                self.logger.error(f"CSV file was not created: {csv_path}")
            
            # Save overlay image
            overlay_path = os.path.join(output_dir, f"{base_filename}-cells-overlay.tiff")
            self.logger.info(f"Creating overlay image: {overlay_path}")
            self.logger.info(f"Using {len(self.contours)} contours and {len(self.cell_data)} cell data entries")
            
            self.create_overlay_image(self.r_flu, self.contours, self.cell_data, overlay_path)
            
            # Verify overlay image was created
            if os.path.exists(overlay_path):
                file_size = os.path.getsize(overlay_path)
                self.logger.info(f"Overlay image created successfully: {overlay_path} ({file_size} bytes)")
            else:
                self.logger.error(f"Overlay image was not created: {overlay_path}")
            
            self.logger.info(f"Results saving completed for: {base_filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise


if __name__ == "__main__":
    # Simple command line interface for testing
    if len(sys.argv) < 2:
        print("Usage: python image_processor.py <image_path> [dark_field_path] [output_dir]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    dark_field_path = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(image_path)
    
    try:
        processor = ImageProcessor()
        results = processor.process_image(image_path, dark_field_path)
        
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        processor.save_results(output_dir, base_filename)
        
        print(f"Processing completed: {results['cell_count']} cells detected")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
