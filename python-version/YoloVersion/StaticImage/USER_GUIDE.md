# YOLO11 Cell Detection - User Guide

Complete guide for detecting cells in JPG/PNG images using YOLO11.

---

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test Installation
```bash
python test_installation.py
```
This downloads the YOLO11 model (~6MB) on first run.

### 3. Add Your Images
Place your cell images (JPG/PNG) in the `input_images/` folder.

### 4. Run Detection
```bash
python cell_detector.py
```

### 5. Check Results
Open the `output_results/` folder:
- `detection_results.csv` - Detection data with positions and sizes
- `detection_results.json` - JSON format
- `annotated_*.jpg` - Visualized results with bounding boxes

**Done!** 🎉

---

## 📊 Output Format

### CSV Columns
| Column | Description |
|--------|-------------|
| `image` | Image filename |
| `detection_id` | Detection number |
| `confidence` | Detection confidence (0-1) |
| `center_x` | Cell center X coordinate (pixels) |
| `center_y` | Cell center Y coordinate (pixels) |
| `width` | Cell width (pixels) |
| `height` | Cell height (pixels) |
| `area` | Cell area (pixels²) |
| `bbox_x1`, `bbox_y1`, `bbox_x2`, `bbox_y2` | Bounding box corners |

### Example Output
```csv
image,detection_id,center_x,center_y,width,height,area,confidence
cell_001.jpg,0,245.3,189.7,42.1,38.5,1620.9,0.87
cell_001.jpg,1,512.8,301.2,39.4,41.2,1623.3,0.92
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize detection:

### Adjust Confidence Threshold
```yaml
model:
  confidence_threshold: 0.25  # Lower = more detections, Higher = fewer but more confident
```

**Recommendations:**
- **0.1-0.2**: Get more detections (may include false positives)
- **0.25-0.4**: Balanced (default)
- **0.5-0.8**: High precision (may miss some cells)

### Filter by Cell Size
```yaml
cell_detection:
  min_size: 10      # Minimum cell size (pixels)
  max_size: 500     # Maximum cell size (pixels)
```

### Filter by Shape
```yaml
cell_detection:
  min_aspect_ratio: 0.3   # Minimum width/height ratio
  max_aspect_ratio: 3.0   # Maximum width/height ratio
```

### Change Visualization
```yaml
visualization:
  box_color: [0, 255, 0]    # Green boxes (BGR format)
  box_thickness: 2          # Line thickness
  draw_confidence: true     # Show confidence scores
```

---

## 💻 Python API

### Single Image Detection
```python
from cell_detector import CellDetector

detector = CellDetector('config.yaml')
detections = detector.detect_cells('path/to/image.jpg')

for det in detections:
    print(f"Cell at ({det['center_x']:.1f}, {det['center_y']:.1f})")
    print(f"Size: {det['width']:.1f} x {det['height']:.1f} pixels")
    print(f"Confidence: {det['confidence']:.2f}")
```

### Batch Processing
```python
detector = CellDetector('config.yaml')
detector.process_directory('input_images')

stats = detector.get_statistics()
print(f"Total cells: {stats['total_detections']}")
print(f"Avg per image: {stats['avg_detections_per_image']:.2f}")
```

### Custom Settings
```python
detector = CellDetector('config.yaml')

# Adjust settings
detector.config['model']['confidence_threshold'] = 0.5
detector.config['cell_detection']['min_size'] = 20

# Process with custom settings
detector.process_directory()
```

---

## 🎯 Command Line Options

### Basic Usage
```bash
python cell_detector.py
```

### Custom Directories
```bash
python cell_detector.py --input /path/to/images --output /path/to/results
```

### Custom Config
```bash
python cell_detector.py --config my_config.yaml
```

---

## 🚀 GPU Acceleration (Optional)

For faster processing:

### 1. Install CUDA PyTorch
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. Enable GPU in Config
```yaml
detection:
  device: "cuda"
  half_precision: true  # FP16 for even faster inference
```

**Speed improvement:** 5-10x faster than CPU

---

## 🔧 Using Custom Trained Models

If you trained your own model (see `TRAINING_GUIDE.md`):

### Update Config
```yaml
model:
  custom_weights: "trained_models/cell_detection/weights/best.pt"
```

### Run Detection
```bash
python cell_detector.py
```

That's it! The system will use your custom model instead of the pretrained one.

---

## 🐛 Troubleshooting

### No Detections Found

**Problem:** Model doesn't detect any cells

**Solutions:**
1. Lower confidence threshold:
   ```yaml
   model:
     confidence_threshold: 0.15
   ```
2. Check if images contain visible cells
3. Adjust size filters if cells are very small/large
4. Consider training a custom model on your cell type

### Too Many False Positives

**Problem:** Detecting non-cell objects

**Solutions:**
1. Increase confidence threshold:
   ```yaml
   model:
     confidence_threshold: 0.5
   ```
2. Adjust size filters:
   ```yaml
   cell_detection:
     min_size: 30
     max_size: 300
   ```
3. Adjust aspect ratio filters to exclude elongated objects

### Slow Processing

**Problem:** Detection takes too long

**Solutions:**
1. Use GPU (5-10x faster):
   ```yaml
   detection:
     device: "cuda"
   ```
2. Use smaller model:
   ```yaml
   model:
     size: "n"  # Nano model (fastest)
   ```
3. Reduce image size:
   ```yaml
   detection:
     image_size: 416  # Smaller than default 640
   ```

### Out of Memory

**Problem:** System runs out of RAM/VRAM

**Solutions:**
1. Reduce image size:
   ```yaml
   detection:
     image_size: 416
   ```
2. Use smaller model:
   ```yaml
   model:
     size: "n"
   ```
3. Process fewer images at once

---

## 📁 File Structure

```
StaticImage/
├── cell_detector.py           # Main detection script
├── config.yaml                # Configuration file
├── requirements.txt           # Dependencies
├── test_installation.py       # Installation checker
├── example_usage.py           # Code examples
├── USER_GUIDE.md             # This file
├── TRAINING_GUIDE.md         # Custom training guide
├── input_images/             # Place your images here
│   └── (your cell images)
├── output_results/           # Results saved here
│   ├── detection_results.csv
│   ├── detection_results.json
│   └── annotated_*.jpg
└── trained_models/           # Custom trained models (optional)
    └── cell_detection/
        └── weights/
            └── best.pt
```

---

## 📊 Model Size Comparison

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| yolo11n | 6MB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Quick testing, CPU |
| yolo11s | 22MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Production use |
| yolo11m | 50MB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | High accuracy |
| yolo11l | 100MB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Maximum accuracy |

Change model size in `config.yaml`:
```yaml
model:
  size: "n"  # n, s, m, l, or x
```

---

## 💡 Tips & Best Practices

1. **Start with defaults** - Test with default settings first
2. **Adjust confidence** - Most common tuning parameter
3. **Use GPU** - Much faster if available
4. **Check visualizations** - Review annotated images to verify results
5. **Tune filters** - Adjust size/aspect ratio for your specific cells
6. **Train custom model** - For best results on specific cell types (see `TRAINING_GUIDE.md`)

---

## 📞 Common Workflows

### Workflow 1: Quick Analysis
```bash
# 1. Add images to input_images/
# 2. Run detection
python cell_detector.py
# 3. Check output_results/detection_results.csv
```

### Workflow 2: High Precision
```bash
# 1. Edit config.yaml:
#    confidence_threshold: 0.6
#    min_size: 30
# 2. Run detection
python cell_detector.py
```

### Workflow 3: Maximum Detections
```bash
# 1. Edit config.yaml:
#    confidence_threshold: 0.15
#    min_size: 5
# 2. Run detection
python cell_detector.py
```

### Workflow 4: Custom Model
```bash
# 1. Train model (see TRAINING_GUIDE.md)
# 2. Edit config.yaml:
#    custom_weights: "trained_models/.../best.pt"
# 3. Run detection
python cell_detector.py
```

---

## 🎓 Example Session

```bash
# Install
pip install -r requirements.txt

# Test installation
python test_installation.py

# Add 10 cell images to input_images/

# Run detection
python cell_detector.py

# Output:
# Processing 10 images...
# Detected 127 cells total
# Average: 12.7 cells per image
# Results saved to output_results/
```

---

## ✅ Quick Reference

### Essential Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Test system
python test_installation.py

# Run detection
python cell_detector.py

# Custom directories
python cell_detector.py --input my_images --output my_results
```

### Essential Config Settings
```yaml
# Confidence (most important)
model:
  confidence_threshold: 0.25

# Size filters
cell_detection:
  min_size: 10
  max_size: 500

# GPU acceleration
detection:
  device: "cuda"
```

### Key Output Files
- `output_results/detection_results.csv` - Main results
- `output_results/annotated_*.jpg` - Visual verification

---

**Need to train a custom model?** → See `TRAINING_GUIDE.md`

**Questions?** Check the troubleshooting section above or review `example_usage.py` for code examples.
