# ToupCam Live Stream Cell Detector with YOLO11

High-performance real-time cell detection using ToupCam cameras and YOLO11 deep learning.

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
python toupcam_live_detector.py
```

### With Custom Config

```bash
python toupcam_live_detector.py --config my_config.yaml
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| **SPACE** | Pause/Resume |
| **Q** | Quit |
| **D** | Toggle detection ON/OFF |
| **R** | Clear ROI |
| **H** | Show help |
| **MOUSE** | Click and drag to select ROI |

## Configuration

Edit `config.yaml` to customize:

### Model Settings
- **size**: YOLO11 model size (n/s/m/l/x)
- **custom_weights**: Path to custom trained model
- **confidence_threshold**: Detection confidence (0.0-1.0)
- **iou_threshold**: NMS IoU threshold

### Detection Settings
- **image_size**: Input size for YOLO (640 recommended)
- **device**: 'cuda' for GPU, 'cpu' for CPU
- **half_precision**: Use FP16 for faster GPU inference

### Filters
- **min/max_cell_size**: Size range in pixels
- **min/max_aspect_ratio**: Shape constraints

### Visualization
- **box_color**: Detection box color (BGR)
- **roi_color**: ROI rectangle color (BGR)
- **box_thickness**: Line thickness

## Performance Optimization

### For Maximum FPS:

1. **Use GPU**: Set `device: "cuda"` in config
2. **Enable FP16**: Set `half_precision: true`
3. **Use Nano Model**: Set `size: "n"` for fastest inference
4. **Reduce Image Size**: Lower `image_size` to 320 or 416

### For Best Accuracy:

1. **Use Larger Model**: Set `size: "m"` or `size: "l"`
2. **Increase Image Size**: Set `image_size: 1280`
3. **Use Custom Weights**: Train on your specific cell types
4. **Adjust Thresholds**: Fine-tune confidence and IoU

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
- Check ToupCam is connected
- Verify SDK path is correct
- Try reconnecting camera

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
