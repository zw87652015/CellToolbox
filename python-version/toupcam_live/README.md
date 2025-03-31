# ToupCam Live Stream Viewer

This is a Python application that connects to a ToupCam camera and displays its live stream using OpenCV.

## Requirements

- Python 3.6+
- OpenCV (`pip install opencv-python`)
- NumPy (`pip install numpy`)
- ToupCam SDK (included in the parent directory)

## How to Use

1. Connect your ToupCam camera to your computer
2. Run the `toupcam_live_stream.py` script:
   ```
   python toupcam_live_stream.py
   ```
3. The application will:
   - List all available ToupCam cameras
   - Connect to the first camera found
   - Display the live stream in a window

## Controls

- Press `q` to quit the application
- Press `s` to save a snapshot of the current frame

## Troubleshooting

If you encounter the error "no module named toupcam", it means Python cannot find the toupcam module. The script automatically adds the SDK path to the Python path, but if you're still having issues:

1. Make sure the ToupCam SDK is in the correct location: `../toupcamsdk.20241216/python/`
2. Check that `toupcam.py` exists in the SDK's python directory
3. If needed, manually add the SDK path to your PYTHONPATH environment variable

## Integration with CellToolbox

This viewer can be integrated with the CellToolbox Python project by:

1. Importing the `ToupCamLiveStream` class from the module
2. Creating an instance of the class
3. Using the `connect()` and `run()` methods to start the live stream

Example:
```python
from toupcam_live_stream import ToupCamLiveStream

# Create an instance
camera = ToupCamLiveStream()

# Connect to the first available camera
if camera.connect(0):
    # Run the live stream viewer
    camera.run()
```
