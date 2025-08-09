"""
Cell Detection Benchmark - CPU vs GPU Performance Test
This module provides comprehensive benchmarking for CPU and GPU cell detection performance.
"""

import time
import numpy as np
import cv2
import statistics
import sys
import os
from typing import List, Dict, Tuple, Optional

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cell_detector import CellDetector
from cell_detector_gpu import CellDetectorGPU
from toupcam_camera_manager import ToupCamCameraManager

class CellDetectionBenchmark:
    """Benchmark class for comparing CPU and GPU cell detection performance"""
    
    def __init__(self):
        self.cpu_detector = None
        self.gpu_detector = None
        self.camera_manager = None
        self.test_frames = []
        self.results = {
            'cpu': {'times': [], 'cell_counts': [], 'errors': 0},
            'gpu': {'times': [], 'cell_counts': [], 'errors': 0}
        }
        
    def initialize_detectors(self):
        """Initialize CPU and GPU detectors"""
        print("Initializing detectors...")
        
        # Initialize CPU detector
        try:
            self.cpu_detector = CellDetector()
            print("✓ CPU detector initialized")
        except Exception as e:
            print(f"✗ CPU detector initialization failed: {e}")
            return False
        
        # Initialize GPU detector
        try:
            self.gpu_detector = CellDetectorGPU()
            if self.gpu_detector.gpu_available:
                print("✓ GPU detector initialized with GPU acceleration")
            else:
                print("⚠ GPU detector initialized but GPU acceleration not available")
        except Exception as e:
            print(f"✗ GPU detector initialization failed: {e}")
            return False
        
        return True
    
    def initialize_camera(self):
        """Initialize camera for live frame capture"""
        print("Initializing camera...")
        
        try:
            self.camera_manager = ToupCamCameraManager(camera_index=0, target_fps=30)
            success = self.camera_manager.start_camera()
            if success:
                print("✓ Camera initialized successfully")
                # Wait a moment for camera to stabilize
                time.sleep(2)
                return True
            else:
                print("✗ Camera initialization failed")
                return False
        except Exception as e:
            print(f"✗ Camera initialization error: {e}")
            return False
    
    def capture_test_frames(self, num_frames: int = 10) -> bool:
        """Capture test frames from camera"""
        print(f"Capturing {num_frames} test frames...")
        
        if not self.camera_manager or not self.camera_manager.is_running():
            print("✗ Camera not available for frame capture")
            return False
        
        captured_frames = 0
        max_attempts = num_frames * 3  # Allow multiple attempts
        attempts = 0
        
        while captured_frames < num_frames and attempts < max_attempts:
            success, frame = self.camera_manager.get_frame()
            if success and frame is not None:
                # Convert to format suitable for detection
                if len(frame.shape) == 3:
                    frame_copy = frame.copy()
                    self.test_frames.append(frame_copy)
                    captured_frames += 1
                    print(f"  Captured frame {captured_frames}/{num_frames}")
            
            attempts += 1
            time.sleep(0.1)  # Small delay between attempts
        
        if captured_frames == num_frames:
            print(f"✓ Successfully captured {num_frames} test frames")
            return True
        else:
            print(f"✗ Only captured {captured_frames}/{num_frames} frames")
            return captured_frames > 0  # Continue with whatever frames we have
    
    def generate_synthetic_frames(self, num_frames: int = 10, width: int = 1280, height: int = 720):
        """Generate synthetic test frames with simulated cells"""
        print(f"Generating {num_frames} synthetic test frames ({width}x{height})...")
        
        for i in range(num_frames):
            # Create base frame with noise
            frame = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
            
            # Add some cell-like circular objects
            num_cells = np.random.randint(5, 20)
            for _ in range(num_cells):
                center_x = np.random.randint(50, width - 50)
                center_y = np.random.randint(50, height - 50)
                radius = np.random.randint(10, 30)
                intensity = np.random.randint(100, 255)
                
                # Draw filled circle (simulated cell)
                cv2.circle(frame, (center_x, center_y), radius, (intensity, intensity, intensity), -1)
                
                # Add some noise around the cell
                noise_radius = radius + 5
                cv2.circle(frame, (center_x, center_y), noise_radius, 
                          (intensity//3, intensity//3, intensity//3), 2)
            
            self.test_frames.append(frame)
        
        print(f"✓ Generated {num_frames} synthetic test frames")
    
    def run_cpu_benchmark(self, iterations: int = 5) -> Dict:
        """Run CPU detection benchmark"""
        print(f"\n=== CPU Benchmark ({iterations} iterations per frame) ===")
        
        if not self.cpu_detector:
            print("✗ CPU detector not available")
            return {}
        
        cpu_times = []
        cpu_cell_counts = []
        cpu_errors = 0
        
        for frame_idx, frame in enumerate(self.test_frames):
            print(f"Frame {frame_idx + 1}/{len(self.test_frames)}:")
            
            frame_times = []
            frame_cell_counts = []
            
            for iteration in range(iterations):
                try:
                    start_time = time.perf_counter()
                    detected_cells = self.cpu_detector.detect_cells(frame)
                    end_time = time.perf_counter()
                    
                    detection_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    cell_count = len(detected_cells) if detected_cells else 0
                    
                    frame_times.append(detection_time)
                    frame_cell_counts.append(cell_count)
                    
                    print(f"  Iteration {iteration + 1}: {detection_time:.2f}ms, {cell_count} cells")
                    
                except Exception as e:
                    print(f"  ✗ CPU detection error in iteration {iteration + 1}: {e}")
                    cpu_errors += 1
            
            if frame_times:
                avg_time = statistics.mean(frame_times)
                avg_cells = statistics.mean(frame_cell_counts)
                cpu_times.extend(frame_times)
                cpu_cell_counts.extend(frame_cell_counts)
                print(f"  Frame average: {avg_time:.2f}ms, {avg_cells:.1f} cells")
        
        self.results['cpu'] = {
            'times': cpu_times,
            'cell_counts': cpu_cell_counts,
            'errors': cpu_errors
        }
        
        return self.results['cpu']
    
    def run_gpu_benchmark(self, iterations: int = 5) -> Dict:
        """Run GPU detection benchmark"""
        print(f"\n=== GPU Benchmark ({iterations} iterations per frame) ===")
        
        if not self.gpu_detector:
            print("✗ GPU detector not available")
            return {}
        
        gpu_times = []
        gpu_cell_counts = []
        gpu_errors = 0
        
        # Warm up GPU
        if self.test_frames:
            print("Warming up GPU...")
            try:
                for _ in range(3):
                    self.gpu_detector.detect_cells(self.test_frames[0])
                print("✓ GPU warmed up")
            except Exception as e:
                print(f"⚠ GPU warmup warning: {e}")
        
        for frame_idx, frame in enumerate(self.test_frames):
            print(f"Frame {frame_idx + 1}/{len(self.test_frames)}:")
            
            frame_times = []
            frame_cell_counts = []
            
            for iteration in range(iterations):
                try:
                    start_time = time.perf_counter()
                    detected_cells = self.gpu_detector.detect_cells(frame)
                    end_time = time.perf_counter()
                    
                    detection_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    cell_count = len(detected_cells) if detected_cells else 0
                    
                    frame_times.append(detection_time)
                    frame_cell_counts.append(cell_count)
                    
                    print(f"  Iteration {iteration + 1}: {detection_time:.2f}ms, {cell_count} cells")
                    
                except Exception as e:
                    print(f"  ✗ GPU detection error in iteration {iteration + 1}: {e}")
                    gpu_errors += 1
            
            if frame_times:
                avg_time = statistics.mean(frame_times)
                avg_cells = statistics.mean(frame_cell_counts)
                gpu_times.extend(frame_times)
                gpu_cell_counts.extend(frame_cell_counts)
                print(f"  Frame average: {avg_time:.2f}ms, {avg_cells:.1f} cells")
        
        self.results['gpu'] = {
            'times': gpu_times,
            'cell_counts': gpu_cell_counts,
            'errors': gpu_errors
        }
        
        return self.results['gpu']
    
    def analyze_results(self):
        """Analyze and display benchmark results"""
        print("\n" + "="*60)
        print("BENCHMARK RESULTS ANALYSIS")
        print("="*60)
        
        cpu_results = self.results['cpu']
        gpu_results = self.results['gpu']
        
        if not cpu_results['times'] and not gpu_results['times']:
            print("No benchmark data available")
            return
        
        # CPU Statistics
        if cpu_results['times']:
            cpu_mean = statistics.mean(cpu_results['times'])
            cpu_median = statistics.median(cpu_results['times'])
            cpu_min = min(cpu_results['times'])
            cpu_max = max(cpu_results['times'])
            cpu_std = statistics.stdev(cpu_results['times']) if len(cpu_results['times']) > 1 else 0
            cpu_avg_cells = statistics.mean(cpu_results['cell_counts']) if cpu_results['cell_counts'] else 0
            
            print(f"\nCPU Performance:")
            print(f"  Mean time:     {cpu_mean:.2f} ms")
            print(f"  Median time:   {cpu_median:.2f} ms")
            print(f"  Min time:      {cpu_min:.2f} ms")
            print(f"  Max time:      {cpu_max:.2f} ms")
            print(f"  Std deviation: {cpu_std:.2f} ms")
            print(f"  Avg cells:     {cpu_avg_cells:.1f}")
            print(f"  Errors:        {cpu_results['errors']}")
            print(f"  Max FPS:       {1000/cpu_min:.1f} FPS" if cpu_min > 0 else "  Max FPS:       N/A")
            print(f"  Avg FPS:       {1000/cpu_mean:.1f} FPS" if cpu_mean > 0 else "  Avg FPS:       N/A")
        
        # GPU Statistics
        if gpu_results['times']:
            gpu_mean = statistics.mean(gpu_results['times'])
            gpu_median = statistics.median(gpu_results['times'])
            gpu_min = min(gpu_results['times'])
            gpu_max = max(gpu_results['times'])
            gpu_std = statistics.stdev(gpu_results['times']) if len(gpu_results['times']) > 1 else 0
            gpu_avg_cells = statistics.mean(gpu_results['cell_counts']) if gpu_results['cell_counts'] else 0
            
            print(f"\nGPU Performance:")
            print(f"  Mean time:     {gpu_mean:.2f} ms")
            print(f"  Median time:   {gpu_median:.2f} ms")
            print(f"  Min time:      {gpu_min:.2f} ms")
            print(f"  Max time:      {gpu_max:.2f} ms")
            print(f"  Std deviation: {gpu_std:.2f} ms")
            print(f"  Avg cells:     {gpu_avg_cells:.1f}")
            print(f"  Errors:        {gpu_results['errors']}")
            print(f"  Max FPS:       {1000/gpu_min:.1f} FPS" if gpu_min > 0 else "  Max FPS:       N/A")
            print(f"  Avg FPS:       {1000/gpu_mean:.1f} FPS" if gpu_mean > 0 else "  Avg FPS:       N/A")
        
        # Comparison
        if cpu_results['times'] and gpu_results['times']:
            speedup_mean = cpu_mean / gpu_mean if gpu_mean > 0 else 0
            speedup_min = cpu_min / gpu_min if gpu_min > 0 else 0
            
            print(f"\nPerformance Comparison:")
            print(f"  GPU Speedup (mean):    {speedup_mean:.2f}x")
            print(f"  GPU Speedup (best):    {speedup_min:.2f}x")
            print(f"  Time reduction:        {((cpu_mean - gpu_mean) / cpu_mean * 100):.1f}%" if cpu_mean > 0 else "  Time reduction:        N/A")
            
            if speedup_mean > 1:
                print(f"  ✓ GPU is {speedup_mean:.2f}x faster than CPU")
            elif speedup_mean < 1:
                print(f"  ⚠ CPU is {1/speedup_mean:.2f}x faster than GPU")
            else:
                print(f"  = CPU and GPU have similar performance")
    
    def cleanup(self):
        """Clean up resources"""
        if self.camera_manager:
            self.camera_manager.stop_camera()
        print("✓ Resources cleaned up")

def main():
    """Main benchmark function"""
    print("Cell Detection Benchmark - CPU vs GPU")
    print("="*50)
    
    benchmark = CellDetectionBenchmark()
    
    try:
        # Initialize detectors
        if not benchmark.initialize_detectors():
            print("Failed to initialize detectors")
            return
        
        # Try to initialize camera for real frames
        camera_available = benchmark.initialize_camera()
        
        if camera_available:
            # Capture real frames from camera
            if not benchmark.capture_test_frames(num_frames=5):
                print("Failed to capture camera frames, falling back to synthetic frames")
                benchmark.test_frames = []  # Clear any partial frames
                benchmark.generate_synthetic_frames(num_frames=5)
        else:
            print("Camera not available, using synthetic frames")
            benchmark.generate_synthetic_frames(num_frames=5)
        
        if not benchmark.test_frames:
            print("No test frames available")
            return
        
        print(f"\nRunning benchmark with {len(benchmark.test_frames)} test frames")
        print(f"Frame size: {benchmark.test_frames[0].shape}")
        
        # Run benchmarks
        benchmark.run_cpu_benchmark(iterations=3)
        benchmark.run_gpu_benchmark(iterations=3)
        
        # Analyze results
        benchmark.analyze_results()
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
    except Exception as e:
        print(f"Benchmark error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        benchmark.cleanup()

if __name__ == "__main__":
    main()
