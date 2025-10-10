"""
图像显示组件
提供图像显示、缩放、平移和像素信息显示功能
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QCursor
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ImageViewer(QWidget):
    """图像显示组件"""
    
    # 信号
    pixel_info_updated = pyqtSignal(int, int, int)  # x, y, value
    zoom_changed = pyqtSignal(float)  # zoom_factor
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.image_array = None
        self.display_image = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 20.0
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        # 创建图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setText("未加载图像")
        self.image_label.setStyleSheet("QLabel { background-color: #2b2b2b; color: #888; }")
        
        # 启用鼠标追踪
        self.image_label.setMouseTracking(True)
        self.image_label.mouseMoveEvent = self.on_mouse_move
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # 设置鼠标滚轮事件
        self.scroll_area.wheelEvent = self.on_wheel_event
        
    def set_image(self, image_array):
        """
        设置要显示的图像
        
        Args:
            image_array: numpy数组（灰度图像或RGB图像）
        """
        if image_array is None:
            return
        
        self.image_array = image_array
        self.zoom_factor = 1.0
        self.update_display()
        
        logger.info(f"图像已加载到查看器: {image_array.shape}")
        
    def update_display(self):
        """更新图像显示"""
        if self.image_array is None:
            return
        
        # 转换为8位用于显示
        display_array = self.normalize_for_display(self.image_array)
        
        # 判断是灰度图还是RGB图
        is_rgb = len(display_array.shape) == 3
        
        # 应用缩放
        if self.zoom_factor != 1.0:
            if is_rgb:
                h, w, c = display_array.shape
                new_h = int(h * self.zoom_factor)
                new_w = int(w * self.zoom_factor)
                
                # 对RGB三个通道分别缩放
                display_array = np.repeat(
                    np.repeat(display_array, int(self.zoom_factor), axis=0),
                    int(self.zoom_factor), axis=1
                )[:new_h, :new_w, :]
            else:
                h, w = display_array.shape
                new_h = int(h * self.zoom_factor)
                new_w = int(w * self.zoom_factor)
                
                # 使用最近邻插值缩放（保持像素块效果）
                display_array = np.repeat(
                    np.repeat(display_array, int(self.zoom_factor), axis=0),
                    int(self.zoom_factor), axis=1
                )[:new_h, :new_w]
        
        # 转换为QImage
        # 确保数组是连续的
        display_array = np.ascontiguousarray(display_array)
        
        if is_rgb:
            h, w, c = display_array.shape
            bytes_per_line = w * 3
            qimage = QImage(display_array.data, w, h, bytes_per_line, QImage.Format_RGB888)
        else:
            h, w = display_array.shape
            bytes_per_line = w
            qimage = QImage(display_array.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        
        # 显示
        pixmap = QPixmap.fromImage(qimage)
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())
        
    def normalize_for_display(self, image_array):
        """
        将图像归一化到8位用于显示
        
        Args:
            image_array: 输入图像数组（灰度或RGB）
            
        Returns:
            numpy数组: 8位图像（灰度或RGB）
        """
        if image_array.dtype == np.uint8:
            return image_array
        
        # 16位转8位：使用线性映射
        img_min = image_array.min()
        img_max = image_array.max()
        
        if img_max > img_min:
            normalized = ((image_array.astype(np.float32) - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(image_array, dtype=np.uint8)
        
        return normalized
        
    def zoom_in(self):
        """放大"""
        new_zoom = min(self.zoom_factor * 1.2, self.max_zoom)
        self.set_zoom(new_zoom)
        
    def zoom_out(self):
        """缩小"""
        new_zoom = max(self.zoom_factor / 1.2, self.min_zoom)
        self.set_zoom(new_zoom)
        
    def zoom_fit(self):
        """适应窗口"""
        if self.image_array is None:
            return
        
        # 计算适应窗口的缩放比例
        # 处理2D灰度图和3D RGB图
        if len(self.image_array.shape) == 2:
            h, w = self.image_array.shape
        else:
            h, w = self.image_array.shape[:2]
        viewport_size = self.scroll_area.viewport().size()
        
        zoom_w = viewport_size.width() / w
        zoom_h = viewport_size.height() / h
        
        new_zoom = min(zoom_w, zoom_h) * 0.95  # 留一点边距
        self.set_zoom(new_zoom)
        
    def zoom_100(self):
        """100%显示"""
        self.set_zoom(1.0)
        
    def set_zoom(self, zoom_factor):
        """
        设置缩放比例
        
        Args:
            zoom_factor: 缩放因子
        """
        zoom_factor = max(self.min_zoom, min(zoom_factor, self.max_zoom))
        
        if abs(zoom_factor - self.zoom_factor) > 0.001:
            self.zoom_factor = zoom_factor
            self.update_display()
            self.zoom_changed.emit(self.zoom_factor)
            
    def on_wheel_event(self, event):
        """鼠标滚轮事件处理"""
        if self.image_array is None:
            return
        
        # Ctrl + 滚轮 = 缩放
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            # 默认滚动行为
            QScrollArea.wheelEvent(self.scroll_area, event)
    
    def on_mouse_move(self, event):
        """鼠标移动事件处理"""
        if self.image_array is None:
            return
        
        # 获取鼠标在图像标签中的位置
        pos = event.pos()
        
        # 转换为原始图像坐标
        img_x = int(pos.x() / self.zoom_factor)
        img_y = int(pos.y() / self.zoom_factor)
        
        # 检查坐标是否在图像范围内
        # 处理灰度图（2D）和RGB图（3D）
        if len(self.image_array.shape) == 2:
            h, w = self.image_array.shape
            if 0 <= img_x < w and 0 <= img_y < h:
                pixel_value = int(self.image_array[img_y, img_x])
                self.pixel_info_updated.emit(img_x, img_y, pixel_value)
        elif len(self.image_array.shape) == 3:
            h, w, c = self.image_array.shape
            if 0 <= img_x < w and 0 <= img_y < h:
                # RGB图像，显示RGB值的平均值或灰度值
                pixel_rgb = self.image_array[img_y, img_x]
                pixel_value = int(pixel_rgb.max())  # 使用最大值作为代表
                self.pixel_info_updated.emit(img_x, img_y, pixel_value)
    
    def clear(self):
        """清除显示"""
        self.image_array = None
        self.display_image = None
        self.image_label.clear()
        self.image_label.setText("未加载图像")
        self.zoom_factor = 1.0
