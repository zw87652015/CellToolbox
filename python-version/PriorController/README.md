# Prior Controller

A user-friendly Python application for controlling Prior Scientific motorized stages and platforms.

## Overview

This application provides a graphical user interface to connect to and control Prior Scientific motorized stages through the Prior Scientific SDK. It allows you to:

- Connect to a Prior controller via COM port
- Move the stage to absolute positions
- Make relative movements with adjustable step sizes
- Set speed and acceleration parameters
- Configure maximum speed settings for precise movement control
- Save and recall positions with custom names
- Stop movement with both smooth and abrupt stopping options
- Monitor the current position in real-time
- View controller information

## Requirements

- Python 3.6 or higher
- tkinter (included with most Python installations)
- Prior Scientific SDK (DLL files included in the x86 and x64 folders)

## Usage

1. Run the application by executing `main.py`:
   ```
   python main.py
   ```

2. Connect to the controller:
   - Enter the COM port number (default is 3)
   - Click "Connect"

3. Control the stage:
   - Use the "Position Control" tab to move to absolute positions or make relative movements
   - Use the arrow buttons for directional control
   - Use "Smooth Stop" for controlled stopping that maintains positional accuracy
   - Use "Abrupt Stop" for emergency stopping (may lose positional accuracy)

4. Adjust speed settings:
   - Use the speed percentage slider for relative speed control
   - Set maximum speed values (in µm/s) for X and Y axes
   - Use preset buttons for common speed settings (Slow, Medium, Fast, Very Fast)

5. Save and recall positions:
   - Enter a name for the current position
   - Click "Save" to store the position
   - Select a saved position from the list
   - Click "Go To" to move to the selected position
   - Click "Delete" to remove a saved position

## File Structure

- `main.py` - Main entry point for the application
- `prior_controller.py` - Python interface to the Prior Scientific SDK (backend)
- `prior_controller_ui.py` - User interface implementation (frontend)
- `x64/` - 64-bit DLL files
- `x86/` - 32-bit DLL files
- `saved_positions.txt` - Stored position data (created automatically)

## New Features

### Position Memory System
- Save current stage positions with custom names
- Recall saved positions by selecting them from a list
- Delete saved positions when no longer needed
- Persistent storage between application sessions

### Maximum Speed Control
- Set specific maximum speed values for X and Y axes (in µm/s)
- Preset buttons for common speed settings:
  - Slow: 1000 µm/s
  - Medium: 5000 µm/s
  - Fast: 10000 µm/s
  - Very Fast: 50000 µm/s
- Default max speed of 10000 µm/s when connecting

### Improved Stop Functionality
- Smooth Stop: Controlled stopping that follows acceleration and jerk settings
- Abrupt Stop: Immediate stopping for emergency situations

## Troubleshooting

If you encounter issues connecting to the controller:

1. Verify the COM port number is correct
2. Ensure the controller is powered on and properly connected
3. Check that the appropriate DLL files are available (x86 or x64 depending on your system)
4. Make sure no other application is using the COM port

## Notes

- Position accuracy may be lost when using the "Abrupt Stop" function
- For best results, use "Smooth Stop" during normal operation
- Maximum speed settings significantly affect actual movement speed even at 100% speed percentage
