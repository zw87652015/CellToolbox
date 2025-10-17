# Rigol DG2052 Signal Source Controller

Python UI controller for the Rigol DG2052 signal generator, matching the functionality of the MATLAB version.

## Features

- **Device Connection**: Connect/Disconnect to Rigol DG2052 via USB using VISA protocol
- **Output Control**: Turn Output 1 ON/OFF with button controls
- **Auto Timer**: Automatic output turn-off after specified duration
- **Countdown Display**: Real-time countdown timer showing remaining time
- **Parameter Management**: 
  - Set number of pulses
  - Configure lasting time (duration)
  - Auto-calculate lasting time (pulses + 0.3 seconds)
- **Device Reading**: Read current device settings (waveform, voltage, frequency, pulse width)
- **Logging**: 
  - Real-time log display
  - Save logs to timestamped files
  - Clear log functionality
- **Menu Options**: About and Clear log via menu bar

## Requirements

Install required dependencies:

```bash
pip install pyvisa
```

You'll also need a VISA backend (e.g., NI-VISA or PyVISA-py):

```bash
# Option 1: Install PyVISA-py (pure Python, no external dependencies)
pip install pyvisa-py

# Option 2: Install NI-VISA (more comprehensive, requires installation)
# Download from: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
```

## Usage

Run the controller:

```bash
python SignalCtrl.py
```

### Basic Workflow

1. **Connect**: Click "Connect" button to establish connection with DG2052
   - The application will automatically search for available devices
   - Connection status will be shown in the log

2. **Configure Parameters**:
   - Enter number of **Pulses** (integer value)
   - The **Lasting** time will auto-calculate as: `Pulses + 0.3 seconds`
   - Click **Set** to apply parameters

3. **Turn On Output**:
   - Click **Output 1 on** to activate the signal generator
   - If lasting time > 0, an auto turn-off timer will start
   - Watch the **Timer** field for countdown

4. **Turn Off Output**:
   - Click **Output 1 off** to manually stop output
   - Or wait for auto turn-off when timer expires

5. **Read Settings**:
   - Click **Read** to query current device settings
   - Settings will be displayed in the log area

6. **Save Logs**:
   - Click **Save log** to save current log to timestamped file
   - Files are saved as `log_YYYY-MM-DD_HH-MM-SS.txt`

7. **Disconnect**: Click "Disconnect" when finished
   - Automatically turns off output before disconnecting

## UI Components

### Buttons
- **Connect/Disconnect**: Establish/close connection to device
- **Output 1 on/off**: Control signal generator output
- **Set**: Apply configured parameters
- **Read**: Query current device settings
- **Save log**: Export log to file

### Input Fields
- **Lasting**: Duration in seconds for output to remain on
- **Timer**: Read-only countdown display (updates every 0.1s)
- **Pulses**: Number of pulses (auto-updates Lasting time)

### Menu Bar
- **Log** → **About**: Show application version
- **Log** → **Clear log**: Clear the log display

## Connection Details

The controller attempts to connect using multiple connection strings:
- `USB0::0x1AB1::0x0644::DG2P232400656::0::INSTR`
- `USB0::0x1AB1::0x0644::DG2P232400656::INSTR`
- `USB::0x1AB1::0x0644::DG2P232400656::0::INSTR`
- `USB::0x1AB1::0x0644::DG2P232400656::INSTR`
- Plus any detected USB VISA resources

## SCPI Commands Used

The controller sends standard SCPI commands to the DG2052:
- `*IDN?` - Query device identification
- `:OUTP1 ON/OFF` - Control output state
- `:SOUR1:FUNC?` - Query waveform type
- `:SOUR1:VOLT:HIGH?` - Query high voltage level
- `:SOUR1:VOLT:LOW?` - Query low voltage level
- `:SOUR1:FREQ?` - Query frequency
- `:SOUR1:PULS:WIDT?` - Query pulse width

## Troubleshooting

### Cannot Connect to Device
1. Ensure DG2052 is powered on and connected via USB
2. Check that no other software is using the device
3. Verify VISA backend is properly installed
4. Try different USB ports

### VISA Backend Issues
```bash
# List available VISA resources
python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
```

### Permission Errors (Linux)
Add your user to the `dialout` group:
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

## Version

Current version: **v1.2**

## Comparison with MATLAB Version

This Python implementation provides identical functionality to the MATLAB version:
- ✅ All buttons and controls
- ✅ Auto turn-off timer
- ✅ Countdown display (0.1s updates)
- ✅ Parameter validation
- ✅ Device connection management
- ✅ Log management and export
- ✅ Menu system

## License

Part of the CellToolbox project.
