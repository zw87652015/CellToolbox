# Training Data Directory

## Structure

Place your training data in this directory following this structure:

```
training_data/
├── dataset.yaml           # Dataset configuration (already created)
├── images/
│   ├── train/            # Training images (70-80%)
│   │   ├── cell_001.jpg
│   │   ├── cell_002.jpg
│   │   └── ...
│   ├── val/              # Validation images (10-20%)
│   │   ├── cell_101.jpg
│   │   └── ...
│   └── test/             # Test images (10%) - optional
│       ├── cell_201.jpg
│       └── ...
└── labels/
    ├── train/            # Training labels
    │   ├── cell_001.txt
    │   ├── cell_002.txt
    │   └── ...
    ├── val/              # Validation labels
    │   ├── cell_101.txt
    │   └── ...
    └── test/             # Test labels - optional
        ├── cell_201.txt
        └── ...
```

## Label Format

Each `.txt` label file contains one line per cell:

```
<class_id> <center_x> <center_y> <width> <height>
```

**All values are normalized (0-1):**
- `class_id`: 0 for single class
- `center_x`: Cell center X / image width
- `center_y`: Cell center Y / image height  
- `width`: Cell width / image width
- `height`: Cell height / image height

**Example (cell_001.txt):**
```
0 0.5234 0.3891 0.0625 0.0521
0 0.7123 0.6234 0.0583 0.0547
```

## Quick Start

### 1. Create Directories

```bash
mkdir -p images/train images/val images/test
mkdir -p labels/train labels/val labels/test
```

### 2. Add Your Images

Copy your cell images to the appropriate folders:
- 70-80% → `images/train/`
- 10-20% → `images/val/`
- 10% → `images/test/` (optional)

### 3. Label Your Images

**Option A: Using LabelImg**
```bash
pip install labelImg
labelImg images/train
```
- Draw boxes around cells
- Save in YOLO format
- Labels automatically saved to `labels/train/`

**Option B: Using Roboflow**
1. Upload images to roboflow.com
2. Label online
3. Export in YOLO format
4. Extract to this directory

### 4. Verify Dataset

```bash
cd ..
python train_model.py --data training_data/dataset.yaml --epochs 1
```

This will verify your dataset structure before full training.

## Tips

- **Minimum dataset size**: 100+ training images, 20+ validation images
- **Better results**: 500+ training images, 100+ validation images
- **Label quality matters**: Accurate boxes are more important than quantity
- **Consistent naming**: Use sequential naming (cell_001.jpg, cell_002.jpg, etc.)
- **Image format**: JPG or PNG
- **Image size**: Any size (will be resized during training)

## Example Label File

For an image with 3 cells at different positions:

**cell_example.txt:**
```
0 0.245 0.312 0.082 0.075
0 0.678 0.523 0.091 0.088
0 0.512 0.789 0.076 0.071
```

This represents:
- Cell 1: Center at (24.5%, 31.2%), size 8.2% × 7.5%
- Cell 2: Center at (67.8%, 52.3%), size 9.1% × 8.8%
- Cell 3: Center at (51.2%, 78.9%), size 7.6% × 7.1%

## Next Steps

After organizing your data:

1. **Verify structure**: Check all folders exist and contain files
2. **Train model**: `python train_model.py --data training_data/dataset.yaml`
3. **Monitor training**: Watch for decreasing loss values
4. **Test model**: `python test_trained_model.py --model trained_models/.../best.pt`
5. **Use for detection**: Update `config.yaml` with trained model path

See `TRAINING_GUIDE.md` for complete instructions.
