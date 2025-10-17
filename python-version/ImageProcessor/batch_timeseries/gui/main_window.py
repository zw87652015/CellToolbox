#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量荧光强度测量工具 - 主应用程序
Batch Fluorescence Measurement Tool - Main Application

根据开发指南实现的单细胞时间序列荧光强度批量测量工具
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
import logging
from datetime import datetime
import json

# 导入自定义模块
from core.image_processor import ImageProcessor
from core.file_manager import FileManager
from config_manager import ConfigManager

class BatchFluoMeasurementApp:
    """批量荧光测量主应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("批量荧光强度测量工具 v1.0")
        self.root.geometry("800x700")
        
        # 初始化组件
        self.config_manager = ConfigManager()
        self.file_manager = FileManager()
        self.image_processor = None
        
        # 细胞检测参数配置管理器
        from core.cell_detection_config import CellDetectionConfig
        self.cell_detection_config = CellDetectionConfig()
        
        # 状态变量
        self.processing = False
        self.current_step = ""
        self.roi = None  # ROI坐标 (x, y, width, height)
        
        # 设置日志
        self.setup_logging()
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置
        self.load_config()
        
        # 设置关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_logging(self):
        """设置日志系统"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('batch_fluo_measurement.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_widgets(self):
        """创建主界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="批量荧光强度测量工具", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 文件选择区域
        self.create_file_selection_area(main_frame, row=1)
        
        # 参数配置区域
        self.create_parameter_area(main_frame, row=2)
        
        # 处理控制区域
        self.create_control_area(main_frame, row=3)
        
        # 进度显示区域
        self.create_progress_area(main_frame, row=4)
        
        # 日志显示区域
        self.create_log_area(main_frame, row=5)
        
    def create_file_selection_area(self, parent, row):
        """创建文件选择区域"""
        # 文件选择框架
        file_frame = ttk.LabelFrame(parent, text="文件选择", padding="10")
        file_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # 明场图像选择
        ttk.Label(file_frame, text="明场图像:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.brightfield_var = tk.StringVar()
        self.brightfield_entry = ttk.Entry(file_frame, textvariable=self.brightfield_var, width=50)
        self.brightfield_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="选择", 
                  command=self.select_brightfield_file).grid(row=0, column=2, pady=2)
        
        # 荧光图像文件夹选择
        ttk.Label(file_frame, text="荧光图像文件夹:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fluorescence_var = tk.StringVar()
        self.fluorescence_entry = ttk.Entry(file_frame, textvariable=self.fluorescence_var, width=50)
        self.fluorescence_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="选择", 
                  command=self.select_fluorescence_folder).grid(row=1, column=2, pady=2)
        
        # 黑场图像选择
        ttk.Label(file_frame, text="黑场图像:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.darkfield_var = tk.StringVar()
        self.darkfield_entry = ttk.Entry(file_frame, textvariable=self.darkfield_var, width=50)
        self.darkfield_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="选择", 
                  command=self.select_darkfield_files).grid(row=2, column=2, pady=2)
        
        # 输出文件夹选择
        ttk.Label(file_frame, text="输出文件夹:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(file_frame, textvariable=self.output_var, width=50)
        self.output_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="选择", 
                  command=self.select_output_folder).grid(row=3, column=2, pady=2)
        
    def create_parameter_area(self, parent, row):
        """创建参数设置区域"""
        param_frame = ttk.LabelFrame(parent, text="参数设置", padding="10")
        param_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        param_frame.columnconfigure(1, weight=1)
        
        # ROI信息显示
        ttk.Label(param_frame, text="ROI区域:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.roi_info_var = tk.StringVar(value="未选择 (将检测整个图像)")
        roi_info_label = ttk.Label(param_frame, textvariable=self.roi_info_var, 
                                  foreground='blue')
        roi_info_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 图像偏移校正设置
        ttk.Label(param_frame, text="明场-荧光偏移校正:").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 偏移校正子框架
        offset_frame = ttk.Frame(param_frame)
        offset_frame.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 启用偏移校正复选框
        self.enable_offset_var = tk.BooleanVar(value=True)
        self.offset_checkbox = ttk.Checkbutton(offset_frame, text="启用偏移校正", 
                                              variable=self.enable_offset_var,
                                              command=self.on_offset_toggle)
        self.offset_checkbox.pack(side=tk.LEFT)
        
        # Y偏移输入框
        ttk.Label(offset_frame, text="Y偏移(像素):").pack(side=tk.LEFT, padx=(10, 5))
        self.y_offset_var = tk.StringVar(value="16")
        self.y_offset_entry = ttk.Entry(offset_frame, textvariable=self.y_offset_var, width=8)
        self.y_offset_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # X偏移输入框
        ttk.Label(offset_frame, text="X偏移(像素):").pack(side=tk.LEFT, padx=(5, 5))
        self.x_offset_var = tk.StringVar(value="0")
        self.x_offset_entry = ttk.Entry(offset_frame, textvariable=self.x_offset_var, width=8)
        self.x_offset_entry.pack(side=tk.LEFT)
        
        # 偏移说明
        offset_info = "明场相对荧光的像素偏移 (正值: 明场向右/上偏移，如Y=16表示明场比荧光高16像素)"
        ttk.Label(param_frame, text=offset_info, foreground='gray', 
                 font=('Arial', 8)).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(2, 5))
        
        # 偏移优化设置
        ttk.Label(param_frame, text="偏移优化:").grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # 偏移优化子框架
        optimization_frame = ttk.Frame(param_frame)
        optimization_frame.grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 启用偏移优化复选框
        self.enable_offset_optimization_var = tk.BooleanVar(value=False)
        self.offset_optimization_checkbox = ttk.Checkbutton(optimization_frame, 
                                                           text="启用偏移优化", 
                                                           variable=self.enable_offset_optimization_var,
                                                           command=self.on_optimization_toggle)
        self.offset_optimization_checkbox.pack(side=tk.LEFT)
        
        # 搜索范围输入框
        ttk.Label(optimization_frame, text="搜索范围(±像素):").pack(side=tk.LEFT, padx=(10, 5))
        self.search_range_var = tk.StringVar(value="5")
        self.search_range_entry = ttk.Entry(optimization_frame, textvariable=self.search_range_var, width=6)
        self.search_range_entry.pack(side=tk.LEFT)
        self.search_range_entry.config(state='disabled')
        
        # 偏移优化说明
        optimization_info = "为每张荧光图像搜索±N像素范围内的最佳偏移位置，以获得最高平均荧光强度"
        ttk.Label(param_frame, text=optimization_info, foreground='gray', 
                 font=('Arial', 8)).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(2, 5))
        
        # 色图样式选择
        colormap_frame = ttk.LabelFrame(param_frame, text="ROI可视化色图样式", padding="10")
        colormap_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 5))
        
        # 色图样式单选按钮
        self.colormap_style_var = tk.StringVar(value="auto")
        
        auto_radio = ttk.Radiobutton(colormap_frame, text="自动缩放 (每张图像独立)", 
                                     variable=self.colormap_style_var, value="auto")
        auto_radio.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        global_radio = ttk.Radiobutton(colormap_frame, text="全局缩放 (所有图像统一)", 
                                       variable=self.colormap_style_var, value="global")
        global_radio.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 色图样式说明
        colormap_info = (
            "• 自动缩放: 每张图像使用自己的最小/最大值映射颜色，最亮像素均为红色\n"
            "• 全局缩放: 所有图像使用相同的最小/最大值，可直接比较不同图像的亮度差异"
        )
        ttk.Label(colormap_frame, text=colormap_info, foreground='gray', 
                 font=('Arial', 8), justify=tk.LEFT).grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # 参数说明
        info_text = "细胞检测参数通过动态预览窗口进行调整和保存"
        ttk.Label(param_frame, text=info_text, foreground='gray', 
                 font=('Arial', 9)).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
                 
    def on_offset_toggle(self):
        """偏移校正开关回调"""
        enabled = self.enable_offset_var.get()
        state = 'normal' if enabled else 'disabled'
        self.y_offset_entry.config(state=state)
        self.x_offset_entry.config(state=state)
    
    def on_optimization_toggle(self):
        """偏移优化开关回调"""
        enabled = self.enable_offset_optimization_var.get()
        state = 'normal' if enabled else 'disabled'
        self.search_range_entry.config(state=state)
        
    def get_offset_correction(self):
        """获取偏移校正参数"""
        if not self.enable_offset_var.get():
            return None
            
        try:
            x_offset = int(self.x_offset_var.get())
            y_offset = int(self.y_offset_var.get())
            return (x_offset, y_offset)
        except ValueError:
            return None
    
    def get_search_range(self):
        """获取搜索范围参数"""
        try:
            search_range = int(self.search_range_var.get())
            return max(1, min(search_range, 20))  # 限制在1-20像素范围内
        except ValueError:
            return 5  # 默认值
        
    def create_control_area(self, parent, row):
        """创建控制按钮区域"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, columnspan=2, pady=(0, 10))
        
        # 预览按钮
        self.preview_btn = ttk.Button(control_frame, text="预览细胞检测", 
                                     command=self.preview_detection)
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # ROI选择按钮
        self.roi_btn = ttk.Button(control_frame, text="选择ROI区域", 
                                 command=self.select_roi)
        self.roi_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 开始处理按钮
        self.start_btn = ttk.Button(control_frame, text="开始批量处理", 
                                   command=self.start_processing)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止按钮
        self.stop_btn = ttk.Button(control_frame, text="停止处理", 
                                  command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存配置按钮
        self.save_config_btn = ttk.Button(control_frame, text="保存配置", 
                                         command=self.save_config)
        self.save_config_btn.pack(side=tk.LEFT)
        
    def create_progress_area(self, parent, row):
        """创建进度显示区域"""
        progress_frame = ttk.LabelFrame(parent, text="处理进度", padding="10")
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 当前步骤显示
        self.step_var = tk.StringVar(value="等待开始...")
        self.step_label = ttk.Label(progress_frame, textvariable=self.step_var, 
                                   font=('Arial', 10, 'bold'))
        self.step_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 进度文本
        self.progress_text_var = tk.StringVar(value="0/0 (0%)")
        self.progress_text_label = ttk.Label(progress_frame, textvariable=self.progress_text_var)
        self.progress_text_label.grid(row=2, column=0, sticky=tk.W)
        
    def create_log_area(self, parent, row):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="处理日志", padding="10")
        log_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # 清除日志按钮
        ttk.Button(log_frame, text="清除日志", 
                  command=self.clear_log).grid(row=1, column=0, pady=(5, 0))
        
    def select_brightfield_file(self):
        """选择明场图像文件"""
        filename = filedialog.askopenfilename(
            title="选择明场图像",
            filetypes=[("TIFF files", "*.tif *.tiff"), ("All files", "*.*")],
            parent=self.root
        )
        if filename:
            self.brightfield_var.set(filename)
            self.log_message(f"已选择明场图像: {os.path.basename(filename)}")
            # 确保窗口保持原始大小
            self.root.geometry("800x700")
            
    def select_fluorescence_folder(self):
        """选择荧光图像文件夹"""
        folder = filedialog.askdirectory(title="选择荧光图像文件夹", parent=self.root)
        if folder:
            self.fluorescence_var.set(folder)
            # 检查文件夹中的TIFF文件数量
            tiff_files = self.file_manager.find_fluorescence_files(folder)
            self.log_message(f"已选择荧光图像文件夹: {os.path.basename(folder)} (找到 {len(tiff_files)} 个TIFF文件)")
            # 确保窗口保持原始大小
            self.root.geometry("800x700")
            
    def select_darkfield_files(self):
        """选择黑场图像文件"""
        filenames = filedialog.askopenfilenames(
            title="选择黑场图像文件",
            filetypes=[("TIFF files", "*.tif *.tiff"), ("All files", "*.*")],
            parent=self.root
        )
        if filenames:
            self.darkfield_var.set(";".join(filenames))
            self.log_message(f"已选择 {len(filenames)} 个黑场图像文件")
            # 确保窗口保持原始大小
            self.root.geometry("800x700")
            
    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹", parent=self.root)
        if folder:
            self.output_var.set(folder)
            self.log_message(f"已选择输出文件夹: {folder}")
            # 确保窗口保持原始大小
            self.root.geometry("800x700")
            
    def select_roi(self):
        """选择ROI区域"""
        if not self.brightfield_var.get():
            messagebox.showerror("错误", "请先选择明场图像文件")
            return
            
        try:
            self.log_message("正在加载明场图像用于ROI选择...")
            
            # 导入ROI选择器
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_utils"))
            from shared_utils import ROISelector
            from core.image_processor import ImageProcessor
            
            # 创建临时图像处理器来加载图像
            temp_processor = ImageProcessor()
            bf_image = temp_processor.load_tiff_image(self.brightfield_var.get())
            
            # 提取R通道用于显示
            bf_r = temp_processor.extract_bayer_r_channel(bf_image)
            
            # 创建ROI选择器
            roi_selector = ROISelector(self.root)
            
            # 选择ROI
            selected_roi = roi_selector.select_roi(bf_r, "选择单细胞ROI区域")
            
            if selected_roi:
                self.roi = selected_roi
                x, y, w, h = selected_roi
                self.roi_info_var.set(f"已选择: ({x}, {y}) 尺寸: {w}×{h}")
                self.log_message(f"ROI选择完成: ({x}, {y}) 尺寸: {w}×{h}")
            else:
                self.log_message("ROI选择已取消")
                
        except Exception as e:
            error_msg = f"ROI选择失败: {str(e)}"
            self.log_message(error_msg, "ERROR")
            messagebox.showerror("ROI选择失败", error_msg)
            
    def preview_detection(self):
        """动态预览细胞检测结果"""
        if not self.validate_inputs(preview_mode=True):
            return
            
        try:
            self.update_step("正在加载动态预览...")
            
            # 创建图像处理器
            if not hasattr(self, 'image_processor') or self.image_processor is None:
                self.image_processor = ImageProcessor()
            
            # 加载明场图像
            brightfield_image = self.image_processor.load_tiff_image(self.brightfield_var.get())
            
            # 计算黑场校正
            dark_correction = None
            darkfield_paths = self.darkfield_var.get().split(";") if self.darkfield_var.get() else []
            if darkfield_paths:
                dark_correction = self.image_processor.calculate_dark_correction(darkfield_paths)
            
            # 打开动态预览窗口
            from gui.dynamic_preview import DynamicPreviewWindow
            
            preview_window = DynamicPreviewWindow(
                parent=self.root,
                image_processor=self.image_processor,
                brightfield_image=brightfield_image,
                dark_correction=dark_correction,
                roi=self.roi
            )
            
            self.update_step("动态预览已打开")
            self.log_message("动态预览窗口已打开，可以实时调整参数")
            
        except Exception as e:
            self.log_message(f"预览失败: {str(e)}", level="ERROR")
            messagebox.showerror("预览失败", f"打开动态预览时发生错误:\n{str(e)}")
            
    def start_processing(self):
        """开始批量处理"""
        if not self.validate_inputs():
            return
            
        # 在启动线程前获取所有UI变量的值（线程安全）
        self.processing_params = {
            'brightfield_path': self.brightfield_var.get(),
            'fluorescence_folder': self.fluorescence_var.get(),
            'darkfield_paths': self.darkfield_var.get().split(";") if self.darkfield_var.get() else [],
            'output_folder': self.output_var.get(),
            'roi': self.roi,
            'offset_correction': self.get_offset_correction(),
            'enable_offset_optimization': self.enable_offset_optimization_var.get(),
            'search_range': self.get_search_range(),
            'colormap_style': self.colormap_style_var.get()
        }
        
        # 在新线程中运行处理
        self.processing = True
        self.update_ui_state(processing=True)
        
        processing_thread = threading.Thread(target=self.run_processing)
        processing_thread.daemon = True
        processing_thread.start()
        
    def run_processing(self):
        """运行批量处理（在后台线程中）"""
        try:
            # 从配置文件加载细胞检测参数
            cell_params = self.cell_detection_config.load_parameters()
            
            # 创建图像处理器
            self.image_processor = ImageProcessor(
                gaussian_sigma=cell_params.get("gaussian_sigma", 1.5),
                threshold_method=cell_params.get("threshold_method", "otsu"),
                min_area=cell_params.get("min_area", 500),
                closing_radius=cell_params.get("closing_radius", 5),
                opening_radius=cell_params.get("opening_radius", 2),
                progress_callback=self.update_progress
                # log_callback disabled - logs only go to terminal now
            )
            
            # 执行批量处理，使用预先获取的参数值
            result = self.image_processor.process_batch(
                brightfield_path=self.processing_params['brightfield_path'],
                fluorescence_folder=self.processing_params['fluorescence_folder'],
                darkfield_paths=self.processing_params['darkfield_paths'],
                output_folder=self.processing_params['output_folder'],
                roi=self.processing_params['roi'],
                offset_correction=self.processing_params['offset_correction'],
                enable_offset_optimization=self.processing_params['enable_offset_optimization'],
                search_range=self.processing_params['search_range'],
                colormap_style=self.processing_params['colormap_style']
            )
            
            if result:
                try:
                    self.root.after(0, self._on_processing_success)
                except RuntimeError as e:
                    if "main thread is not in main loop" in str(e):
                        self.logger.info("批量处理成功完成（GUI已关闭）")
                        print("[处理完成] 批量处理成功完成")
                    else:
                        raise
            else:
                try:
                    self.root.after(0, self._on_processing_failure)
                except RuntimeError as e:
                    if "main thread is not in main loop" in str(e):
                        self.logger.error("批量处理失败（GUI已关闭）")
                        print("[处理失败] 批量处理失败")
                    else:
                        raise
                
        except Exception as e:
            error_msg = str(e)
            try:
                self.root.after(0, lambda: self.processing_failed(error_msg))
            except RuntimeError as e:
                if "main thread is not in main loop" in str(e):
                    # 主线程已退出，记录到文件和控制台
                    self.logger.error(f"处理失败: {error_msg}")
                    print(f"[处理失败] {error_msg}")
                else:
                    raise
            
    def _on_processing_success(self):
        """处理成功回调"""
        self.processing_completed(True)
        
    def _on_processing_failure(self):
        """处理失败回调"""
        self.processing_completed(False)
            
    def processing_completed(self, success):
        """处理完成回调"""
        self.processing = False
        self.update_ui_state(processing=False)
        
        if success:
            self.update_step("处理完成！")
            self.log_message("批量处理成功完成！")
            messagebox.showinfo("处理完成", "批量荧光强度测量已完成！\n请查看输出文件夹中的结果。")
        else:
            self.update_step("处理失败")
            self.log_message("批量处理失败", level="ERROR")
            
    def processing_failed(self, error_msg):
        """处理失败回调"""
        self.processing = False
        self.update_ui_state(processing=False)
        self.update_step("处理失败")
        self.log_message(f"处理失败: {error_msg}", level="ERROR")
        messagebox.showerror("处理失败", f"批量处理时发生错误:\n{error_msg}")
        
    def stop_processing(self):
        """停止处理"""
        if self.image_processor:
            self.image_processor.stop_processing()
        self.processing = False
        self.update_ui_state(processing=False)
        self.update_step("处理已停止")
        self.log_message("用户停止了处理")
        
    def on_close(self):
        """处理窗口关闭事件"""
        if self.processing:
            result = messagebox.askyesno(
                "确认关闭", 
                "批量处理正在进行中。\n是否停止处理并关闭窗口？"
            )
            if result:
                self.stop_processing()
                # 直接关闭窗口 (处理线程会自然终止)
                self.root.destroy()
            # 如果用户选择"否"，不关闭窗口
        else:
            self.root.destroy()
        
    def validate_inputs(self, preview_mode=False):
        """验证输入参数"""
        if not self.brightfield_var.get():
            messagebox.showerror("输入错误", "请选择明场图像文件")
            return False
            
        if not preview_mode and not self.fluorescence_var.get():
            messagebox.showerror("输入错误", "请选择荧光图像文件夹")
            return False
            
        if not preview_mode and not self.output_var.get():
            messagebox.showerror("输入错误", "请选择输出文件夹")
            return False
            
        return True
        
    def update_step(self, step_text):
        """更新当前步骤显示（线程安全）"""
        self.current_step = step_text
        try:
            # 使用after(0)代替after_idle以实现立即更新
            self.root.after(0, lambda: self.step_var.set(step_text))
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                # 主线程已退出，跳过GUI更新
                pass
            else:
                raise
        
    def update_progress(self, current, total, message=""):
        """更新进度显示（线程安全，支持浮点数百分比）"""
        if total > 0:
            progress = (current / total) * 100
            progress_text = f"{progress:.1f}%"
            
            def update_gui():
                self.progress_var.set(progress)
                self.progress_text_var.set(progress_text)
                # 强制立即刷新GUI
                try:
                    self.root.update_idletasks()
                except:
                    pass
            
            try:
                # 使用after(0)实现立即更新
                self.root.after(0, update_gui)
            except RuntimeError as e:
                if "main thread is not in main loop" in str(e):
                    # 主线程已退出，跳过GUI更新
                    pass
                else:
                    raise
        
        if message:
            self.update_step(message)
            
    def update_ui_state(self, processing):
        """更新UI状态（线程安全）"""
        def update_gui():
            if processing:
                self.start_btn.config(state=tk.DISABLED)
                self.preview_btn.config(state=tk.DISABLED)
                self.roi_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
            else:
                self.start_btn.config(state=tk.NORMAL)
                self.preview_btn.config(state=tk.NORMAL)
                self.roi_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
        
        try:
            self.root.after_idle(update_gui)
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                # 主线程已退出，跳过GUI更新
                pass
            else:
                raise
            
    def log_message(self, message, level="INFO"):
        """添加日志消息（线程安全）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # 使用after_idle在主线程更新GUI日志（线程安全）
        def update_gui():
            try:
                self.log_text.insert(tk.END, log_entry)
                self.log_text.see(tk.END)
            except tk.TclError:
                # 窗口已销毁，跳过
                pass
        
        try:
            self.root.after_idle(update_gui)
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                # 主线程已退出，只记录到文件
                print(f"[GUI已关闭] {log_entry}", end='')
            else:
                raise
        
        # 添加到文件日志（文件I/O是线程安全的）
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
            
    def clear_log(self):
        """清除日志显示"""
        self.log_text.delete(1.0, tk.END)
        
    def save_config(self):
        """保存当前配置"""
        config = {
            'brightfield_path': self.brightfield_var.get(),
            'fluorescence_folder': self.fluorescence_var.get(),
            'darkfield_paths': self.darkfield_var.get(),
            'output_folder': self.output_var.get(),
            'roi': self.roi,
            'offset_correction': {
                'enabled': self.enable_offset_var.get(),
                'x_offset': self.x_offset_var.get(),
                'y_offset': self.y_offset_var.get()
            },
            'offset_optimization': {
                'enabled': self.enable_offset_optimization_var.get(),
                'search_range': self.search_range_var.get()
            },
            'visualization': {
                'colormap_style': self.colormap_style_var.get()
            }
        }
        
        self.config_manager.save_config(config)
        self.log_message("配置已保存")
        messagebox.showinfo("保存成功", "配置已保存到 config.json\n细胞检测参数请在动态预览窗口中保存")
        
    def load_config(self):
        """加载配置"""
        config = self.config_manager.load_config()
        if config:
            self.brightfield_var.set(config.get('brightfield_path', ''))
            self.fluorescence_var.set(config.get('fluorescence_folder', ''))
            self.darkfield_var.set(config.get('darkfield_paths', ''))
            self.output_var.set(config.get('output_folder', ''))
            
            # 加载ROI配置
            self.roi = config.get('roi', None)
            if self.roi:
                x, y, w, h = self.roi
                self.roi_info_var.set(f"已选择: ({x}, {y}) 尺寸: {w}×{h}")
            else:
                self.roi_info_var.set("未选择 (将检测整个图像)")
            
            # 加载偏移校正配置
            offset_config = config.get('offset_correction', {})
            self.enable_offset_var.set(offset_config.get('enabled', True))
            self.x_offset_var.set(offset_config.get('x_offset', '0'))
            self.y_offset_var.set(offset_config.get('y_offset', '16'))
            self.on_offset_toggle()  # 更新UI状态
            
            # 加载偏移优化配置
            optimization_config = config.get('offset_optimization', {})
            self.enable_offset_optimization_var.set(optimization_config.get('enabled', False))
            self.search_range_var.set(optimization_config.get('search_range', '5'))
            self.on_optimization_toggle()  # 更新UI状态
            
            # 加载可视化配置
            visualization_config = config.get('visualization', {})
            self.colormap_style_var.set(visualization_config.get('colormap_style', 'auto'))
            
            self.log_message("已加载保存的配置")
            
        # 加载细胞检测参数
        try:
            cell_params = self.cell_detection_config.load_parameters()
            self.log_message(f"已加载细胞检测参数: {cell_params.get('description', '默认参数')}")
        except Exception as e:
            self.log_message(f"加载细胞检测参数失败: {str(e)}", "WARNING")
            

def main():
    """主函数"""
    root = tk.Tk()
    app = BatchFluoMeasurementApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
