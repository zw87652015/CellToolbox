# ToupCam Single Droplet Cell Detection with YOLO11

Real-time single droplet cell detection using ToupCam cameras and YOLOv11 deep learning. This version replaces the traditional Kirsch edge detection algorithm with YOLOv11 for improved accuracy and robustness.

## Features

- **Real-time Detection**: Live cell detection with YOLO11
- **High Performance**: Threaded architecture for fluent streaming
  - Separate camera capture thread
  - Dedicated detection thread (non-blocking)
  - High-FPS render thread (~1000 FPS potential)
- **ROI Support**: Interactive region-of-interest selection
- **GPU Acceleration**: CUDA support for fast inference
- **Configurable**: YAML-based configuration system
- **ToupCam Integration**: Direct SDK integration for optimal performance

## Architecture

The application uses a **3-thread architecture** to maintain high FPS:

1. **Camera Thread**: ToupCam callback captures frames at camera speed
2. **Detection Thread**: Processes frames asynchronously with YOLO11
3. **Render Thread**: High-speed display updates independent of detection

This design ensures the live stream remains fluent even during intensive detection processing.

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. GPU Support (Recommended)

For CUDA acceleration:

```bash
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 3. ToupCam SDK

The ToupCam SDK should be located at:
```
../../toupcamsdk.20241216/
```

## Quick Start

### Basic Usage

```bash
python toupcam_single_droplet_yolo.py
```

The application will:
1. Load the trained YOLO model from `../StaticImage/trained_models/cell_detection_v2/weights/best.pt`
2. Connect to the first available ToupCam camera
3. Display live camera feed with interactive ROI selection
4. Project detected cells to the projector screen

## UI Controls

### Buttons
- **Reconnect Camera**: Reconnect to ToupCam (useful if camera disconnected or had errors)
- **Detect Cells**: Toggle cell detection on/off
- **Save Cells**: Save detected cell information
- **Clear Selection**: Clear selected cells
- **Clear ROI**: Remove the region of interest
- **Exposure Control**: Open exposure settings panel
- **Capture Photo**: Save current frame as TIFF
- **Enable Debug Mode**: Toggle debug visualization

### Mouse
- **Click and drag**: Draw ROI rectangle on camera view
- ROI is automatically used for cell detection

### Pattern Parameters
- **Pattern/Cell Size Ratio**: Adjust the size of projected patterns relative to detected cells

## YOLO Model Configuration

The application uses a trained YOLOv11 model for cell detection. The model path is hardcoded in the script:

```python
YOLO_MODEL_PATH = '../StaticImage/trained_models/cell_detection_v2/weights/best.pt'
```

### Detection Parameters (in code)
- **imgsz**: 640 (standard YOLO input size)
- **conf**: 0.25 (confidence threshold)
- **iou**: 0.45 (IoU threshold for NMS)
- **device**: 'cpu' (use CPU for real-time detection)
- **max_det**: 100 (maximum detections per image)

### To Use a Different Model
Edit the `YOLO_MODEL_PATH` variable in `toupcam_single_droplet_yolo.py` to point to your custom trained model.

### To Adjust Detection Parameters
Modify the `model.predict()` parameters in the `detect_cells_in_roi()` function:
- Increase `conf` for fewer false positives
- Decrease `conf` for more detections
- Change `device` to 'cuda' for GPU acceleration (if available)

## Key Differences from Original Version

| Feature | Original (Kirsch) | YOLO Version |
|---------|------------------|--------------|
| Detection Algorithm | Kirsch edge detection + morphology | YOLOv11 + contour refinement (hybrid) |
| Size Measurement | Contour-based (precise) | YOLO bbox + contour refinement (best of both) |
| Accuracy | Good for clear edges | Better for various conditions |
| Speed | Fast (pure OpenCV) | Moderate (depends on hardware) |
| Robustness | Sensitive to lighting | More robust to variations |
| Training | No training needed | Requires trained model |
| Dependencies | scikit-image | ultralytics YOLO |

### Hybrid Detection Approach

The YOLO version uses a **two-stage hybrid approach**:

1. **Stage 1 - YOLO Detection**: Robust cell localization with bounding boxes
2. **Stage 2 - Contour Refinement**: Precise size measurement within each box
   - Finds the most circular contour (circularity > 0.5)
   - Calculates exact radius from contour area
   - Falls back to YOLO approximation if no good contour found

This combines YOLO's robustness with classical computer vision's precision!

## Performance Optimization

### For Maximum FPS:

1. **Use GPU**: Change `device='cpu'` to `device='cuda'` in `detect_cells_in_roi()`
2. **Reduce Image Size**: Lower `imgsz` from 640 to 320 or 416
3. **Increase Confidence**: Higher `conf` threshold = fewer detections = faster
4. **Use Smaller ROI**: Smaller ROI = less pixels to process

### For Best Accuracy:

1. **Use Custom Trained Model**: Train on your specific cell types
2. **Increase Image Size**: Set `imgsz=1280` for better small object detection
3. **Lower Confidence**: Decrease `conf` to 0.1-0.2 for more detections
4. **Adjust IoU**: Fine-tune `iou` threshold for overlapping cells

## Custom Model Training

To use a custom trained YOLO11 model:

1. Train your model (see `../StaticImage/TRAINING_GUIDE.md`)
2. Update `config.yaml`:
   ```yaml
   model:
     custom_weights: "path/to/your/best.pt"
   ```

## ROI (Region of Interest)

### Interactive Selection:
1. Click and drag on the video window
2. ROI is automatically applied to detections
3. Press 'R' to clear ROI

### Benefits:
- Focus on specific area
- Reduce false positives
- Improve performance

## Troubleshooting

### Camera Not Found
- Check ToupCam is connected via USB
- Verify SDK path is correct
- Click **Reconnect Camera** button to retry connection
- Try unplugging and replugging the camera, then click Reconnect

### Low FPS
- Enable GPU acceleration
- Use smaller YOLO model (nano)
- Reduce image_size in config
- Disable detection temporarily (press 'D')

### No Detections
- Lower confidence_threshold
- Check cell size filters
- Verify model is loaded correctly
- Try pretrained model first

### GPU Not Available
- Install CUDA-enabled PyTorch
- Check CUDA installation: `nvidia-smi`
- Verify GPU compatibility

## Performance Metrics

Typical performance on modern hardware:

| Configuration | FPS | Latency |
|--------------|-----|---------|
| GPU + Nano model | 60-120 | <20ms |
| GPU + Small model | 40-80 | <30ms |
| CPU + Nano model | 10-20 | 50-100ms |

*Note: Camera FPS is independent of detection FPS due to threaded architecture*

## Comparison with Video Detector

| Feature | ToupCam Live | Video Detector |
|---------|-------------|----------------|
| Input | Live camera | Video file |
| Latency | Real-time | Post-processing |
| ROI | Interactive | Interactive |
| Threading | 3 threads | Single thread |
| Performance | Optimized for live | Optimized for accuracy |

## Advanced Usage

### Programmatic Control

```python
from toupcam_live_detector import ToupCamLiveDetector

# Create detector
detector = ToupCamLiveDetector("config.yaml")

# Set ROI programmatically
detector.roi = {'x': 100, 'y': 100, 'width': 500, 'height': 500}

# Run
detector.run()
```

## License

Same as parent CellToolbox project.

## Support

For issues and questions, refer to the main CellToolbox documentation.
