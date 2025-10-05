#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Reorganization Script

This script reorganizes the three fluorescence measurement projects
into a cleaner structure with shared utilities.

Usage:
    python reorganize_projects.py
"""

import shutil
import os
from pathlib import Path
import re

# Define base paths
BASE_DIR = Path(__file__).parent
OLD_BATCH = BASE_DIR / 'BatchFluoMeasurement'
OLD_SINGLE = BASE_DIR / 'FluoImagesSingleMeasurement'
OLD_MANUAL = BASE_DIR / 'ManualFluoMeasurement'

NEW_BATCH = BASE_DIR / 'batch_timeseries'
NEW_SINGLE = BASE_DIR / 'single_image_analysis'
NEW_MANUAL = BASE_DIR / 'manual_bayer_processor'
SHARED_UTILS = BASE_DIR / 'shared_utils'

def copy_and_update_imports(src_file, dst_file, import_updates):
    """
    Copy file and update imports
    
    Args:
        src_file: Source file path
        dst_file: Destination file path
        import_updates: Dict of {old_import: new_import}
    """
    print(f"  Copying: {src_file.name} -> {dst_file}")
    
    # Read source file
    with open(src_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update imports
    for old_import, new_import in import_updates.items():
        content = re.sub(old_import, new_import, content)
    
    # Write to destination
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    with open(dst_file, 'w', encoding='utf-8') as f:
        f.write(content)


def reorganize_batch_timeseries():
    """Reorganize BatchFluoMeasurement -> batch_timeseries"""
    print("\n=== Reorganizing Batch Time-Series Project ===")
    
    # Import updates for batch_timeseries
    import_updates = {
        r'from roi_selector import': 'import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_utils"))\nfrom shared_utils import',
        r'import roi_selector': 'import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_utils"))\nimport shared_utils.roi_selector as roi_selector',
        r'from image_processor import': 'from core.image_processor import',
        r'from file_manager import': 'from core.file_manager import',
        r'from config_manager import': 'from config_manager import',
        r'from cell_detection_config import': 'from core.cell_detection_config import',
        r'from dynamic_preview import': 'from gui.dynamic_preview import',
    }
    
    # Core files
    core_files = ['image_processor.py', 'file_manager.py', 'cell_detection_config.py']
    for filename in core_files:
        src = OLD_BATCH / filename
        if src.exists():
            dst = NEW_BATCH / 'core' / filename
            copy_and_update_imports(src, dst, import_updates)
    
    # GUI files
    gui_mapping = {
        'batch_fluo_measurement.py': 'main_window.py',
        'dynamic_preview.py': 'dynamic_preview.py'
    }
    for old_name, new_name in gui_mapping.items():
        src = OLD_BATCH / old_name
        if src.exists():
            dst = NEW_BATCH / 'gui' / new_name
            copy_and_update_imports(src, dst, import_updates)
    
    # Root files
    root_files = ['cli.py', 'config_manager.py', 'requirements.txt', 
                  'cell_detection_params.json', 'config_template.json']
    for filename in root_files:
        src = OLD_BATCH / filename
        if src.exists():
            dst = NEW_BATCH / filename
            copy_and_update_imports(src, dst, import_updates)
    
    # Documentation
    doc_files = ['README.md', 'Guideline.md', 'INSTALL.md']
    for filename in doc_files:
        src = OLD_BATCH / filename
        if src.exists():
            dst = NEW_BATCH / 'docs' / filename
            shutil.copy2(src, dst)
    
    # Tests
    test_files = ['test_app.py', 'test_minimal.py', 'test_roi_vis.py', 'test_save.py']
    for filename in test_files:
        src = OLD_BATCH / filename
        if src.exists():
            dst = NEW_BATCH / 'tests' / filename
            copy_and_update_imports(src, dst, import_updates)
    
    # Create main.py entry point
    main_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Time-Series Fluorescence Measurement Tool - Main Entry Point
"""

import tkinter as tk
import sys
from pathlib import Path

# Add parent directory to path for shared_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.main_window import BatchFluoMeasurementApp

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = BatchFluoMeasurementApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
'''
    with open(NEW_BATCH / 'main.py', 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    print(f"✓ Batch Time-Series reorganization complete")


def reorganize_single_image():
    """Reorganize FluoImagesSingleMeasurement -> single_image_analysis"""
    print("\n=== Reorganizing Single Image Analysis Project ===")
    
    import_updates = {
        r'from roi_selector import': 'import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_utils"))\nfrom shared_utils import',
        r'import roi_selector': 'import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_utils"))\nimport shared_utils.roi_selector as roi_selector',
        r'from image_processor import': 'from core.image_processor import',
        r'from config_manager import': 'from config_manager import',
    }
    
    # Core files
    src = OLD_SINGLE / 'image_processor.py'
    if src.exists():
        dst = NEW_SINGLE / 'core' / 'image_processor.py'
        copy_and_update_imports(src, dst, import_updates)
    
    # GUI files
    src = OLD_SINGLE / 'gui_app.py'
    if src.exists():
        dst = NEW_SINGLE / 'gui' / 'main_window.py'
        copy_and_update_imports(src, dst, import_updates)
    
    # Root files
    root_files = ['cli.py', 'config_manager.py', 'requirements.txt']
    for filename in root_files:
        src = OLD_SINGLE / filename
        if src.exists():
            dst = NEW_SINGLE / filename
            copy_and_update_imports(src, dst, import_updates)
    
    # Documentation
    doc_files = ['README.md', 'Guideline.md', 'QUICKSTART.md', 'Analyse.md']
    for filename in doc_files:
        src = OLD_SINGLE / filename
        if src.exists():
            dst = NEW_SINGLE / 'docs' / filename
            shutil.copy2(src, dst)
    
    # Tests
    src = OLD_SINGLE / 'test_processor.py'
    if src.exists():
        dst = NEW_SINGLE / 'tests' / 'test_processor.py'
        copy_and_update_imports(src, dst, import_updates)
    
    # Copy existing main.py
    src = OLD_SINGLE / 'main.py'
    if src.exists():
        dst = NEW_SINGLE / 'main.py'
        copy_and_update_imports(src, dst, import_updates)
    
    print(f"✓ Single Image Analysis reorganization complete")


def reorganize_manual_bayer():
    """Reorganize ManualFluoMeasurement -> manual_bayer_processor"""
    print("\n=== Reorganizing Manual Bayer Processor Project ===")
    
    import_updates = {
        r'from image_processor import': 'from core.image_processor import',
    }
    
    # Core files
    src = OLD_MANUAL / 'image_processor.py'
    if src.exists():
        dst = NEW_MANUAL / 'core' / 'image_processor.py'
        copy_and_update_imports(src, dst, import_updates)
    
    # GUI files
    src = OLD_MANUAL / 'gui_app.py'
    if src.exists():
        dst = NEW_MANUAL / 'gui' / 'main_window.py'
        copy_and_update_imports(src, dst, import_updates)
    
    # Root files
    root_files = ['batch_process.py', 'requirements.txt', 'config.yaml']
    for filename in root_files:
        src = OLD_MANUAL / filename
        if src.exists():
            dst = NEW_MANUAL / filename
            copy_and_update_imports(src, dst, import_updates)
    
    # Documentation
    doc_files = ['README.md', 'Guideline.md']
    for filename in doc_files:
        src = OLD_MANUAL / filename
        if src.exists():
            dst = NEW_MANUAL / 'docs' / filename
            shutil.copy2(src, dst)
    
    # Tests
    test_files = ['run_tests.py', 'test_image_processor.py', 'test_image_loading.py']
    for filename in test_files:
        src = OLD_MANUAL / filename
        if src.exists():
            dst = NEW_MANUAL / 'tests' / filename
            copy_and_update_imports(src, dst, import_updates)
    
    # Copy existing main.py
    src = OLD_MANUAL / 'main.py'
    if src.exists():
        dst = NEW_MANUAL / 'main.py'
        copy_and_update_imports(src, dst, import_updates)
    
    print(f"✓ Manual Bayer Processor reorganization complete")


def create_master_readme():
    """Create master README for ImageProcessor"""
    content = '''# Fluorescence Measurement Tools

A collection of specialized tools for fluorescence microscopy image analysis.

## Projects

### 1. Batch Time-Series Analysis (`batch_timeseries/`)
Time-series fluorescence intensity measurement for single-cell tracking over time.

**Features:**
- Automated batch processing of time-series images
- EXIF timestamp-driven time axis
- ROI selection for single-cell analysis
- Offset optimization for cell movement
- 16-bit TIFF support with Bayer pattern processing

**Usage:**
```bash
cd batch_timeseries
python main.py
```

### 2. Single Image Analysis (`single_image_analysis/`)
Fluorescence detection and measurement for single images using white top-hat transform.

**Features:**
- White top-hat transform for background correction
- Adaptive thresholding
- Detects all fluorescent regions
- ROI support
- CSV export of measurements

**Usage:**
```bash
cd single_image_analysis
python main.py
```

### 3. Manual Bayer Processor (`manual_bayer_processor/`)
Interactive step-by-step Bayer RAW image processing tool.

**Features:**
- Manual control over each processing step
- Bayer pattern splitting (RGGB)
- Dark field correction
- Interactive GUI with zoom/pan
- Quality control overlay images

**Usage:**
```bash
cd manual_bayer_processor
python main.py
```

## Shared Utilities

Common functionality is provided by the `shared_utils/` module:
- ROI selection widget
- Image processing utilities
- Configuration management

## Installation

Each project has its own `requirements.txt`. Install dependencies:

```bash
cd <project_directory>
pip install -r requirements.txt
```

## Directory Structure

```
ImageProcessor/
├── shared_utils/           # Common utilities
│   ├── roi_selector.py
│   ├── image_utils.py
│   └── README.md
├── batch_timeseries/       # Time-series analysis
│   ├── core/              # Business logic
│   ├── gui/               # User interface
│   ├── docs/              # Documentation
│   ├── tests/             # Test files
│   └── main.py            # Entry point
├── single_image_analysis/  # Single image tool
│   ├── core/
│   ├── gui/
│   ├── docs/
│   ├── tests/
│   └── main.py
└── manual_bayer_processor/ # Interactive processor
    ├── core/
    ├── gui/
    ├── docs/
    ├── tests/
    └── main.py
```

## Contributing

When adding new features:
1. Follow the established directory structure
2. Use shared utilities when possible
3. Update documentation
4. Add tests for new functionality

## License

[Your License Here]

## Contact

[Your Contact Information]
'''
    
    with open(BASE_DIR / 'README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✓ Created master README.md")


def main():
    """Main reorganization function"""
    print("=" * 60)
    print("  Fluorescence Measurement Tools Reorganization")
    print("=" * 60)
    
    try:
        # Check if old directories exist
        if not OLD_BATCH.exists():
            print(f"⚠ Warning: {OLD_BATCH} not found")
        if not OLD_SINGLE.exists():
            print(f"⚠ Warning: {OLD_SINGLE} not found")
        if not OLD_MANUAL.exists():
            print(f"⚠ Warning: {OLD_MANUAL} not found")
        
        # Reorganize each project
        if OLD_BATCH.exists():
            reorganize_batch_timeseries()
        
        if OLD_SINGLE.exists():
            reorganize_single_image()
        
        if OLD_MANUAL.exists():
            reorganize_manual_bayer()
        
        # Create master README
        create_master_readme()
        
        print("\n" + "=" * 60)
        print("  ✓ Reorganization Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Test each project's main.py entry point")
        print("2. Verify imports are working correctly")
        print("3. Run test suites in each project")
        print("4. Update any external documentation")
        print("\nOld directories are preserved. Remove them manually after verification:")
        print(f"  - {OLD_BATCH}")
        print(f"  - {OLD_SINGLE}")
        print(f"  - {OLD_MANUAL}")
        
    except Exception as e:
        print(f"\n✗ Error during reorganization: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
