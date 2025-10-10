"""
控制面板组件
提供文件选择、参数调整和导出控制
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QPushButton, QLabel, QSpinBox, QComboBox, 
                             QLineEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ControlPanel(QWidget):
    """控制面板"""
    
    # 信号
    file_selected = pyqtSignal(str)  # 文件路径
    scale_changed = pyqtSignal(int)  # 放大倍数
    export_requested = pyqtSignal(str, str, int)  # 保存路径, 格式, 位深度
    preview_requested = pyqtSignal(int)  # 预览放大倍数
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_file = None
        self.original_size = None
        self.bit_depth = None
        
        # 延迟处理定时器
        self.scale_timer = QTimer()
        self.scale_timer.setSingleShot(True)
        self.scale_timer.timeout.connect(self.on_scale_timer)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 文件选择组
        file_group = self.create_file_group()
        layout.addWidget(file_group)
        
        # 放大参数组
        scale_group = self.create_scale_group()
        layout.addWidget(scale_group)
        
        # 输出信息组
        info_group = self.create_info_group()
        layout.addWidget(info_group)
        
        # 导出控制组
        export_group = self.create_export_group()
        layout.addWidget(export_group)
        
        # 添加弹性空间
        layout.addStretch()
        
    def create_file_group(self):
        """创建文件选择组"""
        group = QGroupBox("1. 选择文件")
        layout = QVBoxLayout()
        
        # 文件路径显示
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("QLabel { padding: 5px; background-color: #f0f0f0; }")
        file_layout.addWidget(self.file_label)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # RGB通道选择（默认隐藏）
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("RGB通道:"))
        
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(['灰度转换', 'R-红色', 'G-绿色', 'B-蓝色'])
        self.channel_combo.setEnabled(False)
        self.channel_combo.currentIndexChanged.connect(self.on_channel_changed)
        channel_layout.addWidget(self.channel_combo)
        
        channel_layout.addStretch()
        layout.addLayout(channel_layout)
        
        self.channel_label = QLabel("ℹ️ 灰度图像")
        self.channel_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        layout.addWidget(self.channel_label)
        
        group.setLayout(layout)
        return group
        
    def create_scale_group(self):
        """创建放大参数组"""
        group = QGroupBox("2. 设置放大倍数")
        layout = QVBoxLayout()
        
        # 放大倍数控制
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("放大倍数:"))
        
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setMinimum(1)
        self.scale_spinbox.setMaximum(50)
        self.scale_spinbox.setValue(2)
        self.scale_spinbox.setSuffix(" 倍")
        self.scale_spinbox.valueChanged.connect(self.on_scale_changed)
        scale_layout.addWidget(self.scale_spinbox)
        
        scale_layout.addStretch()
        
        # 预览按钮
        preview_btn = QPushButton("预览")
        preview_btn.clicked.connect(self.request_preview)
        scale_layout.addWidget(preview_btn)
        
        layout.addLayout(scale_layout)
        
        # 提示信息
        tip_label = QLabel("💡 提示: 调整后点击预览查看效果")
        tip_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        layout.addWidget(tip_label)
        
        group.setLayout(layout)
        return group
        
    def create_info_group(self):
        """创建输出信息组"""
        group = QGroupBox("3. 输出信息")
        layout = QVBoxLayout()
        
        # 原始分辨率
        self.original_res_label = QLabel("原始分辨率: --")
        layout.addWidget(self.original_res_label)
        
        # 输出分辨率
        self.output_res_label = QLabel("输出分辨率: --")
        layout.addWidget(self.output_res_label)
        
        # 内存估算
        self.memory_label = QLabel("内存需求: --")
        layout.addWidget(self.memory_label)
        
        # 位深度
        self.bit_depth_label = QLabel("位深度: --")
        layout.addWidget(self.bit_depth_label)
        
        group.setLayout(layout)
        return group
        
    def create_export_group(self):
        """创建导出控制组"""
        group = QGroupBox("4. 导出设置")
        layout = QVBoxLayout()
        
        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(['PNG', 'TIFF'])
        format_layout.addWidget(self.format_combo)
        
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        # 位深度选择
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("输出位深:"))
        
        self.depth_combo = QComboBox()
        self.depth_combo.addItems(['保持原始', '8位', '16位'])
        depth_layout.addWidget(self.depth_combo)
        
        depth_layout.addStretch()
        layout.addLayout(depth_layout)
        
        # 导出按钮
        export_btn = QPushButton("导出图像")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        export_btn.clicked.connect(self.export_image)
        layout.addWidget(export_btn)
        
        group.setLayout(layout)
        return group
        
    def browse_file(self):
        """浏览并选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图像文件",
            "",
            "Image Files (*.tif *.tiff *.png);;TIFF Files (*.tif *.tiff);;PNG Files (*.png);;All Files (*.*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.file_selected.emit(file_path)
            logger.info(f"选择文件: {file_path}")
            
    def on_scale_changed(self, value):
        """放大倍数改变时的处理"""
        # 使用定时器延迟处理，避免频繁更新
        self.scale_timer.stop()
        self.scale_timer.start(200)  # 200ms延迟
        
    def on_scale_timer(self):
        """定时器触发，实际处理放大倍数改变"""
        scale = self.scale_spinbox.value()
        self.update_output_info(scale)
        
    def request_preview(self):
        """请求预览"""
        if self.current_file is None:
            QMessageBox.warning(self, "警告", "请先选择图像文件")
            return
        
        scale = self.scale_spinbox.value()
        self.preview_requested.emit(scale)
        
    def export_image(self):
        """导出图像"""
        if self.current_file is None:
            QMessageBox.warning(self, "警告", "请先选择图像文件")
            return
        
        # 生成默认文件名
        scale = self.scale_spinbox.value()
        format_str = self.format_combo.currentText()
        
        if self.original_size:
            w, h = self.original_size
            output_w, output_h = w * scale, h * scale
            default_name = f"{Path(self.current_file).stem}_{scale}x_{output_w}x{output_h}.{format_str.lower()}"
        else:
            default_name = f"{Path(self.current_file).stem}_{scale}x.{format_str.lower()}"
        
        # 选择保存路径
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存图像",
            default_name,
            f"{format_str} Files (*.{format_str.lower()});;All Files (*.*)"
        )
        
        if save_path:
            # 检查文件是否已存在
            if os.path.exists(save_path):
                reply = QMessageBox.question(
                    self,
                    "确认覆盖",
                    f"文件 {os.path.basename(save_path)} 已存在\n是否覆盖?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # 获取位深度设置
            depth_str = self.depth_combo.currentText()
            if depth_str == '8位':
                bit_depth = 8
            elif depth_str == '16位':
                bit_depth = 16
            else:
                bit_depth = None  # 保持原始
            
            self.export_requested.emit(save_path, format_str, bit_depth)
            
    def on_channel_changed(self, index):
        """通道选择改变"""
        # 发送通道改变信号，需要重新预览
        logger.info(f"通道切换: {self.channel_combo.currentText()}")
    
    def update_info(self, original_size, bit_depth, is_rgb=False):
        """
        更新信息显示
        
        Args:
            original_size: 原始尺寸 (width, height)
            bit_depth: 位深度
            is_rgb: 是否为RGB图像
        """
        self.original_size = original_size
        self.bit_depth = bit_depth
        
        if original_size:
            w, h = original_size
            mp = (w * h) / 1_000_000
            self.original_res_label.setText(f"原始分辨率: {w} × {h} ({mp:.1f} MP)")
        
        if bit_depth:
            self.bit_depth_label.setText(f"位深度: {bit_depth}位灰度")
        
        # 更新RGB通道选择器状态
        if is_rgb:
            self.channel_combo.setEnabled(True)
            self.channel_label.setText("ℹ️ RGB图像 - 请选择通道")
            self.channel_label.setStyleSheet("QLabel { color: #4CAF50; font-size: 10px; font-weight: bold; }")
        else:
            self.channel_combo.setEnabled(False)
            self.channel_combo.setCurrentIndex(0)
            self.channel_label.setText("ℹ️ 灰度图像")
            self.channel_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        
        # 更新输出信息
        scale = self.scale_spinbox.value()
        self.update_output_info(scale)
        
    def update_output_info(self, scale):
        """
        更新输出信息
        
        Args:
            scale: 放大倍数
        """
        if self.original_size:
            w, h = self.original_size
            output_w, output_h = w * scale, h * scale
            mp = (output_w * output_h) / 1_000_000
            
            self.output_res_label.setText(f"输出分辨率: {output_w} × {output_h} ({mp:.1f} MP)")
            
            # 估算内存
            bytes_per_pixel = 2 if self.bit_depth == 16 else 1
            memory_mb = (output_w * output_h * bytes_per_pixel) / (1024 * 1024)
            
            if memory_mb > 1024:
                memory_str = f"{memory_mb / 1024:.2f} GB"
                if memory_mb > 1024:  # 超过1GB，显示警告
                    memory_str += " ⚠️"
            else:
                memory_str = f"{memory_mb:.1f} MB"
            
            self.memory_label.setText(f"内存需求: {memory_str}")
    
    def get_scale_factor(self):
        """获取当前放大倍数"""
        return self.scale_spinbox.value()
    
    def get_selected_channel(self):
        """获取选择的RGB通道"""
        if not self.channel_combo.isEnabled():
            return None
        
        channel_map = {
            0: None,  # 灰度转换
            1: 'R',   # 红色
            2: 'G',   # 绿色
            3: 'B'    # 蓝色
        }
        return channel_map.get(self.channel_combo.currentIndex(), None)
    
    def set_channel_enabled(self, enabled):
        """设置通道选择器启用状态"""
        self.channel_combo.setEnabled(enabled)
        if enabled:
            self.channel_label.setText("ℹ️ TIFF RGB图像 - 请选择通道")
            self.channel_label.setStyleSheet("QLabel { color: #4CAF50; font-size: 10px; font-weight: bold; }")
        else:
            self.channel_combo.setCurrentIndex(0)
            self.channel_label.setText("ℹ️ PNG彩色图像（无需选择通道）")
            self.channel_label.setStyleSheet("QLabel { color: #2196F3; font-size: 10px; font-weight: bold; }")
    
    def set_enabled(self, enabled):
        """设置控件启用状态"""
        self.setEnabled(enabled)
