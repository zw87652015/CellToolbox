# Cell Tracking Python Implementation

This is a Python implementation of the cell tracking algorithm, converted from MATLAB code. The implementation uses OpenCV, NumPy, and scikit-image for efficient image processing operations.

## Requirements

- Python 3.7+
- NumPy
- OpenCV (cv2)
- scikit-image
- matplotlib

Install the required packages using:
```bash
pip install -r requirements.txt
```

## Usage

### Static Image Processing
1. Place your input image (named 'test3.jpg') in the same directory as the script
2. Run the script:
```bash
python cell_tracking.py
```

The script will:
1. Create a 'processing' directory if it doesn't exist
2. Process the image through various stages of the cell tracking pipeline
3. Save intermediate results in the 'processing' directory
4. Generate a final visualization with detected cells marked with rectangles

### Real-time USB Camera Cell Tracking
For real-time cell tracking using a USB camera or microscope, use `cell_tracking_for_usbcam.py`:

```bash
python cell_tracking_for_usbcam.py
```

Features:
- Real-time cell detection and tracking
- Temporal smoothing to maintain cell identity across frames
- Non-Maximum Suppression (NMS) to remove overlapping detections
- Dual display:
  - Original view with green rectangle outlines
  - Fixed 1024x768 black window with white filled rectangles

Parameters (adjustable in the code):
- `CELL_MEMORY_FRAMES`: How long to maintain a cell after it disappears (default: 4 frames)
- `MAX_MOVEMENT`: Maximum allowed cell movement between frames (default: 80 pixels)
- `DISTANCE_THRESHOLD`: Maximum distance for cell matching (default: 50 pixels)
- `NMS_THRESHOLD`: IOU threshold for Non-Maximum Suppression (default: 0.2)

Detection Criteria:
- Area: 50-4000 pixels
- Perimeter: 50-300 pixels
- Circularity: 0.8-1.8
- Aspect ratio: Maximum 1:1.5

To exit the program:
- Press 'q' key
- Click the close button (X) on either window
- Both windows will close automatically if one is closed

## Performance Notes

This Python implementation should perform similarly or better than the MATLAB version because:
1. OpenCV is highly optimized for image processing operations
2. NumPy provides efficient array operations
3. scikit-image implements many image processing algorithms with C-level performance
4. The implementation uses vectorized operations where possible to minimize loops
