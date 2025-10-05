# Fluorescence Measurement Tools

A collection of specialized tools for fluorescence microscopy image analysis.

## Projects

### 1. Batch Time-Series Analysis (`batch_timeseries/`)
Time-series fluorescence intensity measurement for single-cell tracking over time.

**Features:**
- Automated batch processing of time-series images
- EXIF timestamp-driven time axis
- ROI selection for single-cell analysis
- Offset optimization for cell movement
- 16-bit TIFF support with Bayer pattern processing

**Usage:**
```bash
cd batch_timeseries
python main.py
```

### 2. Single Image Analysis (`single_image_analysis/`)
Fluorescence detection and measurement for single images using white top-hat transform.

**Features:**
- White top-hat transform for background correction
- Adaptive thresholding
- Detects all fluorescent regions
- ROI support
- CSV export of measurements

**Usage:**
```bash
cd single_image_analysis
python main.py
```

### 3. Manual Bayer Processor (`manual_bayer_processor/`)
Interactive step-by-step Bayer RAW image processing tool.

**Features:**
- Manual control over each processing step
- Bayer pattern splitting (RGGB)
- Dark field correction
- Interactive GUI with zoom/pan
- Quality control overlay images

**Usage:**
```bash
cd manual_bayer_processor
python main.py
```

## Shared Utilities

Common functionality is provided by the `shared_utils/` module:
- ROI selection widget
- Image processing utilities
- Configuration management

## Installation

Each project has its own `requirements.txt`. Install dependencies:

```bash
cd <project_directory>
pip install -r requirements.txt
```

## Directory Structure

```
ImageProcessor/
├── shared_utils/           # Common utilities
│   ├── roi_selector.py
│   ├── image_utils.py
│   └── README.md
├── batch_timeseries/       # Time-series analysis
│   ├── core/              # Business logic
│   ├── gui/               # User interface
│   ├── docs/              # Documentation
│   ├── tests/             # Test files
│   └── main.py            # Entry point
├── single_image_analysis/  # Single image tool
│   ├── core/
│   ├── gui/
│   ├── docs/
│   ├── tests/
│   └── main.py
└── manual_bayer_processor/ # Interactive processor
    ├── core/
    ├── gui/
    ├── docs/
    ├── tests/
    └── main.py
```

## Contributing

When adding new features:
1. Follow the established directory structure
2. Use shared utilities when possible
3. Update documentation
4. Add tests for new functionality

## License

[Your License Here]

## Contact

[Your Contact Information]
