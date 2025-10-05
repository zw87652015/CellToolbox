# Quick Reference - Fluorescence Measurement Tools

## 📋 Which Tool Should I Use?

| Task | Use This Tool | Command |
|------|---------------|---------|
| **Time-series cell tracking** | `batch_timeseries` | `cd batch_timeseries && python main.py` |
| **Single image analysis** | `single_image_analysis` | `cd single_image_analysis && python main.py` |
| **Interactive Bayer processing** | `manual_bayer_processor` | `cd manual_bayer_processor && python main.py` |

## 🚀 Quick Start

### Batch Time-Series Analysis

**Purpose:** Track fluorescence intensity of a single cell over time

**Input:**
- One brightfield image (16-bit TIFF, Bayer RGGB)
- Multiple fluorescence images (time series)
- Optional: Dark field images

**Output:**
- CSV file with time-series data (timestamp, intensity, area)
- Overlay images showing detected cell
- Processing log

**Typical Workflow:**
```bash
cd batch_timeseries
python main.py
# 1. Select brightfield image
# 2. Select ROI around single cell
# 3. Select fluorescence folder
# 4. Optional: Configure offset optimization
# 5. Click "Start Processing"
```

**CLI Usage:**
```bash
python cli.py \
  -b brightfield.tif \
  -i fluorescence_folder/ \
  -o output_folder/ \
  --offset 0 16 \
  --optimize-offset
```

---

### Single Image Analysis

**Purpose:** Detect and measure ALL fluorescent regions in one image

**Input:**
- Single 16-bit TIFF fluorescence image
- Optional: ROI to limit analysis region

**Output:**
- CSV file with measurements for each detected region
- Overlay image with detection results

**Typical Workflow:**
```bash
cd single_image_analysis
python main.py
# 1. Select input image
# 2. Optional: Select ROI
# 3. Adjust parameters (white top-hat, threshold)
# 4. Preview detection
# 5. Click "Process"
```

**CLI Usage:**
```bash
python cli.py \
  -i input_image.tif \
  -o output_folder/ \
  --roi 100 100 500 500
```

---

### Manual Bayer Processor

**Purpose:** Step-by-step interactive Bayer RAW processing

**Input:**
- 16-bit TIFF Bayer pattern image (RGGB)
- Optional: Dark field image

**Output:**
- R, G1, G2, B channel images
- Processed images at each step
- CSV file with cell measurements
- Quality control overlay images

**Typical Workflow:**
```bash
cd manual_bayer_processor
python main.py
# 1. Load main image
# 2. Step 1: Bayer split
# 3. Step 2: Dark field correction
# 4. Step 3: Gaussian filter
# 5. Step 4: Auto threshold
# 6. Step 5: Find contours
# 7. Step 6: Measure intensity
# 8. Step 7: Save results
```

---

## 🔧 Common Parameters

### Cell Detection Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `gaussian_sigma` | 0.5-5.0 | 1.5 | Blur strength for noise reduction |
| `threshold_method` | otsu/triangle | otsu | Automatic threshold algorithm |
| `min_area` | 50-5000 | 500 | Minimum cell area (pixels) |
| `closing_radius` | 1-10 | 5 | Morphological closing radius |
| `opening_radius` | 1-10 | 2 | Morphological opening radius |

**Edit in:** `cell_detection_params.json` (batch_timeseries)

### Offset Correction (Batch Time-Series)

| Parameter | Description |
|-----------|-------------|
| `offset_x`, `offset_y` | Manual offset in pixels |
| `optimize_offset` | Auto-optimize ±5 pixels per image |

**Use when:** Cell slightly moves between time points

---

## 📁 File Organization

### Recommended Input Structure
```
data/
├── experiment1/
│   ├── brightfield.tif          # One brightfield image
│   ├── dark_field.tif           # Optional dark correction
│   └── fluorescence/            # Time-series folder
│       ├── fluo_001.tif
│       ├── fluo_002.tif
│       └── ...
└── experiment2/
    └── ...
```

### Output Structure
```
output/
├── results.csv                  # Main results
├── processing_log.txt           # Processing details
├── images/                      # Overlay images
│   ├── brightfield_overlay.png
│   └── fluo_001_overlay.png
└── roi_visualizations/          # ROI tracking (if enabled)
    └── ...
```

---

## 🐛 Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'core'`

**Fix:**
```bash
# Make sure you're in the project directory
cd batch_timeseries  # or other project
python main.py       # Not python gui/main_window.py
```

### ROI Selector Issues

**Error:** `ModuleNotFoundError: No module named 'shared_utils'`

**Fix:** This should be automatic. If not, check that `shared_utils/` exists at:
```
ImageProcessor/shared_utils/
```

### Thread Safety Errors

**Error:** `RuntimeError: main thread is not in main loop`

**Status:** ✅ Fixed in latest version! All GUI updates are now thread-safe.

### No Cells Detected

**Possible Causes:**
1. **Parameters too strict** → Decrease `min_area`, adjust `gaussian_sigma`
2. **Wrong threshold method** → Try both 'otsu' and 'triangle'
3. **Poor image quality** → Check brightfield/fluorescence image quality
4. **ROI too small** → Enlarge ROI or remove ROI restriction

**Solution:** Use the dynamic preview feature to adjust parameters in real-time!

---

## 🎯 Best Practices

### 1. Always Use ROI for Single-Cell Tracking
✅ Select tight ROI around target cell
✅ Prevents detection of neighboring cells
✅ Improves tracking accuracy

### 2. Dark Field Correction
✅ Capture dark field images with same exposure
✅ Use multiple dark frames and average them
✅ Significantly improves SNR

### 3. Offset Optimization
✅ Enable for time-series if cell moves slightly
✅ Uses ±5 pixel search to maximize signal
✅ Accounts for stage drift or cell movement

### 4. Parameter Tuning
✅ Use dynamic preview window
✅ Start with default parameters
✅ Adjust one parameter at a time
✅ Save parameters for reproducibility

### 5. Quality Control
✅ Always review overlay images
✅ Check that detected region matches cell
✅ Verify time-series shows expected trends
✅ Log all parameters used

---

## 🔗 Links

- **Migration Guide:** See `MIGRATION_GUIDE.md` for old→new structure changes
- **Detailed Documentation:** Each project has docs in `<project>/docs/`
- **Shared Utilities:** See `shared_utils/README.md`

---

## 💡 Tips & Tricks

### Faster Processing
- Use memory mapping for files >500MB (automatic)
- Process on SSD instead of HDD
- Close other applications during batch processing

### Better Results
- Use 16-bit images (not 8-bit)
- Ensure even image dimensions for Bayer processing
- Calibrate exposure to avoid saturation
- Use consistent lighting conditions

### Reproducibility
- Save configuration files
- Log processing parameters
- Keep original images unchanged
- Document experiment conditions

---

**Last Updated:** 2025-10-05
**Version:** 1.0.0 (Reorganized)
