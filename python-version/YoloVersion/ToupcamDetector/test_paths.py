"""
Quick test to verify all paths are correctly resolved
"""
import os
import sys

# Get the main python-version directory (go up 2 levels from YoloVersion/ToupcamDetector/)
script_dir = os.path.dirname(os.path.abspath(__file__))
python_version_dir = os.path.dirname(os.path.dirname(script_dir))

print("=" * 60)
print("Path Resolution Test")
print("=" * 60)
print(f"Script directory: {script_dir}")
print(f"Python-version directory: {python_version_dir}")
print()

# Test 1: SingleDroplet directory
single_droplet_dir = os.path.join(python_version_dir, 'SingleDroplet')
print(f"1. SingleDroplet directory: {single_droplet_dir}")
print(f"   Exists: {os.path.exists(single_droplet_dir)}")

exposure_panel = os.path.join(single_droplet_dir, 'exposure_control_panel.py')
print(f"   exposure_control_panel.py: {os.path.exists(exposure_panel)}")
print()

# Test 2: ToupCam SDK
sdk_path = os.path.join(python_version_dir, 'toupcamsdk.20241216', 'python')
print(f"2. ToupCam SDK path: {sdk_path}")
print(f"   Exists: {os.path.exists(sdk_path)}")
print()

# Test 3: ToupCam DLL
dll_path = os.path.join(python_version_dir, 'toupcamsdk.20241216', 'win', 'x64')
toupcam_dll_path = os.path.join(dll_path, 'toupcam.dll')
print(f"3. ToupCam DLL path: {toupcam_dll_path}")
print(f"   Exists: {os.path.exists(toupcam_dll_path)}")
print()

# Test 4: Calibration data
calibration_path = os.path.join(python_version_dir, 'calibration', 'latest_calibration.json')
print(f"4. Calibration data: {calibration_path}")
print(f"   Exists: {os.path.exists(calibration_path)}")
print()

# Test 5: YOLO model
yolo_model_path = os.path.join(
    python_version_dir,
    'YoloVersion', 'StaticImage', 'trained_models', 'cell_detection_v2', 'weights', 'best.pt'
)
print(f"5. YOLO model: {yolo_model_path}")
print(f"   Exists: {os.path.exists(yolo_model_path)}")
print()

# Summary
print("=" * 60)
all_exist = all([
    os.path.exists(single_droplet_dir),
    os.path.exists(exposure_panel),
    os.path.exists(sdk_path),
    os.path.exists(toupcam_dll_path),
    os.path.exists(calibration_path),
    os.path.exists(yolo_model_path)
])

if all_exist:
    print("✅ All paths resolved correctly!")
else:
    print("❌ Some paths are missing. Check the output above.")
print("=" * 60)
