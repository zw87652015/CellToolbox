"""
Preview Canvas Module
Interactive canvas with zoom, pan, and drag-to-reorder features
"""
from PyQt5.QtWidgets import QWidget, QScrollArea, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QBrush, QFont
from PIL import Image
import numpy as np
from typing import Optional, Tuple, List


class PreviewCanvas(QScrollArea):
    """
    Interactive preview canvas with zoom and pan
    """
    
    # Signals
    cell_clicked = pyqtSignal(int, int)  # (col, row)
    cell_dragged = pyqtSignal(int, int, int, int)  # (from_col, from_row, to_col, to_row)
    cell_right_clicked = pyqtSignal(int, int)  # (col, row)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Canvas settings
        self.zoom_level = 1.0
        self.min_zoom = 0.05
        self.max_zoom = 8.0
        self.zoom_step = 0.1
        
        # Background color
        self.bg_color = QColor(238, 238, 238)  # #eeeeee
        
        # Grid settings
        self.show_grid = True
        self.grid_color = QColor(200, 200, 200, 100)
        
        # Layout info
        self.cols = 0
        self.rows = 0
        self.cell_width = 100
        self.cell_height = 100
        self.gap = 0
        self.border = 0
        
        # Current composite image
        self.composite_image: Optional[Image.Image] = None
        self.empty_cell_positions: List[Tuple[int, int]] = []
        
        # Interaction state
        self.hover_cell: Optional[Tuple[int, int]] = None
        self.drag_start_cell: Optional[Tuple[int, int]] = None
        self.is_dragging = False
        
        # Create label to display image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self._on_mouse_press
        self.image_label.mouseMoveEvent = self._on_mouse_move
        self.image_label.mouseReleaseEvent = self._on_mouse_release
        
        # Setup scroll area
        self.setWidget(self.image_label)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignCenter)
        
        # Set background
        self.setStyleSheet(f"background-color: {self.bg_color.name()};")
    
    def set_background_color(self, color: str):
        """Set background color (hex string like '#eeeeee')"""
        self.bg_color = QColor(color)
        self.setStyleSheet(f"background-color: {self.bg_color.name()};")
        self.refresh()
    
    def set_show_grid(self, show: bool):
        """Toggle grid display"""
        self.show_grid = show
        self.refresh()
    
    def set_layout_info(self, cols: int, rows: int, cell_width: int, cell_height: int,
                       gap: int = 0, border: int = 0):
        """Set layout parameters"""
        self.cols = cols
        self.rows = rows
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.gap = gap
        self.border = border
    
    def set_composite_image(self, image: Image.Image, 
                           empty_positions: List[Tuple[int, int]] = None):
        """Set the composite image to display"""
        self.composite_image = image
        self.empty_cell_positions = empty_positions or []
        self.refresh()
    
    def zoom_in(self):
        """Zoom in"""
        self.set_zoom(self.zoom_level + self.zoom_step)
    
    def zoom_out(self):
        """Zoom out"""
        self.set_zoom(self.zoom_level - self.zoom_step)
    
    def zoom_fit(self):
        """Fit to window"""
        if not self.composite_image:
            return
        
        # Calculate zoom to fit
        viewport_width = self.viewport().width()
        viewport_height = self.viewport().height()
        image_width = self.composite_image.width
        image_height = self.composite_image.height
        
        zoom_w = viewport_width / image_width
        zoom_h = viewport_height / image_height
        zoom = min(zoom_w, zoom_h) * 0.95  # 95% to add margin
        
        self.set_zoom(zoom)
    
    def zoom_100(self):
        """Reset to 100%"""
        self.set_zoom(1.0)
    
    def set_zoom(self, zoom: float):
        """Set zoom level"""
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, zoom))
        self.refresh()
    
    def get_zoom_percent(self) -> int:
        """Get current zoom as percentage"""
        return int(self.zoom_level * 100)
    
    def refresh(self):
        """Refresh the display"""
        if not self.composite_image:
            return
        
        # Convert PIL Image to QPixmap
        img = self.composite_image
        
        # Draw grid and empty cells if needed
        if self.show_grid or self.empty_cell_positions:
            img = img.copy()
            self._draw_overlays(img)
        
        # Convert to QImage
        if img.mode == 'RGB':
            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
        elif img.mode == 'RGBA':
            data = img.tobytes('raw', 'RGBA')
            qimage = QImage(data, img.width, img.height, img.width * 4, QImage.Format_RGBA8888)
        else:
            img = img.convert('RGB')
            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
        
        # Apply zoom
        scaled_width = int(img.width * self.zoom_level)
        scaled_height = int(img.height * self.zoom_level)
        pixmap = QPixmap.fromImage(qimage).scaled(
            scaled_width, scaled_height, 
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        # Update label
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())
    
    def _draw_overlays(self, img: Image.Image):
        """Draw grid lines and empty cell indicators"""
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Draw grid
        if self.show_grid:
            grid_color = (200, 200, 200, 100)
            for row in range(self.rows + 1):
                y = self.border + row * (self.cell_height + self.gap) - self.gap // 2
                draw.line([(self.border, y), (img.width - self.border, y)], 
                         fill=grid_color, width=1)
            
            for col in range(self.cols + 1):
                x = self.border + col * (self.cell_width + self.gap) - self.gap // 2
                draw.line([(x, self.border), (x, img.height - self.border)], 
                         fill=grid_color, width=1)
        
        # Draw empty cell indicators (diagonal hatching)
        if self.empty_cell_positions:
            for col, row in self.empty_cell_positions:
                x = self.border + col * (self.cell_width + self.gap)
                y = self.border + row * (self.cell_height + self.gap)
                
                # Semi-transparent gray overlay
                overlay_color = (128, 128, 128, 80)
                draw.rectangle([x, y, x + self.cell_width, y + self.cell_height],
                             fill=overlay_color)
                
                # Diagonal lines
                line_color = (100, 100, 100, 150)
                spacing = 20
                for offset in range(-self.cell_height, self.cell_width, spacing):
                    x1 = x + offset
                    y1 = y
                    x2 = x + offset + self.cell_height
                    y2 = y + self.cell_height
                    draw.line([(x1, y1), (x2, y2)], fill=line_color, width=2)
    
    def _get_cell_at_pos(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Get cell coordinates at pixel position"""
        if not self.composite_image:
            return None
        
        # Convert from scaled coordinates to original
        orig_x = int(x / self.zoom_level)
        orig_y = int(y / self.zoom_level)
        
        # Check if within border
        if orig_x < self.border or orig_y < self.border:
            return None
        if orig_x >= self.composite_image.width - self.border:
            return None
        if orig_y >= self.composite_image.height - self.border:
            return None
        
        # Calculate cell
        x_in_grid = orig_x - self.border
        y_in_grid = orig_y - self.border
        
        col = x_in_grid // (self.cell_width + self.gap)
        row = y_in_grid // (self.cell_height + self.gap)
        
        # Check if in gap
        x_in_cell = x_in_grid % (self.cell_width + self.gap)
        y_in_cell = y_in_grid % (self.cell_height + self.gap)
        
        if x_in_cell >= self.cell_width or y_in_cell >= self.cell_height:
            return None
        
        # Check bounds
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return col, row
        
        return None
    
    def _on_mouse_press(self, event):
        """Handle mouse press"""
        pos = event.pos()
        cell = self._get_cell_at_pos(pos.x(), pos.y())
        
        if cell:
            if event.button() == Qt.LeftButton:
                self.drag_start_cell = cell
                self.is_dragging = False
                self.cell_clicked.emit(cell[0], cell[1])
            elif event.button() == Qt.RightButton:
                self.cell_right_clicked.emit(cell[0], cell[1])
    
    def _on_mouse_move(self, event):
        """Handle mouse move"""
        pos = event.pos()
        cell = self._get_cell_at_pos(pos.x(), pos.y())
        
        # Update hover
        if cell != self.hover_cell:
            self.hover_cell = cell
            # Could trigger hover visual feedback here
        
        # Handle drag
        if event.buttons() & Qt.LeftButton and self.drag_start_cell:
            if cell and cell != self.drag_start_cell:
                if not self.is_dragging:
                    self.is_dragging = True
    
    def _on_mouse_release(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton and self.is_dragging:
            pos = event.pos()
            cell = self._get_cell_at_pos(pos.x(), pos.y())
            
            if cell and self.drag_start_cell and cell != self.drag_start_cell:
                # Emit drag signal
                self.cell_dragged.emit(
                    self.drag_start_cell[0], self.drag_start_cell[1],
                    cell[0], cell[1]
                )
        
        self.drag_start_cell = None
        self.is_dragging = False
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        # Zoom with Ctrl+Wheel
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            # Normal scroll
            super().wheelEvent(event)
