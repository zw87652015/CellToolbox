# Video Cell Detection Benchmark Tool

Comprehensive performance testing for video cell detection across different configurations.

## Quick Start

```bash
# Run full benchmark
python benchmark.py your_video.mp4

# Quick benchmark (fewer frames)
python benchmark.py your_video.mp4 --quick

# Custom output directory
python benchmark.py your_video.mp4 --output my_results/
```

---

## Benchmark Design

### **Test 1: ROI Size Impact** 🎯

Tests detection FPS across different ROI coverage areas:

**Coverage Levels:**
- 100% - Full frame (no ROI)
- 75% - Three-quarters coverage
- 50% - Half coverage
- 25% - Quarter coverage
- 10% - Small region
- 5% - Very small region
- 1% - Tiny region

**Plus Practical Sizes:**
- Full HD (1920x1080)
- HD (1280x720)
- VGA (640x480)
- Small (320x240)
- Tiny (160x120)

**Metrics Collected:**
- Average FPS
- Min/Max FPS
- Frame processing time (mean, std, min, max)
- Average detections per frame
- Total detections

---

### **Test 2: Model Size Impact** 🤖

Compares different YOLO11 model sizes:

**Models Tested:**
- yolo11n (nano) - Fastest
- yolo11s (small) - Balanced
- yolo11m (medium) - Accurate

**Fixed Parameters:**
- ROI: 25% coverage (practical size)
- Frames: 50 per model
- Same video, same settings

**Comparison:**
- FPS difference between models
- Accuracy vs speed tradeoff
- Memory usage implications

---

### **Test 3: Image Size Impact** 📐

Tests different YOLO input resolutions:

**Sizes Tested:**
- 320 - Fast, lower accuracy
- 640 - Balanced (default)
- 1280 - Slow, higher accuracy

**Fixed Parameters:**
- ROI: 25% coverage
- Frames: 50 per size
- Same model

**Analysis:**
- Resolution vs FPS tradeoff
- Detection quality impact
- Optimal size for your use case

---

## Output Files

### 1. CSV Results

**roi_benchmark.csv:**
```csv
name,coverage,avg_fps,std_fps,avg_detections,total_detections
Full Frame,1.0,45.2,2.3,28.5,2850
ROI 75%,0.75,58.3,1.8,22.1,2210
ROI 50%,0.50,72.5,1.5,15.3,1530
...
```

**model_benchmark.csv:**
```csv
model_size,avg_fps,avg_detections
n,85.3,18.2
s,52.1,19.5
m,28.7,20.1
```

**image_size_benchmark.csv:**
```csv
image_size,avg_fps,avg_detections
320,120.5,15.3
640,68.2,18.7
1280,22.1,21.2
```

### 2. Visualization Plots

**roi_performance.png:**
- FPS vs ROI Coverage (line plot)
- FPS vs Detection Count (scatter plot)

**model_comparison.png:**
- Bar chart comparing model sizes

**image_size_comparison.png:**
- Bar chart comparing input sizes

### 3. Summary JSON

```json
{
  "video_path": "video.mp4",
  "timestamp": "2025-10-20T23:45:00",
  "roi_benchmark": {
    "best_fps": 120.5,
    "worst_fps": 22.3,
    "full_frame_fps": 45.2
  },
  "model_benchmark": {
    "n": 85.3,
    "s": 52.1,
    "m": 28.7
  },
  "image_size_benchmark": {
    "320": 120.5,
    "640": 68.2,
    "1280": 22.1
  }
}
```

---

## Usage Examples

### Example 1: Basic Benchmark

```bash
python benchmark.py experiment.mp4
```

**Output:**
```
benchmark_results/
├── roi_benchmark.csv
├── model_benchmark.csv
├── image_size_benchmark.csv
├── roi_performance.png
├── model_comparison.png
├── image_size_comparison.png
└── summary.json
```

### Example 2: Quick Test

```bash
# Faster benchmark (30 frames per test)
python benchmark.py video.mp4 --quick
```

### Example 3: Custom Configuration

```bash
# More frames for accuracy
python benchmark.py video.mp4 --frames 200

# Custom output location
python benchmark.py video.mp4 --output results_2025/
```

### Example 4: Python API

```python
from benchmark import DetectionBenchmark

# Create benchmark
benchmark = DetectionBenchmark("config.yaml")

# Run full suite
benchmark.run_full_benchmark(
    video_path="video.mp4",
    output_dir="results/",
    num_frames=100
)

# Or run individual tests
roi_results = benchmark.benchmark_roi_size(...)
model_results = benchmark.benchmark_model_sizes(...)
```

---

## Interpreting Results

### ROI Size Analysis

**Key Findings:**

```
ROI Coverage → FPS Relationship:
100% (full) → 45 FPS   (baseline)
50% (half)  → 72 FPS   (1.6x faster)
25% (quarter)→ 95 FPS  (2.1x faster)
10% (small) → 115 FPS  (2.5x faster)
```

**Recommendation:**
- **For tracking single cell:** Use 10-25% ROI (2-3x speedup)
- **For multiple cells:** Use 50-75% ROI (1.5-2x speedup)
- **For full analysis:** Use 100% (no ROI)

### Model Size Analysis

**Typical Results:**

| Model | FPS | Accuracy | Use Case |
|-------|-----|----------|----------|
| yolo11n | 85 | Good | Real-time, fast processing |
| yolo11s | 52 | Better | Balanced speed/accuracy |
| yolo11m | 29 | Best | Offline, high accuracy |

**Recommendation:**
- **Real-time video:** yolo11n
- **Batch processing:** yolo11s or yolo11m
- **GPU limited:** yolo11n

### Image Size Analysis

**Typical Results:**

| Size | FPS | Detection Quality |
|------|-----|-------------------|
| 320 | 120 | May miss small cells |
| 640 | 68 | Good balance (default) |
| 1280 | 22 | Best for tiny cells |

**Recommendation:**
- **Large cells (>50px):** 320 or 640
- **Small cells (<30px):** 640 or 1280
- **Mixed sizes:** 640 (default)

---

## Performance Optimization Guide

### Based on Benchmark Results

**Scenario 1: Need Real-Time (>60 FPS)**
```yaml
# config.yaml
model:
  size: "n"
detection:
  image_size: 320
  
# Use 25% ROI
# Expected: 100+ FPS
```

**Scenario 2: Balanced Performance**
```yaml
# config.yaml
model:
  size: "n"
detection:
  image_size: 640
  
# Use 50% ROI
# Expected: 60-80 FPS
```

**Scenario 3: Maximum Accuracy**
```yaml
# config.yaml
model:
  size: "s"
detection:
  image_size: 640
  
# Use 100% (no ROI)
# Expected: 40-50 FPS
```

---

## Benchmark Methodology

### Warmup Phase

```python
# 10 warmup frames to:
# - Load model into GPU memory
# - Initialize CUDA kernels
# - Stabilize performance
```

### Measurement Phase

```python
# 100 frames (default) per configuration
# - Measure frame processing time
# - Count detections
# - Calculate statistics
```

### Statistical Analysis

```python
# For each configuration:
avg_fps = 1 / mean(frame_times)
std_fps = std(1 / frame_times)
min_fps = 1 / max(frame_times)
max_fps = 1 / min(frame_times)
```

---

## Hardware Considerations

### GPU Impact

**Expected FPS (yolo11n, 640px, 25% ROI):**

| GPU | FPS |
|-----|-----|
| CPU only | 5-10 |
| GTX 1660 | 60-80 |
| RTX 3060 | 100-120 |
| RTX 4090 | 200-250 |
| A100 | 300-400 |

### Memory Usage

**Typical VRAM usage:**
- yolo11n: 1-2 GB
- yolo11s: 2-3 GB
- yolo11m: 4-6 GB

**ROI impact on memory:** Minimal (mask operation is cheap)

---

## Troubleshooting

### Issue: Low FPS

**Check:**
1. GPU being used? (`device: cuda`)
2. Half precision enabled? (`half_precision: true`)
3. Model size too large? (try yolo11n)
4. Image size too large? (try 320 or 640)

### Issue: Inconsistent Results

**Solutions:**
1. Increase warmup frames: `warmup_frames=20`
2. Increase test frames: `--frames 200`
3. Close other GPU applications
4. Check GPU temperature/throttling

### Issue: Out of Memory

**Solutions:**
1. Use smaller model: yolo11n
2. Reduce image size: 320
3. Enable half precision
4. Reduce batch size (if applicable)

---

## Advanced Usage

### Custom ROI Sizes

```python
from benchmark import DetectionBenchmark

benchmark = DetectionBenchmark()

# Define custom ROI
custom_roi = {
    'name': 'Custom Region',
    'roi': {'x': 500, 'y': 300, 'width': 800, 'height': 600},
    'coverage': 0.3
}

# Benchmark it
result = benchmark.benchmark_roi_size(
    video_path="video.mp4",
    roi_config=custom_roi,
    model=model,
    num_frames=100
)
```

### Batch Benchmarking

```python
import glob

videos = glob.glob("videos/*.mp4")

for video in videos:
    output_dir = f"results/{Path(video).stem}"
    benchmark.run_full_benchmark(video, output_dir, num_frames=50)
```

---

## Expected Results

### Typical Benchmark Output

```
============================================================
STARTING COMPREHENSIVE BENCHMARK
============================================================

Video: experiment.mp4
Resolution: 1920x1080
FPS: 30.00
Total Frames: 5000

Model: yolo11n.pt

============================================================
BENCHMARK 1: ROI Size Impact
============================================================
Benchmarking: Full Frame (100%)
  Avg FPS: 45.2 | Avg Detections: 28.5
Benchmarking: ROI 75%
  Avg FPS: 58.3 | Avg Detections: 22.1
Benchmarking: ROI 50%
  Avg FPS: 72.5 | Avg Detections: 15.3
...

============================================================
BENCHMARK 2: Model Size Impact
============================================================
Testing model size: yolo11n
  Avg FPS: 85.3 | Avg Detections: 18.2
Testing model size: yolo11s
  Avg FPS: 52.1 | Avg Detections: 19.5
...

============================================================
BENCHMARK 3: Image Size Impact
============================================================
Testing image size: 320
  Avg FPS: 120.5 | Avg Detections: 15.3
Testing image size: 640
  Avg FPS: 68.2 | Avg Detections: 18.7
...

============================================================
BENCHMARK COMPLETE
Results saved to: benchmark_results
============================================================
```

---

## Requirements

- Python 3.8+
- ultralytics (YOLO11)
- opencv-python
- numpy
- pandas
- matplotlib
- pyyaml

---

## Tips for Best Results

1. **Close other applications** - Free up GPU memory
2. **Use consistent video** - Same video for all tests
3. **Run multiple times** - Average results for accuracy
4. **Monitor GPU temp** - Ensure no thermal throttling
5. **Use representative video** - Match your actual use case

---

**Happy benchmarking! 🚀📊**
