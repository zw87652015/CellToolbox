#!/usr/bin/env python3
"""
Batch Processing Script for ImageProcessor
Process multiple images in batch mode from command line
"""

import os
import sys
import argparse
import glob
from pathlib import Path
from core.image_processor import ImageProcessor


def process_directory(input_dir, output_dir, dark_field_path=None, pattern="*.tif"):
    """Process all images in a directory"""
    
    # Initialize processor
    processor = ImageProcessor()
    
    # Find all matching image files
    search_pattern = os.path.join(input_dir, pattern)
    image_files = glob.glob(search_pattern)
    
    if not image_files:
        print(f"No images found matching pattern: {search_pattern}")
        return
    
    print(f"Found {len(image_files)} images to process")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each image
    results_summary = []
    
    for i, image_path in enumerate(image_files, 1):
        print(f"\nProcessing {i}/{len(image_files)}: {os.path.basename(image_path)}")
        
        try:
            # Process image
            results = processor.process_image(image_path, dark_field_path)
            
            # Save results
            base_filename = os.path.splitext(os.path.basename(image_path))[0]
            processor.save_results(output_dir, base_filename)
            
            # Store summary
            cell_count = results['cell_count']
            avg_intensity = 0
            if results['cell_data']:
                avg_intensity = sum(cell['mean_intensity'] for cell in results['cell_data']) / len(results['cell_data'])
            
            results_summary.append({
                'filename': os.path.basename(image_path),
                'cell_count': cell_count,
                'avg_intensity': avg_intensity
            })
            
            print(f"  -> Detected {cell_count} cells, avg intensity: {avg_intensity:.2f}")
            
        except Exception as e:
            print(f"  -> ERROR: {str(e)}")
            results_summary.append({
                'filename': os.path.basename(image_path),
                'cell_count': 0,
                'avg_intensity': 0,
                'error': str(e)
            })
    
    # Save batch summary
    save_batch_summary(results_summary, output_dir)
    
    print(f"\nBatch processing completed. Results saved to: {output_dir}")


def save_batch_summary(results_summary, output_dir):
    """Save batch processing summary to CSV"""
    
    summary_path = os.path.join(output_dir, "batch_summary.csv")
    
    with open(summary_path, 'w', newline='') as f:
        f.write("filename,cell_count,avg_intensity,status\n")
        
        for result in results_summary:
            filename = result['filename']
            cell_count = result['cell_count']
            avg_intensity = result['avg_intensity']
            status = "ERROR" if 'error' in result else "SUCCESS"
            
            f.write(f"{filename},{cell_count},{avg_intensity:.2f},{status}\n")
    
    print(f"Batch summary saved to: {summary_path}")


def main():
    """Main entry point for batch processing"""
    
    parser = argparse.ArgumentParser(
        description="Batch process Bayer RAW images for cell detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all TIFF files in a directory
  python batch_process.py input_dir output_dir
  
  # Process with dark field correction
  python batch_process.py input_dir output_dir --dark-field dark.tif
  
  # Process specific pattern
  python batch_process.py input_dir output_dir --pattern "sample_*.tiff"
  
  # Process single image
  python batch_process.py image.tif output_dir --single
        """
    )
    
    parser.add_argument('input', help='Input directory or single image file')
    parser.add_argument('output', help='Output directory for results')
    parser.add_argument('--dark-field', '-d', help='Dark field image path (optional)')
    parser.add_argument('--pattern', '-p', default='*.tif', 
                       help='File pattern to match (default: *.tif)')
    parser.add_argument('--single', '-s', action='store_true',
                       help='Process single image instead of directory')
    parser.add_argument('--config', '-c', help='Custom config file path')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.input):
        print(f"Error: Input path does not exist: {args.input}")
        sys.exit(1)
    
    if args.dark_field and not os.path.exists(args.dark_field):
        print(f"Error: Dark field image does not exist: {args.dark_field}")
        sys.exit(1)
    
    try:
        if args.single:
            # Process single image
            if not os.path.isfile(args.input):
                print(f"Error: Input is not a file: {args.input}")
                sys.exit(1)
            
            # Initialize processor
            config_path = args.config if args.config else "config.yaml"
            processor = ImageProcessor(config_path)
            
            # Process image
            print(f"Processing single image: {args.input}")
            results = processor.process_image(args.input, args.dark_field)
            
            # Save results
            os.makedirs(args.output, exist_ok=True)
            base_filename = os.path.splitext(os.path.basename(args.input))[0]
            processor.save_results(args.output, base_filename)
            
            print(f"Processing completed: {results['cell_count']} cells detected")
            
        else:
            # Process directory
            if not os.path.isdir(args.input):
                print(f"Error: Input is not a directory: {args.input}")
                sys.exit(1)
            
            process_directory(args.input, args.output, args.dark_field, args.pattern)
    
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
