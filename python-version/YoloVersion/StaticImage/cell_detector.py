"""
YOLO11 Cell Detection System for Static Images
Detects cell positions and sizes in JPG and PNG images
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CellDetector:
    """YOLO11-based cell detector for static images"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the cell detector
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.model = self._load_model()
        self.results_data = []
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _load_model(self) -> YOLO:
        """Load YOLO11 model"""
        try:
            model_size = self.config['model']['size']
            custom_weights = self.config['model'].get('custom_weights')
            
            if custom_weights and os.path.exists(custom_weights):
                logger.info(f"Loading custom model from {custom_weights}")
                model = YOLO(custom_weights)
            else:
                # Use pretrained YOLO11 model
                model_name = f"yolo11{model_size}.pt"
                logger.info(f"Loading pretrained YOLO11 model: {model_name}")
                model = YOLO(model_name)
            
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def detect_cells(self, image_path: str) -> List[Dict]:
        """
        Detect cells in a single image
        
        Args:
            image_path: Path to input image
            
        Returns:
            List of detection dictionaries with position and size info
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to read image: {image_path}")
                return []
            
            # Run inference
            results = self.model.predict(
                source=image,
                imgsz=self.config['detection']['image_size'],
                conf=self.config['model']['confidence_threshold'],
                iou=self.config['model']['iou_threshold'],
                device=self.config['detection']['device'],
                half=self.config['detection']['half_precision'],
                max_det=self.config['detection']['max_detections'],
                verbose=False
            )
            
            # Parse results
            detections = self._parse_results(results[0], image_path)
            
            # Apply cell-specific filters
            filtered_detections = self._filter_detections(detections)
            
            logger.info(f"Detected {len(filtered_detections)} cells in {os.path.basename(image_path)}")
            return filtered_detections
            
        except Exception as e:
            logger.error(f"Error detecting cells in {image_path}: {e}")
            return []
    
    def _parse_results(self, result, image_path: str) -> List[Dict]:
        """Parse YOLO results into structured format"""
        detections = []
        
        if result.boxes is None or len(result.boxes) == 0:
            return detections
        
        boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
        confidences = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()
        
        for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
            x1, y1, x2, y2 = box
            
            # Calculate center position and size
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            width = x2 - x1
            height = y2 - y1
            area = width * height
            
            detection = {
                'image': os.path.basename(image_path),
                'detection_id': i,
                'class_id': int(cls),
                'class_name': result.names[int(cls)],
                'confidence': float(conf),
                'center_x': float(center_x),
                'center_y': float(center_y),
                'width': float(width),
                'height': float(height),
                'area': float(area),
                'bbox_x1': float(x1),
                'bbox_y1': float(y1),
                'bbox_x2': float(x2),
                'bbox_y2': float(y2)
            }
            
            detections.append(detection)
        
        return detections
    
    def _filter_detections(self, detections: List[Dict]) -> List[Dict]:
        """Apply cell-specific filters to detections"""
        cell_config = self.config['cell_detection']
        filtered = []
        
        for det in detections:
            # Size filter
            size = max(det['width'], det['height'])
            if size < cell_config['min_size'] or size > cell_config['max_size']:
                continue
            
            # Aspect ratio filter
            aspect_ratio = det['width'] / det['height'] if det['height'] > 0 else 0
            if aspect_ratio < cell_config['min_aspect_ratio'] or \
               aspect_ratio > cell_config['max_aspect_ratio']:
                continue
            
            filtered.append(det)
        
        return filtered
    
    def process_directory(self, input_dir: Optional[str] = None) -> None:
        """
        Process all images in a directory
        
        Args:
            input_dir: Input directory path (uses config if None)
        """
        if input_dir is None:
            input_dir = self.config['paths']['input_dir']
        
        # Create input directory if it doesn't exist
        os.makedirs(input_dir, exist_ok=True)
        
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        image_files = []
        for ext in image_extensions:
            image_files.extend(Path(input_dir).glob(f'*{ext}'))
        
        if not image_files:
            logger.warning(f"No images found in {input_dir}")
            return
        
        logger.info(f"Found {len(image_files)} images to process")
        
        # Process each image
        self.results_data = []
        for image_path in image_files:
            detections = self.detect_cells(str(image_path))
            self.results_data.extend(detections)
            
            # Visualize and save if enabled
            if self.config['paths']['save_images']:
                self._visualize_and_save(str(image_path), detections)
        
        # Save results
        self._save_results()
        
        logger.info(f"Processing complete. Total detections: {len(self.results_data)}")
    
    def _visualize_and_save(self, image_path: str, detections: List[Dict]) -> None:
        """Visualize detections and save annotated image"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return
            
            vis_config = self.config['visualization']
            
            for det in detections:
                x1 = int(det['bbox_x1'])
                y1 = int(det['bbox_y1'])
                x2 = int(det['bbox_x2'])
                y2 = int(det['bbox_y2'])
                
                # Draw bounding box
                if vis_config['draw_boxes']:
                    cv2.rectangle(
                        image,
                        (x1, y1),
                        (x2, y2),
                        tuple(vis_config['box_color']),
                        vis_config['box_thickness']
                    )
                
                # Draw label and confidence
                if vis_config['draw_labels'] or vis_config['draw_confidence']:
                    label_parts = []
                    if vis_config['draw_labels']:
                        label_parts.append(det['class_name'])
                    if vis_config['draw_confidence']:
                        label_parts.append(f"{det['confidence']:.2f}")
                    
                    label = ' '.join(label_parts)
                    
                    # Calculate text size for background
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        vis_config['font_scale'],
                        1
                    )
                    
                    # Draw text background
                    cv2.rectangle(
                        image,
                        (x1, y1 - text_height - baseline - 5),
                        (x1 + text_width, y1),
                        tuple(vis_config['box_color']),
                        -1
                    )
                    
                    # Draw text
                    cv2.putText(
                        image,
                        label,
                        (x1, y1 - baseline - 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        vis_config['font_scale'],
                        tuple(vis_config['text_color']),
                        1
                    )
                
                # Draw center point
                center_x = int(det['center_x'])
                center_y = int(det['center_y'])
                cv2.circle(image, (center_x, center_y), 3, (0, 0, 255), -1)
            
            # Save annotated image
            output_dir = self.config['paths']['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(
                output_dir,
                f"annotated_{os.path.basename(image_path)}"
            )
            cv2.imwrite(output_path, image)
            
        except Exception as e:
            logger.error(f"Error visualizing {image_path}: {e}")
    
    def _save_results(self) -> None:
        """Save detection results to CSV and JSON"""
        if not self.results_data:
            logger.warning("No results to save")
            return
        
        output_dir = self.config['paths']['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        if self.config['paths']['save_csv']:
            csv_path = os.path.join(output_dir, 'detection_results.csv')
            df = pd.DataFrame(self.results_data)
            df.to_csv(csv_path, index=False)
            logger.info(f"Results saved to {csv_path}")
        
        # Save to JSON
        if self.config['paths']['save_json']:
            json_path = os.path.join(output_dir, 'detection_results.json')
            with open(json_path, 'w') as f:
                json.dump(self.results_data, f, indent=2)
            logger.info(f"Results saved to {json_path}")
    
    def get_statistics(self) -> Dict:
        """Calculate detection statistics"""
        if not self.results_data:
            return {}
        
        df = pd.DataFrame(self.results_data)
        
        stats = {
            'total_images': df['image'].nunique(),
            'total_detections': len(df),
            'avg_detections_per_image': len(df) / df['image'].nunique(),
            'avg_confidence': df['confidence'].mean(),
            'avg_cell_width': df['width'].mean(),
            'avg_cell_height': df['height'].mean(),
            'avg_cell_area': df['area'].mean(),
            'min_cell_size': df[['width', 'height']].max(axis=1).min(),
            'max_cell_size': df[['width', 'height']].max(axis=1).max()
        }
        
        return stats


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLO11 Cell Detection for Static Images')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Input directory containing images (overrides config)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output directory for results (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = CellDetector(args.config)
    
    # Override config if command line args provided
    if args.input:
        detector.config['paths']['input_dir'] = args.input
    if args.output:
        detector.config['paths']['output_dir'] = args.output
    
    # Process images
    detector.process_directory()
    
    # Print statistics
    stats = detector.get_statistics()
    if stats:
        print("\n" + "="*50)
        print("DETECTION STATISTICS")
        print("="*50)
        for key, value in stats.items():
            print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        print("="*50)


if __name__ == "__main__":
    main()
