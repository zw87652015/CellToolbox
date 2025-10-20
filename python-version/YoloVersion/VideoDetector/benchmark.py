"""
Video Cell Detection Benchmark Tool
Tests detection FPS across different ROI sizes, model configurations, and settings
"""

import os
import cv2
import numpy as np
import pandas as pd
import json
import yaml
import time
from pathlib import Path
from typing import List, Dict, Tuple
from ultralytics import YOLO
import logging
from datetime import datetime
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DetectionBenchmark:
    """Benchmark tool for video cell detection performance"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize benchmark tool"""
        self.config = self._load_config(config_path)
        self.results = []
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except:
            logger.warning("Config not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'model': {
                'size': 'n',
                'custom_weights': None,
                'confidence_threshold': 0.25,
                'iou_threshold': 0.45
            },
            'detection': {
                'image_size': 640,
                'device': 'cuda',
                'half_precision': True,
                'max_detections': 300
            }
        }
    
    def generate_roi_sizes(self, video_width: int, video_height: int) -> List[Dict]:
        """
        Generate different ROI sizes for testing
        
        Returns list of ROI configs with different coverage percentages
        """
        rois = []
        
        # Full frame (no ROI)
        rois.append({
            'name': 'Full Frame (100%)',
            'roi': None,
            'coverage': 1.0
        })
        
        # Different coverage percentages (centered squares)
        coverage_levels = [0.75, 0.50, 0.25, 0.10, 0.05, 0.01]
        
        for coverage in coverage_levels:
            # Calculate ROI dimensions (centered square)
            roi_area = video_width * video_height * coverage
            roi_size = int(np.sqrt(roi_area))
            
            # Center the ROI
            x = (video_width - roi_size) // 2
            y = (video_height - roi_size) // 2
            
            rois.append({
                'name': f'ROI {int(coverage*100)}%',
                'roi': {
                    'x': max(0, x),
                    'y': max(0, y),
                    'width': min(roi_size, video_width),
                    'height': min(roi_size, video_height)
                },
                'coverage': coverage
            })
        
        return rois
    
    def apply_roi_mask(self, image: np.ndarray, roi: Dict) -> np.ndarray:
        """Apply ROI mask to image"""
        if roi is None:
            return image
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
        mask[y:y+h, x:x+w] = 255
        
        return cv2.bitwise_and(image, image, mask=mask)
    
    def benchmark_roi_size(
        self,
        video_path: str,
        roi_config: Dict,
        model: YOLO,
        num_frames: int = 100,
        warmup_frames: int = 10
    ) -> Dict:
        """
        Benchmark detection performance for a specific ROI size
        
        Args:
            video_path: Path to video file
            roi_config: ROI configuration dict
            model: YOLO model instance
            num_frames: Number of frames to test
            warmup_frames: Number of warmup frames
            
        Returns:
            Benchmark results dict
        """
        logger.info(f"Benchmarking: {roi_config['name']}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return None
        
        roi = roi_config['roi']
        frame_times = []
        detection_counts = []
        
        # Warmup
        for i in range(warmup_frames):
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            
            masked_frame = self.apply_roi_mask(frame, roi)
            _ = model.predict(
                source=masked_frame,
                imgsz=self.config['detection']['image_size'],
                conf=self.config['model']['confidence_threshold'],
                iou=self.config['model']['iou_threshold'],
                device=self.config['detection']['device'],
                half=self.config['detection']['half_precision'],
                verbose=False
            )
        
        # Actual benchmark
        for i in range(num_frames):
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            
            # Apply ROI mask
            masked_frame = self.apply_roi_mask(frame, roi)
            
            # Time the detection
            start_time = time.time()
            results = model.predict(
                source=masked_frame,
                imgsz=self.config['detection']['image_size'],
                conf=self.config['model']['confidence_threshold'],
                iou=self.config['model']['iou_threshold'],
                device=self.config['detection']['device'],
                half=self.config['detection']['half_precision'],
                verbose=False
            )
            end_time = time.time()
            
            frame_time = end_time - start_time
            frame_times.append(frame_time)
            
            # Count detections
            if results[0].boxes is not None:
                detection_counts.append(len(results[0].boxes))
            else:
                detection_counts.append(0)
        
        cap.release()
        
        # Calculate statistics
        frame_times = np.array(frame_times)
        detection_counts = np.array(detection_counts)
        
        results = {
            'name': roi_config['name'],
            'roi': roi,
            'coverage': roi_config['coverage'],
            'num_frames': num_frames,
            'avg_frame_time': float(np.mean(frame_times)),
            'std_frame_time': float(np.std(frame_times)),
            'min_frame_time': float(np.min(frame_times)),
            'max_frame_time': float(np.max(frame_times)),
            'avg_fps': float(1.0 / np.mean(frame_times)),
            'min_fps': float(1.0 / np.max(frame_times)),
            'max_fps': float(1.0 / np.min(frame_times)),
            'avg_detections': float(np.mean(detection_counts)),
            'std_detections': float(np.std(detection_counts)),
            'total_detections': int(np.sum(detection_counts))
        }
        
        logger.info(f"  Avg FPS: {results['avg_fps']:.2f} | "
                   f"Avg Detections: {results['avg_detections']:.1f}")
        
        return results
    
    def benchmark_model_sizes(
        self,
        video_path: str,
        model_sizes: List[str] = ['n', 's', 'm'],
        num_frames: int = 50
    ) -> List[Dict]:
        """
        Benchmark different model sizes
        
        Args:
            video_path: Path to video file
            model_sizes: List of model sizes to test
            num_frames: Number of frames per test
            
        Returns:
            List of benchmark results
        """
        results = []
        
        cap = cv2.VideoCapture(video_path)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Test with 25% ROI (practical size)
        roi_size = int(min(video_width, video_height) * 0.5)
        roi = {
            'x': (video_width - roi_size) // 2,
            'y': (video_height - roi_size) // 2,
            'width': roi_size,
            'height': roi_size
        }
        
        roi_config = {
            'name': 'ROI 25%',
            'roi': roi,
            'coverage': 0.25
        }
        
        for model_size in model_sizes:
            logger.info(f"\nTesting model size: yolo11{model_size}")
            
            # Load model (always use pretrained for comparison)
            model_path = f"yolo11{model_size}.pt"
            logger.info(f"  Loading: {model_path} (pretrained for comparison)")
            model = YOLO(model_path)
            
            # Benchmark
            result = self.benchmark_roi_size(
                video_path, roi_config, model, num_frames, warmup_frames=5
            )
            
            if result:
                result['model_size'] = model_size
                results.append(result)
        
        return results
    
    def benchmark_image_sizes(
        self,
        video_path: str,
        image_sizes: List[int] = [320, 640, 1280],
        num_frames: int = 50
    ) -> List[Dict]:
        """
        Benchmark different YOLO input image sizes
        
        Args:
            video_path: Path to video file
            image_sizes: List of image sizes to test
            num_frames: Number of frames per test
            
        Returns:
            List of benchmark results
        """
        results = []
        
        # Load model
        custom_weights = self.config['model'].get('custom_weights')
        if custom_weights and os.path.exists(custom_weights):
            logger.info(f"Using custom model: {custom_weights}")
            model = YOLO(custom_weights)
        else:
            model_name = f"yolo11{self.config['model']['size']}.pt"
            logger.info(f"Using pretrained model: {model_name}")
            model = YOLO(model_name)
        
        cap = cv2.VideoCapture(video_path)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Test with 25% ROI
        roi_size = int(min(video_width, video_height) * 0.5)
        roi = {
            'x': (video_width - roi_size) // 2,
            'y': (video_height - roi_size) // 2,
            'width': roi_size,
            'height': roi_size
        }
        
        roi_config = {
            'name': 'ROI 25%',
            'roi': roi,
            'coverage': 0.25
        }
        
        for img_size in image_sizes:
            logger.info(f"\nTesting image size: {img_size}")
            
            # Temporarily change config
            original_size = self.config['detection']['image_size']
            self.config['detection']['image_size'] = img_size
            
            # Benchmark
            result = self.benchmark_roi_size(
                video_path, roi_config, model, num_frames, warmup_frames=5
            )
            
            if result:
                result['image_size'] = img_size
                results.append(result)
            
            # Restore config
            self.config['detection']['image_size'] = original_size
        
        return results
    
    def run_full_benchmark(
        self,
        video_path: str,
        output_dir: str = "benchmark_results",
        num_frames: int = 100
    ):
        """
        Run comprehensive benchmark suite
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save results
            num_frames: Number of frames per test
        """
        logger.info("="*60)
        logger.info("STARTING COMPREHENSIVE BENCHMARK")
        logger.info("="*60)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Get video info
        cap = cv2.VideoCapture(video_path)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        logger.info(f"\nVideo: {video_path}")
        logger.info(f"Resolution: {video_width}x{video_height}")
        logger.info(f"FPS: {video_fps:.2f}")
        logger.info(f"Total Frames: {total_frames}")
        
        # Load model
        custom_weights = self.config['model'].get('custom_weights')
        if custom_weights and os.path.exists(custom_weights):
            logger.info(f"\n🎯 Using CUSTOM trained model: {custom_weights}")
            logger.info(f"   (Your trained cell detection model)")
            model = YOLO(custom_weights)
        else:
            model_name = f"yolo11{self.config['model']['size']}.pt"
            logger.info(f"\n⚠️  Using PRETRAINED model: {model_name}")
            logger.info(f"   (Not trained on your cells)")
            model = YOLO(model_name)
        
        # Benchmark 1: Different ROI sizes
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK 1: ROI Size Impact")
        logger.info("="*60)
        
        roi_configs = self.generate_roi_sizes(video_width, video_height)
        roi_results = []
        
        for roi_config in roi_configs:
            result = self.benchmark_roi_size(
                video_path, roi_config, model, num_frames
            )
            if result:
                roi_results.append(result)
        
        # Benchmark 2: Model sizes (only if using pretrained models)
        model_results = []
        if not custom_weights:
            logger.info("\n" + "="*60)
            logger.info("BENCHMARK 2: Model Size Impact")
            logger.info("="*60)
            
            model_results = self.benchmark_model_sizes(
                video_path, ['n', 's', 'm'], num_frames=50
            )
        else:
            logger.info("\n" + "="*60)
            logger.info("BENCHMARK 2: Model Size Impact - SKIPPED")
            logger.info("="*60)
            logger.info("Skipping model size comparison (using custom trained model)")
            logger.info("Your model is based on yolo11n architecture")
        
        # Benchmark 3: Image sizes
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK 3: Image Size Impact")
        logger.info("="*60)
        
        image_results = self.benchmark_image_sizes(
            video_path, [320, 640, 1280], num_frames=50
        )
        
        # Save results
        self._save_results(
            output_dir, video_path,
            roi_results, model_results, image_results
        )
        
        # Generate plots
        self._generate_plots(
            output_dir,
            roi_results, model_results, image_results
        )
        
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK COMPLETE")
        logger.info(f"Results saved to: {output_dir}")
        logger.info("="*60)
    
    def _save_results(
        self,
        output_dir: str,
        video_path: str,
        roi_results: List[Dict],
        model_results: List[Dict],
        image_results: List[Dict]
    ):
        """Save benchmark results to files"""
        
        # Save ROI results
        df_roi = pd.DataFrame(roi_results)
        df_roi.to_csv(os.path.join(output_dir, "roi_benchmark.csv"), index=False)
        
        # Save model results
        if model_results:
            df_model = pd.DataFrame(model_results)
            df_model.to_csv(os.path.join(output_dir, "model_benchmark.csv"), index=False)
        
        # Save image size results
        if image_results:
            df_image = pd.DataFrame(image_results)
            df_image.to_csv(os.path.join(output_dir, "image_size_benchmark.csv"), index=False)
        
        # Save summary
        summary = {
            'video_path': video_path,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'roi_benchmark': {
                'best_fps': max([r['avg_fps'] for r in roi_results]),
                'worst_fps': min([r['avg_fps'] for r in roi_results]),
                'full_frame_fps': next(r['avg_fps'] for r in roi_results if r['coverage'] == 1.0)
            }
        }
        
        if model_results:
            summary['model_benchmark'] = {
                size: next(r['avg_fps'] for r in model_results if r['model_size'] == size)
                for size in set(r['model_size'] for r in model_results)
            }
        
        if image_results:
            summary['image_size_benchmark'] = {
                size: next(r['avg_fps'] for r in image_results if r['image_size'] == size)
                for size in set(r['image_size'] for r in image_results)
            }
        
        with open(os.path.join(output_dir, "summary.json"), 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Results saved to {output_dir}")
    
    def _generate_plots(
        self,
        output_dir: str,
        roi_results: List[Dict],
        model_results: List[Dict],
        image_results: List[Dict]
    ):
        """Generate visualization plots"""
        
        # Plot 1: FPS vs ROI Coverage
        plt.figure(figsize=(12, 6))
        
        # Sort results by coverage for clean line plot
        sorted_results = sorted(roi_results, key=lambda x: x['coverage'], reverse=True)
        coverages = [r['coverage'] * 100 for r in sorted_results]
        fps_values = [r['avg_fps'] for r in sorted_results]
        names = [r['name'] for r in sorted_results]
        
        plt.subplot(1, 2, 1)
        plt.plot(coverages, fps_values, 'bo-', linewidth=2, markersize=8)
        plt.xlabel('ROI Coverage (%)', fontsize=12)
        plt.ylabel('Average FPS', fontsize=12)
        plt.title('Detection FPS vs ROI Size', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.gca().invert_xaxis()  # Invert x-axis so 100% is on left, 0% on right
        
        # Plot 2: FPS vs Detection Count
        plt.subplot(1, 2, 2)
        detections = [r['avg_detections'] for r in sorted_results]
        plt.scatter(detections, fps_values, s=100, c=coverages, cmap='viridis', alpha=0.6)
        plt.colorbar(label='ROI Coverage (%)')
        plt.xlabel('Average Detections per Frame', fontsize=12)
        plt.ylabel('Average FPS', fontsize=12)
        plt.title('FPS vs Detection Load', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "roi_performance.png"), dpi=300)
        plt.close()
        
        # Plot 3: Model size comparison
        if model_results:
            plt.figure(figsize=(10, 6))
            model_sizes = [r['model_size'] for r in model_results]
            model_fps = [r['avg_fps'] for r in model_results]
            
            plt.bar(model_sizes, model_fps, color=['green', 'blue', 'orange'])
            plt.xlabel('Model Size', fontsize=12)
            plt.ylabel('Average FPS', fontsize=12)
            plt.title('FPS by Model Size (yolo11n/s/m)', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='y')
            
            for i, (size, fps) in enumerate(zip(model_sizes, model_fps)):
                plt.text(i, fps + 1, f'{fps:.1f}', ha='center', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "model_comparison.png"), dpi=300)
            plt.close()
        
        # Plot 4: Image size comparison
        if image_results:
            plt.figure(figsize=(10, 6))
            img_sizes = [r['image_size'] for r in image_results]
            img_fps = [r['avg_fps'] for r in image_results]
            
            plt.bar([str(s) for s in img_sizes], img_fps, color=['red', 'green', 'blue'])
            plt.xlabel('YOLO Input Size (pixels)', fontsize=12)
            plt.ylabel('Average FPS', fontsize=12)
            plt.title('FPS by Input Image Size', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='y')
            
            for i, (size, fps) in enumerate(zip(img_sizes, img_fps)):
                plt.text(i, fps + 1, f'{fps:.1f}', ha='center', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "image_size_comparison.png"), dpi=300)
            plt.close()
        
        logger.info(f"Plots saved to {output_dir}")


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Benchmark video cell detection performance"
    )
    parser.add_argument(
        "video",
        help="Path to video file"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file"
    )
    parser.add_argument(
        "--output",
        default="benchmark_results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=100,
        help="Number of frames to test per configuration (default: 100)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick benchmark (fewer frames and configurations)"
    )
    
    args = parser.parse_args()
    
    # Create benchmark
    benchmark = DetectionBenchmark(args.config)
    
    # Run benchmark
    num_frames = 30 if args.quick else args.frames
    benchmark.run_full_benchmark(args.video, args.output, num_frames)


if __name__ == "__main__":
    main()
