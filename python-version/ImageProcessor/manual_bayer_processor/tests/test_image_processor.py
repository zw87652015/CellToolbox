"""
Unit tests for ImageProcessor
Tests the core functionality with synthetic test images
"""

import unittest
import numpy as np
import cv2
import os
import tempfile
import shutil
from core.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = ImageProcessor()
        self.test_dir = tempfile.mkdtemp()
        
        # Create synthetic test images
        self.create_test_images()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def create_test_images(self):
        """Create synthetic test images for testing"""
        # Create a synthetic Bayer pattern image with known cell-like structures
        width, height = 200, 200  # Even dimensions for Bayer
        
        # Create base image
        base_image = np.zeros((height, width), dtype=np.uint16)
        
        # Add background noise
        background_level = 1000
        noise = np.random.normal(0, 50, (height, width))
        base_image = (background_level + noise).astype(np.uint16)
        
        # Add synthetic "cells" - bright circular regions
        cell_centers = [(50, 50), (150, 50), (100, 150)]
        cell_radius = 15
        cell_intensity = 3000
        
        for center_x, center_y in cell_centers:
            y, x = np.ogrid[:height, :width]
            mask = (x - center_x)**2 + (y - center_y)**2 <= cell_radius**2
            base_image[mask] = cell_intensity
        
        # Create RGGB Bayer pattern
        # R channel gets the cell pattern, others get background
        bayer_image = np.zeros((height, width), dtype=np.uint16)
        
        # R positions (even row, even col) - contains cells
        bayer_image[0::2, 0::2] = base_image[0::2, 0::2]
        
        # G1 positions (even row, odd col) - background only
        bayer_image[0::2, 1::2] = background_level + np.random.normal(0, 30, base_image[0::2, 1::2].shape)
        
        # G2 positions (odd row, even col) - background only  
        bayer_image[1::2, 0::2] = background_level + np.random.normal(0, 30, base_image[1::2, 0::2].shape)
        
        # B positions (odd row, odd col) - background only
        bayer_image[1::2, 1::2] = background_level + np.random.normal(0, 30, base_image[1::2, 1::2].shape)
        
        # Ensure values are in valid range
        bayer_image = np.clip(bayer_image, 0, 65535).astype(np.uint16)
        
        # Save test image
        self.test_image_path = os.path.join(self.test_dir, "test_bayer.tif")
        cv2.imwrite(self.test_image_path, bayer_image)
        
        # Create dark field image (uniform background)
        dark_field = np.full((height, width), background_level - 200, dtype=np.uint16)
        self.dark_field_path = os.path.join(self.test_dir, "dark_field.tif")
        cv2.imwrite(self.dark_field_path, dark_field)
        
        # Store expected results
        self.expected_cell_count = len(cell_centers)
    
    def test_load_image(self):
        """Test image loading functionality"""
        # Test successful loading
        image = self.processor.load_image(self.test_image_path)
        self.assertIsNotNone(image)
        self.assertEqual(image.dtype, np.uint16)
        self.assertEqual(len(image.shape), 2)  # Single channel
        
        # Test dimensions are even
        height, width = image.shape
        self.assertEqual(height % 2, 0)
        self.assertEqual(width % 2, 0)
    
    def test_load_image_invalid_dimensions(self):
        """Test error handling for odd dimensions"""
        # Create image with odd dimensions
        odd_image = np.zeros((199, 201), dtype=np.uint16)  # Odd dimensions
        odd_path = os.path.join(self.test_dir, "odd_image.tif")
        cv2.imwrite(odd_path, odd_image)
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.processor.load_image(odd_path)
        
        self.assertIn("Bayer 尺寸非法", str(context.exception))
    
    def test_bayer_split(self):
        """Test Bayer pattern splitting"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        
        # Check all channels exist
        self.assertIn('R', channels)
        self.assertIn('G1', channels)
        self.assertIn('G2', channels)
        self.assertIn('B', channels)
        
        # Check dimensions
        height, width = image.shape
        expected_shape = (height // 2, width // 2)
        
        for channel_name, channel_data in channels.items():
            self.assertEqual(channel_data.shape, expected_shape)
            self.assertEqual(channel_data.dtype, np.float32)
    
    def test_dark_field_calculation(self):
        """Test dark field calculation"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        r_raw = channels['R']
        
        # Test with provided dark field
        dark_field = self.processor.calculate_dark_field(r_raw, self.dark_field_path)
        self.assertEqual(dark_field.shape, r_raw.shape)
        self.assertEqual(dark_field.dtype, np.float32)
        
        # Test without dark field (corner method)
        dark_field_corners = self.processor.calculate_dark_field(r_raw, None)
        self.assertEqual(dark_field_corners.shape, r_raw.shape)
        self.assertEqual(dark_field_corners.dtype, np.float32)
    
    def test_dark_field_subtraction(self):
        """Test dark field subtraction"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        r_raw = channels['R']
        
        dark_field = self.processor.calculate_dark_field(r_raw, self.dark_field_path)
        r_flu = self.processor.subtract_dark_field(r_raw, dark_field)
        
        # Check result properties
        self.assertEqual(r_flu.shape, r_raw.shape)
        self.assertEqual(r_flu.dtype, np.float32)
        
        # Check no negative values
        self.assertGreaterEqual(r_flu.min(), 0)
        
        # Check that subtraction actually reduced values
        self.assertLess(r_flu.mean(), r_raw.mean())
    
    def test_gaussian_filter(self):
        """Test Gaussian filtering"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        r_raw = channels['R']
        
        # Apply filtering
        r_gau = self.processor.apply_gaussian_filter(r_raw)
        
        # Check result properties
        self.assertEqual(r_gau.shape, r_raw.shape)
        self.assertEqual(r_gau.dtype, np.float32)
        
        # Filtered image should be smoother (less variation)
        self.assertLess(r_gau.std(), r_raw.std())
    
    def test_thresholding(self):
        """Test automatic thresholding"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        r_raw = channels['R']
        r_gau = self.processor.apply_gaussian_filter(r_raw)
        
        # Test Otsu thresholding
        self.processor.config['thresholding']['algorithm'] = 'otsu'
        binary_otsu = self.processor.apply_threshold(r_gau)
        
        # Check result properties
        self.assertEqual(binary_otsu.shape, r_gau.shape)
        self.assertEqual(binary_otsu.dtype, np.uint8)
        self.assertEqual(set(np.unique(binary_otsu)), {0, 1})
        
        # Test Triangle thresholding
        self.processor.config['thresholding']['algorithm'] = 'triangle'
        binary_triangle = self.processor.apply_threshold(r_gau)
        
        self.assertEqual(binary_triangle.shape, r_gau.shape)
        self.assertEqual(binary_triangle.dtype, np.uint8)
    
    def test_post_processing(self):
        """Test binary post-processing"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        r_raw = channels['R']
        r_gau = self.processor.apply_gaussian_filter(r_raw)
        binary = self.processor.apply_threshold(r_gau)
        
        # Apply post-processing
        processed = self.processor.post_process_binary(binary)
        
        # Check result properties
        self.assertEqual(processed.shape, binary.shape)
        self.assertEqual(processed.dtype, np.uint8)
        self.assertEqual(set(np.unique(processed)), {0, 1})
    
    def test_contour_detection(self):
        """Test contour detection"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        r_raw = channels['R']
        r_gau = self.processor.apply_gaussian_filter(r_raw)
        binary = self.processor.apply_threshold(r_gau)
        processed = self.processor.post_process_binary(binary)
        
        # Find contours
        contours = self.processor.find_contours(processed)
        
        # Should find some contours
        self.assertGreater(len(contours), 0)
        
        # Each contour should be a numpy array
        for contour in contours:
            self.assertIsInstance(contour, np.ndarray)
            self.assertEqual(len(contour.shape), 2)
            self.assertEqual(contour.shape[1], 2)  # x, y coordinates
    
    def test_intensity_measurement(self):
        """Test intensity measurement"""
        image = self.processor.load_image(self.test_image_path)
        channels = self.processor.split_bayer_rggb(image)
        r_raw = channels['R']
        
        # Create simple dark field and process
        dark_field = self.processor.calculate_dark_field(r_raw, self.dark_field_path)
        r_flu = self.processor.subtract_dark_field(r_raw, dark_field)
        r_gau = self.processor.apply_gaussian_filter(r_flu)
        binary = self.processor.apply_threshold(r_gau)
        processed = self.processor.post_process_binary(binary)
        contours = self.processor.find_contours(processed)
        
        # Measure intensity
        cell_data = self.processor.measure_intensity(r_flu, contours)
        
        # Check results
        self.assertGreater(len(cell_data), 0)
        
        for cell in cell_data:
            # Check required fields
            self.assertIn('label', cell)
            self.assertIn('area_pixel', cell)
            self.assertIn('mean_intensity', cell)
            self.assertIn('total_intensity', cell)
            self.assertIn('contour_csv', cell)
            
            # Check data types and ranges
            self.assertIsInstance(cell['label'], int)
            self.assertIsInstance(cell['area_pixel'], int)
            self.assertIsInstance(cell['mean_intensity'], float)
            self.assertIsInstance(cell['total_intensity'], float)
            self.assertIsInstance(cell['contour_csv'], str)
            
            # Check reasonable values
            self.assertGreater(cell['area_pixel'], 0)
            self.assertGreater(cell['mean_intensity'], 0)
            self.assertGreater(cell['total_intensity'], 0)
            
            # Check contour string format
            self.assertIn(':', cell['contour_csv'])
            self.assertIn('|', cell['contour_csv'])
    
    def test_complete_pipeline(self):
        """Test complete processing pipeline"""
        # Run complete pipeline
        results = self.processor.process_image(self.test_image_path, self.dark_field_path)
        
        # Check results structure
        self.assertIn('cell_count', results)
        self.assertIn('cell_data', results)
        self.assertIn('contours', results)
        self.assertIn('processed_images', results)
        
        # Check cell count is reasonable (should detect synthetic cells)
        self.assertGreaterEqual(results['cell_count'], 1)
        self.assertLessEqual(results['cell_count'], 10)  # Reasonable upper bound
        
        # Check processed images
        processed_images = results['processed_images']
        self.assertIn('raw', processed_images)
        self.assertIn('r_raw', processed_images)
        self.assertIn('r_flu', processed_images)
        self.assertIn('r_gau', processed_images)
        self.assertIn('r_bin', processed_images)
    
    def test_csv_export(self):
        """Test CSV file export"""
        # Process image
        results = self.processor.process_image(self.test_image_path, self.dark_field_path)
        
        # Save CSV
        csv_path = os.path.join(self.test_dir, "test_results.csv")
        self.processor.save_csv(results['cell_data'], csv_path)
        
        # Check file exists
        self.assertTrue(os.path.exists(csv_path))
        
        # Check file content
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        
        # Should have header + data lines
        self.assertGreater(len(lines), 1)
        
        # Check header
        header = lines[0].strip().split(',')
        expected_columns = ['label', 'area_pixel', 'mean_intensity', 'total_intensity', 'contour_csv']
        self.assertEqual(header, expected_columns)
    
    def test_overlay_image_creation(self):
        """Test overlay image creation"""
        # Process image
        results = self.processor.process_image(self.test_image_path, self.dark_field_path)
        
        # Create overlay
        overlay_path = os.path.join(self.test_dir, "test_overlay.tiff")
        self.processor.create_overlay_image(
            self.processor.r_flu, 
            results['contours'], 
            results['cell_data'], 
            overlay_path
        )
        
        # Check file exists
        self.assertTrue(os.path.exists(overlay_path))
        
        # Load and check image
        overlay_image = cv2.imread(overlay_path)
        self.assertIsNotNone(overlay_image)
        self.assertEqual(len(overlay_image.shape), 3)  # Color image
    
    def test_empty_image_handling(self):
        """Test handling of images with no cells"""
        # Create image with no bright regions (no cells)
        width, height = 100, 100
        empty_image = np.full((height, width), 1000, dtype=np.uint16)  # Uniform background
        empty_path = os.path.join(self.test_dir, "empty_image.tif")
        cv2.imwrite(empty_path, empty_image)
        
        # Process empty image
        results = self.processor.process_image(empty_path)
        
        # Should handle gracefully
        self.assertEqual(results['cell_count'], 0)
        self.assertEqual(len(results['cell_data']), 0)
        
        # Test CSV export with empty data
        csv_path = os.path.join(self.test_dir, "empty_results.csv")
        self.processor.save_csv(results['cell_data'], csv_path)
        
        # Should create file with headers only
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)  # Header only


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading and validation"""
    
    def test_default_config(self):
        """Test default configuration loading"""
        processor = ImageProcessor("nonexistent_config.yaml")
        
        # Should load default config
        self.assertIsNotNone(processor.config)
        self.assertIn('gaussian', processor.config)
        self.assertIn('thresholding', processor.config)
        self.assertIn('morphology', processor.config)
    
    def test_custom_config(self):
        """Test custom configuration loading"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
gaussian:
  sigma: 1.5
thresholding:
  algorithm: "triangle"
  min_area: 300
""")
            config_path = f.name
        
        try:
            processor = ImageProcessor(config_path)
            
            # Check custom values loaded
            self.assertEqual(processor.config['gaussian']['sigma'], 1.5)
            self.assertEqual(processor.config['thresholding']['algorithm'], 'triangle')
            self.assertEqual(processor.config['thresholding']['min_area'], 300)
            
        finally:
            os.unlink(config_path)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
