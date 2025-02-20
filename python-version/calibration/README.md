# Camera-Projector Calibration Data Guide

## Overview
The calibration system creates a mapping between camera coordinates and projector screen coordinates. This allows you to accurately project content in specific areas captured by the camera.

## Calibration Files
After running calibration, two files are created in the `calibration` directory:
1. `latest_calibration.json` - Always contains the most recent calibration
2. Timestamped files (e.g., `calibration_2025-02-20T15-42-26.json`) - Archive of all calibrations

## Calibration Data Format
The calibration data is stored in JSON format with the following structure:
```json
{
    "scale": 1.234,              // Scale factor between camera and screen coordinates
    "rotation": 0.567,           // Rotation angle in radians
    "offset_x": 100,             // X-axis offset in screen pixels
    "offset_y": 200,             // Y-axis offset in screen pixels
    "camera_resolution": {
        "width": 640,            // Camera capture width
        "height": 480            // Camera capture height
    },
    "projector_resolution": {
        "width": 2560,           // Projector screen width
        "height": 1600           // Projector screen height
    },
    "fov_corners": [             // Camera's field of view corners on screen
        [x1, y1],               // Top-left
        [x2, y2],               // Top-right
        [x3, y3],               // Bottom-right
        [x4, y4]                // Bottom-left
    ],
    "calibration_time": "2025-02-20T15:42:26.789"  // ISO format timestamp
}
```

## Using the Calibration Data

### 1. Loading Calibration Data
```python
import json

def load_calibration_data():
    try:
        with open('calibration/latest_calibration.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: No calibration data found. Please run calibration first.")
        return None
```

### 2. Transforming Camera to Screen Coordinates
```python
import numpy as np

def transform_point(x, y, calibration_data):
    """Transform a point from camera coordinates to screen coordinates"""
    # Get calibration parameters
    scale = calibration_data['scale']
    rotation = calibration_data['rotation']
    offset_x = calibration_data['offset_x']
    offset_y = calibration_data['offset_y']
    
    # Apply rotation
    rx = x * np.cos(rotation) - y * np.sin(rotation)
    ry = x * np.sin(rotation) + y * np.cos(rotation)
    
    # Apply scale and offset
    screen_x = int(rx * scale + offset_x)
    screen_y = int(ry * scale + offset_y)
    
    return screen_x, screen_y
```

### 3. Checking if a Point is Within FOV
```python
from matplotlib.path import Path

def is_point_in_fov(x, y, calibration_data):
    """Check if a screen coordinate point is within the camera's FOV"""
    fov_corners = calibration_data['fov_corners']
    path = Path(fov_corners)
    return path.contains_point((x, y))
```

## Best Practices
1. Always check if calibration data exists before using it
2. Verify that camera resolution matches the calibration data
3. Keep the camera and projector fixed after calibration
4. Recalibrate if the camera or projector position changes
5. Consider saving multiple calibration profiles for different setups

## Troubleshooting
1. If transformed coordinates are incorrect:
   - Verify the camera hasn't moved since calibration
   - Check if the camera resolution matches the calibration
   - Run calibration again if needed

2. If FOV appears incorrect:
   - Ensure the calibration patterns were clearly visible
   - Check for proper lighting conditions
   - Verify the calibration circles were detected correctly

## Example Usage
```python
# Load calibration
calibration_data = load_calibration_data()
if calibration_data is None:
    print("Please run calibration first")
    exit()

# Transform a camera point to screen coordinates
camera_x, camera_y = 320, 240  # Point in camera coordinates
screen_x, screen_y = transform_point(camera_x, camera_y, calibration_data)

# Check if the transformed point is within FOV
if is_point_in_fov(screen_x, screen_y, calibration_data):
    print(f"Point ({screen_x}, {screen_y}) is within camera's FOV")
else:
    print(f"Point ({screen_x}, {screen_y}) is outside camera's FOV")
```
