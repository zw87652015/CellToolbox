#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
荧光单张图像测量 - GUI应用
Fluorescence Single Image Measurement - GUI Application
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import logging
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageTk

from core.image_processor import FluoImageProcessor
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_utils"))
from shared_utils import ROISelector
import config_manager


class TextHandler(logging.Handler):
    """日志文本处理器"""
    
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        
    def emit(self, record):
        msg = self.format(record)
        
        def append():
            try:
                self.text_widget.config(state='normal')
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                self.text_widget.config(state='disabled')
            except Exception as e:
                # 如果文本控件已销毁，静默失败
                print(f"Log append failed: {e}")
        
        try:
            self.text_widget.after(0, append)
        except Exception:
            # 如果主循环未运行，直接打印到控制台
            print(msg)


class FluoSingleMeasurementGUI:
    """荧光单张图像测量GUI应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("荧光单张图像测量工具 - Fluorescence Single Image Measurement")
        self.root.geometry("1000x800")
        
        # 设置日志
        self.setup_logging()
        
        # 初始化变量
        self.image_path = None
        self.roi = None
        self.processor = None
        self.config = config_manager.load_config()
        
        # 线程通信队列
        self.result_queue = queue.Queue()
        
        # 创建UI
        self.create_ui()
        
        # 启动结果轮询
        self.poll_results()
        
        self.logger.info("应用启动成功")
        
    def setup_logging(self):
        """设置日志系统"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    def create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧面板（控制）
        left_frame = ttk.Frame(main_container, width=350)
        main_container.add(left_frame, weight=0)
        
        # 右侧面板（预览和日志）
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)
        
        # 创建左侧控制区域
        self.create_control_panel(left_frame)
        
        # 创建右侧预览和日志区域
        self.create_preview_panel(right_frame)
        
    def create_control_panel(self, parent):
        """创建控制面板"""
        # 滚动区域
        canvas = tk.Canvas(parent, width=350)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建各个参数区域
        self._create_file_section(scrollable_frame)
        self._create_bayer_section(scrollable_frame)
        self._create_roi_section(scrollable_frame)
        self._create_tophat_section(scrollable_frame)
        self._create_gaussian_section(scrollable_frame)
        self._create_adaptive_section(scrollable_frame)
        self._create_postproc_section(scrollable_frame)
        self._create_config_section(scrollable_frame)
        self._create_process_section(scrollable_frame)
        
    def _create_file_section(self, parent):
        """文件选择部分"""
        file_frame = ttk.LabelFrame(parent, text="图像文件", padding="10")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(file_frame, text="选择荧光图像", 
                  command=self.select_image).pack(fill=tk.X, pady=2)
        
        self.image_label = ttk.Label(file_frame, text="未选择图像", 
                                     foreground="gray", wraplength=300)
        self.image_label.pack(fill=tk.X, pady=2)
    
    def _create_bayer_section(self, parent):
        """Bayer RAW处理选项"""
        bayer_frame = ttk.LabelFrame(parent, text="Bayer RAW处理", padding="10")
        bayer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.is_bayer_var = tk.BooleanVar(value=self.config.get('is_bayer', False))
        ttk.Checkbutton(bayer_frame, text="启用Bayer RAW模式（提取R通道）", 
                       variable=self.is_bayer_var).pack(anchor=tk.W)
        
        ttk.Label(bayer_frame, text="Bayer模式:").pack(anchor=tk.W, pady=(5, 0))
        self.bayer_pattern_var = tk.StringVar(value=self.config.get('bayer_pattern', 'RGGB'))
        pattern_frame = ttk.Frame(bayer_frame)
        pattern_frame.pack(fill=tk.X, pady=2)
        
        for pattern in ['RGGB', 'BGGR', 'GRBG', 'GBRG']:
            ttk.Radiobutton(pattern_frame, text=pattern, 
                           variable=self.bayer_pattern_var, 
                           value=pattern).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(bayer_frame, text="说明: 用于Sony相机的RAW图像荧光测量", 
                 foreground="gray", font=('Arial', 8)).pack(anchor=tk.W)
        
    def _create_roi_section(self, parent):
        """ROI选择部分"""
        roi_frame = ttk.LabelFrame(parent, text="ROI区域选择", padding="10")
        roi_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(roi_frame, text="选择ROI区域", 
                  command=self.select_roi).pack(fill=tk.X, pady=2)
        
        self.roi_label = ttk.Label(roi_frame, text="处理整张图像", 
                                   foreground="blue")
        self.roi_label.pack(fill=tk.X, pady=2)
        
        ttk.Button(roi_frame, text="清除ROI（处理整张图）", 
                  command=self.clear_roi).pack(fill=tk.X, pady=2)
        
    def _create_tophat_section(self, parent):
        """白帽变换参数"""
        frame = ttk.LabelFrame(parent, text="白帽变换参数", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame, text="结构元素大小 (像素):").pack(anchor=tk.W)
        self.tophat_size_var = tk.IntVar(value=self.config.get('tophat_element_size', 15))
        size_frame = ttk.Frame(frame)
        size_frame.pack(fill=tk.X, pady=2)
        ttk.Scale(size_frame, from_=5, to=50, variable=self.tophat_size_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(size_frame, textvariable=self.tophat_size_var, width=4).pack(side=tk.LEFT)
        
        ttk.Label(frame, text="说明: 设置为细胞直径的1.5-2倍", 
                 foreground="gray", font=('Arial', 8)).pack(anchor=tk.W)
        
        ttk.Label(frame, text="结构元素形状:").pack(anchor=tk.W, pady=(5, 0))
        self.tophat_shape_var = tk.StringVar(value=self.config.get('tophat_element_shape', 'disk'))
        ttk.Radiobutton(frame, text="圆形 (disk)", 
                       variable=self.tophat_shape_var, value='disk').pack(anchor=tk.W)
        ttk.Radiobutton(frame, text="矩形 (rect)", 
                       variable=self.tophat_shape_var, value='rect').pack(anchor=tk.W)
        
    def _create_gaussian_section(self, parent):
        """高斯模糊参数"""
        frame = ttk.LabelFrame(parent, text="高斯模糊参数", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.enable_gaussian_var = tk.BooleanVar(value=self.config.get('enable_gaussian', True))
        ttk.Checkbutton(frame, text="启用高斯模糊", 
                       variable=self.enable_gaussian_var).pack(anchor=tk.W)
        
        ttk.Label(frame, text="Sigma值:").pack(anchor=tk.W, pady=(5, 0))
        self.gaussian_sigma_var = tk.DoubleVar(value=self.config.get('gaussian_sigma', 1.0))
        sigma_frame = ttk.Frame(frame)
        sigma_frame.pack(fill=tk.X, pady=2)
        ttk.Scale(sigma_frame, from_=0.5, to=3.0, variable=self.gaussian_sigma_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(sigma_frame, textvariable=self.gaussian_sigma_var, width=6).pack(side=tk.LEFT)
        
    def _create_adaptive_section(self, parent):
        """自适应阈值参数"""
        frame = ttk.LabelFrame(parent, text="自适应阈值参数", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame, text="阈值方法:").pack(anchor=tk.W)
        self.adaptive_method_var = tk.StringVar(value=self.config.get('adaptive_method', 'gaussian'))
        ttk.Radiobutton(frame, text="高斯 (Gaussian)", 
                       variable=self.adaptive_method_var, value='gaussian').pack(anchor=tk.W)
        ttk.Radiobutton(frame, text="均值 (Mean)", 
                       variable=self.adaptive_method_var, value='mean').pack(anchor=tk.W)
        
        ttk.Label(frame, text="窗口大小 (奇数):").pack(anchor=tk.W, pady=(5, 0))
        self.adaptive_block_var = tk.IntVar(value=self.config.get('adaptive_block_size', 41))
        block_frame = ttk.Frame(frame)
        block_frame.pack(fill=tk.X, pady=2)
        ttk.Scale(block_frame, from_=11, to=101, variable=self.adaptive_block_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(block_frame, textvariable=self.adaptive_block_var, width=4).pack(side=tk.LEFT)
        
        ttk.Label(frame, text="说明: 设置为细胞直径的1.5-2倍", 
                 foreground="gray", font=('Arial', 8)).pack(anchor=tk.W)
        
        ttk.Label(frame, text="常数C:").pack(anchor=tk.W, pady=(5, 0))
        self.adaptive_c_var = tk.IntVar(value=self.config.get('adaptive_c', 2))
        c_frame = ttk.Frame(frame)
        c_frame.pack(fill=tk.X, pady=2)
        ttk.Scale(c_frame, from_=0, to=10, variable=self.adaptive_c_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(c_frame, textvariable=self.adaptive_c_var, width=4).pack(side=tk.LEFT)
        
    def _create_postproc_section(self, parent):
        """后处理参数"""
        frame = ttk.LabelFrame(parent, text="后处理参数", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame, text="最小对象面积 (像素):").pack(anchor=tk.W)
        self.min_size_var = tk.IntVar(value=self.config.get('min_object_size', 50))
        min_frame = ttk.Frame(frame)
        min_frame.pack(fill=tk.X, pady=2)
        ttk.Scale(min_frame, from_=10, to=500, variable=self.min_size_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(min_frame, textvariable=self.min_size_var, width=5).pack(side=tk.LEFT)
        
        ttk.Label(frame, text="闭运算大小 (像素):").pack(anchor=tk.W, pady=(5, 0))
        self.closing_size_var = tk.IntVar(value=self.config.get('closing_size', 3))
        closing_frame = ttk.Frame(frame)
        closing_frame.pack(fill=tk.X, pady=2)
        ttk.Scale(closing_frame, from_=0, to=10, variable=self.closing_size_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(closing_frame, textvariable=self.closing_size_var, width=4).pack(side=tk.LEFT)
        
    def _create_config_section(self, parent):
        """配置管理"""
        frame = ttk.LabelFrame(parent, text="配置管理", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="保存配置", 
                  command=self.save_config).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_frame, text="加载配置", 
                  command=self.load_config).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
    def _create_process_section(self, parent):
        """处理按钮"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(frame, text="开始处理", 
                  command=self.process_image).pack(fill=tk.X, pady=2)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
    def create_preview_panel(self, parent):
        """创建预览和日志面板"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 预览标签页
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="图像预览")
        
        canvas_frame = ttk.Frame(preview_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_canvas = tk.Canvas(canvas_frame, bg='white')
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, 
                                command=self.preview_canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, 
                                command=self.preview_canvas.yview)
        
        self.preview_canvas.configure(xscrollcommand=h_scroll.set, 
                                      yscrollcommand=v_scroll.set)
        
        self.preview_canvas.grid(row=0, column=0, sticky='nsew')
        h_scroll.grid(row=1, column=0, sticky='ew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        ctrl_frame = ttk.Frame(preview_frame)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ctrl_frame, text="保存结果图像", 
                  command=self.save_result_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="保存CSV", 
                  command=self.save_csv).pack(side=tk.LEFT, padx=2)
        
        # 日志标签页
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="处理日志")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=30, 
                                                  state='disabled', wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(text_handler)
        logging.getLogger().setLevel(logging.INFO)
        
        ttk.Button(log_frame, text="清空日志", 
                  command=self.clear_log).pack(padx=5, pady=5)
        
    def select_image(self):
        """选择荧光图像"""
        file_path = filedialog.askopenfilename(
            title="选择荧光图像",
            filetypes=[
                ("TIFF files", "*.tif *.tiff"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.image_path = file_path
            self.image_label.config(text=Path(file_path).name, foreground="black")
            self.logger.info(f"选择图像: {file_path}")
            self.show_image_preview()
            
    def select_roi(self):
        """选择ROI区域"""
        if not self.image_path:
            messagebox.showwarning("警告", "请先选择荧光图像")
            return
        
        try:
            pil_image = Image.open(self.image_path)
            image = np.array(pil_image)
            
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            roi_selector = ROISelector(self.root)
            self.roi = roi_selector.select_roi(image, title="选择荧光测量区域")
            
            if self.roi:
                x, y, w, h = self.roi
                self.roi_label.config(
                    text=f"ROI: ({x}, {y}) 尺寸: {w}×{h}",
                    foreground="green"
                )
                self.logger.info(f"ROI已选择: {self.roi}")
            else:
                self.logger.info("ROI选择已取消")
                
        except Exception as e:
            self.logger.error(f"ROI选择失败: {str(e)}")
            messagebox.showerror("错误", f"ROI选择失败:\n{str(e)}")
            
    def clear_roi(self):
        """清除ROI"""
        self.roi = None
        self.roi_label.config(text="处理整张图像", foreground="blue")
        self.logger.info("ROI已清除，将处理整张图像")
        
    def show_image_preview(self):
        """显示图像预览"""
        try:
            pil_image = Image.open(self.image_path)
            image = np.array(pil_image)
            
            if image.dtype == np.uint16:
                display_img = ((image - image.min()) / (image.max() - image.min()) * 255).astype(np.uint8)
            else:
                display_img = image
            
            if len(display_img.shape) == 2:
                display_img = cv2.cvtColor(display_img, cv2.COLOR_GRAY2RGB)
            
            max_size = 600
            h, w = display_img.shape[:2]
            scale = min(max_size / w, max_size / h, 1.0)
            new_w, new_h = int(w * scale), int(h * scale)
            display_img = cv2.resize(display_img, (new_w, new_h))
            
            pil_img = Image.fromarray(display_img)
            self.preview_photo = ImageTk.PhotoImage(pil_img)
            
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_photo)
            self.preview_canvas.config(scrollregion=(0, 0, new_w, new_h))
            
        except Exception as e:
            self.logger.error(f"显示预览失败: {str(e)}")
            
    def get_current_config(self):
        """获取当前UI配置"""
        return {
            'is_bayer': self.is_bayer_var.get(),
            'bayer_pattern': self.bayer_pattern_var.get(),
            'use_r_channel': True,
            'tophat_element_size': self.tophat_size_var.get(),
            'tophat_element_shape': self.tophat_shape_var.get(),
            'enable_gaussian': self.enable_gaussian_var.get(),
            'gaussian_sigma': self.gaussian_sigma_var.get(),
            'adaptive_method': self.adaptive_method_var.get(),
            'adaptive_block_size': self.adaptive_block_var.get(),
            'adaptive_c': self.adaptive_c_var.get(),
            'min_object_size': self.min_size_var.get(),
            'closing_size': self.closing_size_var.get(),
            'measure_metrics': ['area', 'mean_intensity', 'total_intensity'],
        }
        
    def save_config(self):
        """保存当前配置"""
        try:
            config = self.get_current_config()
            if self.roi:
                config['roi'] = self.roi
            config_manager.save_config(config)
            messagebox.showinfo("成功", "配置已保存")
            self.logger.info("配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败:\n{str(e)}")
            
    def load_config(self):
        """加载配置"""
        try:
            self.config = config_manager.load_config()
            
            self.is_bayer_var.set(self.config.get('is_bayer', False))
            self.bayer_pattern_var.set(self.config.get('bayer_pattern', 'RGGB'))
            self.tophat_size_var.set(self.config.get('tophat_element_size', 15))
            self.tophat_shape_var.set(self.config.get('tophat_element_shape', 'disk'))
            self.enable_gaussian_var.set(self.config.get('enable_gaussian', True))
            self.gaussian_sigma_var.set(self.config.get('gaussian_sigma', 1.0))
            self.adaptive_method_var.set(self.config.get('adaptive_method', 'gaussian'))
            self.adaptive_block_var.set(self.config.get('adaptive_block_size', 41))
            self.adaptive_c_var.set(self.config.get('adaptive_c', 2))
            self.min_size_var.set(self.config.get('min_object_size', 50))
            self.closing_size_var.set(self.config.get('closing_size', 3))
            
            if 'roi' in self.config:
                self.roi = tuple(self.config['roi'])
                x, y, w, h = self.roi
                self.roi_label.config(text=f"ROI: ({x}, {y}) 尺寸: {w}×{h}", 
                                     foreground="green")
            
            messagebox.showinfo("成功", "配置已加载")
            self.logger.info("配置已加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败:\n{str(e)}")
            
    def process_image(self):
        """处理图像"""
        if not self.image_path:
            messagebox.showwarning("警告", "请先选择荧光图像")
            return
        
        # 在主线程获取配置（tkinter变量必须在主线程读取）
        config = self.get_current_config()
        image_path = self.image_path
        roi = self.roi
        
        thread = threading.Thread(target=self._process_worker, args=(config, image_path, roi))
        thread.daemon = True
        thread.start()
        
    def _process_worker(self, config, image_path, roi):
        """处理工作线程 - 不直接操作UI"""
        try:
            # 通知开始处理
            self.result_queue.put(('progress', 0))
            self.result_queue.put(('log', '开始处理...'))
            
            processor = FluoImageProcessor(config)
            
            measurements = processor.process_image(image_path, roi)
            self.result_queue.put(('progress', 50))
            
            overlay = processor.create_overlay_image()
            self.result_queue.put(('progress', 100))
            
            # 发送结果
            self.result_queue.put(('success', {'processor': processor, 'overlay': overlay, 'measurements': measurements}))
            
        except Exception as e:
            import traceback
            error_msg = f"处理失败: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.result_queue.put(('error', str(e)))
        finally:
            self.result_queue.put(('done', None))
    
    def poll_results(self):
        """轮询处理结果队列"""
        try:
            while True:
                msg_type, data = self.result_queue.get_nowait()
                
                if msg_type == 'progress':
                    self.progress_var.set(data)
                elif msg_type == 'log':
                    self.logger.info(data)
                elif msg_type == 'success':
                    self.processor = data['processor']
                    self.display_results(data['overlay'], data['measurements'])
                elif msg_type == 'error':
                    messagebox.showerror("错误", f"处理失败:\n{data}")
                elif msg_type == 'done':
                    self.root.after(500, lambda: self.progress_var.set(0))
                    
        except queue.Empty:
            pass
        
        # 继续轮询
        self.root.after(100, self.poll_results)
            
    def display_results(self, overlay, measurements):
        """显示处理结果"""
        try:
            rgb_overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            
            max_size = 800
            h, w = rgb_overlay.shape[:2]
            scale = min(max_size / w, max_size / h, 1.0)
            new_w, new_h = int(w * scale), int(h * scale)
            display_img = cv2.resize(rgb_overlay, (new_w, new_h))
            
            pil_img = Image.fromarray(display_img)
            self.preview_photo = ImageTk.PhotoImage(pil_img)
            
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_photo)
            self.preview_canvas.config(scrollregion=(0, 0, new_w, new_h))
            
            total_area = sum(m.get('area_pixels', 0) for m in measurements)
            total_intensity = sum(m.get('total_intensity', 0) for m in measurements)
            
            self.logger.info("=" * 60)
            self.logger.info("处理结果统计:")
            self.logger.info(f"  检测到荧光区域数: {len(measurements)}")
            self.logger.info(f"  总面积: {total_area} 像素")
            self.logger.info(f"  总强度: {total_intensity:.2f}")
            self.logger.info("=" * 60)
            
            messagebox.showinfo("处理完成", 
                              f"检测到 {len(measurements)} 个荧光区域\n"
                              f"总面积: {total_area} 像素\n"
                              f"总强度: {total_intensity:.2f}")
            
        except Exception as e:
            self.logger.error(f"显示结果失败: {str(e)}")
            
    def save_result_image(self):
        """保存结果图像"""
        if not self.processor or not self.processor.measurements:
            messagebox.showwarning("警告", "请先处理图像")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存结果图像",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.processor.create_overlay_image(file_path)
                messagebox.showinfo("成功", f"结果图像已保存:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{str(e)}")
                
    def save_csv(self):
        """保存CSV文件"""
        if not self.processor or not self.processor.measurements:
            messagebox.showwarning("警告", "请先处理图像")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存测量结果",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.processor.save_measurements_to_csv(file_path)
                messagebox.showinfo("成功", f"测量结果已保存:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{str(e)}")
                
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')


def main():
    """主函数"""
    root = tk.Tk()
    app = FluoSingleMeasurementGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
