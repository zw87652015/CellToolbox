# Migration Guide - Reorganized Fluorescence Measurement Tools

## Overview

The three fluorescence measurement projects have been reorganized for better maintainability, code reusability, and clarity. This guide will help you navigate the changes.

## What Changed?

### Old Structure
```
ImageProcessor/
├── BatchFluoMeasurement/
├── FluoImagesSingleMeasurement/
└── ManualFluoMeasurement/
```

### New Structure
```
ImageProcessor/
├── shared_utils/                 # 🆕 Common utilities
├── batch_timeseries/             # ✏️ Renamed
├── single_image_analysis/        # ✏️ Renamed
└── manual_bayer_processor/       # ✏️ Renamed
```

## Project Renaming

| Old Name | New Name | Purpose |
|----------|----------|---------|
| `BatchFluoMeasurement` | `batch_timeseries` | Time-series batch processing |
| `FluoImagesSingleMeasurement` | `single_image_analysis` | Single image fluorescence detection |
| `ManualFluoMeasurement` | `manual_bayer_processor` | Interactive Bayer RAW processing |

## Internal Structure Changes

Each project now has a cleaner structure:

```
<project_name>/
├── __init__.py              # Package initialization
├── core/                    # 🆕 Business logic modules
│   ├── __init__.py
│   ├── image_processor.py
│   └── [other core modules]
├── gui/                     # 🆕 User interface modules
│   ├── __init__.py
│   └── main_window.py      # Renamed from batch_fluo_measurement.py/gui_app.py
├── docs/                    # 🆕 Documentation
│   ├── README.md
│   └── [other docs]
├── tests/                   # 🆕 Test files
│   ├── __init__.py
│   └── [test files]
├── main.py                  # 🆕 Entry point
├── cli.py                   # Command-line interface
├── config_manager.py        # Configuration management
└── requirements.txt         # Dependencies
```

## Key Changes

### 1. Shared Utilities Module

**New:** `shared_utils/` contains common code used across projects:
- `roi_selector.py` - ROI selection widget (no more duplication!)
- `image_utils.py` - Common image processing functions
- Easy to maintain and extend

### 2. Core/GUI Separation

**Core modules** (`core/`): Business logic, image processing, algorithms
**GUI modules** (`gui/`): User interface, Tkinter windows, controls

**Benefits:**
- Easier testing of business logic
- Can add alternative interfaces (web, CLI) easily
- Better code organization

### 3. Renamed Main GUI Files

| Old Filename | New Filename | Location |
|--------------|--------------|----------|
| `batch_fluo_measurement.py` | `main_window.py` | `batch_timeseries/gui/` |
| `gui_app.py` | `main_window.py` | `single_image_analysis/gui/` |
| `gui_app.py` | `main_window.py` | `manual_bayer_processor/gui/` |

### 4. Entry Points

Each project now has a standardized `main.py` entry point:

```python
# batch_timeseries/main.py
from gui.main_window import BatchFluoMeasurementApp

def main():
    root = tk.Tk()
    app = BatchFluoMeasurementApp(root)
    root.mainloop()
```

## How to Use After Migration

### Running Applications

**Option 1: Use main.py (Recommended)**
```bash
cd batch_timeseries
python main.py
```

**Option 2: Use CLI**
```bash
cd batch_timeseries
python cli.py --help
```

### Importing Modules

**Old way (in BatchFluoMeasurement):**
```python
from image_processor import ImageProcessor
from file_manager import FileManager
```

**New way (in batch_timeseries):**
```python
from core.image_processor import ImageProcessor
from core.file_manager import FileManager
```

**Using shared utilities:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared_utils"))
from shared_utils import ROISelector
```

## Testing After Migration

### 1. Test Each Project

```bash
# Test batch_timeseries
cd batch_timeseries
python main.py

# Test single_image_analysis
cd single_image_analysis
python main.py

# Test manual_bayer_processor
cd manual_bayer_processor
python main.py
```

### 2. Run Test Suites

```bash
# Batch timeseries tests
cd batch_timeseries/tests
python test_app.py

# Single image tests
cd single_image_analysis/tests
python test_processor.py

# Manual bayer tests
cd manual_bayer_processor/tests
python run_tests.py
```

### 3. Test CLI Interfaces

```bash
# Test batch CLI
cd batch_timeseries
python cli.py --help

# Test single image CLI
cd single_image_analysis
python cli.py --help
```

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'core'`

**Solution:** Make sure you're running from the project directory and using the new import paths:
```bash
cd batch_timeseries  # or other project
python main.py
```

### ROI Selector Not Found

**Problem:** `ModuleNotFoundError: No module named 'shared_utils'`

**Solution:** The shared_utils path should be automatically added. If not, ensure the project structure is correct.

### Old Files Still Present

**Solution:** The old directories (`BatchFluoMeasurement`, etc.) are preserved for safety. After verifying everything works, you can manually delete them:

```bash
# ⚠️ Only after thorough testing!
rm -rf BatchFluoMeasurement
rm -rf FluoImagesSingleMeasurement
rm -rf ManualFluoMeasurement
```

## Configuration Files

Configuration files maintain backward compatibility:
- `config.json` (batch_timeseries)
- `config_manager.py` settings
- `cell_detection_params.json`
- `config.yaml` (manual_bayer_processor)

All existing configurations should work without changes.

## Benefits of New Structure

✅ **No code duplication** - Shared utilities in one place
✅ **Clear organization** - Core/GUI separation
✅ **Better naming** - Project names indicate function
✅ **Easier maintenance** - Related files grouped together
✅ **Scalable** - Easy to add new features or projects
✅ **Professional structure** - Follows Python best practices

## Need Help?

If you encounter issues:
1. Check this migration guide
2. Review the project-specific README in `docs/`
3. Check the old directories for comparison
4. Test with example data to ensure functionality

## Rollback (If Needed)

The old directories are preserved. To rollback:
1. Delete new directories: `batch_timeseries`, `single_image_analysis`, `manual_bayer_processor`, `shared_utils`
2. Continue using old directories: `BatchFluoMeasurement`, etc.

However, we recommend adapting to the new structure for long-term benefits!

---

**Date of Migration:** 2025-10-05
**Migration Script:** `reorganize_projects.py`
