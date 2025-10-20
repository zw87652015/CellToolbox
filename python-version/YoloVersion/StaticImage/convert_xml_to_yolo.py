"""
Convert Pascal VOC XML labels to YOLO format
Converts .xml files created by LabelImg to .txt files for YOLO training
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse


def convert_xml_to_yolo(xml_file, output_dir, class_names):
    """
    Convert single XML file to YOLO format
    
    Args:
        xml_file: Path to XML file
        output_dir: Directory to save .txt file
        class_names: List of class names (e.g., ['cell'])
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Get image size
    size = root.find('size')
    img_width = int(size.find('width').text)
    img_height = int(size.find('height').text)
    
    # Prepare output file
    xml_path = Path(xml_file)
    txt_file = Path(output_dir) / f"{xml_path.stem}.txt"
    
    with open(txt_file, 'w') as f:
        # Process each object
        for obj in root.findall('object'):
            class_name = obj.find('name').text
            
            # Get class ID
            if class_name in class_names:
                class_id = class_names.index(class_name)
            else:
                print(f"Warning: Unknown class '{class_name}' in {xml_file}")
                class_id = 0
            
            # Get bounding box
            bbox = obj.find('bndbox')
            xmin = float(bbox.find('xmin').text)
            ymin = float(bbox.find('ymin').text)
            xmax = float(bbox.find('xmax').text)
            ymax = float(bbox.find('ymax').text)
            
            # Convert to YOLO format (normalized center x, center y, width, height)
            center_x = ((xmin + xmax) / 2) / img_width
            center_y = ((ymin + ymax) / 2) / img_height
            width = (xmax - xmin) / img_width
            height = (ymax - ymin) / img_height
            
            # Write to file
            f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
    
    return txt_file


def convert_directory(xml_dir, output_dir, class_names):
    """
    Convert all XML files in directory to YOLO format
    
    Args:
        xml_dir: Directory containing XML files
        output_dir: Directory to save .txt files
        class_names: List of class names
    """
    xml_dir = Path(xml_dir)
    output_dir = Path(output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all XML files
    xml_files = list(xml_dir.glob('*.xml'))
    
    if not xml_files:
        print(f"No XML files found in {xml_dir}")
        return
    
    print(f"Found {len(xml_files)} XML files")
    print(f"Converting to YOLO format...")
    
    # Convert each file
    converted = 0
    for xml_file in xml_files:
        try:
            txt_file = convert_xml_to_yolo(xml_file, output_dir, class_names)
            converted += 1
            print(f"✓ Converted: {xml_file.name} → {txt_file.name}")
        except Exception as e:
            print(f"✗ Error converting {xml_file.name}: {e}")
    
    print(f"\nConversion complete: {converted}/{len(xml_files)} files")
    print(f"Output directory: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Pascal VOC XML labels to YOLO format'
    )
    
    parser.add_argument(
        '--xml-dir',
        type=str,
        default='training_data/images/train',
        help='Directory containing XML files (default: training_data/images/train)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='training_data/labels/train',
        help='Directory to save YOLO .txt files (default: training_data/labels/train)'
    )
    
    parser.add_argument(
        '--classes',
        type=str,
        nargs='+',
        default=['cell'],
        help='Class names in order (default: cell)'
    )
    
    parser.add_argument(
        '--delete-xml',
        action='store_true',
        help='Delete XML files after conversion'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("XML to YOLO Converter")
    print("="*60)
    print(f"XML directory: {args.xml_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Classes: {args.classes}")
    print("="*60 + "\n")
    
    # Convert files
    convert_directory(args.xml_dir, args.output_dir, args.classes)
    
    # Delete XML files if requested
    if args.delete_xml:
        xml_files = list(Path(args.xml_dir).glob('*.xml'))
        print(f"\nDeleting {len(xml_files)} XML files...")
        for xml_file in xml_files:
            xml_file.unlink()
            print(f"✓ Deleted: {xml_file.name}")
        print("XML files deleted")
    
    print("\n" + "="*60)
    print("Next steps:")
    print("1. Check output files in:", args.output_dir)
    print("2. Repeat for validation images if needed")
    print("3. Run training: python train_model.py --data training_data/dataset.yaml")
    print("="*60)


if __name__ == "__main__":
    main()
