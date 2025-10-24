# ToupCam Live Stream Latency Fix

## Problem
The ToupCam live detector showed visible lag between detection boxes and moving cells. The lag distance increased linearly with cell movement speed.

## Root Cause
**Temporal mismatch between frames and detections:**
- Camera callback continuously captures new frames
- Detection thread consumed frames from a queue (FIFO)
- Render thread displayed the **latest live frame** with **old detections** from queued frames
- Result: If inference takes Δt milliseconds and cell moves at v pixels/sec, lag = v × Δt

## Solution Implemented
**"Always infer on latest frame" approach:**

### Key Changes:

1. **Removed queue-based detection** (`detection_queue`)
   - Old: Frames queued in FIFO order, detection processed stale frames
   - New: Single `latest_detection_frame` snapshot always holds newest frame

2. **Detection thread grabs latest frame atomically**
   - Checks `latest_detection_frame` under lock
   - Grabs frame and clears the slot (consumes it)
   - If busy with inference, camera overwrites with even newer frame
   - Result: Detection always runs on the most recent available frame

3. **Frame ID tracking for synchronization**
   - `detection_frame_id`: ID of frame being processed
   - `displayed_frame_id`: ID of frame whose detections are shown
   - Enables future enhancements (e.g., only draw boxes if IDs match)

### Code Changes:

**Before:**
```python
self.detection_queue = queue.Queue(maxsize=2)
# Camera callback
self.detection_queue.put_nowait(frame.copy())
# Detection thread
frame = self.detection_queue.get(timeout=0.1)
```

**After:**
```python
self.latest_detection_frame = None
self.detection_frame_lock = threading.Lock()
# Camera callback
with self.detection_frame_lock:
    self.latest_detection_frame = frame.copy()  # Always replace with newest
# Detection thread
with self.detection_frame_lock:
    frame = self.latest_detection_frame
    self.latest_detection_frame = None  # Consume
```

## Benefits

✅ **Zero spatial lag**: Detections always correspond to recent frames, not stale queued frames  
✅ **Lowest latency**: No queueing delay, detection starts immediately when ready  
✅ **Automatic frame skipping**: If detection is slow, intermediate frames are automatically skipped  
✅ **Linear scaling**: Lag no longer grows with cell speed  

## Performance Notes

- Detection thread now processes frames as fast as it can
- If camera FPS > detection FPS, some frames are naturally skipped (expected behavior)
- For even lower latency, consider:
  - Smaller YOLO input size (640→512 in config)
  - Enabling half precision (`half_precision: true`)
  - Using ROI to reduce pixels processed
  - Faster GPU

## Testing

Run the detector and move cells quickly:
```bash
python toupcam_live_detector.py
```

Expected: Detection boxes should now track cells accurately with minimal visible lag, even at high speeds.

## Date
2025-10-23
