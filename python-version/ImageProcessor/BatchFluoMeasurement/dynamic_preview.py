"""
动态预览窗口 - 实时参数调整和细胞检测预览
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import logging
from cell_detection_config import CellDetectionConfig

class DynamicPreviewWindow:
    """动态预览窗口类"""
    
    def __init__(self, parent, image_processor, brightfield_image, dark_correction=None, roi=None):
        self.parent = parent
        self.main_app = parent  # 保存主应用引用
        self.image_processor = image_processor
        self.brightfield_image = brightfield_image
        self.dark_correction = dark_correction
        self.roi = roi
        self.logger = logging.getLogger(__name__)
        
        # 配置管理器
        self.config_manager = CellDetectionConfig()
        
        # 从配置文件加载参数
        saved_params = self.config_manager.load_parameters()
        
        # 处理参数
        self.gaussian_sigma = tk.DoubleVar(value=saved_params.get("gaussian_sigma", 1.5))
        self.threshold_method = tk.StringVar(value=saved_params.get("threshold_method", "otsu"))
        self.min_area = tk.IntVar(value=saved_params.get("min_area", 500))
        self.closing_radius = tk.IntVar(value=saved_params.get("closing_radius", 5))
        self.opening_radius = tk.IntVar(value=saved_params.get("opening_radius", 2))
        self.smoothing_radius = tk.IntVar(value=saved_params.get("smoothing_radius", 3))
        
        # UI组件
        self.window = None
        self.canvas = None
        self.image_id = None
        self.overlay_id = None
        
        # 图像数据
        self.processed_image = None
        self.cell_mask = None
        self.display_image = None
        
        self.create_window()
        # Initial preview will be triggered by user clicking "更新预览" button
        
    def create_window(self):
        """创建预览窗口"""
        self.window = tk.Toplevel(self.parent)
        if self.roi:
            x, y, w, h = self.roi
            self.window.title(f"动态细胞检测预览 - ROI区域 ({x},{y}) {w}×{h}")
        else:
            self.window.title("动态细胞检测预览 - 全图模式")
        self.window.geometry("1200x800")
        
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧参数控制面板
        control_frame = ttk.LabelFrame(main_frame, text="检测参数", padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.create_parameter_controls(control_frame)
        
        # 右侧图像显示区域
        image_frame = ttk.LabelFrame(main_frame, text="预览图像", padding="10")
        image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_image_display(image_frame)
        
    def create_parameter_controls(self, parent):
        """创建参数控制组件"""
        row = 0
        
        # 高斯模糊参数
        ttk.Label(parent, text="高斯模糊 σ:").grid(row=row, column=0, sticky='w', pady=5)
        sigma_entry = ttk.Entry(parent, textvariable=self.gaussian_sigma, width=10)
        sigma_entry.grid(row=row, column=1, sticky='w', pady=5, padx=(5, 0))
        ttk.Label(parent, text="(0.5-3.0)").grid(row=row, column=2, sticky='w', pady=5, padx=(5, 0))
        row += 1
        
        # 阈值方法
        ttk.Label(parent, text="阈值方法:").grid(row=row, column=0, sticky='w', pady=5)
        threshold_combo = ttk.Combobox(parent, textvariable=self.threshold_method, 
                                      values=["otsu", "triangle"], state="readonly", width=12)
        threshold_combo.grid(row=row, column=1, sticky='w', pady=5, padx=(5, 0))
        row += 1
        
        # 最小细胞面积
        ttk.Label(parent, text="最小面积:").grid(row=row, column=0, sticky='w', pady=5)
        area_entry = ttk.Entry(parent, textvariable=self.min_area, width=10)
        area_entry.grid(row=row, column=1, sticky='w', pady=5, padx=(5, 0))
        ttk.Label(parent, text="(像素)").grid(row=row, column=2, sticky='w', pady=5, padx=(5, 0))
        row += 1
        
        # 形态学关闭半径
        ttk.Label(parent, text="关闭半径:").grid(row=row, column=0, sticky='w', pady=5)
        closing_entry = ttk.Entry(parent, textvariable=self.closing_radius, width=10)
        closing_entry.grid(row=row, column=1, sticky='w', pady=5, padx=(5, 0))
        ttk.Label(parent, text="(1-10)").grid(row=row, column=2, sticky='w', pady=5, padx=(5, 0))
        row += 1
        
        # 形态学打开半径
        ttk.Label(parent, text="打开半径:").grid(row=row, column=0, sticky='w', pady=5)
        opening_entry = ttk.Entry(parent, textvariable=self.opening_radius, width=10)
        opening_entry.grid(row=row, column=1, sticky='w', pady=5, padx=(5, 0))
        ttk.Label(parent, text="(1-10)").grid(row=row, column=2, sticky='w', pady=5, padx=(5, 0))
        row += 1
        
        # 边缘平滑半径
        ttk.Label(parent, text="边缘平滑:").grid(row=row, column=0, sticky='w', pady=5)
        smoothing_entry = ttk.Entry(parent, textvariable=self.smoothing_radius, width=10)
        smoothing_entry.grid(row=row, column=1, sticky='w', pady=5, padx=(5, 0))
        ttk.Label(parent, text="(0-5)").grid(row=row, column=2, sticky='w', pady=5, padx=(5, 0))
        row += 1
        
        # 更新预览按钮
        update_btn = ttk.Button(parent, text="更新预览 (F5)", 
                               command=self.update_preview)
        update_btn.grid(row=row, column=0, columnspan=3, pady=15, sticky='ew')
        row += 1
        
        # 分隔线
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=3, 
                                                       sticky='ew', pady=20)
        row += 1
        
        # 检测结果信息
        ttk.Label(parent, text="检测结果:", font=('Arial', 10, 'bold')).grid(row=row, column=0, 
                                                                        columnspan=3, sticky='w', pady=5)
        row += 1
        
        self.result_text = tk.Text(parent, height=8, width=30, font=('Consolas', 9))
        self.result_text.grid(row=row, column=0, columnspan=3, sticky='ew', pady=5)
        row += 1
        
        # 按钮
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        
        # 第一行按钮
        top_buttons = ttk.Frame(button_frame)
        top_buttons.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(top_buttons, text="保存参数 (Ctrl+S)", 
                  command=self._save_parameters).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_buttons, text="加载参数 (Ctrl+L)", 
                  command=self._load_parameters).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_buttons, text="应用参数 (Ctrl+A)", 
                  command=self._apply_parameters).pack(side=tk.LEFT, padx=2)
        
        # 第二行按钮
        bottom_buttons = ttk.Frame(button_frame)
        bottom_buttons.pack(fill=tk.X)
        
        ttk.Button(bottom_buttons, text="重置参数 (Ctrl+R)", 
                  command=self._reset_parameters).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_buttons, text="配置信息", 
                  command=self._show_config_info).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_buttons, text="关闭 (Esc)", 
                  command=self.window.destroy).pack(side=tk.RIGHT, padx=2)
        
        # 绑定键盘快捷键
        self.window.bind('<F5>', lambda e: self.update_preview())
        self.window.bind('<Control-s>', lambda e: self._save_parameters())
        self.window.bind('<Control-l>', lambda e: self._load_parameters())
        self.window.bind('<Control-a>', lambda e: self._apply_parameters())
        self.window.bind('<Control-r>', lambda e: self._reset_parameters())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        
        # 设置焦点以便键盘快捷键生效
        self.window.focus_set()
        
        # 配置列权重
        parent.grid_columnconfigure(1, weight=1)
        
    def create_image_display(self, parent):
        """创建图像显示区域"""
        # 创建画布和滚动条
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='white')
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky='nsew')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        
    def update_preview(self):
        """更新预览图像"""
        try:
            # 验证和获取当前参数
            try:
                gaussian_sigma = float(self.gaussian_sigma.get())
                if not (0.5 <= gaussian_sigma <= 3.0):
                    raise ValueError("高斯σ必须在0.5-3.0范围内")
                    
                min_area = int(self.min_area.get())
                if min_area < 1:
                    raise ValueError("最小面积必须大于0")
                    
                closing_radius = int(self.closing_radius.get())
                if not (1 <= closing_radius <= 10):
                    raise ValueError("关闭半径必须在1-10范围内")
                    
                opening_radius = int(self.opening_radius.get())
                if not (1 <= opening_radius <= 10):
                    raise ValueError("打开半径必须在1-10范围内")
                    
                smoothing_radius = int(self.smoothing_radius.get())
                if not (0 <= smoothing_radius <= 5):
                    raise ValueError("边缘平滑半径必须在0-5范围内")
                    
            except ValueError as e:
                self.logger.error(f"参数验证失败: {str(e)}")
                # 显示错误信息
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, f"参数错误:\n{str(e)}\n\n请检查参数范围:\n高斯σ: 0.5-3.0\n最小面积: >0\n关闭半径: 1-10\n打开半径: 1-10")
                return
                
            # 获取当前参数
            params = {
                'gaussian_sigma': gaussian_sigma,
                'threshold_method': self.threshold_method.get(),
                'min_area': min_area,
                'closing_radius': closing_radius,
                'opening_radius': opening_radius,
                'smoothing_radius': smoothing_radius,
                'max_components': 1
            }
            
            # 执行细胞检测
            self.cell_mask = self.image_processor.detect_cells_in_brightfield(
                self.brightfield_image, 
                self.dark_correction, 
                self.roi,
                **params
            )
            
            # 创建叠加图像
            self.create_overlay_image()
            
            # 显示图像
            self.display_overlay()
            
            # 更新结果信息
            self.update_result_info()
            
        except Exception as e:
            self.logger.error(f"更新预览失败: {str(e)}")
            
    def create_overlay_image(self):
        """创建叠加图像 - 仅显示ROI区域"""
        # 获取处理后的明场图像
        bf_image = self.brightfield_image.copy()
        
        # 应用Bayer拆分
        if len(bf_image.shape) == 2 and bf_image.shape[0] % 2 == 0 and bf_image.shape[1] % 2 == 0:
            bf_image = self.image_processor.extract_bayer_r_channel(bf_image)
        
        # 应用黑场校正
        if self.dark_correction is not None:
            bf_image = self.image_processor.apply_dark_correction(bf_image, self.dark_correction)
        
        # 如果有ROI，裁剪到ROI区域
        if self.roi:
            x, y, w, h = self.roi
            # 确保ROI在图像范围内
            x = max(0, min(x, bf_image.shape[1] - 1))
            y = max(0, min(y, bf_image.shape[0] - 1))
            x2 = min(x + w, bf_image.shape[1])
            y2 = min(y + h, bf_image.shape[0])
            
            # 裁剪图像到ROI区域
            bf_image_roi = bf_image[y:y2, x:x2].copy()
            
            # 裁剪细胞掩膜到ROI区域
            cell_mask_roi = None
            if self.cell_mask is not None:
                cell_mask_roi = self.cell_mask[y:y2, x:x2].copy()
        else:
            # 如果没有ROI，使用整个图像
            bf_image_roi = bf_image
            cell_mask_roi = self.cell_mask
            
        # 归一化到0-255范围用于显示
        if bf_image_roi.size > 0:
            bf_normalized = ((bf_image_roi - np.min(bf_image_roi)) / 
                            (np.max(bf_image_roi) - np.min(bf_image_roi)) * 255).astype(np.uint8)
        else:
            bf_normalized = np.zeros_like(bf_image_roi, dtype=np.uint8)
        
        # 转换为RGB
        overlay_image = cv2.cvtColor(bf_normalized, cv2.COLOR_GRAY2RGB)
        
        # 绘制细胞轮廓（相对于ROI坐标）
        if cell_mask_roi is not None and cell_mask_roi.size > 0:
            contours, _ = cv2.findContours(cell_mask_roi.astype(np.uint8), 
                                         cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 绘制轮廓（绿色，1像素细线）
            cv2.drawContours(overlay_image, contours, -1, (0, 255, 0), 1)
            
        # 绘制ROI边界（红色边框）
        if self.roi and overlay_image.shape[0] > 0 and overlay_image.shape[1] > 0:
            # 在ROI裁剪图像上绘制边界
            h_roi, w_roi = overlay_image.shape[:2]
            cv2.rectangle(overlay_image, (0, 0), (w_roi-1, h_roi-1), (255, 0, 0), 2)
        
        self.processed_image = overlay_image
        
    def display_overlay(self):
        """显示叠加图像"""
        if self.processed_image is None:
            return
            
        # 转换为PIL图像
        pil_image = Image.fromarray(self.processed_image)
        
        # 对于ROI图像，放大显示以便更好地观察细节
        img_width, img_height = pil_image.size
        
        # 如果是ROI图像（通常较小），放大显示
        if self.roi and max(img_width, img_height) < 400:
            # 放大到至少400像素
            scale_factor = max(2, 400 / max(img_width, img_height))
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)
            # 使用最近邻插值保持像素清晰度
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.NEAREST)
        elif max(img_width, img_height) > 800:
            # 如果图像太大，缩小显示
            scale = 800 / max(img_width, img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 转换为PhotoImage
        self.display_image = ImageTk.PhotoImage(pil_image)
        
        # 更新画布
        self.canvas.configure(scrollregion=(0, 0, pil_image.width, pil_image.height))
        
        if self.image_id:
            self.canvas.delete(self.image_id)
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)
        
    def update_result_info(self):
        """更新检测结果信息"""
        self.result_text.delete(1.0, tk.END)
        
        if self.cell_mask is not None:
            # 计算统计信息
            num_cells = len(np.unique(self.cell_mask)) - 1  # 减去背景
            total_area = np.sum(self.cell_mask > 0)
            
            # 获取轮廓信息
            contours, _ = cv2.findContours(self.cell_mask.astype(np.uint8), 
                                         cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            info_text = f"检测结果:\n"
            info_text += f"细胞数量: {len(contours)}\n"
            info_text += f"总面积: {total_area} 像素\n\n"
            
            info_text += f"当前参数:\n"
            info_text += f"高斯σ: {self.gaussian_sigma.get():.1f}\n"
            info_text += f"阈值方法: {self.threshold_method.get()}\n"
            info_text += f"最小面积: {self.min_area.get()}\n"
            info_text += f"关闭半径: {self.closing_radius.get()}\n"
            info_text += f"打开半径: {self.opening_radius.get()}\n\n"
            
            if self.roi:
                x, y, w, h = self.roi
                info_text += f"ROI区域 (仅显示此区域):\n"
                info_text += f"位置: ({x}, {y})\n"
                info_text += f"尺寸: {w}×{h}\n"
                info_text += f"显示模式: ROI裁剪视图\n"
            else:
                info_text += f"ROI: 全图检测\n"
                info_text += f"显示模式: 完整图像\n"
                
            # 轮廓详细信息
            if contours:
                info_text += f"\n轮廓详情:\n"
                for i, contour in enumerate(contours):
                    area = cv2.contourArea(contour)
                    perimeter = cv2.arcLength(contour, True)
                    info_text += f"细胞{i+1}: 面积={area:.0f}, 周长={perimeter:.1f}\n"
        else:
            info_text = "检测失败或无结果"
            
        self.result_text.insert(1.0, info_text)
        
    def _apply_parameters(self):
        """将当前参数应用到主应用程序"""
        # 保存当前参数到配置文件
        current_params = {
            "gaussian_sigma": self.gaussian_sigma.get(),
            "threshold_method": self.threshold_method.get(),
            "min_area": self.min_area.get(),
            "closing_radius": self.closing_radius.get(),
            "opening_radius": self.opening_radius.get(),
            "smoothing_radius": self.smoothing_radius.get()
        }
        
        success = self.config_manager.save_parameters(current_params, "动态预览应用的参数")
        
        if hasattr(self.main_app, 'log_message'):
            if success:
                self.main_app.log_message("已应用并保存动态预览中的参数设置")
            else:
                self.main_app.log_message("参数应用成功，但保存配置文件失败", "WARNING")
        else:
            print("已应用动态预览中的参数设置")
        
    def _save_parameters(self):
        """保存当前参数到配置文件"""
        try:
            # 获取当前参数
            current_params = {
                "gaussian_sigma": self.gaussian_sigma.get(),
                "threshold_method": self.threshold_method.get(),
                "min_area": self.min_area.get(),
                "closing_radius": self.closing_radius.get(),
                "opening_radius": self.opening_radius.get(),
                "smoothing_radius": self.smoothing_radius.get()
            }
            
            # 弹出对话框让用户输入描述
            description = tk.simpledialog.askstring(
                "保存参数配置", 
                "请输入参数配置的描述信息:",
                initialvalue="优化后的细胞检测参数"
            )
            
            if description is not None:  # 用户没有取消
                success = self.config_manager.save_parameters(current_params, description)
                if success:
                    messagebox.showinfo("保存成功", "细胞检测参数已保存到配置文件")
                else:
                    messagebox.showerror("保存失败", "保存参数配置时发生错误")
                    
        except Exception as e:
            messagebox.showerror("保存失败", f"保存参数时发生错误:\n{str(e)}")
            
    def _load_parameters(self):
        """从配置文件加载参数"""
        try:
            saved_params = self.config_manager.load_parameters()
            
            # 更新界面参数
            self.gaussian_sigma.set(saved_params.get("gaussian_sigma", 1.5))
            self.threshold_method.set(saved_params.get("threshold_method", "otsu"))
            self.min_area.set(saved_params.get("min_area", 500))
            self.closing_radius.set(saved_params.get("closing_radius", 5))
            self.opening_radius.set(saved_params.get("opening_radius", 2))
            self.smoothing_radius.set(saved_params.get("smoothing_radius", 3))
            
            messagebox.showinfo("加载成功", "已从配置文件加载细胞检测参数")
            
        except Exception as e:
            messagebox.showerror("加载失败", f"加载参数时发生错误:\n{str(e)}")
            
    def _show_config_info(self):
        """显示配置文件信息"""
        try:
            config_info = self.config_manager.get_config_info()
            messagebox.showinfo("配置文件信息", config_info)
        except Exception as e:
            messagebox.showerror("信息获取失败", f"获取配置信息时发生错误:\n{str(e)}")
            
    def _reset_parameters(self):
        """重置参数到默认值"""
        result = messagebox.askyesno("重置参数", "确定要重置为默认参数吗？这将清除当前的参数设置。")
        if result:
            self.config_manager.reset_to_default()
            # 重新加载默认参数
            default_params = self.config_manager.load_parameters()
            self.gaussian_sigma.set(default_params.get("gaussian_sigma", 1.5))
            self.threshold_method.set(default_params.get("threshold_method", "otsu"))
            self.min_area.set(default_params.get("min_area", 500))
            self.closing_radius.set(default_params.get("closing_radius", 5))
            self.opening_radius.set(default_params.get("opening_radius", 2))
            self.smoothing_radius.set(default_params.get("smoothing_radius", 3))
            messagebox.showinfo("重置完成", "参数已重置为默认值")
        
    def get_parameters(self):
        """获取当前参数"""
        return {
            'gaussian_sigma': self.gaussian_sigma.get(),
            'threshold_method': self.threshold_method.get(),
            'min_area': self.min_area.get(),
            'closing_radius': self.closing_radius.get(),
            'opening_radius': self.opening_radius.get(),
            'smoothing_radius': self.smoothing_radius.get(),
            'max_components': 1
        }
