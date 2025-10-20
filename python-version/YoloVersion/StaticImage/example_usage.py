"""
Example usage of the YOLO11 Cell Detector
"""

from cell_detector import CellDetector
import os

def example_single_image():
    """Example: Detect cells in a single image"""
    print("Example 1: Single Image Detection")
    print("-" * 50)
    
    # Initialize detector
    detector = CellDetector('config.yaml')
    
    # Detect cells in a single image
    image_path = "input_images/sample_cell_image.jpg"
    
    if os.path.exists(image_path):
        detections = detector.detect_cells(image_path)
        
        print(f"Found {len(detections)} cells")
        for i, det in enumerate(detections):
            print(f"\nCell {i+1}:")
            print(f"  Position: ({det['center_x']:.1f}, {det['center_y']:.1f})")
            print(f"  Size: {det['width']:.1f} x {det['height']:.1f} pixels")
            print(f"  Area: {det['area']:.1f} pixels²")
            print(f"  Confidence: {det['confidence']:.2f}")
    else:
        print(f"Image not found: {image_path}")
        print("Please place your test images in the 'input_images' folder")


def example_batch_processing():
    """Example: Process all images in a directory"""
    print("\n\nExample 2: Batch Processing")
    print("-" * 50)
    
    # Initialize detector
    detector = CellDetector('config.yaml')
    
    # Process all images in input directory
    detector.process_directory()
    
    # Get and display statistics
    stats = detector.get_statistics()
    
    if stats:
        print("\nProcessing Statistics:")
        print(f"  Total images processed: {stats['total_images']}")
        print(f"  Total cells detected: {stats['total_detections']}")
        print(f"  Average cells per image: {stats['avg_detections_per_image']:.2f}")
        print(f"  Average confidence: {stats['avg_confidence']:.2f}")
        print(f"  Average cell size: {stats['avg_cell_width']:.1f} x {stats['avg_cell_height']:.1f} pixels")
        print(f"  Average cell area: {stats['avg_cell_area']:.1f} pixels²")
    
    print("\nResults saved to 'output_results' folder:")
    print("  - detection_results.csv")
    print("  - detection_results.json")
    print("  - annotated_*.jpg/png (visualizations)")


def example_custom_config():
    """Example: Using custom configuration"""
    print("\n\nExample 3: Custom Configuration")
    print("-" * 50)
    
    # Initialize detector with custom config
    detector = CellDetector('config.yaml')
    
    # Modify configuration programmatically
    detector.config['model']['confidence_threshold'] = 0.5  # Higher confidence
    detector.config['cell_detection']['min_size'] = 20  # Larger minimum size
    detector.config['visualization']['box_color'] = [255, 0, 0]  # Blue boxes
    
    print("Modified configuration:")
    print(f"  Confidence threshold: {detector.config['model']['confidence_threshold']}")
    print(f"  Minimum cell size: {detector.config['cell_detection']['min_size']} pixels")
    print(f"  Box color: {detector.config['visualization']['box_color']}")
    
    # Process with custom settings
    detector.process_directory()


if __name__ == "__main__":
    # Create input directory if it doesn't exist
    os.makedirs("input_images", exist_ok=True)
    os.makedirs("output_results", exist_ok=True)
    
    print("="*50)
    print("YOLO11 Cell Detector - Usage Examples")
    print("="*50)
    
    # Run examples
    example_single_image()
    example_batch_processing()
    # example_custom_config()  # Uncomment to run
    
    print("\n" + "="*50)
    print("Examples complete!")
    print("="*50)
