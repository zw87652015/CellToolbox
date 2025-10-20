"""
Test your trained YOLO11 model on sample images
"""

import os
import cv2
from pathlib import Path
from ultralytics import YOLO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_model(
    model_path: str,
    test_images_dir: str = "training_data/images/test",
    output_dir: str = "test_results",
    confidence: float = 0.25
):
    """
    Test trained model on images
    
    Args:
        model_path: Path to trained model weights (.pt file)
        test_images_dir: Directory containing test images
        output_dir: Directory to save results
        confidence: Confidence threshold
    """
    logger.info("="*60)
    logger.info("Testing Trained Model")
    logger.info("="*60)
    
    # Check model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Load model
    logger.info(f"Loading model: {model_path}")
    model = YOLO(model_path)
    
    # Get test images
    test_path = Path(test_images_dir)
    if not test_path.exists():
        logger.warning(f"Test directory not found: {test_images_dir}")
        logger.info("Using validation images instead...")
        test_path = Path("training_data/images/val")
    
    image_files = list(test_path.glob('*.jpg')) + list(test_path.glob('*.png'))
    
    if not image_files:
        raise ValueError(f"No images found in {test_path}")
    
    logger.info(f"Found {len(image_files)} test images")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Test each image
    total_detections = 0
    
    for i, image_path in enumerate(image_files, 1):
        logger.info(f"\nProcessing {i}/{len(image_files)}: {image_path.name}")
        
        # Run inference
        results = model.predict(
            source=str(image_path),
            conf=confidence,
            save=False,
            verbose=False
        )
        
        result = results[0]
        
        # Count detections
        num_detections = len(result.boxes) if result.boxes is not None else 0
        total_detections += num_detections
        logger.info(f"  Detected {num_detections} cells")
        
        # Visualize results
        annotated = result.plot()
        
        # Save annotated image
        output_path = os.path.join(output_dir, f"test_{image_path.name}")
        cv2.imwrite(output_path, annotated)
        logger.info(f"  Saved to: {output_path}")
        
        # Print detection details
        if result.boxes is not None and len(result.boxes) > 0:
            for j, box in enumerate(result.boxes):
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                cls_name = result.names[cls]
                logger.info(f"    Cell {j+1}: {cls_name} (conf: {conf:.2f})")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Total images tested: {len(image_files)}")
    logger.info(f"Total cells detected: {total_detections}")
    logger.info(f"Average cells per image: {total_detections/len(image_files):.2f}")
    logger.info(f"Results saved to: {output_dir}/")
    logger.info("="*60)


def compare_models(
    model1_path: str,
    model2_path: str,
    test_image: str,
    confidence: float = 0.25
):
    """
    Compare two models side by side
    
    Args:
        model1_path: Path to first model
        model2_path: Path to second model
        test_image: Path to test image
        confidence: Confidence threshold
    """
    logger.info("Comparing models...")
    
    # Load models
    model1 = YOLO(model1_path)
    model2 = YOLO(model2_path)
    
    # Run inference
    results1 = model1.predict(test_image, conf=confidence, verbose=False)
    results2 = model2.predict(test_image, conf=confidence, verbose=False)
    
    # Get annotated images
    img1 = results1[0].plot()
    img2 = results2[0].plot()
    
    # Count detections
    count1 = len(results1[0].boxes) if results1[0].boxes is not None else 0
    count2 = len(results2[0].boxes) if results2[0].boxes is not None else 0
    
    logger.info(f"\nModel 1 ({model1_path}): {count1} detections")
    logger.info(f"Model 2 ({model2_path}): {count2} detections")
    
    # Save comparison
    comparison = cv2.hconcat([img1, img2])
    cv2.imwrite("model_comparison.jpg", comparison)
    logger.info("Comparison saved to: model_comparison.jpg")


def main():
    """Main testing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Trained YOLO11 Model')
    
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to trained model (.pt file)'
    )
    
    parser.add_argument(
        '--images',
        type=str,
        default='training_data/images/test',
        help='Directory containing test images'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='test_results',
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--conf',
        type=float,
        default=0.25,
        help='Confidence threshold'
    )
    
    parser.add_argument(
        '--compare',
        type=str,
        default=None,
        help='Compare with another model (provide path)'
    )
    
    parser.add_argument(
        '--test-image',
        type=str,
        default=None,
        help='Single test image for comparison'
    )
    
    args = parser.parse_args()
    
    if args.compare and args.test_image:
        # Comparison mode
        compare_models(args.model, args.compare, args.test_image, args.conf)
    else:
        # Normal testing mode
        test_model(args.model, args.images, args.output, args.conf)


if __name__ == "__main__":
    main()
