# GPU-Accelerated Cell Detection Setup Guide

## Overview
This GPU-accelerated version leverages CUDA and CuPy to significantly improve cell detection performance by offloading computationally intensive operations to the GPU.

## Performance Improvements
- **Gaussian Blur**: GPU-accelerated using CUDA
- **Canny Edge Detection**: GPU-accelerated using OpenCV CUDA
- **Thresholding**: GPU-accelerated using OpenCV CUDA  
- **Morphological Operations**: GPU-accelerated using OpenCV CUDA
- **Array Operations**: GPU-accelerated using CuPy

## Quick Setup (Automatic)

### Option 1: Run the setup script
```bash
setup_gpu_env.bat
```

### Option 2: Manual setup
```bash
# Create new Anaconda environment
conda create -n celldetection_gpu python=3.9 -y
conda activate celldetection_gpu

# Install core packages
conda install -c conda-forge opencv numpy scikit-image pillow scipy -y

# Install GPU acceleration (choose based on your CUDA version)
pip install cupy-cuda11x  # For CUDA 11.x
# OR
pip install cupy-cuda12x  # For CUDA 12.x

# Install additional packages
pip install pywin32
```

## Usage

### Start GPU-accelerated application:
```bash
conda activate celldetection_gpu
python main_gpu.py
```

### Check GPU status:
```bash
python -c "import cupy; print('GPU available')"
```

## GPU Requirements
- **NVIDIA GPU** with CUDA support
- **CUDA Toolkit** 11.x or 12.x installed
- **Sufficient GPU memory** (2GB+ recommended)

## Fallback Behavior
- If GPU is not available, the application automatically falls back to CPU processing
- GPU status is displayed in the control panel
- No functionality is lost in CPU fallback mode

## Performance Monitoring
- Real-time FPS display shows rendering performance
- Detection timing is logged to console
- GPU vs CPU status clearly indicated in UI

## Key Features
- **Automatic GPU Detection**: Seamlessly switches between GPU and CPU
- **Memory Management**: Efficient GPU memory usage with automatic cleanup
- **Error Handling**: Robust fallback to CPU if GPU operations fail
- **Real-time Parameters**: All detection parameters adjustable in real-time
- **Debug Visualization**: GPU-accelerated debug window for segmentation analysis

## Troubleshooting

### GPU not detected:
1. Check NVIDIA GPU is installed: `nvidia-smi`
2. Verify CUDA installation: `nvcc --version`
3. Check CuPy installation: `python -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"`

### Performance issues:
1. Monitor GPU memory usage: `nvidia-smi`
2. Reduce image resolution if GPU memory is limited
3. Adjust detection frequency (currently 10 FPS for optimal GPU utilization)

### Installation issues:
1. Ensure correct CUDA version for your GPU
2. Use conda-forge channel for OpenCV with CUDA support
3. Install CuPy version matching your CUDA installation

## Expected Performance Gains
- **2-5x faster** cell detection on modern GPUs
- **Reduced CPU usage** allowing for higher frame rates
- **Smoother real-time operation** with complex detection algorithms
- **Better responsiveness** during parameter adjustments
