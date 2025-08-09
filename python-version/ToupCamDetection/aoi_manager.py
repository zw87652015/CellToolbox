"""
AOI (Area of Interest) Manager Module
This module handles AOI drawing, management, and overlay functionality.
"""

import tkinter as tk
import numpy as np
import cv2

class AOIManager:
    """Manages Area of Interest (AOI) functionality including drawing and overlay"""
    
    def __init__(self, canvas):
        self.canvas = canvas
        
        # AOI variables
        self.aoi_active = False
        self.aoi_rect = None
        self.aoi_overlay = None
        self.aoi_coords = [0, 0, 0, 0]  # [start_x, start_y, end_x, end_y]
        self.aoi_drawing = False
        self.aoi_adjusting = False
        self.aoi_adjust_handle = None
        self.aoi_handle_size = 8
        self.aoi_handles = []
        self.aoi_handle_coords = {}
        self.aoi_overlay_mode = "darken"
        self.opacity = 0.5
        
        # Display properties (will be set by parent)
        self.display_width = 0
        self.display_height = 0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.frame_width = 0
        self.frame_height = 0
    
    def set_display_properties(self, display_width, display_height, display_offset_x, display_offset_y, frame_width, frame_height):
        """Set display properties for coordinate transformation"""
        self.display_width = display_width
        self.display_height = display_height
        self.display_offset_x = display_offset_x
        self.display_offset_y = display_offset_y
        self.frame_width = frame_width
        self.frame_height = frame_height
    
    def set_active(self, active):
        """Set AOI drawing mode active/inactive"""
        self.aoi_active = active
    
    def set_opacity(self, opacity):
        """Set AOI overlay opacity"""
        self.opacity = opacity
    
    def clear_aoi(self):
        """Clear the AOI rectangle and associated elements"""
        if self.aoi_rect:
            self.canvas.delete(self.aoi_rect)
            self.aoi_rect = None
        
        # Clear handles
        for handle in self.aoi_handles:
            self.canvas.delete(handle)
        self.aoi_handles = []
        self.aoi_handle_coords = {}
        
        # Reset AOI coordinates
        self.aoi_coords = [0, 0, 0, 0]
        
        return "AOI cleared"
    
    def _is_within_video_frame(self, x, y):
        """Check if coordinates are within the video frame area (not the full canvas)"""
        if not hasattr(self, 'display_offset_x') or not hasattr(self, 'display_offset_y'):
            return True  # Allow if display properties not set yet
        
        # Video frame boundaries within the canvas
        video_x1 = self.display_offset_x
        video_y1 = self.display_offset_y
        video_x2 = self.display_offset_x + self.display_width
        video_y2 = self.display_offset_y + self.display_height
        
        return video_x1 <= x <= video_x2 and video_y1 <= y <= video_y2
    
    def _clamp_to_video_frame_x(self, x):
        """Clamp X coordinate to video frame boundaries"""
        if not hasattr(self, 'display_offset_x'):
            return x
        
        video_x1 = self.display_offset_x
        video_x2 = self.display_offset_x + self.display_width
        return max(video_x1, min(x, video_x2))
    
    def _clamp_to_video_frame_y(self, y):
        """Clamp Y coordinate to video frame boundaries"""
        if not hasattr(self, 'display_offset_y'):
            return y
        
        video_y1 = self.display_offset_y
        video_y2 = self.display_offset_y + self.display_height
        return max(video_y1, min(y, video_y2))
    
    def on_canvas_click(self, event):
        """Handle canvas click events for AOI drawing"""
        if not self.aoi_active:
            return None
        
        # Check if click is within video frame area
        if not self._is_within_video_frame(event.x, event.y):
            return "Click within video frame to draw AOI"
        
        # Start drawing new AOI
        self.aoi_drawing = True
        
        # Store canvas coordinates directly
        self.aoi_coords = [event.x, event.y, event.x, event.y]
        
        # Clear existing AOI
        if self.aoi_rect:
            self.canvas.delete(self.aoi_rect)
        
        # Create new rectangle using canvas coordinates directly
        self.aoi_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=2, fill="", tags=("aoi",)
        )
        
        return "AOI drawing started"
    
    def on_canvas_drag(self, event):
        """Handle canvas drag events for AOI drawing"""
        if not self.aoi_drawing or not self.aoi_rect:
            return None
        
        # Clamp coordinates to video frame area
        clamped_x = self._clamp_to_video_frame_x(event.x)
        clamped_y = self._clamp_to_video_frame_y(event.y)
        
        # Update AOI coordinates with clamped values
        self.aoi_coords[2] = clamped_x
        self.aoi_coords[3] = clamped_y
        
        # Update rectangle using clamped coordinates
        self.canvas.coords(self.aoi_rect, 
                          self.aoi_coords[0], self.aoi_coords[1], 
                          self.aoi_coords[2], self.aoi_coords[3])
        
        return "AOI being drawn"
    
    def on_canvas_release(self, event):
        """Handle canvas release events for AOI drawing"""
        if not self.aoi_drawing:
            return None
        
        self.aoi_drawing = False
        
        # Update final coordinates with clamping to video frame
        self.aoi_coords[2] = self._clamp_to_video_frame_x(event.x)
        self.aoi_coords[3] = self._clamp_to_video_frame_y(event.y)
        
        # Ensure coordinates are properly ordered
        if self.aoi_coords[0] > self.aoi_coords[2]:
            self.aoi_coords[0], self.aoi_coords[2] = self.aoi_coords[2], self.aoi_coords[0]
        if self.aoi_coords[1] > self.aoi_coords[3]:
            self.aoi_coords[1], self.aoi_coords[3] = self.aoi_coords[3], self.aoi_coords[1]
        
        # Convert from canvas coordinates to original image coordinates
        # First remove display offset, then scale to original image size
        if self.display_width > 0 and self.display_height > 0:
            # Remove display offset to get coordinates relative to the displayed image
            x1_display = self.aoi_coords[0] - self.display_offset_x
            y1_display = self.aoi_coords[1] - self.display_offset_y
            x2_display = self.aoi_coords[2] - self.display_offset_x
            y2_display = self.aoi_coords[3] - self.display_offset_y
            
            # Scale to original image size
            x1_orig = int(x1_display * (self.frame_width / self.display_width))
            y1_orig = int(y1_display * (self.frame_height / self.display_height))
            x2_orig = int(x2_display * (self.frame_width / self.display_width))
            y2_orig = int(y2_display * (self.frame_height / self.display_height))
            
            # Ensure coordinates are within image bounds
            x1_orig = max(0, min(x1_orig, self.frame_width - 1))
            y1_orig = max(0, min(y1_orig, self.frame_height - 1))
            x2_orig = max(0, min(x2_orig, self.frame_width - 1))
            y2_orig = max(0, min(y2_orig, self.frame_height - 1))
            
            # Store the original image coordinates for detection
            self.aoi_coords = [x1_orig, y1_orig, x2_orig, y2_orig]
            
            return f"AOI set: ({x1_orig},{y1_orig}) to ({x2_orig},{y2_orig})"
        
        return "AOI drawing completed"
    
    def get_aoi_coords(self):
        """Get current AOI coordinates in original image space"""
        if any(coord != 0 for coord in self.aoi_coords):
            return self.aoi_coords.copy()
        return None
    
    def has_aoi(self):
        """Check if AOI is set"""
        return self.aoi_rect is not None and any(coord != 0 for coord in self.aoi_coords)
    
    def apply_aoi_overlay(self, frame):
        """
        Apply AOI overlay to darken areas outside the AOI
        
        Args:
            frame: Input frame to apply overlay to
            
        Returns:
            numpy.ndarray: Frame with AOI overlay applied
        """
        if not self.has_aoi():
            return frame
        
        try:
            # Scale AOI coordinates to display frame size
            x1, y1, x2, y2 = self.aoi_coords
            
            # Ensure coordinates are in correct order
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            # Scale coordinates from original image size to display size
            if self.frame_width > 0 and self.frame_height > 0:
                x1_display = int(x1 * (self.display_width / self.frame_width))
                y1_display = int(y1 * (self.display_height / self.frame_height))
                x2_display = int(x2 * (self.display_width / self.frame_width))
                y2_display = int(y2 * (self.display_height / self.frame_height))
                
                # Ensure coordinates are within frame bounds
                x1_display = max(0, min(x1_display, self.display_width - 1))
                y1_display = max(0, min(y1_display, self.display_height - 1))
                x2_display = max(0, min(x2_display, self.display_width - 1))
                y2_display = max(0, min(y2_display, self.display_height - 1))
                
                # Create overlay
                overlay = frame.copy()
                
                if self.aoi_overlay_mode == "darken":
                    # Darken areas outside AOI
                    overlay[:y1_display, :] = overlay[:y1_display, :] * (1 - self.opacity)  # Top
                    overlay[y2_display:, :] = overlay[y2_display:, :] * (1 - self.opacity)  # Bottom
                    overlay[y1_display:y2_display, :x1_display] = overlay[y1_display:y2_display, :x1_display] * (1 - self.opacity)  # Left
                    overlay[y1_display:y2_display, x2_display:] = overlay[y1_display:y2_display, x2_display:] * (1 - self.opacity)  # Right
                else:
                    # Brighten AOI area
                    overlay[y1_display:y2_display, x1_display:x2_display] = np.clip(
                        overlay[y1_display:y2_display, x1_display:x2_display] * (1 + self.opacity), 0, 255
                    )
                
                return overlay.astype(np.uint8)
            
        except Exception as e:
            print(f"Error applying AOI overlay: {e}")
        
        return frame
    
    def apply_aoi_overlay_with_offset(self, frame, display_offset_x, display_offset_y):
        """
        Apply AOI overlay to frame accounting for display offset
        
        Args:
            frame: Input frame (final display frame)
            display_offset_x: X offset of video display within frame
            display_offset_y: Y offset of video display within frame
            
        Returns:
            numpy.ndarray: Frame with AOI overlay applied
        """
        if not self.has_aoi():
            return frame
        
        try:
            # Get AOI coordinates in original image space
            x1, y1, x2, y2 = self.aoi_coords
            
            # Ensure coordinates are in correct order
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            # Scale coordinates from original image size to display size
            if self.frame_width > 0 and self.frame_height > 0:
                x1_display = int(x1 * (self.display_width / self.frame_width))
                y1_display = int(y1 * (self.display_height / self.frame_height))
                x2_display = int(x2 * (self.display_width / self.frame_width))
                y2_display = int(y2 * (self.display_height / self.frame_height))
                
                # Add display offset to position within final frame
                x1_final = x1_display + display_offset_x
                y1_final = y1_display + display_offset_y
                x2_final = x2_display + display_offset_x
                y2_final = y2_display + display_offset_y
                
                # Ensure coordinates are within frame bounds
                frame_height, frame_width = frame.shape[:2]
                x1_final = max(0, min(x1_final, frame_width - 1))
                y1_final = max(0, min(y1_final, frame_height - 1))
                x2_final = max(0, min(x2_final, frame_width - 1))
                y2_final = max(0, min(y2_final, frame_height - 1))
                
                # Create overlay
                overlay = frame.copy()
                
                if self.aoi_overlay_mode == "darken":
                    # Darken areas outside AOI
                    # Top area
                    if y1_final > 0:
                        overlay[:y1_final, :] = overlay[:y1_final, :] * (1 - self.opacity)
                    # Bottom area
                    if y2_final < frame_height:
                        overlay[y2_final:, :] = overlay[y2_final:, :] * (1 - self.opacity)
                    # Left area
                    if x1_final > 0:
                        overlay[y1_final:y2_final, :x1_final] = overlay[y1_final:y2_final, :x1_final] * (1 - self.opacity)
                    # Right area
                    if x2_final < frame_width:
                        overlay[y1_final:y2_final, x2_final:] = overlay[y1_final:y2_final, x2_final:] * (1 - self.opacity)
                else:
                    # Brighten AOI area
                    overlay[y1_final:y2_final, x1_final:x2_final] = np.clip(
                        overlay[y1_final:y2_final, x1_final:x2_final] * (1 + self.opacity), 0, 255
                    )
                
                return overlay.astype(np.uint8)
            
        except Exception as e:
            print(f"Error applying AOI overlay with offset: {e}")
        
        return frame
