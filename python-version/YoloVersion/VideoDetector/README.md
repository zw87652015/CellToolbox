# Real-Time Video Cell Detector with ROI

Real-time cell detection and tracking for video files using YOLO11 with ROI (Region of Interest) support.

## Features

✅ **Real-time video processing** - Process video files frame-by-frame
✅ **ROI selection** - Interactive mouse-based ROI drawing
✅ **Live visualization** - See detections in real-time
✅ **Pause/Resume** - Control playback with spacebar
✅ **Frame skipping** - Speed up processing by skipping frames
✅ **Statistics export** - CSV and JSON output with detection data
✅ **Annotated video** - Save processed video with bounding boxes
✅ **GPU acceleration** - Fast inference with CUDA support

## Quick Start

### 1. Installation

```bash
# Install dependencies (if not already installed)
pip install ultralytics opencv-python pandas pyyaml numpy

# Verify CUDA is available (for GPU acceleration)
python -c "import torch; print(torch.cuda.is_available())"
```

### 2. Basic Usage

```bash
# Process a video file
python video_cell_detector.py path/to/video.mp4

# Specify output directory
python video_cell_detector.py video.mp4 --output results/

# Use custom config
python video_cell_detector.py video.mp4 --config my_config.yaml

# Set ROI from command line (x, y, width, height)
python video_cell_detector.py video.mp4 --roi 100 100 500 500
```

## Interactive Controls

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| **SPACE** | Pause/Resume | Toggle video playback |
| **Q** | Quit | Exit the application |
| **R** | Clear ROI | Remove current ROI selection |
| **S** | Save Frame | Save current annotated frame |
| **H** | Help | Show keyboard controls |
| **+** / **=** | Speed Up | Decrease frame skip (process more frames) |
| **-** | Slow Down | Increase frame skip (skip more frames) |

### Mouse Controls

**ROI Selection:**
1. Click and hold left mouse button
2. Drag to draw rectangle
3. Release to confirm ROI
4. Only cells within ROI will be detected

**Clear ROI:** Press **R** key

## Configuration

Edit `config.yaml` to customize detection parameters:

### Model Settings

```yaml
model:
  size: "n"  # Model size: n, s, m, l, x
  custom_weights: "path/to/best.pt"  # Your trained model
  confidence_threshold: 0.25  # Detection confidence (0-1)
  iou_threshold: 0.45  # NMS IoU threshold
```

### Video Settings

```yaml
video:
  display_width: 1280  # Display window width
  display_height: 720  # Display window height
  save_annotated: true  # Save annotated video
  save_statistics: true  # Save detection CSV/JSON
  show_fps: true  # Show FPS counter
  show_count: true  # Show cell count
```

### Cell Filters

```yaml
filters:
  min_cell_size: 40  # Minimum cell size (pixels)
  max_cell_size: 500  # Maximum cell size (pixels)
  min_aspect_ratio: 0.5  # Minimum width/height ratio
  max_aspect_ratio: 2.0  # Maximum width/height ratio
```

### ROI Visualization

```yaml
visualization:
  roi_color: [255, 0, 0]  # Red rectangle
  roi_thickness: 2  # Line thickness
  roi_dim_factor: 0.4  # Dimming (0.0-1.0, lower = darker outside ROI)
```

**Dimming Effect:**
- `roi_dim_factor: 0.4` - Dims outside ROI to 40% brightness (default)
- `roi_dim_factor: 0.2` - Very dark outside ROI (20% brightness)
- `roi_dim_factor: 0.6` - Lighter dimming (60% brightness)
- `roi_dim_factor: 1.0` - No dimming (full brightness everywhere)

## Output Files

The detector creates an output directory with:

### 1. Annotated Video
```
output_video/annotated_video.mp4
```
- Original video with bounding boxes
- Cell count and FPS overlay
- ROI visualization (if active)

### 2. Detection Data (CSV)
```
output_video/detections.csv
```

Columns:
- `frame` - Frame number
- `detection_id` - Detection ID within frame
- `confidence` - Detection confidence (0-1)
- `bbox_x1, bbox_y1, bbox_x2, bbox_y2` - Bounding box coordinates
- `center_x, center_y` - Cell center position
- `width, height` - Cell dimensions
- `area` - Cell area (pixels²)

### 3. Summary Statistics (JSON)
```
output_video/summary.json
```

Contains:
- Total frames processed
- Total detections
- Average detections per frame
- Average confidence
- Average cell size
- ROI coordinates (if used)
- Processing timestamp

## Workflow Examples

### Example 1: Basic Video Processing

```bash
# 1. Process video with default settings
python video_cell_detector.py experiment_video.mp4

# 2. Watch real-time detection
#    - Green boxes show detected cells
#    - Top-left shows FPS and cell count

# 3. Check output files
#    - output_video/annotated_video.mp4
#    - output_video/detections.csv
#    - output_video/summary.json
```

### Example 2: ROI-Based Detection

```bash
# 1. Run detector
python video_cell_detector.py experiment_video.mp4

# 2. Press SPACE to pause

# 3. Click and drag to draw ROI rectangle

# 4. Press SPACE to resume
#    - Only cells in ROI are detected

# 5. Press R to clear ROI if needed
```

### Example 3: Fast Processing (Skip Frames)

```bash
# 1. Run detector
python video_cell_detector.py long_video.mp4

# 2. Press - key multiple times
#    - Increases frame skip
#    - Processes every Nth frame
#    - Faster processing

# 3. Press + to decrease skip
#    - More frames processed
#    - More accurate tracking
```

### Example 4: Command-Line ROI

```bash
# Process only specific region (x=200, y=150, width=600, height=400)
python video_cell_detector.py video.mp4 --roi 200 150 600 400

# Useful for:
# - Batch processing multiple videos
# - Automated pipelines
# - Consistent ROI across videos
```

## Performance Tips

### GPU Acceleration

**Check GPU availability:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**Enable GPU in config.yaml:**
```yaml
detection:
  device: "cuda"  # Use GPU
  half_precision: true  # FP16 for faster inference
```

**Expected speeds:**
- **CPU**: 2-5 FPS
- **GPU (GTX 1660)**: 30-50 FPS
- **GPU (RTX 3060)**: 60-100 FPS
- **GPU (RTX 4090)**: 150-200 FPS

### Frame Skipping

Process every Nth frame for faster analysis:

```bash
# Press - key during playback to skip frames
# frame_skip = 0: Process all frames (slowest, most accurate)
# frame_skip = 1: Process every 2nd frame (2x faster)
# frame_skip = 4: Process every 5th frame (5x faster)
```

### Model Size

Choose model based on speed/accuracy tradeoff:

```yaml
model:
  size: "n"  # Fastest (100+ FPS on GPU)
  size: "s"  # Fast (60-80 FPS)
  size: "m"  # Balanced (30-50 FPS)
  size: "l"  # Accurate (20-30 FPS)
  size: "x"  # Most accurate (10-20 FPS)
```

## Use Cases

### 1. Cell Migration Analysis
- Track cells moving across field of view
- Use ROI to focus on specific region
- Export CSV for trajectory analysis

### 2. Cell Proliferation
- Count cells over time
- Detect cell division events
- Generate time-series statistics

### 3. Drug Response
- Monitor cell morphology changes
- Track cell count over treatment period
- Compare before/after conditions

### 4. Quality Control
- Verify cell culture density
- Detect contamination
- Monitor cell health

## Troubleshooting

### Issue: Low FPS

**Solutions:**
1. Enable GPU: Set `device: "cuda"` in config
2. Use smaller model: Set `size: "n"` in config
3. Reduce image size: Set `image_size: 320` in config
4. Enable frame skip: Press `-` key during playback

### Issue: Too Many False Positives

**Solutions:**
1. Increase confidence: Set `confidence_threshold: 0.5` in config
2. Adjust size filters: Increase `min_cell_size` in config
3. Use ROI: Select only relevant region
4. Retrain model with better data

### Issue: Missing Cells

**Solutions:**
1. Lower confidence: Set `confidence_threshold: 0.15` in config
2. Adjust size filters: Check `min_cell_size` and `max_cell_size`
3. Use larger model: Set `size: "s"` or `"m"` in config
4. Check ROI: Ensure ROI includes all cells

### Issue: Video Won't Open

**Solutions:**
1. Check video codec: Convert to MP4 with H.264
2. Check file path: Use absolute path
3. Install codecs: `pip install opencv-python-headless`

## Advanced Usage

### Python API

```python
from video_cell_detector import VideoCellDetector

# Create detector
detector = VideoCellDetector("config.yaml")

# Set ROI programmatically
detector.roi = {
    'x': 100,
    'y': 100,
    'width': 500,
    'height': 400
}

# Process video
detector.process_video("input.mp4", "output_dir")

# Access detections
detections = detector.frame_detections
print(f"Total detections: {len(detections)}")
```

### Batch Processing

```python
import glob
from video_cell_detector import VideoCellDetector

detector = VideoCellDetector("config.yaml")

# Process all videos in directory
for video_path in glob.glob("videos/*.mp4"):
    output_dir = f"results/{Path(video_path).stem}"
    detector.process_video(video_path, output_dir)
    detector.frame_detections = []  # Reset for next video
```

## Requirements

- Python 3.8+
- ultralytics (YOLO11)
- opencv-python
- numpy
- pandas
- pyyaml
- torch (with CUDA for GPU support)

## Related Tools

- **StaticImage/cell_detector.py** - Batch image processing
- **DatasetGetter/dataset_creator.py** - Create training datasets
- **StaticImage/train_model.py** - Train custom models

## Support

For issues or questions:
1. Check configuration in `config.yaml`
2. Review console logs for errors
3. Test with smaller video first
4. Verify model weights exist

---

**Happy cell tracking! 🔬🎥**
