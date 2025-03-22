# Prior Controller

A user-friendly Python application for controlling Prior Scientific motorized stages and platforms.

## Overview

This application provides a graphical user interface to connect to and control Prior Scientific motorized stages through the Prior Scientific SDK. It allows you to:

- Connect to a Prior controller via COM port
- Move the stage to absolute positions
- Make relative movements with adjustable step sizes
- Set speed and acceleration parameters
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
   - Use the "Settings" tab to adjust speed and acceleration parameters

## File Structure

- `main.py` - Main entry point for the application
- `prior_controller.py` - Python interface to the Prior Scientific SDK
- `prior_controller_ui.py` - User interface implementation
- `x64/` - 64-bit DLL files
- `x86/` - 32-bit DLL files

## Troubleshooting

If you encounter issues connecting to the controller:

1. Verify the COM port number is correct
2. Ensure the controller is powered on and properly connected
3. Check that the appropriate DLL files are available (x86 or x64 depending on your system)
4. Make sure no other application is using the COM port

## Notes

- The application automatically detects the DLL files in the x86 and x64 folders
- Position values are in microns
- Speed and acceleration are set as percentages of maximum (0-100%)
