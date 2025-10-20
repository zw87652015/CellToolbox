"""
YOLO11 Custom Model Training Script
Train your own cell detection model on custom data
"""

import os
from pathlib import Path
from ultralytics import YOLO
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CellModelTrainer:
    """Train custom YOLO11 model for cell detection"""
    
    def __init__(self, dataset_yaml: str = "training_data/dataset.yaml"):
        """
        Initialize trainer
        
        Args:
            dataset_yaml: Path to dataset configuration file
        """
        self.dataset_yaml = dataset_yaml
        self.verify_dataset()
    
    def verify_dataset(self):
        """Verify dataset structure and files"""
        logger.info("Verifying dataset structure...")
        
        if not os.path.exists(self.dataset_yaml):
            raise FileNotFoundError(
                f"Dataset config not found: {self.dataset_yaml}\n"
                "Please create training_data/dataset.yaml"
            )
        
        # Load dataset config
        with open(self.dataset_yaml, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required fields
        required = ['path', 'train', 'val', 'nc', 'names']
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required field in dataset.yaml: {field}")
        
        # Verify directories exist
        base_path = Path(config['path'])
        train_path = base_path / config['train']
        val_path = base_path / config['val']
        
        if not train_path.exists():
            raise FileNotFoundError(f"Training images not found: {train_path}")
        if not val_path.exists():
            raise FileNotFoundError(f"Validation images not found: {val_path}")
        
        # Count images
        train_images = list(train_path.glob('*.jpg')) + list(train_path.glob('*.png'))
        val_images = list(val_path.glob('*.jpg')) + list(val_path.glob('*.png'))
        
        logger.info(f"✓ Found {len(train_images)} training images")
        logger.info(f"✓ Found {len(val_images)} validation images")
        
        if len(train_images) == 0:
            raise ValueError("No training images found!")
        if len(val_images) == 0:
            raise ValueError("No validation images found!")
        
        # Check for label files
        labels_path = base_path / 'labels' / 'train'
        if labels_path.exists():
            label_files = list(labels_path.glob('*.txt'))
            logger.info(f"✓ Found {len(label_files)} training label files")
            
            if len(label_files) == 0:
                logger.warning("⚠ No label files found! Make sure to create labels.")
        
        logger.info("✓ Dataset verification complete")
    
    def train(
        self,
        model_size: str = 'n',
        epochs: int = 100,
        batch_size: int = 16,
        image_size: int = 640,
        device: str = 'cpu',
        project: str = 'trained_models',
        name: str = 'cell_detection',
        resume: bool = False,
        **kwargs
    ):
        """
        Train the model
        
        Args:
            model_size: YOLO11 model size (n/s/m/l/x)
            epochs: Number of training epochs
            batch_size: Batch size (reduce if out of memory)
            image_size: Input image size
            device: 'cpu' or 'cuda'
            project: Project folder for saving results
            name: Experiment name
            resume: Resume from last checkpoint
            **kwargs: Additional training arguments
        """
        logger.info("="*60)
        logger.info("Starting YOLO11 Model Training")
        logger.info("="*60)
        
        # Load pretrained model
        model_name = f'yolo11{model_size}.pt'
        logger.info(f"Loading base model: {model_name}")
        model = YOLO(model_name)
        
        # Training parameters
        logger.info(f"\nTraining Configuration:")
        logger.info(f"  Dataset: {self.dataset_yaml}")
        logger.info(f"  Model: YOLO11{model_size}")
        logger.info(f"  Epochs: {epochs}")
        logger.info(f"  Batch size: {batch_size}")
        logger.info(f"  Image size: {image_size}")
        logger.info(f"  Device: {device}")
        logger.info(f"  Output: {project}/{name}")
        
        # Start training
        logger.info("\n" + "="*60)
        logger.info("Training started...")
        logger.info("="*60 + "\n")
        
        results = model.train(
            data=self.dataset_yaml,
            epochs=epochs,
            batch=batch_size,
            imgsz=image_size,
            device=device,
            project=project,
            name=name,
            resume=resume,
            patience=50,  # Early stopping patience
            save=True,
            save_period=10,  # Save checkpoint every 10 epochs
            plots=True,  # Generate training plots
            **kwargs
        )
        
        logger.info("\n" + "="*60)
        logger.info("Training Complete!")
        logger.info("="*60)
        
        # Get best model path
        best_model = Path(project) / name / 'weights' / 'best.pt'
        last_model = Path(project) / name / 'weights' / 'last.pt'
        
        logger.info(f"\n✓ Best model saved to: {best_model}")
        logger.info(f"✓ Last model saved to: {last_model}")
        
        # Validation results
        if hasattr(results, 'results_dict'):
            logger.info("\nValidation Metrics:")
            metrics = results.results_dict
            if 'metrics/mAP50(B)' in metrics:
                logger.info(f"  mAP@0.5: {metrics['metrics/mAP50(B)']:.4f}")
            if 'metrics/mAP50-95(B)' in metrics:
                logger.info(f"  mAP@0.5:0.95: {metrics['metrics/mAP50-95(B)']:.4f}")
        
        logger.info("\nNext steps:")
        logger.info(f"1. Review training plots in: {project}/{name}/")
        logger.info(f"2. Test the model: python test_trained_model.py")
        logger.info(f"3. Update config.yaml to use: {best_model}")
        
        return results, str(best_model)
    
    def validate(self, model_path: str):
        """
        Validate trained model
        
        Args:
            model_path: Path to trained model weights
        """
        logger.info(f"Validating model: {model_path}")
        
        model = YOLO(model_path)
        results = model.val(data=self.dataset_yaml)
        
        logger.info("\nValidation Results:")
        logger.info(f"  mAP@0.5: {results.box.map50:.4f}")
        logger.info(f"  mAP@0.5:0.95: {results.box.map:.4f}")
        logger.info(f"  Precision: {results.box.mp:.4f}")
        logger.info(f"  Recall: {results.box.mr:.4f}")
        
        return results


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train YOLO11 Cell Detection Model')
    
    # Dataset
    parser.add_argument(
        '--data',
        type=str,
        default='training_data/dataset.yaml',
        help='Path to dataset.yaml'
    )
    
    # Model
    parser.add_argument(
        '--model',
        type=str,
        default='n',
        choices=['n', 's', 'm', 'l', 'x'],
        help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)'
    )
    
    # Training parameters
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of training epochs'
    )
    
    parser.add_argument(
        '--batch',
        type=int,
        default=16,
        help='Batch size (reduce if out of memory)'
    )
    
    parser.add_argument(
        '--imgsz',
        type=int,
        default=640,
        help='Input image size'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        help='Device: cpu, cuda, cuda:0, etc.'
    )
    
    # Output
    parser.add_argument(
        '--project',
        type=str,
        default='trained_models',
        help='Project folder for saving results'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default='cell_detection',
        help='Experiment name'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume training from last checkpoint'
    )
    
    # Validation only
    parser.add_argument(
        '--validate',
        type=str,
        default=None,
        help='Validate model instead of training (provide model path)'
    )
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = CellModelTrainer(args.data)
    
    if args.validate:
        # Validation mode
        trainer.validate(args.validate)
    else:
        # Training mode
        results, best_model = trainer.train(
            model_size=args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            image_size=args.imgsz,
            device=args.device,
            project=args.project,
            name=args.name,
            resume=args.resume
        )
        
        print("\n" + "="*60)
        print("TRAINING SUMMARY")
        print("="*60)
        print(f"Best model: {best_model}")
        print(f"Training plots: {args.project}/{args.name}/")
        print("\nTo use this model for detection:")
        print(f"1. Edit config.yaml")
        print(f"2. Set: custom_weights: '{best_model}'")
        print(f"3. Run: python cell_detector.py")
        print("="*60)


if __name__ == "__main__":
    main()
