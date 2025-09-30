# ImageProcessor - Bayer RAW Cell Detection

A Python application for processing 16-bit single-channel TIFF images exported from RawDigger RGGB Bayer RAW format to detect and analyze cell fluorescence intensity.

## Features

- **Bayer Pattern Processing**: Splits RGGB Bayer pattern into separate channels (R, G1, G2, B)
- **Dark Field Correction**: Automatic dark field subtraction using provided dark field image or corner regions
- **Advanced Filtering**: Gaussian blur with edge preservation for noise reduction
- **Automatic Thresholding**: Otsu or Triangle algorithms for binary segmentation
- **Cell Detection**: Contour-based cell detection with morphological post-processing
- **Intensity Measurement**: Quantitative fluorescence intensity analysis
- **Interactive GUI**: Step-by-step processing with zoom/pan image viewers
- **Export Results**: CSV data export and quality control overlay images

## Requirements

- Python >= 3.8
- See `requirements.txt` for package dependencies

## Installation

1. Clone or download the project files
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Application (Recommended)

Run the interactive GUI application:
```bash
python gui_app.py
```

**Workflow:**
1. **File Selection**: Select main 16-bit TIFF image, optional dark field image, and output directory
2. **Load Main Image**: Load and view the raw Bayer image
3. **Bayer Split**: Extract R channel from RGGB pattern
4. **Dark Field Subtraction**: Remove background using dark field or corner regions
5. **Gaussian Filter**: Apply noise reduction while preserving edges
6. **Auto Threshold**: Binary segmentation using Otsu or Triangle algorithm
7. **Find Contours**: Detect cell boundaries using OpenCV contours
8. **Measure Intensity**: Calculate area and mean intensity for each cell
9. **Save Results**: Export CSV data and overlay quality control image

### Command Line Interface

For batch processing:
```bash
python image_processor.py <image_path> [dark_field_path] [output_dir]
```

**Example:**
```bash
python image_processor.py sample_image.tif dark_field.tif ./output/
```

## Configuration

Edit `config.yaml` to customize processing parameters:

```yaml
# Gaussian filtering
gaussian:
  sigma: 0.8  # Standard deviation (pixels)

# Thresholding
thresholding:
  algorithm: "otsu"  # Options: "otsu", "triangle"
  min_area: 200     # Minimum cell area (pixels)

# Morphological operations
morphology:
  closing_radius: 3  # Disk radius for closing (pixels)

# Dark field processing
dark_field:
  corner_size: 50   # Corner region size (pixels)

# Output settings
output:
  overlay_colormap: "jet"  # Colormap: "jet", "magma"
  contour_color: [0, 255, 0]  # RGB green contours
```

## Output Files

### CSV Data File
**Format**: `{image_name}-cells.csv`

| Column | Description |
|--------|-------------|
| label | Cell ID number |
| area_pixel | Cell area in pixels |
| mean_intensity | Average fluorescence intensity |
| total_intensity | Total fluorescence intensity |
| contour_csv | Contour coordinates (x1:y1\|x2:y2\|...) |

### Quality Control Image
**Format**: `{image_name}-cells-overlay.tiff`

- 8-bit pseudocolor image with jet/magma colormap
- Green contour overlays showing detected cells
- Metadata in bottom-right corner:
  - Number of cells detected
  - Average intensity
  - Processing parameters

## Image Viewer Controls

Each processing step opens an interactive image viewer with:

- **Zoom Controls**: Zoom In, Zoom Out, Fit to Window, 100%
- **Mouse Navigation**: 
  - Click and drag to pan
  - Mouse wheel to zoom
  - Nearest neighbor interpolation for pixel-perfect clarity
- **Scrollbars**: For navigation of large images

## Troubleshooting

### Common Issues

**"Bayer 尺寸非法" Error**
- **Cause**: Image dimensions are not even numbers
- **Solution**: Ensure image width and height are both even (required for Bayer pattern)

**No Cells Detected (Zero Output)**
- **Cause**: Threshold too high, cells too small, or poor image quality
- **Solutions**:
  - Check image quality and contrast
  - Adjust `min_area` parameter in config.yaml
  - Try different thresholding algorithm (otsu vs triangle)
  - Verify dark field correction is working properly

**Black/Dark Images**
- **Cause**: Incorrect bit depth or exposure settings
- **Solutions**:
  - Ensure image is 16-bit TIFF format
  - Check camera exposure settings
  - Verify RawDigger export settings

**Memory Issues with Large Images**
- **Solutions**:
  - Close unused image viewers
  - Process images in smaller regions
  - Increase system RAM

### File Format Requirements

- **Input**: 16-bit single-channel TIFF
- **Bayer Pattern**: RGGB (Red-Green-Green-Blue)
- **Dimensions**: Must be even numbers (width % 2 == 0, height % 2 == 0)
- **Export Source**: RawDigger or compatible RAW processor

### Performance Tips

- Close image viewers when not needed to save memory
- Use dark field images when possible for better background correction
- Adjust `min_area` parameter to filter out noise artifacts
- For batch processing, use command line interface

## Algorithm Details

### Bayer Pattern Splitting
```python
R:  raw[0::2, 0::2]  # Even rows, even columns
G1: raw[0::2, 1::2]  # Even rows, odd columns  
G2: raw[1::2, 0::2]  # Odd rows, even columns
B:  raw[1::2, 1::2]  # Odd rows, odd columns
```

### Dark Field Correction
- **With dark field image**: Direct subtraction after Bayer split
- **Without dark field**: Median of four 50×50 corner regions
- **Post-processing**: Negative values clipped to zero

### Cell Detection Pipeline
1. **Gaussian Filter**: σ=0.8 pixels, preserves edges
2. **Thresholding**: Otsu or Triangle algorithm
3. **Morphological Closing**: 3-pixel disk radius
4. **Small Object Removal**: < 200 pixels (configurable)
5. **Contour Detection**: OpenCV RETR_EXTERNAL mode

### Intensity Measurement
- **Area**: Sum of pixels within contour mask
- **Total Intensity**: Sum of fluorescence values within mask
- **Mean Intensity**: Total intensity / Area

## License

This project is part of the CellToolbox suite for microscopy image analysis.

## Support

For issues and questions, please check the troubleshooting section above or review the log output in the GUI status panel.
