# ToupCam Live Detector - Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
cd e:\Documents\Codes\Matlab\CellToolbox\python-version\YoloVersion\ToupcamDetector
pip install -r requirements.txt
```

**For GPU acceleration (recommended):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Step 2: Connect ToupCam (30 seconds)

1. Connect your ToupCam to USB
2. Wait for Windows to recognize the device
3. No driver installation needed (SDK handles it)

## Step 3: Run the Detector (30 seconds)

```bash
python toupcam_live_detector.py
```

That's it! The live stream window should open with real-time cell detection.

## Step 4: Basic Controls (1 minute)

- **SPACE**: Pause/Resume
- **D**: Toggle detection ON/OFF
- **R**: Clear ROI
- **Q**: Quit
- **Mouse drag**: Select ROI

## Step 5: Adjust Settings (1 minute)

Edit `config.yaml` to customize:

```yaml
model:
  confidence_threshold: 0.25  # Lower = more detections
  
filters:
  min_cell_size: 40  # Minimum cell size in pixels
  max_cell_size: 500  # Maximum cell size in pixels
```

## Common First-Time Issues

### "No ToupCam found"
- Check USB connection
- Try a different USB port
- Restart the application

### "CUDA not available" (GPU warning)
- This is OK! The app will use CPU
- For better performance, install CUDA PyTorch (see Step 1)

### Too many/few detections
- Adjust `confidence_threshold` in config.yaml
- Lower value = more detections
- Higher value = fewer, more confident detections

## Next Steps

- Read `README.md` for detailed documentation
- Try selecting ROI for focused detection
- Experiment with different YOLO models (n/s/m/l/x)
- Train a custom model for your specific cells

## Performance Tips

**For maximum FPS:**
1. Use GPU (install CUDA PyTorch)
2. Use nano model: `size: "n"` in config
3. Enable FP16: `half_precision: true`

**For best accuracy:**
1. Use larger model: `size: "m"` or `"l"`
2. Train custom model on your cells
3. Adjust confidence threshold

## Help

Press **'H'** in the application window to see all keyboard controls.

Enjoy real-time cell detection! 🔬
