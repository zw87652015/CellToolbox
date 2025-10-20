# YOLO Dataset Creator - Cell Detection

A tool for creating YOLO training datasets from JPG images by detecting cells within user-defined ROI regions and generating YOLO format labels.

## Tools

### 1. Dataset Creator (`dataset_creator.py`)
Main tool for creating YOLO training datasets from cell images.

### 2. Negative Sample Creator (`negative_sample_creator.py`)
Tool for creating negative samples (background regions with no cells) to improve model training.

### 3. Dataset Organizer (`dataset_organizer.py`)
Tool for collecting and organizing scattered image-label pairs into YOLO-ready directory structure.

## Features

- **Interactive ROI Selection**: Draw rectangle regions to focus cell detection
- **Advanced Cell Detection**: Uses Kirsch edge detection algorithm (same as ToupCam SingleDroplet)
- **Size Filtering**: Filter cells by bounding box dimensions (min/max size)
- **BBox Expansion**: Optionally expand bounding boxes for better YOLO training
- **YOLO Format Output**: Generates standard YOLO labels with normalized coordinates
- **Annotated Visualization**: Creates annotated images showing detected bounding boxes
- **Keyboard Shortcuts**: Fast navigation and saving with keyboard
- **Manual Labeling**: Draw, edit, and delete bounding boxes manually
- **Zoom Support**: Zoom in/out for precise labeling
- **Negative Samples**: Generate background patches for better training
- **Metadata Export**: JSON metadata with detection parameters and statistics

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Dataset Creator

**Run the main tool:**
```bash
python dataset_creator.py
```

#### Single Image Workflow

1. **Launch the application**:
   ```bash
   python dataset_creator.py
   ```

2. **Load an image**: Click "Load Image" and select a JPG/PNG file

3. **Adjust parameters**:
   - Size filter: 20-200 pixels (min-max)
   - BBox expansion: 10% (0-50%)

4. **Detect cells**:
   - **"Detect Cells (ROI)"**: Draw ROI first, then detect in selected region
   - **"Detect Cells (Whole Image)"**: Detect in entire image without ROI

5. **Save YOLO labels**: Click "Save YOLO Labels" or press **S** key

### Keyboard Shortcuts

| Key | Action | Notes |
|-----|--------|-------|
| **R** | Detect cells | Run detection on whole image |
| **S** | Save YOLO labels | Saves current image labels |
| **Q** | Copy from previous | Copy boxes from previous frame + enable group drag |
| **E** | Toggle Group Drag | Enable/disable group drag mode |
| **D** | Next image | Navigate forward |
| **A** | Previous image | Navigate backward |
| **Right Arrow** | Next image | Alternative to D |
| **Left Arrow** | Previous image | Alternative to A |
| **M** | Toggle Manual Mode | Switch between ROI and manual mode |
| **Delete** | Delete selected box | Click box first to select |
| **Mouse Wheel** | Zoom in/out | Scroll to zoom (50%-500%) |
| **+** / **=** | Zoom in | Keyboard zoom in |
| **-** | Zoom out | Keyboard zoom out |
| **0** | Reset zoom | Back to 100% |

**Important Notes:**
- **Manual boxes are cleared** when navigating to next/previous image
- **Delete key only** deletes boxes (not D key)
- **Save before navigating** if you want to keep manual boxes

**Ultra-Fast Workflow:** Load image → **R** (detect) → **S** (save) → **D** (next) → Repeat

**Video Frame Workflow:** Load frame → **R** (detect) → **S** (save) → **D** (next) → **Q** (copy) → Drag to shift → **S** (save) → **D** (next) → Repeat

**Manual Group Drag:** Load image → **R** (detect) → **E** (enable drag) → Click box → Drag → **E** (disable) → **S** (save)

**All with left hand (WASD + R + Q + E)!** ⌨️

### Video Frame Labeling (Q Key + Group Drag Button)

**Perfect for MP4-exported image sequences** where cells shift slightly between frames:

**Workflow:**
1. **Label first frame**: Detect cells normally (R key or button)
2. **Save**: Press **S**
3. **Next frame**: Press **D**
4. **Copy boxes**: Press **Q** - copies ALL boxes from previous frame
5. **Group drag enabled**: Button shows "Group Drag: ON"
6. **Drag boxes**: Click and drag anywhere to shift all boxes together
7. **Save**: Press **S** - saves adjusted boxes
8. **Repeat**: Press **D** for next frame, **Q** to copy again

**Alternative: Manual Group Drag**
- Press **E** key or click **"Group Drag: OFF"** button to enable
- Works with current boxes (no need to copy from previous)
- Press **E** again or click button to toggle off

**Key Features:**
- ✅ **Button control**: Toggle group drag mode on/off manually
- ✅ **One-time drag**: After dragging, automatically returns to normal mode
- ✅ **Copies everything**: Both auto-detected cells AND manual boxes
- ✅ **Auto manual mode**: Automatically enables manual mode for dragging
- ✅ **Visual feedback**: Boxes turn orange during group drag
- ✅ **Resets on navigation**: Moving to next image clears the mode

**Example:**
```
Frame 1: R (detect) → S (save) → D (next)
Frame 2: Q (copy) → Drag 10px right → S (save) → D (next)
Frame 3: Q (copy) → Drag 5px down → S (save) → D (next)
...

Or manually:
Frame 1: R (detect) → Click "Group Drag: OFF" → Drag → S (save)
```

### Manual Labeling Mode

For images where automatic detection fails or needs correction:

1. **Enable Manual Mode**: Press **M** or click "Manual Mode: OFF" button
2. **Draw bounding boxes**: Click and drag to draw rectangles around cells
3. **Select boxes**: Click on any box to select it (turns yellow)
4. **Delete boxes**: Press **Delete** to remove selected box
5. **Save labels**: Press **S** to save (includes both auto-detected and manual boxes)
6. **Navigate**: Press **D** or **A** to move to next/previous image (manual boxes cleared)
7. **Clear all**: Click "Clear All Labels" to remove everything

**Visual Indicators:**
- **Cyan boxes**: Manual boxes (unselected)
- **Yellow boxes**: Selected manual box
- **Blue boxes**: Auto-detected cells
- **Green rectangle**: ROI region

**Use Cases:**
- Fix missed detections (add boxes manually)
- Remove false positives (delete auto-detected boxes)
- Label images with poor detection quality
- Create ground truth labels for training

### Batch Processing Workflow (2000+ Images)

1. **Load one sample image** from your folder

2. **Test parameters** on the sample:
   - Adjust size filter to match your cell size
   - Set appropriate BBox expansion
   - Use "Detect Cells (Whole Image)" to verify

3. **Batch process entire folder**:
   - Click **"Batch Process Folder"**
   - Confirms parameters and image count
   - Processes all images automatically
   - Generates YOLO labels for all

**Time Estimate (with multicore parallelization):**
- Automatically uses 75% of available CPU cores (leaves 25% for system)
- ~0.5-1 second per image (on 8-core CPU using 6 cores)
- 100 images: **1-2 minutes**
- 500 images: **4-10 minutes**  
- 2000 images: **15-40 minutes** (4-6x faster than sequential!)

### Output Structure

**Single Image:**
```
saved/
├── imagename.jpg                  # Original image (copy)
├── imagename.txt                  # YOLO format labels
├── imagename_annotated.jpg        # Visualization with bounding boxes
└── imagename_metadata.json        # Detection metadata
```

All files are saved directly in the `saved/` directory with the same base filename.

**Batch Processing:**
```
saved/
└── batch_20250120_121530/
    ├── image001.jpg               # Original images
    ├── image001.txt               # YOLO labels
    ├── image001_annotated.jpg     # Annotated for verification
    ├── image002.jpg
    ├── image002.txt
    ├── image002_annotated.jpg
    ├── ...
    └── batch_summary.json         # Processing statistics
```

**Batch Summary JSON:**
```json
{
  "timestamp": "20250120_121530",
  "source_folder": "path/to/images",
  "total_images": 2000,
  "processed": 1998,
  "skipped": 2,
  "total_cells_detected": 45678,
  "parameters": {
    "min_size": 20,
    "max_size": 200,
    "expansion_percent": 10
  },
  "skipped_files": ["corrupted.jpg"]
}
```

### YOLO Label Format

Each line in the `.txt` file represents one detected cell:
```
0 0.512345 0.678901 0.123456 0.098765
```

Format: `class_id center_x center_y width height`
- **class_id**: Always `0` for "cell"
- **center_x, center_y**: Normalized center coordinates (0-1)
- **width, height**: Normalized bounding box dimensions (0-1)

### Metadata Format

```json
{
  "source_image": "path/to/original.jpg",
  "image_size": {"width": 2688, "height": 1520},
  "roi": [x, y, width, height],
  "expansion_percent": 10,
  "expansion_ratio": 0.1,
  "timestamp": "20250120_121530",
  "num_cells": 15,
  "yolo_format": "class_id center_x center_y width height (normalized)",
  "class_names": {0: "cell"}
}
```

## Detection Algorithm

The cell detection uses the same advanced algorithm as the ToupCam SingleDroplet application:

1. **CLAHE Enhancement**: Contrast Limited Adaptive Histogram Equalization
2. **Gaussian Blur**: Noise reduction (σ=2)
3. **Kirsch Edge Detection**: 4-directional edge operators
4. **Otsu Thresholding**: Automatic threshold calculation
5. **Morphological Processing**: Small object removal, thinning, hole filling
6. **Eccentricity Filtering**: Remove elongated objects
7. **Contour Analysis**: Area, perimeter, and circularity filtering

### Default Detection Parameters

- **Area**: 100-5000 pixels
- **Perimeter**: 30-1000 pixels
- **Circularity**: 0.2-1.0
- **Size Filter**: 20-200 pixels (bounding box width and height)

## BBox Expansion

The expansion percentage determines how much to enlarge the bounding box around each detected cell:

- **0%**: No expansion, use exact detected bbox
- **10%**: Default, slight expansion for better coverage
- **20%**: Moderate expansion, includes more context
- **50%**: Maximum expansion, doubles bbox size

Larger expansion helps ensure the entire cell is captured, especially for cells with irregular shapes or fuzzy edges. Enter values between 0-50 in the text field.

## Size Filter

The size filter removes cells that are too small or too large based on their bounding box dimensions:

- **Min Size**: Minimum width/height in pixels (default: 20)
- **Max Size**: Maximum width/height in pixels (default: 200)
- **Filter Logic**: Both width AND height must be within the range

This helps eliminate:
- **Small debris** or noise (set higher min size)
- **Cell clusters** or artifacts (set lower max size)
- **Out-of-focus objects** that appear too large

## Batch Processing Benefits

### **For 2000 Images:**

**Without Batch Processing:**
- Manual labeling: ~100-200 hours
- One-by-one processing: ~10-20 hours

**With Batch Processing (Multicore):**
- Auto-labeling: **15-40 minutes** (fully automated, all CPU cores)
- Sample review: 2-3 hours (200 images)
- **Total: 2.5-4 hours** (97% time saved!)

### **Workflow Optimization:**

1. **Test on 5-10 samples** to find optimal parameters
2. **Batch process all 2000** images automatically
3. **Review random 100-200** samples for quality check
4. **If accuracy > 85%**: Use labels directly for training
5. **If accuracy < 85%**: Adjust parameters and re-run batch

---

## Negative Sample Creator

### Purpose

Create **negative samples** (background regions with no cells) to improve YOLO training by teaching the model what is NOT a cell.

### Quick Start

```bash
python negative_sample_creator.py
```

### Workflow

1. **Load Image** - Select image with background regions
2. **Draw ROI** - Drag mouse to define search area (choose empty regions)
3. **Set Parameters**:
   - Number of patches: 5 (default)
   - Min patch size: 100 pixels
   - Max patch size: 400 pixels
4. **Generate Patches** - Tool randomly selects background regions
5. **Review** - Check patches don't contain cells
6. **Save** - Creates image patches + empty label files

### Output

```
negative_samples/
├── image001_neg_1.jpg         # Background patch
├── image001_neg_1.txt         # Empty label (no cells)
├── image001_neg_2.jpg
├── image001_neg_2.txt
└── ...
```

### Why Use Negative Samples?

**Benefits:**
- ✅ Reduces false positives
- ✅ Improves background discrimination
- ✅ Better model precision
- ✅ More robust detection

**Recommended Ratio:**
- 80-90% positive samples (with cells)
- 10-20% negative samples (no cells)

**Example:** For 1000 training images, include 100-200 negative patches

### Integration with Training

**Copy negative samples to training directory:**
```
training_data/
├── images/train/
│   ├── cell_001.jpg          # Positive (has cells)
│   ├── cell_002.jpg
│   ├── image001_neg_1.jpg    # Negative (no cells)
│   ├── image001_neg_2.jpg
│   └── ...
└── labels/train/
    ├── cell_001.txt          # Has labels
    ├── cell_002.txt
    ├── image001_neg_1.txt    # Empty file
    ├── image001_neg_2.txt    # Empty file
    └── ...
```

**See [NEGATIVE_SAMPLES_GUIDE.md](NEGATIVE_SAMPLES_GUIDE.md) for detailed instructions.**

---

## Dataset Organizer

### Purpose

Automatically find and organize scattered JPG/TXT pairs into YOLO-ready directory structure.

### Quick Start

```bash
python dataset_organizer.py
```

### Workflow

1. **Select Source** - Where your scattered files are
2. **Select Output** - Where to create organized dataset
3. **Scan for Pairs** - Find matching image-label pairs
4. **Organize** - Copy/move into YOLO structure

### Features

**Automatic Pair Matching:**
- Finds .jpg and .txt with same filename
- Recursive subdirectory search
- Reports orphan files (no matching pair)

**Organization Options:**
- Copy or move files
- Auto train/val split (configurable %)
- Handles duplicate filenames
- Creates YOLO-standard structure

**Output Structure:**
```
organized/
├── images/
│   ├── train/  (80%)
│   └── val/    (20%)
└── labels/
    ├── train/
    └── val/
```

### Use Cases

✅ **Organize scattered files** from multiple folders
✅ **Prepare for training** with auto train/val split
✅ **Clean up dataset** by detecting orphans
✅ **Merge multiple sources** into single dataset

**See [DATASET_ORGANIZER_GUIDE.md](DATASET_ORGANIZER_GUIDE.md) for detailed instructions.**

---

### **Key Advantages:**

- ✅ **Multicore parallelization** - uses 75% of CPU cores (leaves system responsive)
- ✅ **4-6x faster** than sequential processing
- ✅ **Consistent parameters** across all images
- ✅ **Progress tracking** with real-time updates
- ✅ **Error handling** - skips corrupted files
- ✅ **Batch summary** - statistics and skipped files
- ✅ **No manual intervention** - fully automated

## Tips for Best Results

1. **Parameter Tuning**: Test on 5-10 sample images first
2. **Size Filter**: Adjust min/max to match your cell size range
3. **BBox Expansion**: Start with 10% expansion, increase if cells are cut off
4. **Quality Check**: Review random samples after batch processing
5. **Folder Organization**: Keep all images in one folder for batch processing

## Integration with YOLO Training

The generated YOLO labels are ready for training:

### **Workflow:**

1. **Generate labels** for multiple images using this tool
2. **Organize files** into YOLO training structure:
   ```
   training_data/
   ├── images/
   │   ├── train/      # 70-80% of your images
   │   └── val/        # 20-30% of your images
   └── labels/
       ├── train/      # Corresponding .txt label files
       └── val/        # Corresponding .txt label files
   ```

3. **Create dataset.yaml**:
   ```yaml
   path: training_data
   train: images/train
   val: images/val
   
   nc: 1  # number of classes
   names: ['cell']
   ```

4. **Train YOLO model**:
   ```bash
   python train_model.py --data training_data/dataset.yaml --epochs 100
   ```

## Troubleshooting

### No cells detected
- Adjust ROI to focus on clear cell regions
- Check image quality and contrast
- **Adjust size filter**: Cells may be filtered out by min/max size limits

### Too many false detections
- Draw smaller, more focused ROI
- Ensure good image quality
- **Increase min size**: Filter out small debris
- **Decrease max size**: Filter out large artifacts
- Check that objects are roughly circular

### Bounding boxes don't cover entire cells
- **Increase BBox expansion**: Try 20-30% for better coverage
- Verify cell detection is accurate in annotated visualization
- **Adjust size filter** to match your expected cell dimensions

### YOLO labels look incorrect
- Check annotated visualization to verify bounding boxes
- Ensure image dimensions match between image and label files
- Verify YOLO format: class_id center_x center_y width height (all normalized 0-1)

## Related Tools

- **Video2dataset**: Extract frames from videos for dataset creation
- **YoloVersion/StaticImage**: YOLO-based cell detection
- **YoloVersion/Training**: Train custom YOLO models

## Technical Details

- **Cell Detection**: Kirsch edge detection with morphological processing
- **Image Format**: Supports JPG, JPEG, PNG input
- **Label Format**: YOLO standard (class_id center_x center_y width height)
- **Coordinate Normalization**: All coordinates normalized to 0-1 range
- **Class ID**: Single class (0 = "cell")
- **Visualization**: Green bounding boxes with red center points
