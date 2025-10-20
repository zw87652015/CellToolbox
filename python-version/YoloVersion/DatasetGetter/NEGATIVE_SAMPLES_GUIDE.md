# Negative Sample Creator - Guide

## Purpose

This tool creates **negative samples** (background regions with no cells) for YOLO training. Negative samples help the model learn what is **NOT** a cell, reducing false positives.

## Why Negative Samples?

**Problem:**
- YOLO may detect background noise as cells
- False positives in empty regions
- Poor generalization to different backgrounds

**Solution:**
- Train with negative samples (empty regions)
- Model learns to ignore background
- Improved precision and accuracy

## Usage

### Quick Start

```bash
python negative_sample_creator.py
```

### Workflow

1. **Load Image**
   - Click "Load Image"
   - Select an image with background regions

2. **Draw ROI**
   - Drag mouse on image to draw rectangle
   - ROI defines the search area for patches
   - Choose regions WITHOUT cells

3. **Set Parameters**
   - **Number of patches**: 5 (default)
   - **Min patch size**: 100 pixels
   - **Max patch size**: 400 pixels

4. **Generate Patches**
   - Click "Generate Patches"
   - Tool randomly selects regions within ROI
   - Patches shown in magenta

5. **Review**
   - Check that patches don't contain cells
   - If needed, click "Clear Patches" and regenerate

6. **Save**
   - Click "Save Negative Samples"
   - Creates image patches + empty label files

## Output Structure

```
negative_samples/
├── image001_neg_1.jpg         # Patch 1 image
├── image001_neg_1.txt         # Empty label (no cells)
├── image001_neg_2.jpg         # Patch 2 image
├── image001_neg_2.txt         # Empty label
├── image001_neg_3.jpg
├── image001_neg_3.txt
├── image001_neg_4.jpg
├── image001_neg_4.txt
├── image001_neg_5.jpg
├── image001_neg_5.txt
└── image001_negative_metadata.json
```

## Label Files

**Empty .txt files** tell YOLO "no objects in this image"

```
# image001_neg_1.txt
(empty file - 0 bytes)
```

This is **valid YOLO format** for negative samples!

## Parameters

### Number of Patches
- **Default**: 5
- **Range**: 1-20
- **Recommendation**: 5-10 per image

### Patch Size
- **Min**: 100 pixels (not too small)
- **Max**: 400 pixels (not too large)
- **Why**: Similar size to typical cell detection windows

### ROI Selection
- **Best practice**: Select background-only regions
- **Avoid**: Regions with cells or cell fragments
- **Tip**: Use empty corners or clear background areas

## Integration with YOLO Training

### 1. Organize Files

**Copy to training directory:**
```
training_data/
├── images/
│   ├── train/
│   │   ├── cell_001.jpg          # Positive samples (with cells)
│   │   ├── cell_002.jpg
│   │   ├── image001_neg_1.jpg    # Negative samples (no cells)
│   │   ├── image001_neg_2.jpg
│   │   └── ...
│   └── val/
│       └── ...
└── labels/
    ├── train/
    │   ├── cell_001.txt          # Has labels
    │   ├── cell_002.txt          # Has labels
    │   ├── image001_neg_1.txt    # Empty (no labels)
    │   ├── image001_neg_2.txt    # Empty
    │   └── ...
    └── val/
        └── ...
```

### 2. Training Ratio

**Recommended ratio:**
- **Positive samples** (with cells): 80-90%
- **Negative samples** (no cells): 10-20%

**Example for 1000 images:**
- 850 images with cells
- 150 negative patches

### 3. Training Benefits

✅ **Reduced false positives**
✅ **Better background discrimination**
✅ **Improved precision**
✅ **More robust model**

## Best Practices

### 1. Source Images

**Good sources for negative samples:**
- Images with large empty areas
- Background-only regions
- Clear buffer zones
- Empty microscope fields

**Avoid:**
- Regions with partial cells
- Blurry or ambiguous areas
- Artifacts that look like cells

### 2. ROI Selection

**Tips:**
- Draw ROI in clearly empty regions
- Avoid edges of cells
- Use multiple images for variety
- Include different background types

### 3. Patch Generation

**Strategy:**
- Generate 5-10 patches per source image
- Use different source images
- Vary patch sizes
- Ensure no overlap with cells

### 4. Quality Control

**Before saving:**
- ✅ Check each patch visually
- ✅ Confirm no cells present
- ✅ Verify patch sizes are reasonable
- ✅ Ensure good background representation

## Example Workflow

### Creating 100 Negative Samples

```
1. Select 10-20 source images with empty regions

2. For each image:
   - Load image
   - Draw ROI in empty area
   - Generate 5-10 patches
   - Save negative samples

3. Result: 50-200 negative patches

4. Copy to training_data/images/train/
5. Copy empty .txt files to training_data/labels/train/

6. Train YOLO with mixed dataset
```

## Visual Indicators

**In the tool:**
- **Green rectangle**: ROI (search area)
- **Magenta rectangles**: Generated patches
- **Yellow rectangle**: Selected patch

## Keyboard Shortcuts

Currently none - use mouse and buttons.

## Troubleshooting

### "No patches generated"
- **Cause**: ROI too small or patch size too large
- **Solution**: Increase ROI size or decrease max patch size

### "Patches overlap"
- **Cause**: Normal - some overlap allowed (<50%)
- **Solution**: Regenerate if too much overlap

### "Patches contain cells"
- **Cause**: ROI includes cell regions
- **Solution**: Redraw ROI in empty area, regenerate

## Advanced Usage

### Multiple Background Types

**Create variety:**
```
1. Empty microscope field → 10 patches
2. Buffer solution → 10 patches
3. Slide edges → 10 patches
4. Out-of-focus regions → 10 patches
```

**Total: 40 diverse negative samples**

### Batch Processing

**For multiple images:**
```python
# Process 20 images
for each image:
    1. Load
    2. Draw ROI
    3. Generate 5 patches
    4. Save

# Result: 100 negative samples
```

## Metadata

**JSON file contains:**
```json
{
  "source_image": "path/to/image.jpg",
  "roi": [x, y, width, height],
  "num_patches": 5,
  "patches": [
    {"id": 1, "x": 100, "y": 200, "width": 150, "height": 180},
    ...
  ],
  "purpose": "negative_samples",
  "description": "Background regions with no cells"
}
```

## Summary

**Negative Sample Creator helps you:**
1. ✅ Extract background regions automatically
2. ✅ Generate empty YOLO labels
3. ✅ Improve model training
4. ✅ Reduce false positives
5. ✅ Create balanced datasets

**Result:** Better YOLO model that knows what is NOT a cell! 🎯
