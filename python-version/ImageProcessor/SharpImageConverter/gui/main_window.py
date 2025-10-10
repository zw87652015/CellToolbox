"""
主窗口
整合图像显示和控制面板，提供完整的用户界面
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QStatusBar, QMenuBar, QMenu, QAction,
                             QMessageBox, QProgressDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import sys
import logging

from .image_viewer import ImageViewer
from .controls import ControlPanel
from core.image_processor import ImageProcessor
from core.utils import validate_tiff_file, format_file_size

logger = logging.getLogger(__name__)


class ProcessingThread(QThread):
    """图像处理线程"""
    
    finished = pyqtSignal(object)  # 处理完成，传递结果
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(int)  # 进度信号
    
    def __init__(self, processor, scale_factor):
        super().__init__()
        self.processor = processor
        self.scale_factor = scale_factor
        
    def run(self):
        """执行处理"""
        try:
            result = self.processor.expand_current_image(self.scale_factor)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ProcessingThreadWithChannel(QThread):
    """支持通道选择的图像处理线程"""
    
    finished = pyqtSignal(object)  # 处理完成，传递结果
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(int)  # 进度信号
    
    def __init__(self, processor, scale_factor, channel=None):
        super().__init__()
        self.processor = processor
        self.scale_factor = scale_factor
        self.channel = channel
        
    def run(self):
        """执行处理"""
        try:
            result = self.processor.expand_current_image(self.scale_factor, self.channel)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.processor = ImageProcessor()
        self.processing_thread = None
        
        self.init_ui()
        self.connect_signals()
        
        logger.info("应用启动")
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("灰度TIFF像素放大工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分隔器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：图像显示
        self.image_viewer = ImageViewer()
        splitter.addWidget(self.image_viewer)
        
        # 右侧：控制面板
        self.control_panel = ControlPanel()
        self.control_panel.setMaximumWidth(350)
        splitter.addWidget(self.control_panel)
        
        # 设置分隔器比例
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态栏标签
        self.pixel_info_label = QLabel()
        self.zoom_info_label = QLabel()
        
        self.status_bar.addPermanentWidget(self.pixel_info_label)
        self.status_bar.addPermanentWidget(self.zoom_info_label)
        
        self.update_status("就绪")
        
        # 创建菜单栏（必须在控件创建之后）
        self.create_menu_bar()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开图像...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.control_panel.browse_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出图像...", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self.control_panel.export_image)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 查看菜单
        view_menu = menubar.addMenu("查看")
        
        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.image_viewer.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.image_viewer.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_fit_action = QAction("适应窗口", self)
        zoom_fit_action.setShortcut("Ctrl+0")
        zoom_fit_action.triggered.connect(self.image_viewer.zoom_fit)
        view_menu.addAction(zoom_fit_action)
        
        zoom_100_action = QAction("实际大小 (100%)", self)
        zoom_100_action.setShortcut("Ctrl+1")
        zoom_100_action.triggered.connect(self.image_viewer.zoom_100)
        view_menu.addAction(zoom_100_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def connect_signals(self):
        """连接信号"""
        # 控制面板信号
        self.control_panel.file_selected.connect(self.on_file_selected)
        self.control_panel.preview_requested.connect(self.on_preview_requested)
        self.control_panel.export_requested.connect(self.on_export_requested)
        
        # 图像查看器信号
        self.image_viewer.pixel_info_updated.connect(self.on_pixel_info_updated)
        self.image_viewer.zoom_changed.connect(self.on_zoom_changed)
        
    def on_file_selected(self, file_path):
        """文件选择处理"""
        try:
            # 验证文件
            if not validate_tiff_file(file_path):
                QMessageBox.warning(self, "错误", "无效的图像文件\n仅支持TIFF和PNG格式")
                return
            
            self.update_status("正在加载图像...")
            
            # 获取选择的通道
            channel = self.control_panel.get_selected_channel()
            
            # 检查文件类型
            from pathlib import Path
            file_ext = Path(file_path).suffix.lower()
            is_png = file_ext == '.png'
            
            # 加载图像（支持RGB）
            img_array, size, bit_depth, is_rgb = self.processor.load_tiff(file_path, channel)
            
            # PNG RGB图像禁用通道选择器
            if is_png and is_rgb:
                self.control_panel.set_channel_enabled(False)
                logger.info("PNG RGB图像：禁用通道选择器")
            elif is_rgb:
                self.control_panel.set_channel_enabled(True)
                logger.info("TIFF RGB图像：启用通道选择器")
            
            # 获取显示图像（可能是伪色图）
            display_img = self.processor.get_display_image(img_array, use_pseudocolor=True)
            
            # 显示图像
            self.image_viewer.set_image(display_img)
            
            # 更新控制面板信息（传递RGB标志，但PNG不显示为RGB）
            display_is_rgb = is_rgb and not is_png  # PNG显示为普通图像
            self.control_panel.update_info(size, bit_depth, display_is_rgb)
            
            # 适应窗口
            self.image_viewer.zoom_fit()
            
            self.update_status(f"已加载: {file_path}")
            
            # 显示加载信息
            if is_png and is_rgb:
                img_type = "PNG彩色图像"
            elif is_rgb:
                img_type = "TIFF RGB图像"
            else:
                img_type = "灰度图像"
            channel_info = f"\n选择通道: {channel}" if (channel and not is_png) else ""
            QMessageBox.information(
                self,
                "加载成功",
                f"图像已加载\n类型: {img_type}\n尺寸: {size[0]} × {size[1]}\n位深度: {bit_depth}位{channel_info}"
            )
            
        except Exception as e:
            logger.error(f"加载图像失败: {e}")
            QMessageBox.critical(self, "错误", f"加载图像失败:\n{str(e)}")
            self.update_status("加载失败")
            
    def on_preview_requested(self, scale_factor):
        """预览请求处理"""
        try:
            # 检查内存
            memory_mb = self.processor.get_memory_estimate(scale_factor)
            if memory_mb > 1024:
                reply = QMessageBox.question(
                    self,
                    "内存警告",
                    f"放大后的图像将占用约 {memory_mb / 1024:.2f} GB 内存\n是否继续?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # 获取选择的通道
            channel = self.control_panel.get_selected_channel()
            
            self.update_status(f"正在放大图像 ({scale_factor}倍)...")
            self.control_panel.set_enabled(False)
            
            # 创建处理线程（传递通道参数）
            self.processing_thread = ProcessingThreadWithChannel(self.processor, scale_factor, channel)
            self.processing_thread.finished.connect(self.on_processing_finished)
            self.processing_thread.error.connect(self.on_processing_error)
            
            # 启动线程
            self.processing_thread.start()
            
        except Exception as e:
            logger.error(f"预览失败: {e}")
            QMessageBox.critical(self, "错误", f"预览失败:\n{str(e)}")
            self.update_status("预览失败")
            self.control_panel.set_enabled(True)
            
    def on_processing_finished(self, result):
        """处理完成"""
        try:
            # 获取显示图像（可能是伪色图）
            display_img = self.processor.get_display_image(result, use_pseudocolor=True)
            
            # 显示结果
            self.image_viewer.set_image(display_img)
            self.image_viewer.zoom_fit()
            
            self.update_status(f"预览完成 ({self.processor.scale_factor}倍放大)")
            
            # 显示信息时说明是否使用了伪色图
            pseudocolor_info = ""
            if self.processor.selected_channel in ['R', 'G', 'B']:
                pseudocolor_info = f"\n通道: {self.processor.selected_channel} (伪色图)"
            
            # 获取尺寸（处理2D和3D数组）
            if len(result.shape) == 2:
                h, w = result.shape
            else:
                h, w = result.shape[:2]
            
            QMessageBox.information(
                self,
                "预览完成",
                f"图像已放大 {self.processor.scale_factor} 倍\n"
                f"输出尺寸: {w} × {h}{pseudocolor_info}"
            )
            
        except Exception as e:
            logger.error(f"显示处理结果失败: {e}")
            QMessageBox.critical(self, "错误", f"显示失败:\n{str(e)}")
        finally:
            self.control_panel.set_enabled(True)
            
    def on_processing_error(self, error_msg):
        """处理错误"""
        logger.error(f"处理错误: {error_msg}")
        QMessageBox.critical(self, "处理错误", error_msg)
        self.update_status("处理失败")
        self.control_panel.set_enabled(True)
        
    def on_export_requested(self, save_path, format_str, bit_depth):
        """导出请求处理"""
        try:
            if self.processor.expanded_image is None:
                QMessageBox.warning(self, "警告", "请先预览图像再导出")
                return
            
            self.update_status(f"正在导出图像: {save_path}")
            
            # 保存图像
            success = self.processor.save_image(
                save_path,
                format=format_str,
                bit_depth=bit_depth
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "导出成功",
                    f"图像已成功保存到:\n{save_path}"
                )
                self.update_status(f"导出成功: {save_path}")
            else:
                QMessageBox.warning(self, "导出失败", "图像保存失败，请查看日志")
                self.update_status("导出失败")
                
        except Exception as e:
            logger.error(f"导出失败: {e}")
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
            self.update_status("导出失败")
            
    def on_pixel_info_updated(self, x, y, value):
        """像素信息更新"""
        self.pixel_info_label.setText(f"  坐标: ({x}, {y})  灰度值: {value}  ")
        
    def on_zoom_changed(self, zoom_factor):
        """缩放改变"""
        self.zoom_info_label.setText(f"  缩放: {zoom_factor * 100:.0f}%  ")
        
    def update_status(self, message):
        """更新状态栏"""
        self.status_bar.showMessage(message)
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "<h3>灰度TIFF像素放大工具</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>使用最近邻插值算法进行像素级图像放大</p>"
            "<p>支持8位和16位灰度TIFF图像</p>"
            "<hr>"
            "<p><b>快捷键:</b></p>"
            "<ul>"
            "<li>Ctrl+O: 打开图像</li>"
            "<li>Ctrl+S: 导出图像</li>"
            "<li>Ctrl++: 放大视图</li>"
            "<li>Ctrl+-: 缩小视图</li>"
            "<li>Ctrl+0: 适应窗口</li>"
            "<li>Ctrl+1: 实际大小</li>"
            "<li>Ctrl+滚轮: 缩放</li>"
            "</ul>"
        )
        
    def closeEvent(self, event):
        """关闭事件"""
        # 停止处理线程
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
        
        logger.info("应用关闭")
        event.accept()


# 导入QLabel（之前忘记导入了）
from PyQt5.QtWidgets import QLabel
