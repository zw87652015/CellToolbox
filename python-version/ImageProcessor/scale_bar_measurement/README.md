# Scale Bar Measurement Tool

A simple tool for measuring scale bars in microscopy images and calculating pixel-to-micron ratios.

## Features

- **Image Loading**: Load grayscale TIFF images (8-bit or 16-bit)
- **Chinese Path Support**: Full support for file paths with Chinese characters (中文路径支持)
- **Image Processing**: Adjustable Gaussian blur (σ = 0-5.0) for noise reduction before measurement
- **Interactive Zoom**: 
  - Mouse wheel zoom with center on cursor
  - Zoom in/out buttons
  - Fit to window
  - Keyboard shortcuts: `+`, `-`, `F`
- **Pan Support**: Right-click and drag to pan the image
- **Line Drawing**: Click and drag to draw a measurement line
- **Adaptive Line Thickness**: Line thickness automatically scales based on image size
- **Automatic Calculation**: Calculates pixels-per-micron ratio based on your measurement
- **Export Results**: Save measurement data to JSON format

## Usage

### 1. Start the Application

```bash
python scale_bar_measurement.py
```

### 2. Load an Image

- Click "Load Image" button
- Select a grayscale TIFF file (8-bit or 16-bit supported)

### 3. Navigate the Image

- **Zoom**: Use mouse wheel or `+`/`-` keys
- **Pan**: Right-click and drag
- **Fit to Window**: Click "Fit (F)" or press `F` key

### 4. Draw Measurement Line

1. Enter the real-world distance in the "Real Distance (μm)" field (default: 100 μm)
2. Click and drag on the image to draw a line along the scale bar
3. The tool automatically calculates the pixel-to-micron ratio

### 5. Review Results

The results panel shows:
- Image filename and dimensions
- Pixel distance of drawn line
- Real world distance
- Pixels per micron ratio
- Microns per pixel (inverse ratio)

### 6. Save Results

- Click "Save Result" to export measurement data to JSON format
- The JSON file contains all measurement parameters and calibration data

## Output Format

The JSON output contains:

```json
{
  "timestamp": "2025-10-11T16:00:00",
  "image_path": "path/to/image.tif",
  "image_size": {"width": 2048, "height": 2048},
  "line_start": {"x": 100, "y": 1900},
  "line_end": {"x": 400, "y": 1900},
  "pixel_distance": 300.0,
  "real_world_distance_um": 100.0,
  "pixels_per_micron": 3.0,
  "microns_per_pixel": 0.3333
}
```

## Keyboard Shortcuts

- `+` or `=`: Zoom in
- `-`: Zoom out
- `F` or `f`: Fit to window

## Mouse Controls

- **Left Click + Drag**: Draw measurement line
- **Right Click + Drag**: Pan image
- **Mouse Wheel**: Zoom in/out (centered on cursor)

## Use Cases

1. **Calibration**: Measure known scale bars to calibrate microscope images
2. **Documentation**: Save calibration data for future reference
3. **Quality Control**: Verify scale bar accuracy across different imaging sessions
4. **Batch Processing**: Use saved calibration data in automated image analysis pipelines

## Technical Details

- Supports 8-bit and 16-bit grayscale TIFF images
- **Chinese path support**: Uses `numpy.fromfile()` + `cv2.imdecode()` for UTF-8 path compatibility
- Automatic normalization for display
- Pixel-perfect zoom using nearest neighbor interpolation
- Thread-safe image processing
- Precise coordinate transformation between display and image space

## Dependencies

- Python 3.x
- OpenCV (cv2)
- NumPy
- PIL/Pillow
- tkinter (usually included with Python)

## Integration

The calibration data can be used in other ImageProcessor tools:

```python
import json

# Load calibration
with open('calibration.json', 'r') as f:
    calib = json.load(f)
    
pixels_per_micron = calib['pixels_per_micron']

# Convert pixel measurements to microns
area_pixels = 1000
area_microns = area_pixels / (pixels_per_micron ** 2)
```
