# Quick Start - Video Cell Detector

Get started with real-time video cell detection in 5 minutes! 🚀

## 1. Run the Detector (30 seconds)

```bash
python video_cell_detector.py your_video.mp4
```

**That's it!** A window will open showing real-time cell detection.

---

## 2. Interactive Controls (1 minute)

### Essential Keys:

```
SPACE  - Pause/Resume
Q      - Quit
R      - Clear ROI
S      - Save current frame
```

### Select ROI (Region of Interest):

1. Press **SPACE** to pause
2. **Click and drag** with mouse to draw rectangle
3. Press **SPACE** to resume
4. Only cells in ROI are detected! ✅

---

## 3. Check Results (30 seconds)

Output files in `output_video/`:

```
annotated_video.mp4  ← Video with bounding boxes
detections.csv       ← All detection data
summary.json         ← Statistics summary
```

---

## 4. Common Workflows

### Workflow 1: Quick Analysis
```bash
python video_cell_detector.py video.mp4
# Watch → Press Q when done → Check CSV
```

### Workflow 2: ROI Focus
```bash
python video_cell_detector.py video.mp4
# Pause → Draw ROI → Resume → Save
```

### Workflow 3: Fast Processing
```bash
python video_cell_detector.py video.mp4
# Press - key to skip frames (faster)
# Press + key to process more frames (accurate)
```

---

## 5. Customize Settings (2 minutes)

Edit `config.yaml`:

### Change Detection Threshold:
```yaml
model:
  confidence_threshold: 0.25  # Lower = more detections
```

### Change Cell Size Filter:
```yaml
filters:
  min_cell_size: 40   # Minimum cell size
  max_cell_size: 500  # Maximum cell size
```

### Use Your Trained Model:
```yaml
model:
  custom_weights: "path/to/your/best.pt"
```

---

## Keyboard Cheat Sheet

```
╔═══════════════════════════════════════╗
║  SPACE  - Pause/Resume                ║
║  Q      - Quit                        ║
║  R      - Clear ROI                   ║
║  S      - Save frame                  ║
║  H      - Show help                   ║
║  +/-    - Adjust frame skip           ║
║  MOUSE  - Draw ROI (click & drag)     ║
╚═══════════════════════════════════════╝
```

---

## Troubleshooting

### Video won't open?
```bash
# Convert to MP4 first
ffmpeg -i input.avi -c:v libx264 output.mp4
```

### Too slow?
```bash
# Press - key to skip frames
# Or edit config.yaml:
detection:
  image_size: 320  # Smaller = faster
```

### Too many false detections?
```yaml
# Edit config.yaml:
model:
  confidence_threshold: 0.5  # Higher = fewer detections
```

---

## Next Steps

- **Read full README.md** for advanced features
- **Adjust config.yaml** for your specific cells
- **Train custom model** if default doesn't work well

**Happy detecting! 🔬✨**
