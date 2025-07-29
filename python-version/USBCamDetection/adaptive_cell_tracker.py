"""
Adaptive Cell Tracker with Velocity-based Thresholds and Kalman Filter Prediction

This module implements an advanced cell tracking system that:
1. Learns individual cell velocities over time
2. Adapts search thresholds based on movement patterns
3. Uses Kalman filters for position prediction during missed detections
4. Maintains stable cell IDs across frames with intermittent detections
"""

import numpy as np
import cv2
import math
from collections import OrderedDict, deque
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
import time

class KalmanCellTracker:
    """Individual Kalman filter tracker for a single cell"""
    
    def __init__(self, initial_position):
        # State: [x, y, vx, vy] - position and velocity
        self.kalman = cv2.KalmanFilter(4, 2)
        
        # Measurement matrix (we only observe position, not velocity)
        self.kalman.measurementMatrix = np.array([[1, 0, 0, 0],
                                                  [0, 1, 0, 0]], dtype=np.float32)
        
        # Transition matrix (constant velocity model)
        self.kalman.transitionMatrix = np.array([[1, 0, 1, 0],
                                                 [0, 1, 0, 1],
                                                 [0, 0, 1, 0],
                                                 [0, 0, 0, 1]], dtype=np.float32)
        
        # Process noise covariance
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        
        # Measurement noise covariance
        self.kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1.0
        
        # Error covariance
        self.kalman.errorCovPost = np.eye(4, dtype=np.float32)
        
        # Initialize state
        self.kalman.statePre = np.array([initial_position[0], initial_position[1], 0, 0], dtype=np.float32)
        self.kalman.statePost = np.array([initial_position[0], initial_position[1], 0, 0], dtype=np.float32)
        
        self.last_prediction = initial_position
        self.velocity_history = deque(maxlen=10)
        
    def predict(self):
        """Predict next position"""
        prediction = self.kalman.predict()
        self.last_prediction = (float(prediction[0]), float(prediction[1]))
        return self.last_prediction
    
    def update(self, measurement):
        """Update with new measurement"""
        measurement_array = np.array([[measurement[0]], [measurement[1]]], dtype=np.float32)
        self.kalman.correct(measurement_array)
        
        # Update velocity history
        state = self.kalman.statePost
        velocity = (float(state[2]), float(state[3]))
        self.velocity_history.append(velocity)
    
    def get_velocity(self):
        """Get current velocity estimate"""
        if len(self.velocity_history) > 0:
            return self.velocity_history[-1]
        return (0, 0)
    
    def get_average_speed(self):
        """Get average speed over recent history"""
        if len(self.velocity_history) == 0:
            return 0
        
        speeds = [math.sqrt(vx**2 + vy**2) for vx, vy in self.velocity_history]
        return sum(speeds) / len(speeds)

class TrackedCell:
    """Represents a tracked cell with its history and properties"""
    
    def __init__(self, cell_id, initial_centroid, initial_bbox):
        self.id = cell_id
        self.kalman_tracker = KalmanCellTracker(initial_centroid)
        self.centroid_history = deque([initial_centroid], maxlen=50)
        self.bbox_history = deque([initial_bbox], maxlen=10)
        self.disappeared_count = 0
        self.total_detections = 1
        self.creation_time = time.time()
        self.last_seen_frame = 0
        self.confidence_score = 1.0
        
    def predict_position(self):
        """Predict next position using Kalman filter"""
        return self.kalman_tracker.predict()
    
    def update_position(self, centroid, bbox, frame_number):
        """Update with new detection"""
        self.kalman_tracker.update(centroid)
        self.centroid_history.append(centroid)
        self.bbox_history.append(bbox)
        self.disappeared_count = 0
        self.total_detections += 1
        self.last_seen_frame = frame_number
        
        # Update confidence based on detection consistency
        self.confidence_score = min(1.0, self.total_detections / 10.0)
    
    def mark_disappeared(self):
        """Mark cell as disappeared for this frame"""
        self.disappeared_count += 1
    
    def get_adaptive_search_radius(self, base_radius=50):
        """Calculate adaptive search radius based on cell's movement pattern"""
        avg_speed = self.kalman_tracker.get_average_speed()
        
        # Adaptive radius: base + speed factor + uncertainty factor
        speed_factor = min(avg_speed * 2, 100)  # Cap at 100 pixels
        uncertainty_factor = self.disappeared_count * 5  # Increase with disappearance
        
        return base_radius + speed_factor + uncertainty_factor
    
    def get_movement_vector(self):
        """Get recent movement vector"""
        if len(self.centroid_history) < 2:
            return (0, 0)
        
        recent = list(self.centroid_history)[-2:]
        dx = recent[1][0] - recent[0][0]
        dy = recent[1][1] - recent[0][1]
        return (dx, dy)

class AdaptiveCellTracker:
    """Main adaptive cell tracking system"""
    
    def __init__(self, max_disappeared=15, base_search_radius=50, min_track_length=3):
        self.next_id = 0
        self.tracked_cells = OrderedDict()
        self.max_disappeared = max_disappeared
        self.base_search_radius = base_search_radius
        self.min_track_length = min_track_length
        self.frame_number = 0
        
        # Statistics
        self.total_cells_tracked = 0
        self.active_tracks = 0
        
    def update(self, detections):
        """
        Update tracker with new detections
        
        Args:
            detections: List of detection dictionaries with 'centroid' and 'bbox' keys
            
        Returns:
            Dictionary of {cell_id: (centroid, bbox, confidence)} for active tracks
        """
        self.frame_number += 1
        
        # Extract centroids from detections
        if len(detections) == 0:
            # No detections - mark all cells as disappeared
            for cell in self.tracked_cells.values():
                cell.mark_disappeared()
            self._cleanup_lost_tracks()
            return self._get_active_tracks()
        
        centroids = [det['centroid'] for det in detections]
        
        # Handle first frame or no existing tracks
        if len(self.tracked_cells) == 0:
            for i, detection in enumerate(detections):
                self._register_new_cell(detection['centroid'], detection['bbox'])
            return self._get_active_tracks()
        
        # Predict positions for all tracked cells
        predictions = {}
        search_radii = {}
        for cell_id, cell in self.tracked_cells.items():
            predictions[cell_id] = cell.predict_position()
            search_radii[cell_id] = cell.get_adaptive_search_radius(self.base_search_radius)
        
        # Create distance matrix between predictions and detections
        predicted_positions = list(predictions.values())
        cell_ids = list(predictions.keys())
        
        if len(predicted_positions) > 0 and len(centroids) > 0:
            # Calculate distance matrix
            dist_matrix = distance.cdist(predicted_positions, centroids)
            
            # Apply adaptive thresholds - set distances beyond threshold to infinity
            for i, cell_id in enumerate(cell_ids):
                max_dist = search_radii[cell_id]
                dist_matrix[i][dist_matrix[i] > max_dist] = np.inf
            
            # Solve assignment problem
            try:
                row_indices, col_indices = linear_sum_assignment(dist_matrix)
                
                # Process assignments
                used_detection_indices = set()
                for row_idx, col_idx in zip(row_indices, col_indices):
                    if dist_matrix[row_idx, col_idx] != np.inf:
                        cell_id = cell_ids[row_idx]
                        detection = detections[col_idx]
                        self.tracked_cells[cell_id].update_position(
                            detection['centroid'], 
                            detection['bbox'], 
                            self.frame_number
                        )
                        used_detection_indices.add(col_idx)
                    else:
                        # No valid assignment for this cell
                        cell_id = cell_ids[row_idx]
                        self.tracked_cells[cell_id].mark_disappeared()
                
                # Register new cells for unassigned detections
                for i, detection in enumerate(detections):
                    if i not in used_detection_indices:
                        self._register_new_cell(detection['centroid'], detection['bbox'])
                        
            except ValueError:
                # Assignment failed - mark all existing as disappeared and register new
                for cell in self.tracked_cells.values():
                    cell.mark_disappeared()
                for detection in detections:
                    self._register_new_cell(detection['centroid'], detection['bbox'])
        
        # Clean up lost tracks
        self._cleanup_lost_tracks()
        
        return self._get_active_tracks()
    
    def _register_new_cell(self, centroid, bbox):
        """Register a new cell for tracking"""
        cell = TrackedCell(self.next_id, centroid, bbox)
        self.tracked_cells[self.next_id] = cell
        self.next_id += 1
        self.total_cells_tracked += 1
    
    def _cleanup_lost_tracks(self):
        """Remove cells that have been disappeared for too long"""
        to_remove = []
        for cell_id, cell in self.tracked_cells.items():
            if cell.disappeared_count > self.max_disappeared:
                to_remove.append(cell_id)
        
        for cell_id in to_remove:
            del self.tracked_cells[cell_id]
    
    def _get_active_tracks(self):
        """Get currently active tracks with minimum track length filter"""
        active = {}
        for cell_id, cell in self.tracked_cells.items():
            # Only return tracks that have been detected enough times
            if cell.total_detections >= self.min_track_length:
                latest_centroid = cell.centroid_history[-1] if cell.centroid_history else (0, 0)
                latest_bbox = cell.bbox_history[-1] if cell.bbox_history else (0, 0, 0, 0)
                active[cell_id] = {
                    'centroid': latest_centroid,
                    'bbox': latest_bbox,
                    'confidence': cell.confidence_score,
                    'disappeared_count': cell.disappeared_count,
                    'total_detections': cell.total_detections,
                    'predicted_position': cell.kalman_tracker.last_prediction,
                    'velocity': cell.kalman_tracker.get_velocity(),
                    'search_radius': cell.get_adaptive_search_radius(self.base_search_radius)
                }
        
        self.active_tracks = len(active)
        return active
    
    def get_statistics(self):
        """Get tracking statistics"""
        return {
            'total_tracked': self.total_cells_tracked,
            'currently_active': self.active_tracks,
            'frame_number': self.frame_number,
            'disappeared_tracks': len([c for c in self.tracked_cells.values() if c.disappeared_count > 0])
        }
    
    def get_track_trajectories(self, min_length=5):
        """Get trajectories for visualization"""
        trajectories = {}
        for cell_id, cell in self.tracked_cells.items():
            if len(cell.centroid_history) >= min_length:
                trajectories[cell_id] = {
                    'points': list(cell.centroid_history),
                    'confidence': cell.confidence_score,
                    'active': cell.disappeared_count == 0
                }
        return trajectories
