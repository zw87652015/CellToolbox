"""
UI Panels - Parameter Panel Implementation
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from layout_engine import LayoutPreset, EmptyCellStrategy
from numbering import NumberingFormat, NumberingPosition
from scale_bar import Objective


class ParameterPanel(QWidget):
    """Left parameter panel with all controls"""
    
    # Signals
    load_folder_requested = pyqtSignal()
    load_files_requested = pyqtSignal()
    parameters_changed = pyqtSignal()
    update_preview_requested = pyqtSignal()
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)  # Reduced spacing for compact layout
        
        # Image source
        layout.addWidget(self.create_image_source_group())
        
        # Cell size
        layout.addWidget(self.create_cell_size_group())
        
        # Layout scheme
        layout.addWidget(self.create_layout_scheme_group())
        
        # Numbering
        layout.addWidget(self.create_numbering_group())
        
        # Scale bar
        layout.addWidget(self.create_scale_bar_group())
        
        # Export
        layout.addWidget(self.create_export_group())
        
        # Action buttons
        layout.addWidget(self.create_action_buttons())
        
        layout.addStretch()
    
    def create_image_source_group(self) -> QGroupBox:
        """Image source controls"""
        group = QGroupBox("图片源")
        layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_load_folder = QPushButton("选择文件夹")
        self.btn_load_files = QPushButton("选择文件")
        btn_layout.addWidget(self.btn_load_folder)
        btn_layout.addWidget(self.btn_load_files)
        layout.addLayout(btn_layout)
        
        # Drag and drop hint
        hint_label = QLabel("💡 提示: 可拖拽文件夹到窗口")
        hint_label.setStyleSheet("color: #2196F3; font-size: 10px; padding: 3px;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)
        
        self.lbl_image_info = QLabel("未加载图片")
        self.lbl_image_info.setWordWrap(True)
        layout.addWidget(self.lbl_image_info)
        
        group.setLayout(layout)
        return group
    
    def create_cell_size_group(self) -> QGroupBox:
        """Cell size controls"""
        group = QGroupBox("单元格尺寸 (比例)")
        layout = QVBoxLayout()
        
        # Scale factor
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("缩放比例:"))
        self.spin_cell_scale = QDoubleSpinBox()
        self.spin_cell_scale.setRange(0.01, 10.0)
        self.spin_cell_scale.setValue(1.0)
        self.spin_cell_scale.setSingleStep(0.1)
        self.spin_cell_scale.setDecimals(2)
        self.spin_cell_scale.setSuffix(" x")
        scale_layout.addWidget(self.spin_cell_scale)
        layout.addLayout(scale_layout)
        
        # Pixel display (read-only)
        self.lbl_cell_pixels = QLabel("实际像素: --")
        self.lbl_cell_pixels.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.lbl_cell_pixels)
        
        # Lock aspect
        self.chk_lock_aspect = QCheckBox("锁定宽高比")
        self.chk_lock_aspect.setChecked(True)
        layout.addWidget(self.chk_lock_aspect)
        
        # Reset button
        self.btn_reset_size = QPushButton("还原原始尺寸 (1.0x)")
        layout.addWidget(self.btn_reset_size)
        
        # Store original size
        self.original_width = 200
        self.original_height = 200
        
        group.setLayout(layout)
        return group
    
    def create_layout_scheme_group(self) -> QGroupBox:
        """Layout scheme controls"""
        group = QGroupBox("拼图方案")
        layout = QVBoxLayout()
        
        # Preset
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设:"))
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(LayoutPreset.get_preset_names())
        preset_layout.addWidget(self.combo_preset)
        layout.addLayout(preset_layout)
        
        # Custom cols/rows
        grid_layout = QHBoxLayout()
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 50)
        self.spin_cols.setValue(5)
        grid_layout.addWidget(QLabel("列:"))
        grid_layout.addWidget(self.spin_cols)
        
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 50)
        self.spin_rows.setValue(5)
        grid_layout.addWidget(QLabel("行:"))
        grid_layout.addWidget(self.spin_rows)
        layout.addLayout(grid_layout)
        
        # Info
        self.lbl_layout_info = QLabel("5×5 布局")
        self.lbl_layout_info.setWordWrap(True)
        layout.addWidget(self.lbl_layout_info)
        
        # Empty cell strategy - compact
        layout.addWidget(QLabel("末行空格策略:"))
        strategy_layout = QHBoxLayout()
        self.radio_left = QRadioButton("居左")
        self.radio_center = QRadioButton("居中")
        self.radio_distributed = QRadioButton("分散")
        self.radio_center.setChecked(True)
        
        strategy_layout.addWidget(self.radio_left)
        strategy_layout.addWidget(self.radio_center)
        strategy_layout.addWidget(self.radio_distributed)
        layout.addLayout(strategy_layout)
        
        group.setLayout(layout)
        return group
    
    def create_numbering_group(self) -> QGroupBox:
        """Numbering controls"""
        group = QGroupBox("编号样式")
        layout = QVBoxLayout()
        
        # Enable
        self.chk_numbering = QCheckBox("显示编号")
        self.chk_numbering.setChecked(True)
        layout.addWidget(self.chk_numbering)
        
        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("格式:"))
        self.combo_numbering_format = QComboBox()
        for fmt in NumberingFormat:
            self.combo_numbering_format.addItem(fmt.value)
        format_layout.addWidget(self.combo_numbering_format)
        layout.addLayout(format_layout)
        
        # Position
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("位置:"))
        self.combo_numbering_position = QComboBox()
        for pos in NumberingPosition:
            self.combo_numbering_position.addItem(pos.value)
        pos_layout.addWidget(self.combo_numbering_position)
        layout.addLayout(pos_layout)
        
        # Font size
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字号:"))
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 200)
        self.spin_font_size.setValue(24)
        self.spin_font_size.setSuffix(" px")
        font_layout.addWidget(self.spin_font_size)
        layout.addLayout(font_layout)
        
        # Color
        self.btn_text_color = QPushButton("文字颜色")
        self.text_color = (255, 255, 255)
        self.btn_text_color.setStyleSheet("background-color: white;")
        layout.addWidget(self.btn_text_color)
        
        # Background
        self.chk_numbering_bg = QCheckBox("显示背景")
        self.chk_numbering_bg.setChecked(True)
        layout.addWidget(self.chk_numbering_bg)
        
        group.setLayout(layout)
        return group
    
    def create_scale_bar_group(self) -> QGroupBox:
        """Scale bar controls"""
        group = QGroupBox("Scale Bar (比例尺)")
        layout = QVBoxLayout()
        
        # Enable checkbox
        self.chk_scalebar = QCheckBox("显示 Scale Bar")
        self.chk_scalebar.setChecked(False)
        layout.addWidget(self.chk_scalebar)
        
        # Objective selection
        obj_layout = QHBoxLayout()
        obj_layout.addWidget(QLabel("物镜:"))
        self.combo_objective = QComboBox()
        for obj in Objective:
            self.combo_objective.addItem(obj.value)
        obj_layout.addWidget(self.combo_objective)
        layout.addLayout(obj_layout)
        
        # Scale length
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("长度:"))
        self.spin_scale_length = QSpinBox()
        self.spin_scale_length.setRange(1, 1000)
        self.spin_scale_length.setValue(10)
        self.spin_scale_length.setSuffix(" μm")
        length_layout.addWidget(self.spin_scale_length)
        layout.addLayout(length_layout)
        
        # Position selection
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("位置:"))
        self.combo_scalebar_position = QComboBox()
        self.combo_scalebar_position.addItems(["左下", "居中", "右下"])
        self.combo_scalebar_position.setCurrentIndex(1)  # Default to center
        pos_layout.addWidget(self.combo_scalebar_position)
        layout.addLayout(pos_layout)
        
        # Info label - compact
        self.lbl_scalebar_info = QLabel("选择物镜查看比例")
        self.lbl_scalebar_info.setWordWrap(True)
        self.lbl_scalebar_info.setStyleSheet("color: gray; font-size: 9px; padding: 2px;")
        self.lbl_scalebar_info.setMaximumHeight(35)
        layout.addWidget(self.lbl_scalebar_info)
        
        group.setLayout(layout)
        return group
    
    def create_export_group(self) -> QGroupBox:
        """Export controls"""
        group = QGroupBox("输出格式")
        layout = QVBoxLayout()
        
        # Format checkboxes - compact layout
        self.chk_formats = {}
        from export_manager import ExportFormat
        
        # First row: PNG, JPG, TIFF
        format_row1 = QHBoxLayout()
        for fmt in ['PNG', 'JPG', 'TIFF']:
            chk = QCheckBox(fmt)
            if fmt == 'PNG':
                chk.setChecked(True)
            self.chk_formats[fmt] = chk
            format_row1.addWidget(chk)
        layout.addLayout(format_row1)
        
        # Second row: PDF, SVG, EPS
        format_row2 = QHBoxLayout()
        for fmt in ['PDF', 'SVG', 'EPS']:
            chk = QCheckBox(fmt)
            self.chk_formats[fmt] = chk
            format_row2.addWidget(chk)
        layout.addLayout(format_row2)
        
        # DPI
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("DPI:"))
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 1200)
        self.spin_dpi.setValue(300)
        dpi_layout.addWidget(self.spin_dpi)
        layout.addLayout(dpi_layout)
        
        # Output dir
        layout.addWidget(QLabel("输出目录:"))
        output_layout = QHBoxLayout()
        self.line_output_dir = QLineEdit()
        self.line_output_dir.setPlaceholderText("点击选择...")
        self.btn_output_dir = QPushButton("浏览...")
        self.btn_output_dir.setMaximumWidth(60)
        output_layout.addWidget(self.line_output_dir)
        output_layout.addWidget(self.btn_output_dir)
        layout.addLayout(output_layout)
        
        group.setLayout(layout)
        return group
    
    def create_action_buttons(self) -> QWidget:
        """Action buttons"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        self.btn_update_preview = QPushButton("更新预览")
        self.btn_update_preview.setStyleSheet("font-weight: bold; padding: 8px;")
        self.btn_update_preview.setMinimumHeight(40)
        layout.addWidget(self.btn_update_preview)
        
        self.btn_export = QPushButton("导出拼图")
        self.btn_export.setStyleSheet("font-weight: bold; padding: 8px; background-color: #4CAF50; color: white;")
        self.btn_export.setMinimumHeight(40)
        layout.addWidget(self.btn_export)
        
        return widget
    
    def connect_signals(self):
        """Connect signals"""
        self.btn_load_folder.clicked.connect(self.load_folder_requested)
        self.btn_load_files.clicked.connect(self.load_files_requested)
        
        self.spin_cell_scale.valueChanged.connect(self.on_cell_scale_changed)
        self.btn_reset_size.clicked.connect(self.on_reset_size)
        
        self.combo_preset.currentIndexChanged.connect(self.on_preset_changed)
        self.spin_cols.valueChanged.connect(self.parameters_changed)
        self.spin_rows.valueChanged.connect(self.parameters_changed)
        
        self.chk_numbering.stateChanged.connect(self.parameters_changed)
        self.combo_numbering_format.currentIndexChanged.connect(self.parameters_changed)
        self.combo_numbering_position.currentIndexChanged.connect(self.parameters_changed)
        self.spin_font_size.valueChanged.connect(self.parameters_changed)
        self.chk_numbering_bg.stateChanged.connect(self.parameters_changed)
        
        self.chk_scalebar.stateChanged.connect(self.parameters_changed)
        self.combo_objective.currentIndexChanged.connect(self.on_objective_changed)
        self.spin_scale_length.valueChanged.connect(self.on_scale_length_changed)
        self.combo_scalebar_position.currentIndexChanged.connect(self.parameters_changed)
        
        self.btn_text_color.clicked.connect(self.choose_text_color)
        self.btn_output_dir.clicked.connect(self.choose_output_dir)
        
        self.btn_update_preview.clicked.connect(self.update_preview_requested)
        self.btn_export.clicked.connect(self.export_requested)
    
    def on_cell_scale_changed(self, value):
        """Handle cell scale change"""
        self.update_pixel_display()
        self.parameters_changed.emit()
    
    def on_reset_size(self):
        """Reset to original size (1.0x)"""
        self.spin_cell_scale.setValue(1.0)
    
    def update_pixel_display(self):
        """Update pixel display based on scale"""
        scale = self.spin_cell_scale.value()
        width_px = int(self.original_width * scale)
        height_px = int(self.original_height * scale)
        self.lbl_cell_pixels.setText(f"实际像素: {width_px} × {height_px} px")
    
    def set_original_size(self, width: int, height: int):
        """Set original image size for scale calculation"""
        self.original_width = width
        self.original_height = height
        self._aspect_ratio = width / height if height > 0 else 1.0
        self.update_pixel_display()
    
    def set_image_info(self, count: int, width: int, height: int):
        """Update image info display"""
        aspect_ratio = width / height if height > 0 else 1.0
        self.lbl_image_info.setText(
            f"已加载 {count} 张图片\n"
            f"尺寸: {width}×{height}\n"
            f"宽高比: {aspect_ratio:.2f}:1"
        )
    
    def set_layout(self, cols: int, rows: int):
        """Set layout cols and rows"""
        self.spin_cols.blockSignals(True)
        self.spin_rows.blockSignals(True)
        self.spin_cols.setValue(cols)
        self.spin_rows.setValue(rows)
        self.spin_cols.blockSignals(False)
        self.spin_rows.blockSignals(False)
        
        # Update layout info
        self.lbl_layout_info.setText(f"{cols}×{rows} 布局")
    
    def on_preset_changed(self, index):
        """Handle preset change"""
        preset_text = self.combo_preset.currentText()
        if preset_text == "自定义":
            return
        
        preset = None
        for p in LayoutPreset:
            if p.value == preset_text:
                preset = p
                break
        
        if preset:
            rows, cols = LayoutPreset.get_grid_size(preset, 25)  # Default 25 images
            self.spin_cols.blockSignals(True)
            self.spin_rows.blockSignals(True)
            self.spin_cols.setValue(cols)
            self.spin_rows.setValue(rows)
            self.spin_cols.blockSignals(False)
            self.spin_rows.blockSignals(False)
            
            self.parameters_changed.emit()
    
    def on_objective_changed(self):
        """Handle objective selection change"""
        self.update_scalebar_info()
        self.parameters_changed.emit()
    
    def on_scale_length_changed(self):
        """Handle scale length change"""
        self.update_scalebar_info()
        self.parameters_changed.emit()
    
    def update_scalebar_info(self):
        """Update scale bar info label"""
        obj_text = self.combo_objective.currentText()
        
        # Find matching objective
        objective = Objective.NONE
        for obj in Objective:
            if obj.value == obj_text:
                objective = obj
                break
        
        # Update info label
        from scale_bar import ScaleBarStyle
        style = ScaleBarStyle()
        calibration = style.calibrations.get(objective, None)
        
        if calibration:
            scale_length = self.spin_scale_length.value()
            bar_width_px_original = scale_length / calibration
            self.lbl_scalebar_info.setText(
                f"{objective.value}: {scale_length} μm = {bar_width_px_original:.1f} px (原图)\n"
                f"比例: {calibration:.4f} μm/px"
            )
        elif objective == Objective.NONE:
            self.lbl_scalebar_info.setText("选择物镜查看比例")
        else:
            self.lbl_scalebar_info.setText(f"{objective.value}: 未配置比例")
    
    def choose_text_color(self):
        """Choose text color"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color = (color.red(), color.green(), color.blue())
            self.btn_text_color.setStyleSheet(f"background-color: {color.name()};")
            self.parameters_changed.emit()
    
    def choose_output_dir(self):
        """Choose output directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.line_output_dir.setText(dir_path)
    
    def get_parameters(self) -> dict:
        """Get all parameters"""
        # Calculate pixel size from scale
        scale = self.spin_cell_scale.value()
        cell_width = int(self.original_width * scale)
        cell_height = int(self.original_height * scale)
        
        # Empty cell strategy
        if self.radio_left.isChecked():
            strategy = EmptyCellStrategy.LEFT
        elif self.radio_center.isChecked():
            strategy = EmptyCellStrategy.CENTER
        else:
            strategy = EmptyCellStrategy.DISTRIBUTED
        
        # Numbering format
        format_text = self.combo_numbering_format.currentText()
        numbering_format = NumberingFormat.ARABIC
        for fmt in NumberingFormat:
            if fmt.value == format_text:
                numbering_format = fmt
                break
        
        # Numbering position
        pos_text = self.combo_numbering_position.currentText()
        numbering_position = NumberingPosition.TOP_LEFT
        for pos in NumberingPosition:
            if pos.value == pos_text:
                numbering_position = pos
                break
        
        # Scale bar objective
        obj_text = self.combo_objective.currentText()
        objective = Objective.NONE
        for obj in Objective:
            if obj.value == obj_text:
                objective = obj
                break
        
        # Scale bar position
        scalebar_pos_map = {"左下": "bottom_left", "居中": "bottom_center", "右下": "bottom_right"}
        scalebar_position = scalebar_pos_map.get(self.combo_scalebar_position.currentText(), "bottom_center")
        
        return {
            'cols': self.spin_cols.value(),
            'rows': self.spin_rows.value(),
            'cell_width': cell_width,
            'cell_height': cell_height,
            'cell_scale': scale,
            'empty_strategy': strategy,
            'numbering_enabled': self.chk_numbering.isChecked(),
            'numbering_format': numbering_format,
            'numbering_position': numbering_position,
            'font_size': self.spin_font_size.value(),
            'text_color': self.text_color,
            'numbering_bg': self.chk_numbering_bg.isChecked(),
            'scalebar_enabled': self.chk_scalebar.isChecked(),
            'scalebar_objective': objective,
            'scalebar_length': self.spin_scale_length.value(),
            'scalebar_position': scalebar_position,
        }
    
    def get_export_parameters(self) -> dict:
        """Get export parameters"""
        formats = []
        for fmt, chk in self.chk_formats.items():
            if chk.isChecked():
                formats.append(fmt)
        
        return {
            'formats': formats,
            'dpi': self.spin_dpi.value(),
            'output_dir': self.line_output_dir.text(),
        }
