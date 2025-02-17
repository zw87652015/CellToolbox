# CellToolbox - Python Version

A powerful tool for real-time cell detection and tracking using computer vision techniques. This toolbox provides both USB camera-based live tracking and static photo analysis capabilities.

## Features

- Real-time cell detection and tracking from USB camera feed
- Static photo analysis
- Interactive parameter adjustment
- Snapshot analysis for parameter optimization
- Multiple visualization windows:
  - Main detection view (with green bounding boxes)
  - Segmentation view (with white rectangles)
  - Analysis window for parameter calculation

## Installation

1. Clone the repository
2. Install the required dependencies:
```bash
pip install numpy opencv-python opencv-contrib-python scikit-image
```

## Usage

### Live Cell Tracking (`cell_tracking_for_usbcam.py`)

1. Run the program:
```bash
python cell_tracking_for_usbcam.py
```

2. The program will open three windows:
   - **Cell Detection Control Panel**: For parameter adjustment
   - **Cell Detection View**: Shows detected cells with green bounding boxes
   - **White Rectangles View**: Shows detected cells with white filled rectangles

3. Adjustable Parameters:
   - **Area**: Min and max area of cells (in pixels)
   - **Perimeter**: Min and max perimeter of cells (in pixels)
   - **Circularity**: Min and max circularity (0-1, where 1 is perfectly circular)
   - **Memory Frames**: Number of frames to keep tracking a cell after detection
   - **Max Movement**: Maximum allowed movement between frames (in pixels)
   - **Distance Threshold**: Maximum distance for cell tracking

4. Controls:
   - **Take Snapshot for Analysis**: Captures current frame for parameter optimization
   - **Update Parameters**: Applies the current parameter values
   - **Quit**: Closes the program

### Static Photo Analysis (`cell_tracking_for_staticPhoto.py`)

1. Run the program:
```bash
python cell_tracking_for_staticPhoto.py
```

2. Use the file dialog to select an image for analysis

3. The program will display:
   - Original image with detected cells
   - Segmentation mask
   - Analysis results

## Parameter Optimization

1. Click "Take Snapshot for Analysis" in the live view
2. Label regions as cells or non-cells in the analysis window
3. Click "Calculate Optimal Thresholds" to compute optimal parameters
4. The program will suggest parameters based on the labeled data

## Tips for Best Results

1. **Lighting**: Ensure consistent, well-lit conditions
2. **Camera Focus**: Adjust camera focus for sharp cell boundaries
3. **Parameter Tuning**:
   - Start with area constraints
   - Fine-tune circularity for cell shape
   - Adjust tracking parameters based on cell movement speed

## Troubleshooting

1. **No Cells Detected**:
   - Check if area range is appropriate for your cells
   - Ensure proper lighting and focus
   - Verify circularity constraints aren't too strict

2. **False Positives**:
   - Increase minimum area
   - Tighten circularity range
   - Use snapshot analysis to optimize parameters

3. **Tracking Issues**:
   - Increase max movement if cells move quickly
   - Adjust memory frames based on frame rate
   - Tune distance threshold for your application

## Dependencies

- numpy
- opencv-python
- opencv-contrib-python
- scikit-image

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
