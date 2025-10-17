"""Test CUDA availability"""
import sys

# Test PyTorch CUDA
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"GPU Count: {torch.cuda.device_count()}")
    else:
        print("CUDA not available in PyTorch")
except ImportError:
    print("PyTorch not installed")

print()

# Test OpenCV
try:
    import cv2
    print(f"OpenCV version: {cv2.__version__}")
    cuda_count = cv2.cuda.getCudaEnabledDeviceCount()
    print(f"OpenCV CUDA devices: {cuda_count}")
    if cuda_count > 0:
        print("OpenCV CUDA is enabled")
    else:
        print("OpenCV CUDA is NOT enabled (this is OK - PyTorch will handle GPU)")
except Exception as e:
    print(f"Error checking OpenCV CUDA: {e}")

print()

# Test NVIDIA Management Library
try:
    import pynvml
    pynvml.nvmlInit()
    driver_version = pynvml.nvmlSystemGetDriverVersion()
    device_count = pynvml.nvmlDeviceGetCount()
    print(f"NVIDIA Driver version: {driver_version}")
    print(f"NVIDIA GPU count: {device_count}")
    
    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle)
        memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
        print(f"GPU {i}: {name}")
        print(f"  Total memory: {memory.total / 1024**3:.2f} GB")
        print(f"  Free memory: {memory.free / 1024**3:.2f} GB")
    
    pynvml.nvmlShutdown()
except Exception as e:
    print(f"Error checking NVIDIA devices: {e}")
