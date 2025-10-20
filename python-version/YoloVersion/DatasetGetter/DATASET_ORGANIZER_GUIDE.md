# Dataset Organizer - Guide

## Purpose

Automatically finds JPG images and their corresponding TXT label files, then organizes them into a clean YOLO-ready directory structure.

## Quick Start

```bash
python dataset_organizer.py
```

## Problem It Solves

**Before:**
```
messy_folder/
├── subfolder1/
│   ├── image001.jpg
│   ├── image001.txt
│   └── image002.jpg  (no label!)
├── subfolder2/
│   ├── image003.jpg
│   ├── image003.txt
│   └── random.txt  (no image!)
└── image004.jpg
    image004.txt
```

**After:**
```
organized/
├── images/
│   ├── train/
│   │   ├── image001.jpg
│   │   ├── image003.jpg
│   │   └── ...
│   └── val/
│       └── image004.jpg
└── labels/
    ├── train/
    │   ├── image001.txt
    │   ├── image003.txt
    │   └── ...
    └── val/
        └── image004.txt
```

## Workflow

### 1. Select Directories

**Source Directory:**
- Where your scattered images/labels are
- Can search subdirectories recursively

**Output Directory:**
- Where organized dataset will be created
- Creates YOLO-standard structure

### 2. Configure Options

**Search Mode:**
- ✅ **Recursive**: Search all subdirectories
- ❌ **Non-recursive**: Only search top level

**File Mode:**
- **Copy**: Keep original files (safer)
- **Move**: Remove originals (saves space)

**Split Mode:**
- **No split**: All files in one folder
- **Train/Val split**: Automatically split dataset
  - Default: 80% train / 20% val
  - Configurable: 0-50% validation

### 3. Scan for Pairs

Click **"1. Scan for Pairs"**

**What it does:**
- Finds all .jpg files
- Finds all .txt files
- Matches by filename
- Reports orphans (files without pairs)

**Output:**
```
=== Scanning for Image-Label Pairs ===
Found 850 matching pairs
Found 12 images without labels
Found 3 labels without images

Sample pairs:
  1. cell_001
  2. cell_002
  3. cell_003
  ...
```

### 4. Organize Dataset

Click **"2. Organize Dataset"**

**Confirmation dialog shows:**
- Number of pairs to organize
- Output location
- Mode (copy/move)
- Split configuration

**Processing:**
- Creates directory structure
- Copies/moves files
- Handles duplicates
- Saves metadata

## Output Structures

### Without Split

```
output/
├── images/
│   ├── image001.jpg
│   ├── image002.jpg
│   └── ...
├── labels/
│   ├── image001.txt
│   ├── image002.txt
│   └── ...
└── organization_metadata.json
```

### With Train/Val Split (80/20)

```
output/
├── images/
│   ├── train/
│   │   ├── image001.jpg
│   │   ├── image002.jpg
│   │   └── ... (680 images)
│   └── val/
│       ├── image003.jpg
│       └── ... (170 images)
├── labels/
│   ├── train/
│   │   ├── image001.txt
│   │   ├── image002.txt
│   │   └── ... (680 labels)
│   └── val/
│       ├── image003.txt
│       └── ... (170 labels)
└── organization_metadata.json
```

## Features

### 1. Automatic Pair Matching

**Matches by filename:**
```
cell_001.jpg  ←→  cell_001.txt  ✅ Pair
cell_002.jpg  ←→  (no txt)      ❌ Orphan image
(no jpg)      ←→  cell_003.txt  ❌ Orphan label
```

### 2. Recursive Search

**Searches all subdirectories:**
```
source/
├── batch1/
│   └── image001.jpg + .txt
├── batch2/
│   └── image002.jpg + .txt
└── batch3/
    └── image003.jpg + .txt

All found and organized! ✅
```

### 3. Duplicate Handling

**If filename exists:**
```
image001.jpg  → image001.jpg
image001.jpg  → image001_1.jpg  (auto-renamed)
image001.jpg  → image001_2.jpg
```

### 4. Orphan Detection

**Reports files without pairs:**
- Images without labels
- Labels without images
- These are skipped (not organized)

### 5. Metadata Export

**JSON file contains:**
```json
{
  "timestamp": "2025-01-20 16:08:00",
  "source_directory": "e:/messy_data",
  "output_directory": "e:/organized",
  "total_pairs": 850,
  "orphan_images": 12,
  "orphan_labels": 3,
  "mode": "copy",
  "split": true,
  "val_percent": 20
}
```

## Use Cases

### 1. Organize Scattered Files

**Problem:** Files in multiple folders
**Solution:** Recursive scan + organize

### 2. Prepare for YOLO Training

**Problem:** Need train/val split
**Solution:** Enable split option (80/20)

### 3. Clean Up Dataset

**Problem:** Mixed with orphan files
**Solution:** Scan shows orphans, organizes only pairs

### 4. Merge Multiple Sources

**Problem:** Data from different sessions
**Solution:** Point to parent folder, recursive scan

## Best Practices

### 1. Always Scan First

**Before organizing:**
- ✅ Scan to see what will be organized
- ✅ Check orphan count
- ✅ Verify pair count matches expectation

### 2. Use Copy Mode First

**Safer approach:**
- ✅ Copy files first
- ✅ Verify organized dataset
- ✅ Then delete originals manually if needed

### 3. Check Orphans

**If many orphans:**
- ❓ Are labels missing?
- ❓ Are filenames mismatched?
- ❓ Are files in wrong format?

### 4. Validate Output

**After organizing:**
- ✅ Check image count
- ✅ Check label count
- ✅ Verify train/val split ratio
- ✅ Open few samples to verify

## Troubleshooting

### "No pairs found"

**Possible causes:**
- ❌ Wrong source directory
- ❌ Files not named .jpg or .txt
- ❌ Filenames don't match
- ❌ Need to enable recursive search

**Solutions:**
- ✅ Check file extensions
- ✅ Enable recursive search
- ✅ Verify filename matching

### "Many orphan images"

**Cause:** Images without labels

**Solutions:**
- Label them using dataset_creator.py
- Or exclude from training

### "Many orphan labels"

**Cause:** Labels without images

**Solutions:**
- Check if images were deleted
- Check filename mismatches
- Remove orphan labels

## Integration with Training

### After Organization

**Your dataset is ready:**
```
organized/
├── images/train/  ← Point YOLO here
├── images/val/
├── labels/train/
└── labels/val/
```

**Create dataset.yaml:**
```yaml
path: /path/to/organized
train: images/train
val: images/val

nc: 1
names: ['cell']
```

**Train YOLO:**
```bash
python train_model.py --data dataset.yaml
```

## Statistics

**Processing speed:**
- ~1000 pairs/second (copy mode)
- ~2000 pairs/second (move mode)

**For 1000 pairs:**
- Scan: <1 second
- Organize: 1-2 seconds

## Summary

**Dataset Organizer helps you:**
1. ✅ Find scattered image-label pairs
2. ✅ Organize into YOLO structure
3. ✅ Auto-split train/val
4. ✅ Handle duplicates
5. ✅ Detect orphan files
6. ✅ Ready for training

**Result:** Clean, organized dataset in seconds! 🎯
