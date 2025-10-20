"""
Test script to verify YOLO11 installation and basic functionality
"""

import sys
import os

def test_imports():
    """Test if all required packages are installed"""
    print("Testing package imports...")
    print("-" * 50)
    
    packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'yaml': 'pyyaml',
        'ultralytics': 'ultralytics'
    }
    
    failed = []
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            failed.append(package)
    
    if failed:
        print("\nMissing packages. Install with:")
        print(f"pip install {' '.join(failed)}")
        return False
    
    print("\n✓ All packages installed successfully!")
    return True


def test_yolo_model():
    """Test YOLO11 model loading"""
    print("\n\nTesting YOLO11 model...")
    print("-" * 50)
    
    try:
        from ultralytics import YOLO
        
        print("Loading YOLO11n model (this may download ~6MB on first run)...")
        model = YOLO('yolo11n.pt')
        
        print("✓ YOLO11 model loaded successfully!")
        print(f"  Model type: {type(model)}")
        
        # Test inference on a dummy image
        import numpy as np
        dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
        
        print("\nTesting inference on dummy image...")
        results = model.predict(dummy_image, verbose=False)
        print("✓ Inference test successful!")
        
        return True
        
    except Exception as e:
        print(f"✗ YOLO11 test failed: {e}")
        return False


def test_config():
    """Test configuration file"""
    print("\n\nTesting configuration...")
    print("-" * 50)
    
    try:
        import yaml
        
        if not os.path.exists('config.yaml'):
            print("✗ config.yaml not found")
            return False
        
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("✓ Configuration file loaded successfully!")
        print(f"  Model size: {config['model']['size']}")
        print(f"  Confidence threshold: {config['model']['confidence_threshold']}")
        print(f"  Device: {config['detection']['device']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_directories():
    """Test directory structure"""
    print("\n\nTesting directories...")
    print("-" * 50)
    
    dirs = ['input_images', 'output_results']
    
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✓ Created {dir_name}/")
        else:
            print(f"✓ {dir_name}/ exists")
    
    return True


def test_detector():
    """Test CellDetector class"""
    print("\n\nTesting CellDetector class...")
    print("-" * 50)
    
    try:
        from cell_detector import CellDetector
        
        print("Initializing detector...")
        detector = CellDetector('config.yaml')
        
        print("✓ CellDetector initialized successfully!")
        print(f"  Model: {type(detector.model)}")
        print(f"  Config loaded: {bool(detector.config)}")
        
        return True
        
    except Exception as e:
        print(f"✗ CellDetector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*50)
    print("YOLO11 Cell Detector - Installation Test")
    print("="*50)
    
    tests = [
        ("Package Imports", test_imports),
        ("YOLO11 Model", test_yolo_model),
        ("Configuration", test_config),
        ("Directories", test_directories),
        ("CellDetector Class", test_detector)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Place your cell images in 'input_images/' folder")
        print("2. Run: python cell_detector.py")
        print("3. Check results in 'output_results/' folder")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1
    
    print("="*50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
