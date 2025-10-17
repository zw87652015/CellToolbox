"""
Worker Threads for Background Processing
"""
from PyQt5.QtCore import QThread, pyqtSignal


class CompositeThread(QThread):
    """Thread for creating composite image"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    
    def __init__(self, compositor, cell_width, cell_height, numbering_renderer, 
                 scale_bar_renderer, scale_bar_position, gap, border, bg_color):
        super().__init__()
        self.compositor = compositor
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.numbering_renderer = numbering_renderer
        self.scale_bar_renderer = scale_bar_renderer
        self.scale_bar_position = scale_bar_position
        self.gap = gap
        self.border = border
        self.bg_color = bg_color
    
    def run(self):
        """Create composite"""
        try:
            self.compositor.set_progress_callback(lambda p, m: self.progress.emit(p, m))
            composite = self.compositor.create_composite(
                self.cell_width, self.cell_height, self.numbering_renderer,
                self.scale_bar_renderer, self.scale_bar_position,
                self.gap, self.border, self.bg_color
            )
            self.finished.emit(composite)
        except Exception as e:
            print(f"Error in composite thread: {e}")
            import traceback
            traceback.print_exc()
            # Emit None to indicate failure
            self.finished.emit(None)


class ExportThread(QThread):
    """Thread for export operations"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, list)
    
    def __init__(self, export_manager, composite_image, cols, rows, cell_width, cell_height):
        super().__init__()
        self.export_manager = export_manager
        self.composite_image = composite_image
        self.cols = cols
        self.rows = rows
        self.cell_width = cell_width
        self.cell_height = cell_height
    
    def run(self):
        """Run export"""
        self.export_manager.set_progress_callback(lambda p, m: self.progress.emit(p, m))
        success, message, files = self.export_manager.export(
            self.composite_image, self.cols, self.rows, 
            self.cell_width, self.cell_height
        )
        self.finished.emit(success, message, files)
