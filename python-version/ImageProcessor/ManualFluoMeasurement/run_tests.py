#!/usr/bin/env python3
"""
Test Runner for ImageProcessor
Runs unit tests and displays results
"""

import sys
import os
import unittest
from io import StringIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    """Run all unit tests and display results"""
    
    print("ImageProcessor Unit Tests")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    
    # Display results
    output = stream.getvalue()
    print(output)
    
    # Summary
    print("\nTest Summary:")
    print("-" * 30)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Return success status
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return success


def check_test_dependencies():
    """Check if test dependencies are available"""
    
    required_modules = ['numpy', 'cv2', 'skimage', 'PIL', 'yaml']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"Missing test dependencies: {', '.join(missing)}")
        print("Please install requirements: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main entry point"""
    
    if not check_test_dependencies():
        sys.exit(1)
    
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
