"""
Real-Time Video Cell Detector with ROI Support
Processes video files frame-by-frame with YOLO11 cell detection
Supports ROI selection, tracking, and statistics export
"""

import os
import cv2
import numpy as np
import pandas as pd
import json
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from ultralytics import YOLO
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoCellDetector:
    """Real-time video cell detector with ROI support"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the video cell detector
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.model = self._load_model()
        self.roi = None
        self.roi_selecting = False
        self.roi_start = None
        self.roi_end = None
        self.paused = False
        self.frame_skip = 0
        self.current_frame_num = 0
        self.total_frames = 0
        self.fps = 0
        self.frame_detections = []
        self.current_display_frame = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            # Resolve config path relative to script directory if not absolute
            if not os.path.isabs(config_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(script_dir, config_path)
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
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
            },
            'video': {
                'display_width': 1280,
                'display_height': 720,
                'save_annotated': True,
                'save_statistics': True,
                'show_fps': True,
                'show_count': True
            },
            'filters': {
                'min_cell_size': 40,
                'max_cell_size': 500,
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0
            },
            'visualization': {
                'box_color': [0, 255, 0],
                'box_thickness': 2,
                'text_color': [255, 255, 255],
                'text_scale': 0.6,
                'roi_color': [255, 0, 0],
                'roi_thickness': 2,
                'roi_dim_factor': 0.4
            }
        }
    
    def _load_model(self) -> YOLO:
        """Load YOLO11 model"""
        try:
            model_size = self.config['model']['size']
            custom_weights = self.config['model'].get('custom_weights')
            
            if custom_weights and os.path.exists(custom_weights):
                logger.info(f"Loading custom model from {custom_weights}")
                model = YOLO(custom_weights)
            else:
                model_name = f"yolo11{model_size}.pt"
                logger.info(f"Loading pretrained YOLO11 model: {model_name}")
                model = YOLO(model_name)
            
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _mouse_callback(self, event, x, y, flags, param):
        """Mouse callback for ROI selection"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.roi_selecting = True
            self.roi_start = (x, y)
            self.roi_end = (x, y)
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.roi_selecting:
                self.roi_end = (x, y)
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.roi_selecting = False
            self.roi_end = (x, y)
            
            # Convert display coordinates to original image coordinates
            if self.roi_start and self.roi_end:
                x1, y1 = self.roi_start
                x2, y2 = self.roi_end
                
                # Ensure x1 < x2 and y1 < y2
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                # Convert to original image coordinates
                scale_x = self.original_width / self.display_width
                scale_y = self.original_height / self.display_height
                
                self.roi = {
                    'x': int(x1 * scale_x),
                    'y': int(y1 * scale_y),
                    'width': int((x2 - x1) * scale_x),
                    'height': int((y2 - y1) * scale_y)
                }
                
                logger.info(f"ROI selected: {self.roi}")
    
    def _apply_roi_mask(self, image: np.ndarray) -> np.ndarray:
        """Apply ROI mask to image"""
        if self.roi is None:
            return image
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        x, y, w, h = self.roi['x'], self.roi['y'], self.roi['width'], self.roi['height']
        mask[y:y+h, x:x+w] = 255
        
        return cv2.bitwise_and(image, image, mask=mask)
    
    def _filter_detections_by_roi(self, detections: List[Dict]) -> List[Dict]:
        """Filter detections to only include those within ROI"""
        if self.roi is None:
            return detections
        
        filtered = []
        roi_x, roi_y = self.roi['x'], self.roi['y']
        roi_w, roi_h = self.roi['width'], self.roi['height']
        
        for det in detections:
            cx, cy = det['center_x'], det['center_y']
            
            # Check if center is within ROI
            if (roi_x <= cx <= roi_x + roi_w and
                roi_y <= cy <= roi_y + roi_h):
                filtered.append(det)
        
        return filtered
    
    def _parse_results(self, result, frame_num: int) -> List[Dict]:
        """Parse YOLO results into detection dictionaries"""
        detections = []
        
        if result.boxes is None or len(result.boxes) == 0:
            return detections
        
        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()
        
        min_size = self.config['filters']['min_cell_size']
        max_size = self.config['filters']['max_cell_size']
        min_aspect = self.config['filters']['min_aspect_ratio']
        max_aspect = self.config['filters']['max_aspect_ratio']
        
        for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1
            
            # Apply size filters
            if width < min_size or height < min_size:
                continue
            if width > max_size or height > max_size:
                continue
            
            # Apply aspect ratio filter
            aspect_ratio = width / height if height > 0 else 0
            if aspect_ratio < min_aspect or aspect_ratio > max_aspect:
                continue
            
            detection = {
                'frame': frame_num,
                'detection_id': i,
                'confidence': float(conf),
                'class_id': int(cls),
                'bbox_x1': float(x1),
                'bbox_y1': float(y1),
                'bbox_x2': float(x2),
                'bbox_y2': float(y2),
                'center_x': float((x1 + x2) / 2),
                'center_y': float((y1 + y2) / 2),
                'width': float(width),
                'height': float(height),
                'area': float(width * height)
            }
            
            detections.append(detection)
        
        return detections
    
    def _draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw detection boxes on image"""
        annotated = image.copy()
        
        box_color = tuple(self.config['visualization']['box_color'])
        thickness = self.config['visualization']['box_thickness']
        text_color = tuple(self.config['visualization']['text_color'])
        text_scale = self.config['visualization']['text_scale']
        
        for det in detections:
            x1 = int(det['bbox_x1'])
            y1 = int(det['bbox_y1'])
            x2 = int(det['bbox_x2'])
            y2 = int(det['bbox_y2'])
            conf = det['confidence']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, thickness)
            
            # Draw confidence label
            label = f"{conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, text_scale, 1)
            cv2.rectangle(annotated, (x1, y1 - label_size[1] - 4), 
                         (x1 + label_size[0], y1), box_color, -1)
            cv2.putText(annotated, label, (x1, y1 - 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_color, 1)
        
        return annotated
    
    def _draw_roi_on_display(self, display_image: np.ndarray) -> np.ndarray:
        """Draw ROI rectangle with dimmed mask on display-sized image"""
        if self.roi is None and not self.roi_selecting:
            return display_image
        
        annotated = display_image.copy()
        roi_color = tuple(self.config['visualization']['roi_color'])
        roi_thickness = self.config['visualization']['roi_thickness']
        
        if self.roi_selecting and self.roi_start and self.roi_end:
            # Draw temporary ROI during selection (already in display coordinates)
            x1, y1 = self.roi_start
            x2, y2 = self.roi_end
            
            # Ensure x1 < x2 and y1 < y2
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Create dimmed mask overlay
            mask = np.zeros_like(annotated)
            mask[:] = (0, 0, 0)  # Black mask
            
            # Create ROI hole in mask (keep original brightness)
            mask[y1:y2, x1:x2] = annotated[y1:y2, x1:x2]
            
            # Blend: darken outside ROI
            alpha = 0.5  # Dimming factor (0.5 = 50% darker)
            annotated = cv2.addWeighted(annotated, alpha, mask, 1 - alpha, 0)
            
            # Restore ROI area to full brightness
            annotated[y1:y2, x1:x2] = display_image[y1:y2, x1:x2]
            
            # Draw ROI rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), roi_color, roi_thickness)
            
        elif self.roi:
            # Convert original ROI coordinates to display coordinates
            scale_x = self.display_width / self.original_width
            scale_y = self.display_height / self.original_height
            
            x = int(self.roi['x'] * scale_x)
            y = int(self.roi['y'] * scale_y)
            w = int(self.roi['width'] * scale_x)
            h = int(self.roi['height'] * scale_y)
            
            # Ensure ROI is within display bounds
            img_h, img_w = annotated.shape[:2]
            x = max(0, min(x, img_w))
            y = max(0, min(y, img_h))
            w = min(w, img_w - x)
            h = min(h, img_h - y)
            
            # Get dimming factor from config
            dim_factor = self.config['visualization'].get('roi_dim_factor', 0.4)
            
            # Create dimmed mask overlay
            mask = annotated.copy()
            mask = cv2.addWeighted(mask, dim_factor, np.zeros_like(mask), 1 - dim_factor, 0)
            
            # Restore ROI area to full brightness
            mask[y:y+h, x:x+w] = annotated[y:y+h, x:x+w]
            
            annotated = mask
            
            # Draw ROI rectangle
            cv2.rectangle(annotated, (x, y), (x + w, y + h), roi_color, roi_thickness)
            
            # Draw ROI label
            label = "ROI"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            # Draw label background
            cv2.rectangle(annotated, (x, y - label_size[1] - 10), 
                         (x + label_size[0] + 10, y), roi_color, -1)
            cv2.putText(annotated, label, (x + 5, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated
    
    def _draw_roi(self, image: np.ndarray) -> np.ndarray:
        """Draw ROI rectangle with dimmed mask on image"""
        if self.roi is None and not self.roi_selecting:
            return image
        
        annotated = image.copy()
        roi_color = tuple(self.config['visualization']['roi_color'])
        roi_thickness = self.config['visualization']['roi_thickness']
        
        # Convert original coordinates to display coordinates
        scale_x = self.display_width / self.original_width
        scale_y = self.display_height / self.original_height
        
        if self.roi_selecting and self.roi_start and self.roi_end:
            # Draw temporary ROI during selection with dimmed mask
            x1, y1 = self.roi_start
            x2, y2 = self.roi_end
            
            # Ensure x1 < x2 and y1 < y2
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Create dimmed mask overlay
            mask = np.zeros_like(annotated)
            mask[:] = (0, 0, 0)  # Black mask
            
            # Create ROI hole in mask (keep original brightness)
            mask[y1:y2, x1:x2] = annotated[y1:y2, x1:x2]
            
            # Blend: darken outside ROI
            alpha = 0.5  # Dimming factor (0.5 = 50% darker)
            annotated = cv2.addWeighted(annotated, alpha, mask, 1 - alpha, 0)
            
            # Restore ROI area to full brightness
            annotated[y1:y2, x1:x2] = image[y1:y2, x1:x2]
            
            # Draw ROI rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), roi_color, roi_thickness)
            
        elif self.roi:
            # Draw confirmed ROI with dimmed mask
            x = int(self.roi['x'] * scale_x)
            y = int(self.roi['y'] * scale_y)
            w = int(self.roi['width'] * scale_x)
            h = int(self.roi['height'] * scale_y)
            
            # Ensure ROI is within image bounds
            img_h, img_w = annotated.shape[:2]
            x = max(0, min(x, img_w))
            y = max(0, min(y, img_h))
            w = min(w, img_w - x)
            h = min(h, img_h - y)
            
            # Get dimming factor from config
            dim_factor = self.config['visualization'].get('roi_dim_factor', 0.4)
            
            # Create dimmed mask overlay
            mask = annotated.copy()
            mask = cv2.addWeighted(mask, dim_factor, np.zeros_like(mask), 1 - dim_factor, 0)
            
            # Restore ROI area to full brightness
            mask[y:y+h, x:x+w] = annotated[y:y+h, x:x+w]
            
            annotated = mask
            
            # Draw ROI rectangle
            cv2.rectangle(annotated, (x, y), (x + w, y + h), roi_color, roi_thickness)
            
            # Draw ROI label
            label = "ROI"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            # Draw label background
            cv2.rectangle(annotated, (x, y - label_size[1] - 10), 
                         (x + label_size[0] + 10, y), roi_color, -1)
            cv2.putText(annotated, label, (x + 5, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated
    
    def _draw_info(self, image: np.ndarray, detections: List[Dict], 
                   fps: float, frame_num: int) -> np.ndarray:
        """Draw information overlay on image"""
        annotated = image.copy()
        
        # Prepare info text
        info_lines = []
        
        if self.config['video']['show_fps']:
            info_lines.append(f"FPS: {fps:.1f}")
        
        if self.config['video']['show_count']:
            info_lines.append(f"Cells: {len(detections)}")
        
        info_lines.append(f"Frame: {frame_num}/{self.total_frames}")
        
        if self.paused:
            info_lines.append("PAUSED")
        
        if self.roi:
            info_lines.append("ROI: Active")
        
        # Draw info panel
        panel_height = 30 + len(info_lines) * 25
        cv2.rectangle(annotated, (10, 10), (250, panel_height), (0, 0, 0), -1)
        cv2.rectangle(annotated, (10, 10), (250, panel_height), (255, 255, 255), 2)
        
        y_offset = 35
        for line in info_lines:
            cv2.putText(annotated, line, (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_offset += 25
        
        return annotated
    
    def process_video(self, video_path: str, output_dir: str = "output_video"):
        """
        Process video file with real-time cell detection
        
        Args:
            video_path: Path to input video file
            output_dir: Directory to save outputs
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return
        
        # Get video properties
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Set display size
        self.display_width = self.config['video']['display_width']
        self.display_height = self.config['video']['display_height']
        
        logger.info(f"Video: {video_path}")
        logger.info(f"Resolution: {self.original_width}x{self.original_height}")
        logger.info(f"FPS: {self.fps:.2f}")
        logger.info(f"Total frames: {self.total_frames}")
        
        # Setup video writer if saving
        video_writer = None
        if self.config['video']['save_annotated']:
            output_video_path = os.path.join(output_dir, "annotated_video.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                output_video_path, fourcc, self.fps,
                (self.original_width, self.original_height)
            )
        
        # Create window and set mouse callback
        window_name = "Video Cell Detector - Press 'h' for help"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, self.display_width, self.display_height)
        cv2.setMouseCallback(window_name, self._mouse_callback)
        
        # Show controls
        self._show_controls()
        
        # Processing loop
        frame_count = 0
        start_time = time.time()
        
        while True:
            if not self.paused:
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.info("End of video reached")
                    break
                
                frame_count += 1
                self.current_frame_num = frame_count
                
                # Skip frames if needed
                if self.frame_skip > 0 and frame_count % (self.frame_skip + 1) != 0:
                    continue
                
                # Run detection
                detection_start = time.time()
                
                # Apply ROI if set
                detection_frame = self._apply_roi_mask(frame) if self.roi else frame
                
                results = self.model.predict(
                    source=detection_frame,
                    imgsz=self.config['detection']['image_size'],
                    conf=self.config['model']['confidence_threshold'],
                    iou=self.config['model']['iou_threshold'],
                    device=self.config['detection']['device'],
                    half=self.config['detection']['half_precision'],
                    max_det=self.config['detection']['max_detections'],
                    verbose=False
                )
                
                # Parse detections
                detections = self._parse_results(results[0], frame_count)
                
                # Filter by ROI
                detections = self._filter_detections_by_roi(detections)
                
                # Store detections
                self.frame_detections.extend(detections)
                
                detection_time = time.time() - detection_start
                
                # Draw annotations on original frame
                annotated = self._draw_detections(frame, detections)
                
                # Calculate FPS
                elapsed = time.time() - start_time
                current_fps = frame_count / elapsed if elapsed > 0 else 0
                
                annotated = self._draw_info(annotated, detections, current_fps, frame_count)
                
                # Save frame if needed (without ROI overlay)
                if video_writer:
                    video_writer.write(annotated)
                
                # Resize for display FIRST
                display_frame = cv2.resize(annotated, (self.display_width, self.display_height))
                
                # Draw ROI on display-sized frame
                display_frame = self._draw_roi_on_display(display_frame)
                
                # Store for pause mode
                self.current_display_frame = display_frame
                
                # Show frame
                cv2.imshow(window_name, display_frame)
            else:
                # Paused - show current frame with updated ROI
                if self.current_display_frame is not None:
                    display_frame = self._draw_roi_on_display(self.current_display_frame.copy())
                    cv2.imshow(window_name, display_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                logger.info("Quit requested")
                break
            elif key == ord(' '):
                self.paused = not self.paused
                logger.info(f"{'Paused' if self.paused else 'Resumed'}")
            elif key == ord('r'):
                self.roi = None
                logger.info("ROI cleared")
            elif key == ord('s'):
                # Save current frame
                frame_path = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(frame_path, annotated)
                logger.info(f"Frame saved: {frame_path}")
            elif key == ord('h'):
                self._show_controls()
            elif key == ord('+') or key == ord('='):
                self.frame_skip = max(0, self.frame_skip - 1)
                logger.info(f"Frame skip: {self.frame_skip}")
            elif key == ord('-'):
                self.frame_skip += 1
                logger.info(f"Frame skip: {self.frame_skip}")
        
        # Cleanup
        cap.release()
        if video_writer:
            video_writer.release()
        cv2.destroyAllWindows()
        
        # Save statistics
        if self.config['video']['save_statistics'] and self.frame_detections:
            self._save_statistics(output_dir, video_path)
        
        logger.info(f"Processing complete. Total detections: {len(self.frame_detections)}")
    
    def _show_controls(self):
        """Show keyboard controls"""
        controls = """
        ╔═══════════════════════════════════════════════════════════╗
        ║          VIDEO CELL DETECTOR - KEYBOARD CONTROLS         ║
        ╠═══════════════════════════════════════════════════════════╣
        ║  SPACE   - Pause/Resume                                   ║
        ║  Q       - Quit                                           ║
        ║  R       - Clear ROI                                      ║
        ║  S       - Save current frame                             ║
        ║  H       - Show this help                                 ║
        ║  +/=     - Decrease frame skip (faster processing)        ║
        ║  -       - Increase frame skip (skip frames)              ║
        ║                                                           ║
        ║  MOUSE   - Click and drag to select ROI                   ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        print(controls)
    
    def _save_statistics(self, output_dir: str, video_path: str):
        """Save detection statistics to files"""
        # Save frame-by-frame detections
        df = pd.DataFrame(self.frame_detections)
        csv_path = os.path.join(output_dir, "detections.csv")
        df.to_csv(csv_path, index=False)
        logger.info(f"Detections saved to: {csv_path}")
        
        # Calculate summary statistics
        summary = {
            'video_path': video_path,
            'total_frames': self.total_frames,
            'processed_frames': self.current_frame_num,
            'total_detections': len(self.frame_detections),
            'avg_detections_per_frame': len(self.frame_detections) / self.current_frame_num if self.current_frame_num > 0 else 0,
            'roi': self.roi,
            'timestamp': datetime.now().isoformat()
        }
        
        if len(self.frame_detections) > 0:
            summary.update({
                'avg_confidence': float(df['confidence'].mean()),
                'avg_cell_width': float(df['width'].mean()),
                'avg_cell_height': float(df['height'].mean()),
                'avg_cell_area': float(df['area'].mean()),
                'min_cell_size': float(min(df['width'].min(), df['height'].min())),
                'max_cell_size': float(max(df['width'].max(), df['height'].max()))
            })
        
        # Save summary
        summary_path = os.path.join(output_dir, "summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Summary saved to: {summary_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("DETECTION SUMMARY")
        print("="*60)
        for key, value in summary.items():
            if key != 'roi' and key != 'timestamp':
                print(f"{key}: {value}")
        print("="*60 + "\n")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time video cell detector with ROI")
    parser.add_argument("video", help="Path to input video file")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--output", default="output_video", help="Output directory")
    parser.add_argument("--roi", nargs=4, type=int, metavar=('X', 'Y', 'W', 'H'),
                       help="ROI coordinates: x y width height")
    
    args = parser.parse_args()
    
    # Create detector
    detector = VideoCellDetector(args.config)
    
    # Set ROI if provided
    if args.roi:
        detector.roi = {
            'x': args.roi[0],
            'y': args.roi[1],
            'width': args.roi[2],
            'height': args.roi[3]
        }
        logger.info(f"ROI set from command line: {detector.roi}")
    
    # Process video
    detector.process_video(args.video, args.output)


if __name__ == "__main__":
    main()
