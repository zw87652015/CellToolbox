# YOLO11 Custom Training Guide

Complete guide for training your own cell detection model on custom data.

---

## 🎯 Why Train a Custom Model?

- **Better accuracy** on your specific cell types
- **Detect multiple cell types** (different classes)
- **Adapt to your imaging conditions** (microscope, staining, etc.)
- **Improve performance** on challenging images

---

## 📁 Step 1: Organize Your Data (30 minutes)

### Directory Structure

Your data goes in `training_data/`:

```
StaticImage/training_data/
├── dataset.yaml          # Already created ✓
├── images/
│   ├── train/           # 70-80% of your images
│   │   ├── cell_001.jpg
│   │   ├── cell_002.jpg
│   │   └── ...
│   ├── val/             # 10-20% of your images
│   │   ├── cell_101.jpg
│   │   └── ...
│   └── test/            # 10% (optional)
│       └── ...
└── labels/
    ├── train/           # Created by labeling tool
    │   ├── cell_001.txt
    │   ├── cell_002.txt
    │   └── ...
    ├── val/
    │   └── ...
    └── test/
        └── ...
```

### Split Your Images

**Recommended split:**
- **Training (70-80%)**: Used to train the model
- **Validation (10-20%)**: Used to tune the model
- **Test (10%)**: Optional, for final evaluation

**Example:** If you have 200 images:
- 140 → `images/train/`
- 40 → `images/val/`
- 20 → `images/test/`

### Minimum Dataset Size

- **Minimum**: 100 training images, 20 validation images
- **Recommended**: 500+ training images, 100+ validation images
- **Better results**: 1000+ training images

---

## 🏷️ Step 2: Label Your Images (1-2 hours)

### Install LabelImg (Easiest Tool)

```bash
pip install labelImg
```

### Start Labeling

```bash
labelImg training_data/images/train
```

### Labeling Instructions

1. **Start LabelImg**: `labelImg training_data/images/train`
2. **⚠️ IMPORTANT: Switch to YOLO format**
   - Click **"PascalVOC"** button on the left sidebar
   - It will change to **"YOLO"** 
   - This makes LabelImg create `.txt` files instead of `.xml`
3. **Change Save Dir** → Select `training_data/labels/train/`
4. **Press 'W'** → Draw box around each cell
5. **Press Ctrl+S** → Save (creates .txt file automatically)
6. **Press 'D'** → Next image
7. **Repeat** for all training and validation images

**⚠️ Already created .xml files?** Use the conversion script:

```bash
# Convert XML to YOLO format
python convert_xml_to_yolo.py --xml-dir training_data/images/train --output-dir training_data/labels/train

# For validation images
python convert_xml_to_yolo.py --xml-dir training_data/images/val --output-dir training_data/labels/val

# Delete XML files after conversion (optional)
python convert_xml_to_yolo.py --xml-dir training_data/images/train --output-dir training_data/labels/train --delete-xml
```

### Label Format (YOLO Format)

Each `.txt` file contains one line per cell:

```
<class_id> <center_x> <center_y> <width> <height>
```

**All values are normalized (0-1)**:
- `class_id`: 0 for single cell class
- `center_x`: Cell center X / image width
- `center_y`: Cell center Y / image height
- `width`: Cell width / image width
- `height`: Cell height / image height

**Example (cell_001.txt):**
```
0 0.5234 0.3891 0.0625 0.0521
0 0.7123 0.6234 0.0583 0.0547
```

This means:
- Cell 1: Center at (52.34%, 38.91%), size 6.25% × 5.21%
- Cell 2: Center at (71.23%, 62.34%), size 5.83% × 5.47%

### Alternative Labeling Tools

**Roboflow (Web-based)**:
- Upload images to roboflow.com
- Label in browser
- Export in YOLO format
- Good for team collaboration

**CVAT (Advanced)**:
- Self-hosted or cloud
- Professional features
- Team collaboration
- Export in YOLO format

---

## 📝 Step 3: Verify Dataset Configuration

The file `training_data/dataset.yaml` is already created. Verify it looks like this:

```yaml
path: .  # Current directory
train: images/train
val: images/val
test: images/test

nc: 1  # Number of classes
names: ['cell']  # Class names
```

**For multiple cell types**, edit to:
```yaml
nc: 3
names: ['cell_type1', 'cell_type2', 'cell_type3']
```

---

## 🚀 Step 4: Train Your Model (10 min - 2 hours)

### Basic Training (CPU)

```bash
python train_model.py --data training_data/dataset.yaml
```

**Training time:** 1-2 hours for 100 epochs

### GPU Training (Much Faster) ⭐

```bash
python train_model.py --data training_data/dataset.yaml --device cuda
```

**Training time:** 10-20 minutes for 100 epochs

### Custom Settings

```bash
python train_model.py \
    --data training_data/dataset.yaml \
    --model s \              # Model size: n/s/m/l/x
    --epochs 200 \           # More epochs for better results
    --batch 32 \             # Larger batch if you have GPU memory
    --device cuda            # Use GPU
```

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--data` | required | Path to dataset.yaml |
| `--model` | n | Model size: **n** (fastest), s, m, l, x (best) |
| `--epochs` | 100 | Training duration (more = better, but slower) |
| `--batch` | 16 | Batch size (reduce if out of memory) |
| `--imgsz` | 640 | Image size (416/640/1280) |
| `--device` | cpu | **cpu** or **cuda** (GPU) |

### Model Size Guide

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| **yolo11n** | 6MB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Quick testing, small datasets |
| **yolo11s** | 22MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | **Recommended for most cases** |
| **yolo11m** | 50MB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | High accuracy needed |
| **yolo11l** | 100MB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Maximum accuracy |

**Recommendation:** Start with `n` for testing, use `s` for production.

### What Happens During Training

You'll see output like this:

```
Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
  1/100      1.2G      1.234      0.567      1.123         45        640
  2/100      1.2G      1.156      0.523      1.089         42        640
  ...
 100/100     1.2G      0.234      0.067      0.223         42        640
```

**Key metrics** (lower is better):
- **box_loss**: How accurate the bounding boxes are
- **cls_loss**: How accurate the classification is
- **mAP@0.5**: Overall accuracy (higher is better, aim for >0.7)

### Training Output

After training completes, find your model here:

```
trained_models/cell_detection/
├── weights/
│   ├── best.pt              # ⭐ USE THIS MODEL
│   └── last.pt              # Last checkpoint
├── results.png              # Training curves (check this!)
├── confusion_matrix.png     # Performance visualization
└── F1_curve.png, P_curve.png, R_curve.png
```

**The file you need:** `trained_models/cell_detection/weights/best.pt` ⭐

### Resume Training

If training is interrupted:

```bash
python train_model.py --resume
```

---

## 🧪 Step 5: Test Your Model (1 minute)

### Test on Sample Images

```bash
python test_trained_model.py \
    --model trained_models/cell_detection/weights/best.pt \
    --images training_data/images/test
```

Results saved to `test_results/` folder.

### Compare with Pretrained Model

```bash
python test_trained_model.py \
    --model trained_models/cell_detection/weights/best.pt \
    --compare yolo11n.pt \
    --test-image sample_image.jpg
```

---

## 🎯 Step 6: Use Your Trained Model

### Method 1: Update Config (Recommended) ⭐

Edit `config.yaml`:

```yaml
model:
  custom_weights: "trained_models/cell_detection/weights/best.pt"
  confidence_threshold: 0.25  # Adjust as needed
```

Then run detection normally:

```bash
python cell_detector.py
```

### Method 2: Command Line

```bash
python cell_detector.py \
    --model trained_models/cell_detection/weights/best.pt
```

### Method 3: Python API

```python
from cell_detector import CellDetector

detector = CellDetector('config.yaml')
detector.config['model']['custom_weights'] = \
    'trained_models/cell_detection/weights/best.pt'

detector.process_directory('input_images')
```

---

## 💡 Training Tips

### Data Quality

✅ **Good practices:**
- Clear, well-focused images
- Consistent lighting and quality
- Accurate bounding boxes (not too tight, not too loose)
- Label ALL cells in each image
- Varied cell sizes and positions

❌ **Avoid:**
- Blurry or low-quality images
- Missing labels (unlabeled cells)
- Inconsistent image quality
- Too few images (<100)

### Training Duration

**How many epochs?**
- **50 epochs**: Quick test
- **100 epochs**: Standard (recommended)
- **200 epochs**: Better results for large datasets
- **300+ epochs**: Maximum accuracy

Training stops early if no improvement (patience=50 epochs).

### Batch Size

**If you get "Out of Memory" error:**

```bash
# Reduce batch size
python train_model.py --batch 8 --data training_data/dataset.yaml

# Or reduce image size
python train_model.py --batch 8 --imgsz 416 --data training_data/dataset.yaml
```

**Recommended batch sizes:**
- CPU: 4-8
- GPU (4GB): 8-16
- GPU (8GB): 16-32
- GPU (16GB+): 32-64

---

## 🐛 Troubleshooting

### "No labels found"

**Problem:** Training can't find label files

**Solutions:**
1. Check `training_data/labels/train/` has .txt files
2. Verify filenames match images: `cell_001.jpg` → `cell_001.txt`
3. Make sure you saved labels in YOLO format

### "Out of memory"

**Problem:** Not enough RAM/VRAM

**Solutions:**
```bash
# Use smaller model
python train_model.py --model n --batch 4 --imgsz 416 --data training_data/dataset.yaml
```

### "Low mAP scores" (< 0.5)

**Problem:** Model not learning well

**Solutions:**
1. Add more training images (aim for 500+)
2. Check label quality (are boxes accurate?)
3. Train longer: `--epochs 200`
4. Use larger model: `--model s` or `--model m`
5. Verify images are clear and consistent

### "Training too slow"

**Problem:** Taking too long

**Solutions:**
1. Use GPU: `--device cuda` (10x faster)
2. Use smaller model: `--model n`
3. Reduce image size: `--imgsz 416`
4. Reduce epochs: `--epochs 50` (for testing)

### "Model not detecting cells after training"

**Problem:** Trained model doesn't work

**Solutions:**
1. Check model path in config.yaml is correct
2. Lower confidence threshold:
   ```yaml
   model:
     confidence_threshold: 0.15
   ```
3. Verify test images are similar to training images
4. Check training mAP was > 0.5

---

## ✅ Complete Workflow Example

### Scenario: You have 300 cell images

**1. Organize (10 minutes)**
```bash
# Split images:
# 210 → training_data/images/train/
# 60 → training_data/images/val/
# 30 → training_data/images/test/
```

**2. Label (2-3 hours)**
```bash
pip install labelImg
labelImg training_data/images/train
# Draw boxes around all cells
# Repeat for val/ folder
```

**3. Train (20 minutes with GPU)**
```bash
python train_model.py \
    --data training_data/dataset.yaml \
    --model s \
    --epochs 100 \
    --device cuda
```

**4. Test (1 minute)**
```bash
python test_trained_model.py \
    --model trained_models/cell_detection/weights/best.pt \
    --images training_data/images/test
```

**5. Use (ongoing)**
```bash
# Edit config.yaml with model path
python cell_detector.py
```

---

## 📊 Evaluating Your Model

### Good Model Performance

- **mAP@0.5 > 0.7**: Good model ✅
- **mAP@0.5 > 0.8**: Excellent model ✅✅
- **mAP@0.5 > 0.9**: Outstanding model ✅✅✅

### Check Training Curves

Open `trained_models/cell_detection/results.png`:

- **Loss curves should decrease** over time
- **mAP curves should increase** over time
- **Validation and training curves should be close** (not diverging)

If curves are flat or diverging, you may need:
- More training data
- Better label quality
- Different hyperparameters

---

## 🎓 Advanced: Multiple Cell Types

### Dataset Configuration

Edit `training_data/dataset.yaml`:

```yaml
nc: 3
names: ['cell_type1', 'cell_type2', 'cell_type3']
```

### Labeling

Use different class IDs in label files:

```
0 0.5234 0.3891 0.0625 0.0521  # cell_type1
1 0.7123 0.6234 0.0583 0.0547  # cell_type2
2 0.2891 0.4567 0.0612 0.0534  # cell_type3
```

### Training

Same command:

```bash
python train_model.py --data training_data/dataset.yaml --device cuda
```

The model will automatically detect multiple classes!

---

## 📚 Quick Reference

### Essential Commands

```bash
# Install labeling tool
pip install labelImg

# Label images
labelImg training_data/images/train

# Train model (CPU)
python train_model.py --data training_data/dataset.yaml

# Train model (GPU - faster)
python train_model.py --data training_data/dataset.yaml --device cuda

# Test model
python test_trained_model.py --model trained_models/.../best.pt

# Use model for detection
# (Edit config.yaml first)
python cell_detector.py
```

### Key File Locations

| What | Where |
|------|-------|
| **Your training images** | `training_data/images/train/` |
| **Your validation images** | `training_data/images/val/` |
| **Label files** | `training_data/labels/train/` (auto-created) |
| **Dataset config** | `training_data/dataset.yaml` ✓ |
| **Training script** | `train_model.py` |
| **Your trained model** | `trained_models/.../weights/best.pt` ⭐ |
| **Detection config** | `config.yaml` (update with model path) |

### Checklist

Before training:
- [ ] Images in `training_data/images/train/` (70-80%)
- [ ] Images in `training_data/images/val/` (10-20%)
- [ ] All images labeled with LabelImg
- [ ] At least 100 training images
- [ ] `dataset.yaml` configured correctly

After training:
- [ ] Training completed (mAP > 0.5)
- [ ] Model at `trained_models/.../weights/best.pt`
- [ ] Tested on sample images
- [ ] Results look good
- [ ] Updated `config.yaml` with model path

---

**That's it!** You now have a custom-trained YOLO11 model for your specific cell types. 🎉

For detection usage, see `USER_GUIDE.md`.
