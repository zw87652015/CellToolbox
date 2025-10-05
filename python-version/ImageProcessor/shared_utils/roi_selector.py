#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI选择器 - 交互式区域选择工具
ROI Selector - Interactive region selection tool

Shared utility module for all fluorescence measurement projects.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import logging

class ROISelector:
    """ROI选择器类"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # ROI相关变量
        self.roi = None  # (x, y, width, height) - 原始图像坐标
        self.image = None
        self.display_image = None
        self.scale_factor = 1.0
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # 鼠标绘制状态
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        
        # 平移状态
        self.panning = False
        self.last_pan_x = 0
        self.last_pan_y = 0
        
        # UI组件
        self.window = None
        self.canvas = None
        self.image_id = None
        self.rect_id = None
        
    def select_roi(self, image, title="选择感兴趣区域 (ROI)"):
        """
        交互式选择ROI
        
        Args:
            image: 输入图像 (numpy数组)
            title: 窗口标题
            
        Returns:
            ROI坐标 (x, y, width, height) 或 None
        """
        try:
            self.image = image.copy()
            self.roi = None
            
            # 创建选择窗口
            self._create_roi_window(title)
            
            # 显示图像
            self._display_image()
            
            # 运行窗口
            self.window.mainloop()
            
            return self.roi
            
        except Exception as e:
            self.logger.error(f"ROI选择失败: {str(e)}")
            if self.window:
                self.window.destroy()
            return None
            
    def _create_roi_window(self, title):
        """创建ROI选择窗口"""
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title(title)
        self.window.geometry("900x700")
        
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 说明标签
        instruction_text = (
            "使用说明:\n"
            "1. 左键拖拽绘制矩形ROI，右键拖拽平移图像\n"
            "2. 使用鼠标滚轮或缩放按钮进行缩放\n"
            "3. ROI会在缩放时自动保持位置\n"
            "4. 点击'确认选择'保存ROI，或'取消'退出"
        )
        instruction_label = ttk.Label(main_frame, text=instruction_text, 
                                    font=('Arial', 10), foreground='blue')
        instruction_label.pack(pady=(0, 10))
        
        # 图像显示区域
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(canvas_frame, bg='white', cursor='crosshair')
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # 布局滚动条和画布
        self.canvas.grid(row=0, column=0, sticky='nsew')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self._on_left_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_left_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_mouse_up)
        
        # 右键平移
        self.canvas.bind("<Button-3>", self._on_right_mouse_down)
        self.canvas.bind("<B3-Motion>", self._on_right_mouse_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_right_mouse_up)
        
        # 鼠标滚轮缩放
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # ROI信息显示
        self.roi_info_var = tk.StringVar(value="ROI: 未选择")
        roi_info_label = ttk.Label(button_frame, textvariable=self.roi_info_var, 
                                  font=('Arial', 10, 'bold'))
        roi_info_label.pack(side=tk.LEFT)
        
        # 缩放信息显示
        self.zoom_info_var = tk.StringVar(value="缩放: 100%")
        zoom_info_label = ttk.Label(button_frame, textvariable=self.zoom_info_var, 
                                   font=('Arial', 9))
        zoom_info_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 缩放控制按钮
        zoom_frame = ttk.Frame(button_frame)
        zoom_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(zoom_frame, text="放大", width=6,
                  command=self._zoom_in).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="缩小", width=6,
                  command=self._zoom_out).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="适应", width=6,
                  command=self._zoom_fit).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="100%", width=6,
                  command=self._zoom_100).pack(side=tk.LEFT, padx=1)
        
        # 主要按钮
        ttk.Button(button_frame, text="清除ROI", 
                  command=self._clear_roi).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", 
                  command=self._cancel_selection).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="确认选择", 
                  command=self._confirm_selection).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._cancel_selection)
        
    def _display_image(self):
        """显示图像到画布"""
        try:
            # 转换图像格式用于显示
            if len(self.image.shape) == 2:  # 灰度图
                display_array = self.image
            else:  # 彩色图
                display_array = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                
            # 归一化到0-255范围
            if display_array.dtype != np.uint8:
                display_array = ((display_array - np.min(display_array)) / 
                               (np.max(display_array) - np.min(display_array)) * 255).astype(np.uint8)
            
            # 应用缩放
            img_height, img_width = display_array.shape[:2]
            
            # 计算显示尺寸
            display_width = int(img_width * self.zoom_level)
            display_height = int(img_height * self.zoom_level)
            
            # 缩放图像
            if self.zoom_level != 1.0:
                display_array = cv2.resize(display_array, (display_width, display_height), 
                                         interpolation=cv2.INTER_LINEAR if self.zoom_level > 1 else cv2.INTER_AREA)
            
            # 转换为PIL图像
            if len(display_array.shape) == 2:
                pil_image = Image.fromarray(display_array, mode='L')
            else:
                pil_image = Image.fromarray(display_array, mode='RGB')
                
            # 转换为PhotoImage
            self.display_image = ImageTk.PhotoImage(pil_image)
            
            # 更新画布大小和滚动区域
            self.canvas.configure(scrollregion=(0, 0, display_width, display_height))
            
            # 显示图像
            if self.image_id:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.display_image)
            
            # 重绘ROI矩形
            self._redraw_roi()
            
            # 更新缩放信息
            self.zoom_info_var.set(f"缩放: {self.zoom_level*100:.0f}%")
            
        except Exception as e:
            self.logger.error(f"显示图像失败: {str(e)}")
            
    def _on_left_mouse_down(self, event):
        """左键按下事件 - 绘制ROI"""
        self.drawing = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_x = self.start_x
        self.current_y = self.start_y
        
        # 清除之前的矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            
    def _on_left_mouse_drag(self, event):
        """左键拖拽事件 - 绘制ROI"""
        if not self.drawing:
            return
            
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)
        
        # 更新矩形显示
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.current_x, self.current_y,
            outline='red', width=2, dash=(5, 5)
        )
        
    def _on_left_mouse_up(self, event):
        """左键释放事件 - 完成ROI绘制"""
        if not self.drawing:
            return
            
        self.drawing = False
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)
        
        # 计算ROI坐标（原始图像坐标）
        canvas_x1 = min(self.start_x, self.current_x) - self.pan_x
        canvas_y1 = min(self.start_y, self.current_y) - self.pan_y
        canvas_x2 = max(self.start_x, self.current_x) - self.pan_x
        canvas_y2 = max(self.start_y, self.current_y) - self.pan_y
        
        # 转换到原始图像坐标
        x1 = canvas_x1 / self.zoom_level
        y1 = canvas_y1 / self.zoom_level
        x2 = canvas_x2 / self.zoom_level
        y2 = canvas_y2 / self.zoom_level
        
        # 确保ROI在图像范围内
        img_height, img_width = self.image.shape[:2]
        x1 = max(0, min(x1, img_width - 1))
        y1 = max(0, min(y1, img_height - 1))
        x2 = max(0, min(x2, img_width - 1))
        y2 = max(0, min(y2, img_height - 1))
        
        # 计算宽度和高度
        width = int(x2 - x1)
        height = int(y2 - y1)
        
        if width > 10 and height > 10:  # 最小ROI尺寸
            self.roi = (int(x1), int(y1), width, height)
            self._update_roi_info()
        else:
            self._clear_roi()
            messagebox.showwarning("ROI太小", "请绘制更大的ROI区域（最小10x10像素）")
            
    def _on_right_mouse_down(self, event):
        """右键按下事件 - 开始平移"""
        self.panning = True
        self.last_pan_x = event.x
        self.last_pan_y = event.y
        
    def _on_right_mouse_drag(self, event):
        """右键拖拽事件 - 平移图像"""
        if not self.panning:
            return
            
        dx = event.x - self.last_pan_x
        dy = event.y - self.last_pan_y
        
        self.pan_x += dx
        self.pan_y += dy
        
        self.last_pan_x = event.x
        self.last_pan_y = event.y
        
        # 重新显示图像
        self._display_image()
        
    def _on_right_mouse_up(self, event):
        """右键释放事件 - 结束平移"""
        self.panning = False
        
    def _on_mouse_wheel(self, event):
        """鼠标滚轮事件 - 缩放"""
        # 获取鼠标位置
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        # 计算缩放因子
        if event.delta > 0 or event.num == 4:  # 向上滚动
            zoom_factor = 1.2
        else:  # 向下滚动
            zoom_factor = 1.0 / 1.2
            
        # 应用缩放
        self._zoom_at_point(zoom_factor, mouse_x, mouse_y)
            
    def _update_roi_info(self):
        """更新ROI信息显示"""
        if self.roi:
            x, y, w, h = self.roi
            self.roi_info_var.set(f"ROI: ({x}, {y}) 尺寸: {w}×{h}")
        else:
            self.roi_info_var.set("ROI: 未选择")
            
    def _clear_roi(self):
        """清除ROI选择"""
        self.roi = None
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        self._update_roi_info()
        
    def _confirm_selection(self):
        """确认ROI选择"""
        if self.roi is None:
            messagebox.showwarning("未选择ROI", "请先绘制ROI区域")
            return
            
        self.window.quit()
        self.window.destroy()
        
    def _cancel_selection(self):
        """取消ROI选择"""
        self.roi = None
        self.window.quit()
        self.window.destroy()
        
    def _zoom_at_point(self, zoom_factor, mouse_x, mouse_y):
        """在指定点进行缩放"""
        old_zoom = self.zoom_level
        new_zoom = old_zoom * zoom_factor
        
        # 限制缩放范围
        new_zoom = max(0.1, min(new_zoom, 10.0))
        
        if new_zoom != old_zoom:
            # 计算缩放中心点在图像中的位置
            image_x = (mouse_x - self.pan_x) / old_zoom
            image_y = (mouse_y - self.pan_y) / old_zoom
            
            # 更新缩放级别
            self.zoom_level = new_zoom
            
            # 调整平移以保持鼠标点位置不变
            self.pan_x = mouse_x - image_x * new_zoom
            self.pan_y = mouse_y - image_y * new_zoom
            
            # 重新显示图像
            self._display_image()
            
    def _zoom_in(self):
        """放大"""
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        self._zoom_at_point(1.2, canvas_center_x, canvas_center_y)
        
    def _zoom_out(self):
        """缩小"""
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        self._zoom_at_point(1.0/1.2, canvas_center_x, canvas_center_y)
        
    def _zoom_fit(self):
        """适应窗口"""
        if self.image is None:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        img_height, img_width = self.image.shape[:2]
        
        # 计算适应缩放
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.zoom_level = min(scale_x, scale_y, 1.0)
        
        # 居中显示
        self.pan_x = (canvas_width - img_width * self.zoom_level) / 2
        self.pan_y = (canvas_height - img_height * self.zoom_level) / 2
        
        self._display_image()
        
    def _zoom_100(self):
        """100%缩放"""
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        
        # 计算当前中心点在图像中的位置
        image_x = (canvas_center_x - self.pan_x) / self.zoom_level
        image_y = (canvas_center_y - self.pan_y) / self.zoom_level
        
        # 设置100%缩放
        self.zoom_level = 1.0
        
        # 调整平移以保持中心点
        self.pan_x = canvas_center_x - image_x
        self.pan_y = canvas_center_y - image_y
        
        self._display_image()
        
    def _redraw_roi(self):
        """重绘ROI矩形"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            
        if self.roi is None:
            return
            
        # 将ROI坐标转换为当前显示坐标
        x, y, w, h = self.roi
        
        # 转换到显示坐标
        display_x1 = x * self.zoom_level + self.pan_x
        display_y1 = y * self.zoom_level + self.pan_y
        display_x2 = (x + w) * self.zoom_level + self.pan_x
        display_y2 = (y + h) * self.zoom_level + self.pan_y
        
        # 绘制ROI矩形
        self.rect_id = self.canvas.create_rectangle(
            display_x1, display_y1, display_x2, display_y2,
            outline='red', width=2, dash=(5, 5)
        )

def apply_roi_to_image(image, roi):
    """
    将ROI应用到图像上
    
    Args:
        image: 输入图像
        roi: ROI坐标 (x, y, width, height)
        
    Returns:
        裁剪后的图像
    """
    if roi is None:
        return image
        
    x, y, w, h = roi
    return image[y:y+h, x:x+w]

def create_roi_mask(image_shape, roi):
    """
    创建ROI掩膜
    
    Args:
        image_shape: 原始图像形状
        roi: ROI坐标 (x, y, width, height)
        
    Returns:
        布尔掩膜，ROI区域为True，其他为False
    """
    if roi is None:
        return np.ones(image_shape[:2], dtype=bool)
        
    mask = np.zeros(image_shape[:2], dtype=bool)
    x, y, w, h = roi
    
    # 确保坐标在图像范围内
    x = max(0, min(x, image_shape[1] - 1))
    y = max(0, min(y, image_shape[0] - 1))
    x2 = min(x + w, image_shape[1])
    y2 = min(y + h, image_shape[0])
    
    mask[y:y2, x:x2] = True
    return mask
