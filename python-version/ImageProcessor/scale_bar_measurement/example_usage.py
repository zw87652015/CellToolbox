"""
Example usage script for Scale Bar Measurement Tool
Shows how to integrate calibration data in image processing pipelines
"""

import json
import numpy as np


def load_calibration(json_path):
    """Load calibration data from JSON file"""
    with open(json_path, 'r') as f:
        calib = json.load(f)
    return calib


def convert_pixels_to_microns(pixel_value, calibration):
    """Convert pixel measurements to microns"""
    pixels_per_micron = calibration['pixels_per_micron']
    return pixel_value / pixels_per_micron


def convert_area_to_microns_squared(area_pixels, calibration):
    """Convert area from pixels to square microns"""
    pixels_per_micron = calibration['pixels_per_micron']
    return area_pixels / (pixels_per_micron ** 2)


def example_cell_area_analysis():
    """Example: Convert cell area measurements to real-world units"""
    
    # Example calibration data (would be loaded from JSON file)
    calibration = {
        "pixels_per_micron": 3.0,
        "microns_per_pixel": 0.3333
    }
    
    # Example cell detection results (in pixels)
    cell_areas_pixels = [1200, 1450, 980, 1300, 1100]
    
    print("Cell Area Analysis")
    print("=" * 60)
    print(f"Calibration: {calibration['pixels_per_micron']:.4f} pixels/μm")
    print(f"Inverse: {calibration['microns_per_pixel']:.4f} μm/pixel")
    print()
    
    for i, area_px in enumerate(cell_areas_pixels, 1):
        area_um2 = convert_area_to_microns_squared(area_px, calibration)
        diameter_px = 2 * np.sqrt(area_px / np.pi)
        diameter_um = convert_pixels_to_microns(diameter_px, calibration)
        
        print(f"Cell {i}:")
        print(f"  Area: {area_px} px² = {area_um2:.2f} μm²")
        print(f"  Equivalent diameter: {diameter_px:.2f} px = {diameter_um:.2f} μm")
        print()


def example_distance_measurement():
    """Example: Convert distance measurements to real-world units"""
    
    calibration = {
        "pixels_per_micron": 3.0,
        "microns_per_pixel": 0.3333
    }
    
    # Example measurements (in pixels)
    measurements = {
        "Cell diameter": 45,
        "Migration distance": 120,
        "Nucleus diameter": 25,
        "Cell-to-cell distance": 85
    }
    
    print("Distance Measurements")
    print("=" * 60)
    
    for name, distance_px in measurements.items():
        distance_um = convert_pixels_to_microns(distance_px, calibration)
        print(f"{name}: {distance_px} px = {distance_um:.2f} μm")


def example_batch_processing():
    """Example: Batch process multiple measurements with calibration"""
    
    # Simulated calibration file path
    # calibration = load_calibration('calibration.json')
    
    # For demonstration, use mock data
    calibration = {
        "pixels_per_micron": 2.5,
        "microns_per_pixel": 0.4,
        "image_path": "test_image.tif",
        "timestamp": "2025-10-11T16:00:00"
    }
    
    print("Batch Processing Example")
    print("=" * 60)
    print(f"Using calibration from: {calibration['image_path']}")
    print(f"Calibration date: {calibration['timestamp']}")
    print(f"Scale: {calibration['pixels_per_micron']:.4f} px/μm")
    print()
    
    # Simulated batch measurements
    batch_data = [
        {"name": "Frame_001", "area_px": 1150, "perimeter_px": 125},
        {"name": "Frame_002", "area_px": 1320, "perimeter_px": 135},
        {"name": "Frame_003", "area_px": 1080, "perimeter_px": 118},
    ]
    
    results = []
    for data in batch_data:
        result = {
            "frame": data["name"],
            "area_um2": convert_area_to_microns_squared(data["area_px"], calibration),
            "perimeter_um": convert_pixels_to_microns(data["perimeter_px"], calibration),
            "circularity": 4 * np.pi * data["area_px"] / (data["perimeter_px"] ** 2)
        }
        results.append(result)
        
        print(f"{result['frame']}:")
        print(f"  Area: {result['area_um2']:.2f} μm²")
        print(f"  Perimeter: {result['perimeter_um']:.2f} μm")
        print(f"  Circularity: {result['circularity']:.3f}")
        print()
    
    return results


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Scale Bar Calibration - Example Usage")
    print("="*60 + "\n")
    
    example_cell_area_analysis()
    print("\n")
    
    example_distance_measurement()
    print("\n")
    
    example_batch_processing()
    
    print("\n" + "="*60)
    print("To use with actual calibration data:")
    print("  1. Run scale_bar_measurement.py")
    print("  2. Load your image and draw measurement line")
    print("  3. Save calibration to JSON")
    print("  4. Load JSON in your analysis script:")
    print("     calibration = load_calibration('your_calibration.json')")
    print("="*60 + "\n")
