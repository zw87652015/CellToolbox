# Video Frame Extractor

A simple Python application that extracts frames from video files at specified intervals.

## Features

- Extract 1 frame from every N frames (default: 10)
- Support for all video formats supported by OpenCV
- Progress tracking during extraction
- Automatic output directory creation
- Configurable frame interval via command line

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Extract 1 frame every 10 frames (default):

```bash
python video_frame_extractor.py input.mp4 -o output_frames
```

### Custom Frame Interval

Extract 1 frame every 30 frames:

```bash
python video_frame_extractor.py input.mp4 -o output_frames -i 30
```

### Full Path Example

```bash
python video_frame_extractor.py C:/videos/input.mp4 -o C:/frames
```

## Command Line Arguments

- `video`: Path to input video file (required)
- `-o, --output`: Output directory for extracted frames (default: `output_frames`)
- `-i, --interval`: Frame interval - extract 1 frame every N frames (default: 10)

## Output

Extracted frames are saved as JPEG images with filenames in the format:
- `frame_000000.jpg`
- `frame_000010.jpg`
- `frame_000020.jpg`
- etc.

The frame number in the filename corresponds to the original frame number in the video.

## Example

```bash
python video_frame_extractor.py my_video.mp4 -o frames -i 10
```

Output:
```
Video Properties:
  Total frames: 1000
  FPS: 30.00
  Resolution: 1920x1080
  Frame interval: 10
  Expected output frames: 100

Saved 10 frames... (current frame: 90/1000)
Saved 20 frames... (current frame: 190/1000)
...

Extraction complete!
  Total frames processed: 1000
  Frames saved: 100
  Output directory: frames
```

## Use Cases

- Creating training datasets for YOLO or other ML models
- Video sampling for analysis
- Reducing video data for processing
- Creating image sequences from videos
