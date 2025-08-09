@echo off
echo Setting up GPU-accelerated Cell Detection Environment
echo =====================================================

echo.
echo Step 1: Creating Anaconda environment...
conda create -n celldetection_gpu python=3.9 -y

echo.
echo Step 2: Activating environment...
call conda activate celldetection_gpu

echo.
echo Step 3: Installing core packages...
conda install -c conda-forge opencv numpy scikit-image pillow scipy -y

echo.
echo Step 4: Installing GPU acceleration packages...
echo Detecting CUDA version...
nvidia-smi >nul 2>&1
if %errorlevel% == 0 (
    echo NVIDIA GPU detected, installing CuPy...
    pip install cupy-cuda11x
    echo Note: If you have CUDA 12.x, run: pip install cupy-cuda12x
) else (
    echo No NVIDIA GPU detected, GPU acceleration will fall back to CPU
)

echo.
echo Step 5: Installing additional packages...
pip install pywin32

echo.
echo Setup complete!
echo.
echo To use the GPU environment:
echo 1. conda activate celldetection_gpu
echo 2. python main_gpu.py
echo.
echo To check GPU status, run: python -c "import cupy; print('GPU available')"
pause
