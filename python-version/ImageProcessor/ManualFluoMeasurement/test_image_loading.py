#!/usr/bin/env python3
"""
Test script to diagnose image loading issues
"""

import os
import sys
import cv2
import numpy as np


def load_image_unicode_safe(image_path: str) -> np.ndarray:
    """Load image with Unicode path support"""
    try:
        # First try standard OpenCV method (works for ASCII paths)
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is not None:
            print("✅ Loaded using standard OpenCV method")
            return image
        
        print("⚠️  Standard OpenCV failed, trying Unicode-safe method...")
        
        # If that fails, try numpy + cv2.imdecode for Unicode paths
        # Read file as binary data
        with open(image_path, 'rb') as f:
            file_bytes = f.read()
        
        # Convert to numpy array
        file_array = np.frombuffer(file_bytes, dtype=np.uint8)
        
        # Decode using OpenCV
        image = cv2.imdecode(file_array, cv2.IMREAD_UNCHANGED)
        
        if image is not None:
            print("✅ Loaded using cv2.imdecode method (Unicode-safe)")
            return image
        
        print("⚠️  OpenCV decode failed, trying PIL fallback...")
        
        # If OpenCV fails, try PIL as fallback for TIFF files
        from PIL import Image as PILImage
        
        pil_image = PILImage.open(image_path)
        
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
        
        print("✅ Loaded using PIL fallback method")
        return image
        
    except Exception as e:
        print(f"❌ All image loading methods failed: {str(e)}")
        return None


def test_image_loading(image_path):
    """Test image loading with detailed diagnostics"""
    
    # Normalize path separators for Windows
    normalized_path = os.path.normpath(image_path)
    
    print(f"Testing image loading for: {normalized_path}")
    print("-" * 50)
    
    # Check if file exists
    if not os.path.exists(normalized_path):
        print(f"❌ ERROR: File does not exist: {normalized_path}")
        return False
    
    print(f"✅ File exists: {normalized_path}")
    
    # Check file size
    file_size = os.path.getsize(normalized_path)
    print(f"📁 File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    # Check file extension
    _, ext = os.path.splitext(normalized_path)
    print(f"📄 File extension: {ext}")
    
    if ext.lower() not in ['.tif', '.tiff']:
        print(f"⚠️  WARNING: File extension '{ext}' is not .tif or .tiff")
    
    # Try to load with OpenCV (Unicode-safe method)
    try:
        print("\n🔄 Loading image with Unicode-safe method...")
        image = load_image_unicode_safe(normalized_path)
        
        if image is None:
            print("❌ ERROR: OpenCV returned None - file may be corrupted or unsupported format")
            return False
        
        print(f"✅ Image loaded successfully")
        print(f"📐 Image shape: {image.shape}")
        print(f"🎨 Image dtype: {image.dtype}")
        print(f"📊 Value range: [{image.min()}, {image.max()}]")
        
        # Check if single channel
        if len(image.shape) == 2:
            print("✅ Single channel (grayscale) image")
        elif len(image.shape) == 3:
            print(f"⚠️  Multi-channel image with {image.shape[2]} channels")
            print("   Note: Bayer processing requires single channel")
        else:
            print(f"❌ ERROR: Unexpected image dimensions: {len(image.shape)}")
            return False
        
        # Check bit depth
        if image.dtype == np.uint16:
            print("✅ 16-bit image (correct for Bayer RAW)")
        elif image.dtype == np.uint8:
            print("⚠️  8-bit image (will be converted to 16-bit)")
        else:
            print(f"⚠️  Unexpected bit depth: {image.dtype}")
        
        # Check dimensions for Bayer pattern
        height, width = image.shape[:2]
        if height % 2 == 0 and width % 2 == 0:
            print(f"✅ Even dimensions ({width}x{height}) - suitable for Bayer pattern")
        else:
            print(f"❌ ERROR: Odd dimensions ({width}x{height}) - not suitable for Bayer pattern")
            print("   Bayer pattern requires even width and height")
            return False
        
        # Show some statistics
        print(f"\n📈 Image statistics:")
        print(f"   Mean: {image.mean():.2f}")
        print(f"   Std:  {image.std():.2f}")
        print(f"   Min:  {image.min()}")
        print(f"   Max:  {image.max()}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR loading image: {str(e)}")
        return False


def main():
    """Main function"""
    
    print("ImageProcessor - Image Loading Test")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage: python test_image_loading.py <image_path>")
        print("\nExample:")
        print("python test_image_loading.py sample_image.tif")
        return
    
    image_path = sys.argv[1]
    
    # Test the image
    success = test_image_loading(image_path)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Image loading test PASSED")
        print("   The image should work with ImageProcessor")
    else:
        print("❌ Image loading test FAILED")
        print("   Please check the error messages above")
        print("\nCommon solutions:")
        print("- Ensure the file is a valid TIFF image")
        print("- Check that the image has even dimensions (width and height)")
        print("- Verify the image is single-channel (grayscale)")
        print("- Try opening the image in another program to verify it's not corrupted")


if __name__ == "__main__":
    main()
