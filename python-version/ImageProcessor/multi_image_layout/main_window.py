"""
Main Window Implementation
Complete GUI with all panels and interactions
"""
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor
from PIL import Image

from image_manager import ImageManager
from layout_engine import LayoutEngine, LayoutPreset, EmptyCellStrategy
from numbering import NumberingStyle, NumberingRenderer, NumberingFormat, NumberingPosition
from scale_bar import ScaleBarStyle, ScaleBarRenderer
from export_manager import ExportManager, ExportSettings, ExportFormat
from preview_canvas import PreviewCanvas
from layout_compositor import LayoutCompositor
from ui_panels import ParameterPanel
from worker_threads import CompositeThread, ExportThread


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Core components
        self.image_manager = ImageManager()
        self.layout_engine = LayoutEngine()
        self.numbering_style = NumberingStyle()
        self.scale_bar_style = ScaleBarStyle()
        self.export_settings = ExportSettings()
        
        # State
        self.current_composite = None
        self.auto_refresh = True
        
        # Thread references
        self.composite_thread = None
        self.export_thread = None
        self.progress_dialog = None
        self.export_progress = None
        
        # UI setup
        self.init_ui()
        self.connect_signals()
        
        # Show window
        self.showMaximized()
        self.update_status("就绪 - 可拖拽文件夹到窗口加载图片")
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("多图拼接工具 - Multi-Image Layout")
        self.setMinimumSize(1200, 800)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left parameter panel with scroll area
        self.param_panel = ParameterPanel(self)
        
        # Wrap parameter panel in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.param_panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumWidth(320)
        
        splitter.addWidget(scroll_area)
        
        # Right preview canvas
        self.preview_canvas = PreviewCanvas()
        splitter.addWidget(self.preview_canvas)
        
        splitter.setSizes([320, 880])
        main_layout.addWidget(splitter)
        
        # Menu and toolbar
        self.create_menu_bar()
        self.create_toolbar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("打开文件夹", self.load_folder)
        file_menu.addAction("打开文件", self.load_files)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)
        
        # View menu
        view_menu = menubar.addMenu("视图")
        view_menu.addAction("放大", self.preview_canvas.zoom_in)
        view_menu.addAction("缩小", self.preview_canvas.zoom_out)
        view_menu.addAction("适应窗口", self.preview_canvas.zoom_fit)
        view_menu.addAction("实际大小", self.preview_canvas.zoom_100)
        view_menu.addSeparator()
        
        self.action_grid = QAction("显示网格", self)
        self.action_grid.setCheckable(True)
        self.action_grid.setChecked(True)
        self.action_grid.triggered.connect(lambda: self.preview_canvas.set_show_grid(self.action_grid.isChecked()))
        view_menu.addAction(self.action_grid)
        
        # Help menu
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("关于", self.show_about)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        self.zoom_label = QLabel(" 缩放: 100% ")
        toolbar.addWidget(self.zoom_label)
        
        self.chk_auto_refresh = QCheckBox("自动刷新")
        self.chk_auto_refresh.setChecked(True)
        toolbar.addWidget(self.chk_auto_refresh)
    
    def connect_signals(self):
        """Connect all signals"""
        # From parameter panel
        self.param_panel.load_folder_requested.connect(self.load_folder)
        self.param_panel.load_files_requested.connect(self.load_files)
        self.param_panel.parameters_changed.connect(self.on_parameters_changed)
        self.param_panel.update_preview_requested.connect(self.update_preview)
        self.param_panel.export_requested.connect(self.export_layout)
        
        # Auto-refresh
        self.chk_auto_refresh.stateChanged.connect(lambda: setattr(self, 'auto_refresh', self.chk_auto_refresh.isChecked()))
        
        # Preview canvas
        self.preview_canvas.cell_dragged.connect(self.on_cell_dragged)
    
    def load_folder(self):
        """Load images from folder (with dialog)"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if not folder:
            return
        
        self.load_folder_path(folder)
    
    def load_folder_path(self, folder: str):
        """Load images from folder path"""
        if not folder or not os.path.isdir(folder):
            return
        
        self.update_status(f"正在加载: {folder}...")
        
        success, message = self.image_manager.load_from_folder(folder)
        
        if not success and "宽高比" in message:
            reply = QMessageBox.question(
                self, "宽高比不匹配",
                f"{message}\n\n是(Yes) - 自动裁切\n否(No) - 取消",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                count = self.image_manager.crop_incompatible_images()
                self.update_status(f"已裁切 {count} 张图片")
                self.on_images_loaded()
            return
        elif not success:
            QMessageBox.warning(self, "加载失败", message)
            self.update_status("加载失败")
            return
        
        self.update_status(message)
        self.on_images_loaded()
    
    def load_files(self):
        """Load specific files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "Images (*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.webp)"
        )
        if not files:
            return
        
        success, message = self.image_manager.load_from_files(files)
        
        if not success and "宽高比" in message:
            reply = QMessageBox.question(
                self, "宽高比不匹配",
                f"{message}\n\n是(Yes) - 自动裁切\n否(No) - 取消",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                count = self.image_manager.crop_incompatible_images()
                self.update_status(f"已裁切 {count} 张图片")
                self.on_images_loaded()
            return
        elif not success:
            QMessageBox.warning(self, "加载失败", message)
            return
        
        self.update_status(message)
        self.on_images_loaded()
    
    def on_images_loaded(self):
        """Handle images loaded"""
        count = self.image_manager.get_image_count()
        width, height = self.image_manager.get_base_size()
        
        self.param_panel.set_image_info(count, width, height)
        self.param_panel.set_original_size(width, height)  # Set for scale calculation
        self.layout_engine.set_image_count(count)
        
        # Suggest layout
        suggestions = self.layout_engine.suggest_optimal_layout(count)
        if suggestions:
            cols, rows, reason = suggestions[0]
            self.param_panel.set_layout(cols, rows)
            self.update_status(f"建议布局: {reason}")
        
        # Auto-refresh with longer delay for large image sets
        if self.auto_refresh:
            delay = 1000 if count > 20 else 500
            QTimer.singleShot(delay, self.update_preview)
    
    def on_parameters_changed(self):
        """Handle parameter change"""
        if self.auto_refresh:
            QTimer.singleShot(200, self.update_preview)
    
    def on_cell_dragged(self, from_col, from_row, to_col, to_row):
        """Handle cell drag"""
        from_idx = from_row * self.layout_engine.cols + from_col
        to_idx = to_row * self.layout_engine.cols + to_col
        
        self.image_manager.swap_images(from_idx, to_idx)
        self.update_preview()
        self.update_status(f"已交换 {from_idx + 1} 和 {to_idx + 1}")
    
    def update_preview(self):
        """Update preview canvas"""
        if self.image_manager.get_image_count() == 0:
            QMessageBox.warning(self, "提示", "请先加载图片")
            return
        
        # Check if thread is already running
        try:
            if self.composite_thread and self.composite_thread.isRunning():
                self.update_status("预览正在生成中，请稍候...")
                return
        except RuntimeError:
            # Thread object has been deleted, safe to proceed
            pass
        
        # Get parameters
        params = self.param_panel.get_parameters()
        
        # Update layout engine
        self.layout_engine.set_layout(params['cols'], params['rows'])
        self.layout_engine.set_empty_cell_strategy(params['empty_strategy'])
        
        # Update numbering style
        self.numbering_style.enabled = params['numbering_enabled']
        self.numbering_style.format = params['numbering_format']
        self.numbering_style.position = params['numbering_position']
        self.numbering_style.font_size = params['font_size']
        self.numbering_style.color = params['text_color']
        self.numbering_style.with_background = params['numbering_bg']
        
        # Update scale bar style
        self.scale_bar_style.enabled = params['scalebar_enabled']
        self.scale_bar_style.objective = params['scalebar_objective']
        self.scale_bar_style.scale_length_um = params['scalebar_length']
        
        # Validate
        is_valid, message = self.layout_engine.validate_layout()
        if not is_valid:
            QMessageBox.warning(self, "布局无效", message)
            return
        
        # Create renderers
        compositor = LayoutCompositor(self.image_manager, self.layout_engine)
        numbering_renderer = NumberingRenderer(self.numbering_style)
        scale_bar_renderer = ScaleBarRenderer(self.scale_bar_style)
        
        # Create preview in thread
        self.composite_thread = CompositeThread(
            compositor, params['cell_width'], params['cell_height'],
            numbering_renderer, scale_bar_renderer, params['scalebar_position'],
            0, 0, (255, 255, 255)
        )
        
        # Progress dialog
        self.progress_dialog = QProgressDialog("创建预览...", "取消", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(500)  # Show after 500ms
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.canceled.connect(self.on_preview_canceled)
        
        self.composite_thread.progress.connect(self.progress_dialog.setValue)
        self.composite_thread.finished.connect(self.on_preview_ready)
        self.composite_thread.finished.connect(self.on_composite_thread_finished)
        self.composite_thread.start()
    
    def on_composite_thread_finished(self):
        """Handle composite thread cleanup"""
        if self.composite_thread:
            self.composite_thread.deleteLater()
            self.composite_thread = None
    
    def on_preview_canceled(self):
        """Handle preview canceled"""
        try:
            if self.composite_thread and self.composite_thread.isRunning():
                self.composite_thread.terminate()
                self.composite_thread.wait(1000)  # Wait max 1 second
        except RuntimeError:
            pass
        self.update_status("预览已取消")
    
    def on_preview_ready(self, composite):
        """Handle preview ready"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        # Check if composite creation failed
        if composite is None:
            QMessageBox.critical(self, "错误", "预览生成失败，请检查图片文件")
            self.update_status("预览生成失败")
            return
        
        self.current_composite = composite
        
        # Get empty cell positions
        empty_positions = self.layout_engine.get_empty_cell_positions()
        
        # Update preview canvas
        params = self.param_panel.get_parameters()
        self.preview_canvas.set_layout_info(
            params['cols'], params['rows'],
            params['cell_width'], params['cell_height'], 0, 0
        )
        self.preview_canvas.set_composite_image(composite, empty_positions)
        self.preview_canvas.zoom_fit()
        
        self.update_zoom_label()
        self.update_status("预览已更新")
    
    def export_layout(self):
        """Export layout"""
        if not self.current_composite:
            QMessageBox.warning(self, "提示", "请先生成预览")
            return
        
        # Check if export is already running
        try:
            if self.export_thread and self.export_thread.isRunning():
                QMessageBox.warning(self, "提示", "导出正在进行中")
                return
        except RuntimeError:
            # Thread object has been deleted, safe to proceed
            pass
        
        # Get export parameters
        export_params = self.param_panel.get_export_parameters()
        
        if not export_params['output_dir']:
            QMessageBox.warning(self, "提示", "请选择输出目录")
            return
        
        if not export_params['formats']:
            QMessageBox.warning(self, "提示", "请至少选择一种输出格式")
            return
        
        # Update export settings
        self.export_settings.formats = export_params['formats']
        self.export_settings.dpi = export_params['dpi']
        self.export_settings.output_dir = export_params['output_dir']
        
        # Create export manager
        export_manager = ExportManager(self.export_settings)
        
        # Get layout params
        params = self.param_panel.get_parameters()
        
        # Start export thread
        self.export_thread = ExportThread(
            export_manager, self.current_composite,
            params['cols'], params['rows'],
            params['cell_width'], params['cell_height']
        )
        
        # Progress dialog
        self.export_progress = QProgressDialog("导出中...", None, 0, 100, self)
        self.export_progress.setWindowModality(Qt.WindowModal)
        self.export_progress.setMinimumDuration(0)
        
        self.export_thread.progress.connect(lambda p, m: self.export_progress.setLabelText(m))
        self.export_thread.progress.connect(self.export_progress.setValue)
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.finished.connect(self.on_export_thread_finished)
        self.export_thread.start()
    
    def on_export_thread_finished(self):
        """Handle export thread cleanup"""
        if self.export_thread:
            self.export_thread.deleteLater()
            self.export_thread = None
    
    def on_export_finished(self, success, message, files):
        """Handle export finished"""
        if self.export_progress:
            self.export_progress.close()
        
        if success:
            reply = QMessageBox.information(
                self, "导出成功",
                f"{message}\n\n是否打开输出文件夹？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                import subprocess
                subprocess.Popen(f'explorer "{self.export_settings.output_dir}"')
        else:
            QMessageBox.critical(self, "导出失败", message)
    
    def update_zoom_label(self):
        """Update zoom label"""
        percent = self.preview_canvas.get_zoom_percent()
        self.zoom_label.setText(f" 缩放: {percent}% ")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.setText(message)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "关于",
            "多图拼接工具 v1.0\n\n"
            "支持任意张同比例图片的自动拼图\n"
            "可选单元格尺寸、拼图方案、编号样式\n"
            "支持多种输出格式(PNG, JPG, TIFF, PDF, SVG, EPS)\n\n"
            "CellToolbox Project"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Check if threads are running
        threads_running = False
        
        try:
            if self.composite_thread and self.composite_thread.isRunning():
                threads_running = True
        except RuntimeError:
            pass
        
        try:
            if self.export_thread and self.export_thread.isRunning():
                threads_running = True
        except RuntimeError:
            pass
        
        if threads_running:
            reply = QMessageBox.question(
                self, "确认退出",
                "后台任务正在运行，确定要退出吗？\n\n线程将被强制终止。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # Terminate threads
            try:
                if self.composite_thread and self.composite_thread.isRunning():
                    self.composite_thread.terminate()
                    self.composite_thread.wait(1000)
            except RuntimeError:
                pass
            
            try:
                if self.export_thread and self.export_thread.isRunning():
                    self.export_thread.terminate()
                    self.export_thread.wait(1000)
            except RuntimeError:
                pass
        
        # Close progress dialogs
        if self.progress_dialog:
            self.progress_dialog.close()
        if self.export_progress:
            self.export_progress.close()
        
        # Release image cache
        self.image_manager.release_all_caches()
        
        event.accept()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            # Check if any URL is a folder
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.isdir(path):
                        event.acceptProposedAction()
                        self.update_status("释放以加载文件夹中的图片")
                        return
            # If no folder found, check for image files
            for url in urls:
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.isfile(path):
                        ext = os.path.splitext(path)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp']:
                            event.acceptProposedAction()
                            self.update_status("释放以加载图片文件")
                            return
    
    def dropEvent(self, event):
        """Handle drop event"""
        urls = event.mimeData().urls()
        if not urls:
            return
        
        # Collect folders and files
        folders = []
        files = []
        
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    folders.append(path)
                elif os.path.isfile(path):
                    ext = os.path.splitext(path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp']:
                        files.append(path)
        
        # Priority: folders first
        if folders:
            # Load the first folder
            folder = folders[0]
            if len(folders) > 1:
                QMessageBox.information(
                    self, "提示", 
                    f"检测到 {len(folders)} 个文件夹，将加载第一个:\n{folder}"
                )
            self.load_folder_path(folder)
            event.acceptProposedAction()
        elif files:
            # Load files
            self.load_files_list(files)
            event.acceptProposedAction()
        else:
            QMessageBox.warning(self, "无效拖放", "请拖放图片文件夹或图片文件")
    
    def load_files_list(self, file_paths: list):
        """Load images from file list"""
        if not file_paths:
            return
        
        self.update_status(f"正在加载 {len(file_paths)} 个文件...")
        
        success, message = self.image_manager.load_from_files(file_paths)
        
        if not success and "宽高比" in message:
            reply = QMessageBox.question(
                self, "宽高比不匹配",
                f"{message}\n\n是(Yes) - 自动裁切\n否(No) - 取消",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                count = self.image_manager.crop_incompatible_images()
                self.update_status(f"已裁切 {count} 张图片")
                self.on_images_loaded()
            return
        elif not success:
            QMessageBox.warning(self, "加载失败", message)
            self.update_status("加载失败")
            return
        
        self.update_status(message)
        self.on_images_loaded()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
