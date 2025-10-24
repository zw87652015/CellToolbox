"""
ToupCam Live Stream Cell Detector with YOLO11
High-performance live stream processing with threaded architecture
"""

import os
import sys
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
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add ToupCam SDK path
sdk_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                        'toupcamsdk.20241216', 'python')
sys.path.append(sdk_path)

dll_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                        'toupcamsdk.20241216', 'win', 'x64')
os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']

try:
    import ctypes
    toupcam_dll_path = os.path.join(dll_path, 'toupcam.dll')
    if os.path.exists(toupcam_dll_path):
        ctypes.WinDLL(toupcam_dll_path)
    import toupcam
except ImportError as e:
    logger.error(f"Failed to import toupcam: {e}")
    sys.exit(1)


class ToupCamLiveDetector:
    """High-performance ToupCam live stream detector with YOLO11"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the detector"""
        # If config_path is relative, look for it in the script directory
        if not os.path.isabs(config_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, config_path)
        self.config = self._load_config(config_path)
        self.model = self._load_model()
        
        # Camera
        self.hcam = None
        self.cam_buffer = None
        self.frame_width = 0
        self.frame_height = 0
        
        # ROI
        self.roi = None
        self.roi_selecting = False
        self.roi_start = None
        self.roi_end = None
        
        # State
        self.running = False
        self.paused = False
        self.detection_enabled = True
        
        # Threading
        self.frame_lock = threading.Lock()
        self.current_frame = None
        self.display_frame = None
        
        # Detection synchronization - always use latest frame
        self.latest_detection_frame = None
        self.detection_frame_lock = threading.Lock()
        self.detections = []
        self.detection_lock = threading.Lock()
        self.detection_frame_id = 0
        self.displayed_frame_id = 0
        
        # Performance
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()
        
        # Display
        self.display_width = self.config['video']['display_width']
        self.display_height = self.config['video']['display_height']
        
        # Statistics
        self.all_detections = []
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except:
            logger.warning("Config not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Default configuration"""
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
                'max_detections': 300,
                'detect_every_n_frames': 2  # run detection every N frames to reduce contention
            },
            'video': {
                'display_width': 1280,
                'display_height': 720,
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
                'roi_thickness': 2
            }
        }
    
    def _load_model(self) -> YOLO:
        """Load YOLO11 model"""
        try:
            custom_weights = self.config['model'].get('custom_weights')
            if custom_weights:
                # Expand path and check existence
                custom_weights = os.path.expanduser(custom_weights)
                if os.path.exists(custom_weights):
                    logger.info(f"Loading custom model: {custom_weights}")
                    return YOLO(custom_weights)
                else:
                    logger.warning(f"Custom weights not found: {custom_weights}")
                    logger.warning("Falling back to pretrained model")
            
            model_name = f"yolo11{self.config['model']['size']}.pt"
            logger.info(f"Loading YOLO11 pretrained model: {model_name}")
            return YOLO(model_name)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def start_camera(self):
        """Initialize ToupCam"""
        try:
            devices = toupcam.Toupcam.EnumV2()
            if len(devices) == 0:
                raise Exception("No ToupCam found")
            
            self.hcam = toupcam.Toupcam.Open(None)
            if self.hcam is None:
                raise Exception("Failed to open ToupCam")
            
            self.frame_width, self.frame_height = self.hcam.get_Size()
            logger.info(f"Camera: {self.frame_width}x{self.frame_height}")
            
            # Configure camera
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BYTEORDER, 0)
            # Reduce internal buffering and ensure callback runs on a dedicated thread with higher priority
            if hasattr(toupcam, 'TOUPCAM_OPTION_CALLBACK_THREAD'):
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_CALLBACK_THREAD, 1)
            if hasattr(toupcam, 'TOUPCAM_OPTION_THREAD_PRIORITY'):
                # 2 corresponds to higher priority in SDKs used in this repo
                self.hcam.put_Option(toupcam.TOUPCAM_OPTION_THREAD_PRIORITY, 2)
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_FRAME_DEQUE_LENGTH, 2)
            self.hcam.put_AutoExpoEnable(False)
            self.hcam.put_ExpoTime(8333)  # 8.333ms
            
            # Allocate buffer
            buffer_size = toupcam.TDIBWIDTHBYTES(self.frame_width * 24) * self.frame_height
            self.cam_buffer = bytes(buffer_size)
            self.frame_buffer_shape = (self.frame_height, 
                                      toupcam.TDIBWIDTHBYTES(self.frame_width * 24) // 3, 3)
            
            # Start capture
            self.hcam.StartPullModeWithCallback(self._frame_callback, self)
            self.running = True
            
            return True
        except Exception as e:
            logger.error(f"Camera error: {e}")
            return False
    
    @staticmethod
    def _frame_callback(nEvent, ctx):
        """ToupCam frame callback"""
        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            ctx._on_frame_received()
    
    def _on_frame_received(self):
        """Handle new frame from camera"""
        if not self.running or self.hcam is None:
            return
        
        try:
            self.hcam.PullImageV4(self.cam_buffer, 0, 24, 0, None)
            # Zero-copy view into SDK buffer; keep in BGR to avoid conversion cost here
            frame = np.frombuffer(self.cam_buffer, dtype=np.uint8).reshape(self.frame_buffer_shape)
            frame = frame[:, :self.frame_width, :]
            
            with self.frame_lock:
                # Store reference; do not copy to minimize latency
                self.current_frame = frame
                self.frame_count += 1
                current_id = self.frame_count
            
            # Update latest frame for detection (always use newest frame)
            if self.detection_enabled and not self.paused:
                with self.detection_frame_lock:
                    # Always replace with latest frame - detection will grab it when ready
                    self.latest_detection_frame = frame.copy()
                    self.detection_frame_id = current_id
                    
        except Exception as e:
            logger.error(f"Frame error: {e}")
    
    def _detection_thread(self):
        """Detection thread - always processes latest frame"""
        while self.running:
            try:
                # Grab the latest frame snapshot
                with self.detection_frame_lock:
                    if self.latest_detection_frame is None:
                        time.sleep(0.01)
                        continue
                    frame = self.latest_detection_frame
                    frame_id = self.detection_frame_id
                    # Clear to indicate we've consumed it
                    self.latest_detection_frame = None
                
                # Apply ROI if set
                detection_frame = self._apply_roi_mask(frame) if self.roi else frame
                
                # Convert BGR->RGB only for the frame we send to YOLO
                detection_frame = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2RGB)
                
                # Run YOLO detection
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
                
                # Parse results
                detections = self._parse_results(results[0])
                detections = self._filter_detections_by_roi(detections)
                
                with self.detection_lock:
                    self.detections = detections
                    self.displayed_frame_id = frame_id  # Track which frame these detections came from
                    self.all_detections.extend(detections)
                    
            except Exception as e:
                logger.error(f"Detection error: {e}")
    
    def _render_thread(self):
        """Render thread - high FPS display"""
        while self.running:
            try:
                with self.frame_lock:
                    if self.current_frame is not None:
                        # Use latest frame reference; copy only when drawing
                        frame = self.current_frame
                    else:
                        time.sleep(0.01)
                        continue
                
                # Get detections
                with self.detection_lock:
                    detections = self.detections.copy()
                
                # Draw annotations
                annotated = self._draw_detections(frame, detections)
                
                # Calculate FPS
                elapsed = time.time() - self.fps_start_time
                if elapsed > 1.0:
                    self.fps = self.frame_count / elapsed
                    self.frame_count = 0
                    self.fps_start_time = time.time()
                
                annotated = self._draw_info(annotated, detections, self.fps)
                
                # Resize for display
                display = cv2.resize(annotated, (self.display_width, self.display_height))
                display = self._draw_roi_on_display(display)
                
                self.display_frame = display
                
                # Keep sleep minimal to reduce display latency
                time.sleep(0.0005)
                
            except Exception as e:
                logger.error(f"Render error: {e}")
                time.sleep(0.01)
    
    def _apply_roi_mask(self, image: np.ndarray) -> np.ndarray:
        """Apply ROI mask"""
        if self.roi is None:
            return image
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        x, y, w, h = self.roi['x'], self.roi['y'], self.roi['width'], self.roi['height']
        mask[y:y+h, x:x+w] = 255
        return cv2.bitwise_and(image, image, mask=mask)
    
    def _filter_detections_by_roi(self, detections: List[Dict]) -> List[Dict]:
        """Filter detections by ROI"""
        if self.roi is None:
            return detections
        filtered = []
        for det in detections:
            cx, cy = det['center_x'], det['center_y']
            if (self.roi['x'] <= cx <= self.roi['x'] + self.roi['width'] and
                self.roi['y'] <= cy <= self.roi['y'] + self.roi['height']):
                filtered.append(det)
        return filtered
    
    def _parse_results(self, result) -> List[Dict]:
        """Parse YOLO results"""
        detections = []
        if result.boxes is None or len(result.boxes) == 0:
            return detections
        
        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        
        for i, (box, conf) in enumerate(zip(boxes, confidences)):
            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1
            
            # Apply filters
            if (width < self.config['filters']['min_cell_size'] or 
                height < self.config['filters']['min_cell_size']):
                continue
            if (width > self.config['filters']['max_cell_size'] or 
                height > self.config['filters']['max_cell_size']):
                continue
            
            aspect_ratio = width / height if height > 0 else 0
            if (aspect_ratio < self.config['filters']['min_aspect_ratio'] or 
                aspect_ratio > self.config['filters']['max_aspect_ratio']):
                continue
            
            detections.append({
                'detection_id': i,
                'confidence': float(conf),
                'bbox_x1': float(x1), 'bbox_y1': float(y1),
                'bbox_x2': float(x2), 'bbox_y2': float(y2),
                'center_x': float((x1 + x2) / 2),
                'center_y': float((y1 + y2) / 2),
                'width': float(width),
                'height': float(height),
                'area': float(width * height)
            })
        
        return detections
    
    def _draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw detection boxes"""
        annotated = image.copy()
        color = tuple(self.config['visualization']['box_color'])
        thickness = self.config['visualization']['box_thickness']
        
        for det in detections:
            x1, y1 = int(det['bbox_x1']), int(det['bbox_y1'])
            x2, y2 = int(det['bbox_x2']), int(det['bbox_y2'])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            label = f"{det['confidence']:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return annotated
    
    def _draw_info(self, image: np.ndarray, detections: List[Dict], fps: float) -> np.ndarray:
        """Draw info overlay"""
        annotated = image.copy()
        info_lines = []
        
        if self.config['video']['show_fps']:
            info_lines.append(f"FPS: {fps:.1f}")
        if self.config['video']['show_count']:
            info_lines.append(f"Cells: {len(detections)}")
        if self.paused:
            info_lines.append("PAUSED")
        if self.roi:
            info_lines.append("ROI: Active")
        
        panel_height = 30 + len(info_lines) * 25
        cv2.rectangle(annotated, (10, 10), (250, panel_height), (0, 0, 0), -1)
        cv2.rectangle(annotated, (10, 10), (250, panel_height), (255, 255, 255), 2)
        
        y_offset = 35
        for line in info_lines:
            cv2.putText(annotated, line, (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_offset += 25
        
        return annotated
    
    def _draw_roi_on_display(self, display: np.ndarray) -> np.ndarray:
        """Draw ROI on display"""
        if self.roi is None and not self.roi_selecting:
            return display
        
        annotated = display.copy()
        roi_color = tuple(self.config['visualization']['roi_color'])
        
        if self.roi:
            scale_x = self.display_width / self.frame_width
            scale_y = self.display_height / self.frame_height
            
            x = int(self.roi['x'] * scale_x)
            y = int(self.roi['y'] * scale_y)
            w = int(self.roi['width'] * scale_x)
            h = int(self.roi['height'] * scale_y)
            
            # Dim outside ROI
            mask = annotated.copy()
            mask = cv2.addWeighted(mask, 0.4, np.zeros_like(mask), 0.6, 0)
            mask[y:y+h, x:x+w] = annotated[y:y+h, x:x+w]
            annotated = mask
            
            cv2.rectangle(annotated, (x, y), (x + w, y + h), roi_color, 2)
        
        return annotated
    
    def _mouse_callback(self, event, x, y, flags, param):
        """Mouse callback for ROI selection"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.roi_selecting = True
            self.roi_start = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.roi_selecting:
            self.roi_end = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.roi_selecting = False
            if self.roi_start and self.roi_end:
                x1, y1 = self.roi_start
                x2, y2 = self.roi_end
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                scale_x = self.frame_width / self.display_width
                scale_y = self.frame_height / self.display_height
                
                self.roi = {
                    'x': int(x1 * scale_x),
                    'y': int(y1 * scale_y),
                    'width': int((x2 - x1) * scale_x),
                    'height': int((y2 - y1) * scale_y)
                }
                logger.info(f"ROI set: {self.roi}")
    
    def run(self):
        """Main run loop"""
        if not self.start_camera():
            return
        
        # Start threads
        detection_thread = threading.Thread(target=self._detection_thread, daemon=True)
        render_thread = threading.Thread(target=self._render_thread, daemon=True)
        detection_thread.start()
        render_thread.start()
        
        # Create window
        window_name = "ToupCam Live Detector - Press 'h' for help"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, self.display_width, self.display_height)
        cv2.setMouseCallback(window_name, self._mouse_callback)
        
        self._show_controls()
        
        # Display loop
        while self.running:
            if self.display_frame is not None:
                cv2.imshow(window_name, self.display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord(' '):
                self.paused = not self.paused
                logger.info(f"{'Paused' if self.paused else 'Resumed'}")
            elif key == ord('d'):
                self.detection_enabled = not self.detection_enabled
                logger.info(f"Detection: {'ON' if self.detection_enabled else 'OFF'}")
            elif key == ord('r'):
                self.roi = None
                logger.info("ROI cleared")
            elif key == ord('h'):
                self._show_controls()
        
        # Cleanup
        self.running = False
        time.sleep(0.5)
        if self.hcam:
            self.hcam.Close()
        cv2.destroyAllWindows()
        
        logger.info(f"Total detections: {len(self.all_detections)}")
    
    def _show_controls(self):
        """Show keyboard controls"""
        print("""
        ╔═══════════════════════════════════════════════════════════╗
        ║       TOUPCAM LIVE DETECTOR - KEYBOARD CONTROLS          ║
        ╠═══════════════════════════════════════════════════════════╣
        ║  SPACE   - Pause/Resume                                   ║
        ║  Q       - Quit                                           ║
        ║  D       - Toggle detection ON/OFF                        ║
        ║  R       - Clear ROI                                      ║
        ║  H       - Show this help                                 ║
        ║  MOUSE   - Click and drag to select ROI                   ║
        ╚═══════════════════════════════════════════════════════════╝
        """)


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="ToupCam Live Stream Cell Detector")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()
    
    detector = ToupCamLiveDetector(args.config)
    detector.run()


if __name__ == "__main__":
    main()
