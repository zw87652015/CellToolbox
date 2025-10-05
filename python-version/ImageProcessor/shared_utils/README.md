# Shared Utilities Module

This module contains common utilities used across multiple fluorescence measurement projects to avoid code duplication and maintain consistency.

## Modules

### `roi_selector.py`
Interactive ROI (Region of Interest) selection widget with the following features:
- Mouse drag to draw rectangular ROI
- Zoom and pan support
- Coordinate transformation between display and image space
- ROI validation and persistence

**Usage:**
```python
from shared_utils import ROISelector

selector = ROISelector()
roi = selector.select_roi(image, title="Select ROI")
# Returns: (x, y, width, height) or None
```

### `image_utils.py`
Common image processing functions:
- TIFF image loading with memory mapping support
- Bayer pattern splitting (RGGB)
- Dark field correction
- Image normalization
- Overlay image creation
- Image validation

**Usage:**
```python
from shared_utils.image_utils import load_tiff_image, split_bayer_rggb

# Load TIFF image
image = load_tiff_image("image.tif")

# Split Bayer pattern
R, G1, G2, B = split_bayer_rggb(image)
```

## Installation

The shared utilities are automatically available when you install any of the fluorescence measurement tools. No separate installation is required.

## Dependencies

- numpy
- opencv-python
- Pillow
- tifffile
- tkinter (included with Python)

## Integration

To use shared utilities in your project:

```python
import sys
from pathlib import Path

# Add shared_utils to path
shared_utils_path = Path(__file__).parent.parent / 'shared_utils'
sys.path.insert(0, str(shared_utils_path))

# Import utilities
from shared_utils import ROISelector
from shared_utils.image_utils import load_tiff_image
```

## Contributing

When adding new shared utilities:
1. Ensure the functionality is genuinely shared across multiple projects
2. Add comprehensive docstrings
3. Include error handling
4. Update this README
5. Test with all dependent projects

## Projects Using This Module

1. **batch_timeseries**: Time-series fluorescence measurement
2. **single_image_analysis**: Single image fluorescence detection  
3. **manual_bayer_processor**: Interactive Bayer RAW processing
