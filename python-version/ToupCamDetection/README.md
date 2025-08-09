# ToupCam Live Stream with Cell Detection

This application provides real-time live streaming from ToupCam cameras with integrated cell detection capabilities. It's designed to use ToupCam SDK for professional camera control while maintaining all the original functionality.

## Features

- **Live ToupCam Streaming**: Real-time video capture from ToupCam cameras
- **Multi-Camera Support**: Easy switching between different ToupCam devices
- **Cell Detection**: Advanced cell detection algorithms with real-time parameter adjustment
- **Area of Interest (AOI)**: Draw and manage regions of interest for focused analysis
- **Fullscreen Mode**: Optimized for full-screen viewing with ESC key toggle
- **Multi-Monitor Support**: Automatic positioning on secondary monitors when available
- **Real-time Parameter Control**: Live adjustment of detection parameters via UI

## File Structure

```
ToupCamDetection/
├── main.py                 # Main entry point
├── toupcam_live.py         # Main application class
├── toupcam_camera_manager.py # ToupCam handling and management
├── camera_manager.py       # Legacy USB camera handling (deprecated)
├── cell_detector.py        # Cell detection algorithms
├── aoi_manager.py          # Area of Interest functionality
├── monitor_utils.py        # Multi-monitor support utilities
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have a ToupCam camera connected to your system.
3. The ToupCam SDK is located in the toupcamsdk.20241216 directory.

## Usage

Run the application:
```bash
python main.py
```

### Controls

- **ESC**: Toggle fullscreen mode
- **Camera Selection**: Select different ToupCam devices from available cameras
- **Reconnect**: Switch to the selected camera without restarting
- **Draw AOI**: Enable area of interest drawing mode
- **Cell Detection**: Start/stop real-time cell detection
- **Parameter Tabs**: Adjust CLAHE and area filtering parameters in real-time

### Camera Settings

- **Camera Index Selection**: Choose from cameras 0-10 using the spinbox control
- **Reconnect Functionality**: Switch cameras without application restart
- **Automatic Resolution Detection**: Displays current camera resolution and FPS
- **Buffer Optimization**: Reduced buffer size for minimal latency

### Cell Detection Parameters

#### CLAHE Tab
- **Clip Limit**: Controls contrast enhancement (1.0-5.0)
- **Tile Size**: Grid size for adaptive histogram equalization (2-20)

#### Area Tab
- **Min Area**: Minimum cell area for detection (10-200 pixels)
- **Max Area**: Maximum cell area for detection (100-1000 pixels)

### Area of Interest (AOI)

1. Check "Draw AOI" to enable drawing mode
2. Click and drag on the video to define the region of interest
3. Adjust opacity slider to control overlay visibility
4. Use "Clear AOI" to remove the current region
5. Cell detection will focus only on the AOI region when active

## Technical Details

### Architecture

The application is built with a modular architecture:

- **CameraManager**: Handles all USB camera operations including initialization, frame capture, and reconnection
- **CellDetector**: Implements advanced cell detection algorithms using OpenCV and scikit-image
- **AOIManager**: Manages area of interest drawing, coordinate transformation, and overlay rendering
- **USBCameraLive**: Main orchestrator class that coordinates all components

### Threading

- **Camera Capture Thread**: Continuous frame capture from USB camera
- **Render Thread**: 60 FPS UI updates and frame display
- **Cell Detection Thread**: 20 FPS cell detection processing (configurable)

### Cell Detection Algorithm

The cell detection pipeline includes:

1. **Preprocessing**: CLAHE enhancement and Gaussian denoising
2. **Segmentation**: Adaptive thresholding and edge detection
3. **Morphological Operations**: Opening, closing, and hole filling
4. **Feature Extraction**: Area, perimeter, eccentricity, circularity analysis
5. **Filtering**: Multi-criteria filtering based on shape and size parameters

### Coordinate System

- **Original Image Space**: Raw camera frame coordinates
- **Display Space**: Scaled coordinates for UI display
- **AOI Transformation**: Automatic coordinate conversion between spaces

## Compatibility

- **Operating System**: Windows (with win32api for multi-monitor support)
- **Python**: 3.7+
- **Cameras**: Any USB camera compatible with OpenCV VideoCapture
- **Dependencies**: OpenCV, NumPy, scikit-image, Pillow, scipy, tkinter

## Troubleshooting

### Camera Issues
- Ensure camera is properly connected and not in use by other applications
- Try different camera indices (0, 1, 2, etc.) if the default doesn't work
- Check camera permissions in Windows settings

### Performance Issues
- Reduce target FPS if experiencing lag
- Lower camera resolution if available
- Close other applications using the camera

### Detection Issues
- Adjust CLAHE parameters for better contrast
- Modify area thresholds based on your cell sizes
- Use AOI to focus detection on specific regions

## Development

To extend or modify the application:

1. **Adding New Detection Parameters**: Modify `cell_detector.py` and add UI controls in `usb_camera_live.py`
2. **Camera Features**: Extend `camera_manager.py` for additional camera controls
3. **UI Enhancements**: Modify the UI creation methods in `usb_camera_live.py`
4. **New Analysis Tools**: Add modules following the existing pattern

## License

This project is part of the CellToolbox suite and follows the same licensing terms.
