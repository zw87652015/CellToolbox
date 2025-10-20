"""
Video Frame Extractor
Extracts 1 frame from every 10 frames of a video file.
"""

import cv2
import os
import argparse
from pathlib import Path


class VideoFrameExtractor:
    """Extract frames from video at specified intervals."""
    
    def __init__(self, video_path, output_dir, frame_interval=10):
        """
        Initialize the frame extractor.
        
        Args:
            video_path: Path to input video file
            output_dir: Directory to save extracted frames
            frame_interval: Extract 1 frame every N frames (default: 10)
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.frame_interval = frame_interval
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_frames(self):
        """Extract frames from video."""
        # Open video file
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {self.video_path}")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video Properties:")
        print(f"  Total frames: {total_frames}")
        print(f"  FPS: {fps:.2f}")
        print(f"  Resolution: {width}x{height}")
        print(f"  Frame interval: {self.frame_interval}")
        print(f"  Expected output frames: {total_frames // self.frame_interval}")
        print()
        
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Save frame if it's at the interval
            if frame_count % self.frame_interval == 0:
                # Generate output filename
                output_filename = f"frame_{frame_count:06d}.jpg"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # Save frame
                cv2.imwrite(output_path, frame)
                saved_count += 1
                
                if saved_count % 200 == 0:
                    print(f"Saved {saved_count} frames... (current frame: {frame_count}/{total_frames})")
            
            frame_count += 1
        
        cap.release()
        
        print()
        print(f"Extraction complete!")
        print(f"  Total frames processed: {frame_count}")
        print(f"  Frames saved: {saved_count}")
        print(f"  Output directory: {self.output_dir}")
        
        return saved_count


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Extract frames from video at specified intervals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract 1 frame every 10 frames (default)
  python video_frame_extractor.py input.mp4 -o output_frames
  
  # Extract 1 frame every 30 frames
  python video_frame_extractor.py input.mp4 -o output_frames -i 30
  
  # Specify full paths
  python video_frame_extractor.py C:/videos/input.mp4 -o C:/frames
        """
    )
    
    parser.add_argument(
        "video",
        type=str,
        help="Path to input video file"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output_frames",
        help="Output directory for extracted frames (default: output_frames)"
    )
    
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=10,
        help="Frame interval - extract 1 frame every N frames (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Validate input video exists
    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        return
    
    # Create extractor and run
    try:
        extractor = VideoFrameExtractor(
            video_path=args.video,
            output_dir=args.output,
            frame_interval=args.interval
        )
        
        extractor.extract_frames()
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
