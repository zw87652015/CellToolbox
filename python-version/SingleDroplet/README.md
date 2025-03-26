# SingleDroplet Cell Detection

This module provides functionality for detecting and analyzing cells within a user-selected rectangular area using a USB camera.

## Features

- **Rectangle Selection**: Draw a rectangle on the screen to select an area for cell detection
- **Cell Detection**: Automatically detect cells within and crossing the selected rectangle
- **Cell Marking**: Mark the center of detected cells for easy visualization
- **Data Recording**: Save position and size information of detected cells for later use

## Usage

1. Launch the application using the launcher script:
   ```
   python launcher.py
   ```

2. The application will open two windows:
   - A full-screen window for drawing the selection rectangle
   - A control panel with camera view and cell information

3. Draw a rectangle by:
   - Clicking and dragging to move the rectangle
   - Clicking and dragging the bottom-right corner to resize

4. Use the control panel to:
   - Toggle cell detection on/off
   - Save selected cells to a JSON file
   - Clear the current selection
   - View detailed information about detected cells

5. Press ESC to exit the application

## Requirements

- Python 3.6 or higher
- OpenCV (cv2)
- NumPy
- pygame
- tkinter
- PIL (Pillow)
- scikit-image

## Implementation Details

The module uses a combination of image processing techniques for cell detection:
- CLAHE contrast enhancement
- Gaussian blur for noise reduction
- Kirsch operators for edge detection
- Morphological operations for cleaning up the binary image
- Contour detection and filtering based on area, perimeter, and circularity

Cell detection parameters can be adjusted to optimize for different cell types and imaging conditions.

## Integration with CellToolbox

This module integrates with the CellToolbox system by:
- Using the same calibration data for coordinate transformations
- Saving cell data in a compatible format
- Maintaining a consistent user interface style
