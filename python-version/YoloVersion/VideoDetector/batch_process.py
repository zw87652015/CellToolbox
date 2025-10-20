"""
Batch Video Processing Script
Process multiple video files with consistent settings
"""

import os
import glob
from pathlib import Path
from video_cell_detector import VideoCellDetector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def batch_process_videos(
    video_dir: str,
    output_base_dir: str = "batch_results",
    config_path: str = "config.yaml",
    roi: dict = None,
    video_pattern: str = "*.mp4"
):
    """
    Process multiple videos in a directory
    
    Args:
        video_dir: Directory containing video files
        output_base_dir: Base directory for all outputs
        config_path: Path to config file
        roi: Optional ROI dict {'x': int, 'y': int, 'width': int, 'height': int}
        video_pattern: Glob pattern for video files
    """
    # Find all video files
    video_files = glob.glob(os.path.join(video_dir, video_pattern))
    
    if not video_files:
        logger.error(f"No videos found in {video_dir} matching {video_pattern}")
        return
    
    logger.info(f"Found {len(video_files)} videos to process")
    
    # Create detector
    detector = VideoCellDetector(config_path)
    
    # Set ROI if provided
    if roi:
        detector.roi = roi
        logger.info(f"Using ROI: {roi}")
    
    # Process each video
    for i, video_path in enumerate(video_files, 1):
        video_name = Path(video_path).stem
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing video {i}/{len(video_files)}: {video_name}")
        logger.info(f"{'='*60}")
        
        # Create output directory for this video
        output_dir = os.path.join(output_base_dir, video_name)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Process video (non-interactive mode would be better for batch)
            # For now, this will open windows - press Q to move to next video
            detector.process_video(video_path, output_dir)
            
            # Reset detections for next video
            detector.frame_detections = []
            
            logger.info(f"✓ Completed: {video_name}")
            
        except Exception as e:
            logger.error(f"✗ Failed to process {video_name}: {e}")
            continue
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Batch processing complete!")
    logger.info(f"Processed {len(video_files)} videos")
    logger.info(f"Results saved to: {output_base_dir}")
    logger.info(f"{'='*60}")


def main():
    """Command-line interface for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch process multiple videos with cell detection"
    )
    parser.add_argument(
        "video_dir",
        help="Directory containing video files"
    )
    parser.add_argument(
        "--output",
        default="batch_results",
        help="Base output directory (default: batch_results)"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )
    parser.add_argument(
        "--pattern",
        default="*.mp4",
        help="Video file pattern (default: *.mp4)"
    )
    parser.add_argument(
        "--roi",
        nargs=4,
        type=int,
        metavar=('X', 'Y', 'W', 'H'),
        help="ROI coordinates: x y width height (applied to all videos)"
    )
    
    args = parser.parse_args()
    
    # Parse ROI if provided
    roi = None
    if args.roi:
        roi = {
            'x': args.roi[0],
            'y': args.roi[1],
            'width': args.roi[2],
            'height': args.roi[3]
        }
    
    # Run batch processing
    batch_process_videos(
        video_dir=args.video_dir,
        output_base_dir=args.output,
        config_path=args.config,
        roi=roi,
        video_pattern=args.pattern
    )


if __name__ == "__main__":
    main()
