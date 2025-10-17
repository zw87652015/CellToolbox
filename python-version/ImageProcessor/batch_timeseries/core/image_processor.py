#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理器 - 核心图像处理和细胞检测功能
Image Processor - Core image processing and cell detection functionality
"""

import numpy as np
import cv2
import tifffile
from PIL import Image, ExifTags
import os
import logging
from datetime import datetime
import pandas as pd
from skimage import filters, morphology, measure, segmentation
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy import ndimage
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 忽略一些常见的警告
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

class ImageProcessor:
    """图像处理器类"""
    
    def __init__(self, gaussian_sigma=1.5, threshold_method='otsu', min_area=500,
                 closing_radius=3, opening_radius=2, max_components=1,
                 progress_callback=None, log_callback=None):
        """
        初始化图像处理器
        
        Args:
            gaussian_sigma: 高斯模糊参数
            threshold_method: 阈值方法 ('otsu' 或 'triangle')
            min_area: 最小细胞面积
            closing_radius: 形态学关闭操作半径
            opening_radius: 形态学打开操作半径
            max_components: 保留的最大连通域数量
            progress_callback: 进度回调函数
            log_callback: 日志回调函数
        """
        self.gaussian_sigma = gaussian_sigma
        self.threshold_method = threshold_method
        self.min_area = min_area
        self.closing_radius = closing_radius
        self.opening_radius = opening_radius
        self.max_components = max_components
        
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        self.logger = logging.getLogger(__name__)
        self.stop_flag = False
        
        # 创建持久化线程池用于偏移优化 (避免重复创建/销毁线程开销)
        self._thread_pool = None
        self._max_workers = min(os.cpu_count() or 4, 16)
        
        # 缓存变量
        self.cell_mask = None
        self.dark_correction = None
    
    def __del__(self):
        """清理资源"""
        self.cleanup()
    
    def cleanup(self):
        """清理线程池资源"""
        if self._thread_pool is not None:
            try:
                self._thread_pool.shutdown(wait=True, cancel_futures=False)
                self._thread_pool = None
            except Exception as e:
                self.logger.warning(f"清理线程池时出错: {str(e)}")
        
    def log(self, message, level="INFO"):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            if level == "ERROR":
                self.logger.error(message)
            elif level == "WARNING":
                self.logger.warning(message)
            else:
                self.logger.info(message)
                
    def update_progress(self, current, total, message=""):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(current, total, message)
            
    def stop_processing(self):
        """停止处理"""
        self.stop_flag = True
        self.log("收到停止信号")
        
    def load_tiff_image(self, file_path, use_memmap=None, silent=False):
        """
        加载TIFF图像，支持16位和BigTIFF
        
        Args:
            file_path: 图像文件路径
            use_memmap: 是否使用内存映射，None为自动判断
            silent: 是否静默加载 (不输出日志)
            
        Returns:
            numpy数组形式的图像数据
        """
        try:
            # 检查文件大小决定是否使用内存映射
            if use_memmap is None:
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                use_memmap = file_size_mb > 500  # 大于500MB使用内存映射
                
            if use_memmap:
                if not silent:
                    self.log(f"使用内存映射加载大文件: {os.path.basename(file_path)}")
                # 使用内存映射加载大文件
                with tifffile.TiffFile(file_path) as tif:
                    image = tif.asarray(out='memmap')
            else:
                # 直接加载到内存
                image = tifffile.imread(file_path)
            
            if not silent:
                self.log(f"成功加载图像: {os.path.basename(file_path)}, 形状: {image.shape}, 数据类型: {image.dtype}")
            
            # 验证图像尺寸（必须为偶数，用于Bayer拆分）
            if image.shape[0] % 2 != 0 or image.shape[1] % 2 != 0:
                raise ValueError(f"Bayer 尺寸非法: 图像尺寸必须为偶数 {image.shape}")
                
            return image
            
        except Exception as e:
            error_msg = f"加载TIFF图像失败 {file_path}: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def extract_bayer_r_channel(self, image, silent=False):
        """
        从Bayer图像中提取R通道 (RGGB模式)
        
        Args:
            image: 输入的Bayer图像
            silent: 是否静默执行 (不输出日志)
            
        Returns:
            R通道图像 (float32)
        """
        try:
            # RGGB模式: R = 偶行偶列
            r_channel = image[0::2, 0::2].astype(np.float32)
            
            if not silent:
                self.log(f"Bayer R通道提取完成，形状: {r_channel.shape}")
            return r_channel
            
        except Exception as e:
            error_msg = f"Bayer R通道提取失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def calculate_dark_correction(self, darkfield_paths):
        """
        计算黑场校正值
        
        Args:
            darkfield_paths: 黑场图像文件路径列表
            
        Returns:
            平均黑场校正图像
        """
        if not darkfield_paths:
            self.log("未提供黑场图像，跳过黑场校正")
            return None
            
        try:
            self.log(f"开始计算黑场校正，共 {len(darkfield_paths)} 个文件")
            
            dark_images = []
            for i, dark_path in enumerate(darkfield_paths):
                if self.stop_flag:
                    return None
                    
                self.update_progress(i, len(darkfield_paths), f"加载黑场图像 {i+1}/{len(darkfield_paths)}")
                
                # 加载黑场图像
                dark_image = self.load_tiff_image(dark_path)
                
                # 提取R通道
                dark_r = self.extract_bayer_r_channel(dark_image)
                dark_images.append(dark_r)
                
            # 计算平均值
            self.update_progress(len(darkfield_paths), len(darkfield_paths), "计算黑场平均值")
            dark_correction = np.mean(dark_images, axis=0).astype(np.float32)
            
            self.log(f"黑场校正计算完成，平均值: {np.mean(dark_correction):.2f}")
            return dark_correction
            
        except Exception as e:
            error_msg = f"计算黑场校正失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def apply_dark_correction(self, image, dark_correction, silent=False):
        """
        应用黑场校正
        
        Args:
            image: 输入图像
            dark_correction: 黑场校正图像
            silent: 是否静默执行 (不输出日志)
            
        Returns:
            校正后的图像
        """
        if dark_correction is None:
            return image
            
        try:
            # 减去黑场并限制最小值为0
            corrected = image - dark_correction
            corrected = np.maximum(corrected, 0)
            
            if not silent:
                self.log(f"黑场校正完成，校正前均值: {np.mean(image):.2f}, 校正后均值: {np.mean(corrected):.2f}")
            return corrected
            
        except Exception as e:
            error_msg = f"应用黑场校正失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def detect_cells_in_brightfield(self, brightfield_image, dark_correction=None, roi=None, **kwargs):
        """
        在明场图像中检测细胞
        
        Args:
            brightfield_image: 明场图像
            dark_correction: 黑场校正图像
            roi: ROI区域 (x, y, width, height)，None表示使用整个图像
            
        Returns:
            细胞掩膜 (布尔数组)
        """
        try:
            # 收集处理步骤信息用于批量输出
            detection_steps = []
            detection_steps.append("开始明场细胞检测")
            
            # 提取R通道
            bf_r = self.extract_bayer_r_channel(brightfield_image)
            
            # 应用黑场校正
            bf_r_corrected = self.apply_dark_correction(bf_r, dark_correction)
            
            # 应用ROI限制
            if roi is not None:
                x, y, w, h = roi
                detection_steps.append(f"应用ROI限制: ({x}, {y}) 尺寸: {w}×{h}")
                
                # 创建ROI掩膜
                roi_mask = np.zeros(bf_r_corrected.shape, dtype=bool)
                
                # 确保ROI在图像范围内
                x = max(0, min(x, bf_r_corrected.shape[1] - 1))
                y = max(0, min(y, bf_r_corrected.shape[0] - 1))
                x2 = min(x + w, bf_r_corrected.shape[1])
                y2 = min(y + h, bf_r_corrected.shape[0])
                
                roi_mask[y:y2, x:x2] = True
                
                # 只在ROI区域内进行处理
                processing_image = bf_r_corrected.copy()
                processing_image[~roi_mask] = np.mean(bf_r_corrected[roi_mask])  # 用ROI区域均值填充外部
            else:
                processing_image = bf_r_corrected
                roi_mask = np.ones(bf_r_corrected.shape, dtype=bool)
            
            # 获取动态参数，如果没有提供则使用默认值
            gaussian_sigma = kwargs.get('gaussian_sigma', self.gaussian_sigma)
            threshold_method = kwargs.get('threshold_method', self.threshold_method)
            min_area = kwargs.get('min_area', self.min_area)
            closing_radius = kwargs.get('closing_radius', self.closing_radius)
            opening_radius = kwargs.get('opening_radius', self.opening_radius)
            smoothing_radius = kwargs.get('smoothing_radius', 0)
            
            # 高斯模糊去噪
            detection_steps.append(f"应用高斯模糊，σ = {gaussian_sigma}")
            blurred = filters.gaussian(processing_image, sigma=gaussian_sigma, preserve_range=True)
            
            # 自动阈值分割
            detection_steps.append(f"应用阈值分割，方法: {threshold_method}")
            if threshold_method == 'otsu':
                threshold = filters.threshold_otsu(blurred)
            elif threshold_method == 'triangle':
                threshold = filters.threshold_triangle(blurred)
            else:
                raise ValueError(f"不支持的阈值方法: {threshold_method}")
                
            binary_mask = blurred < threshold  # 细胞通常比背景暗
            
            # 形态学处理
            detection_steps.append("应用形态学处理")
            
            # 关闭操作 - 填充小洞
            if closing_radius > 0:
                closing_kernel = morphology.disk(closing_radius)
                binary_mask = morphology.binary_closing(binary_mask, closing_kernel)
                
            # 打开操作 - 去除小噪声
            if opening_radius > 0:
                opening_kernel = morphology.disk(opening_radius)
                binary_mask = morphology.binary_opening(binary_mask, opening_kernel)
                
            # 移除小对象
            binary_mask = morphology.remove_small_objects(binary_mask, min_size=min_area)
            
            # 边缘平滑处理 - 让细胞边缘更圆润
            if smoothing_radius > 0:
                detection_steps.append(f"应用边缘平滑，半径 = {smoothing_radius}")
                # 使用额外的关闭操作来平滑边缘
                smoothing_kernel = morphology.disk(smoothing_radius)
                binary_mask = morphology.binary_closing(binary_mask, smoothing_kernel)
                # 再用稍小的开操作来保持大小
                if smoothing_radius > 1:
                    smaller_kernel = morphology.disk(smoothing_radius - 1)
                    binary_mask = morphology.binary_opening(binary_mask, smaller_kernel)
            
            # 标记连通域
            labeled_mask = measure.label(binary_mask)
            regions = measure.regionprops(labeled_mask)
            
            detection_steps.append(f"检测到 {len(regions)} 个连通域")
            
            # 保留最大的几个连通域
            if len(regions) > self.max_components:
                # 按面积排序
                regions_sorted = sorted(regions, key=lambda x: x.area, reverse=True)
                keep_labels = [r.label for r in regions_sorted[:self.max_components]]
                
                # 创建新的掩膜
                final_mask = np.zeros_like(labeled_mask, dtype=bool)
                for label in keep_labels:
                    final_mask |= (labeled_mask == label)
                    
                detection_steps.append(f"保留最大的 {self.max_components} 个连通域")
            else:
                final_mask = binary_mask
                
            # 应用ROI限制到最终掩膜
            if roi is not None:
                final_mask = final_mask & roi_mask
                detection_steps.append("已将细胞掩膜限制在ROI区域内")
            
            # 计算最终统计信息
            final_regions = measure.regionprops(measure.label(final_mask))
            total_area = sum(r.area for r in final_regions)
            
            detection_steps.append(f"细胞检测完成，最终细胞数: {len(final_regions)}, 总面积: {total_area} 像素")
            
            # 批量输出所有检测步骤 (单次日志输出，避免I/O瓶颈)
            detection_summary = "\n".join(detection_steps)
            self.log(detection_summary)
            
            return final_mask
            
        except Exception as e:
            error_msg = f"明场细胞检测失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def _evaluate_single_offset(self, fluo_r_corrected, cell_mask, current_x, current_y, dx, dy, search_count, total_searches):
        """
        评估单个偏移位置的荧光强度 (并行处理辅助方法)
        
        Args:
            fluo_r_corrected: 校正后的荧光R通道
            cell_mask: 细胞掩膜
            current_x: 当前X偏移
            current_y: 当前Y偏移
            dx: X方向改进量
            dy: Y方向改进量
            search_count: 搜索序号
            total_searches: 总搜索数
            
        Returns:
            评估结果字典或None
        """
        # 应用偏移到掩膜
        corrected_mask = self._apply_offset_to_mask(cell_mask, current_x, current_y, fluo_r_corrected.shape)
        
        # 测量强度
        cell_pixels = fluo_r_corrected[corrected_mask]
        
        if len(cell_pixels) > 0:
            mean_intensity = float(np.mean(cell_pixels))
            total_intensity = float(np.sum(cell_pixels))
            area = len(cell_pixels)
            
            return {
                'offset': (current_x, current_y),
                'improvement': (dx, dy),
                'mean': mean_intensity,
                'total': total_intensity,
                'area': area
            }
        else:
            return None
    
    def optimize_offset_for_max_intensity(self, fluorescence_image, cell_mask, dark_correction=None, base_offset=(0, 0), search_range=5):
        """
        优化偏移量以获得最大平均荧光强度 (并行版本)
        
        Args:
            fluorescence_image: 荧光图像
            cell_mask: 细胞掩膜 (基于明场图像)
            dark_correction: 黑场校正图像
            base_offset: 基础偏移量 (x_offset, y_offset)
            search_range: 搜索范围 (±像素数)
            
        Returns:
            字典包含最优偏移量和对应的强度数据
        """
        try:
            # 提取R通道 (静默模式)
            fluo_r = self.extract_bayer_r_channel(fluorescence_image, silent=True)
            
            # 应用黑场校正 (静默模式)
            fluo_r_corrected = self.apply_dark_correction(fluo_r, dark_correction, silent=True)
            
            base_x, base_y = base_offset
            total_searches = (2 * search_range + 1) ** 2
            
            # 使用持久化线程池 (避免重复创建/销毁线程开销)
            if self._thread_pool is None:
                self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers)
                self.log(f"创建持久化线程池: {self._max_workers}线程")
            
            self.log(f"开始偏移优化搜索 (并行处理, {self._max_workers}线程): 基础偏移=({base_x}, {base_y}), 搜索范围=±{search_range}像素，共{total_searches}个位置...")
            
            # 生成所有要测试的偏移位置
            offset_tasks = []
            search_count = 0
            for dx in range(-search_range, search_range + 1):
                for dy in range(-search_range, search_range + 1):
                    search_count += 1
                    current_x = base_x + dx
                    current_y = base_y + dy
                    offset_tasks.append((current_x, current_y, dx, dy, search_count))
            
            # 并行评估所有偏移位置
            best_result = None
            best_mean = -1
            results_lock = threading.Lock()
            completed_count = 0
            
            executor = self._thread_pool
            # 提交所有任务
            future_to_offset = {}
            for current_x, current_y, dx, dy, search_count in offset_tasks:
                future = executor.submit(
                    self._evaluate_single_offset,
                    fluo_r_corrected,
                    cell_mask,
                    current_x,
                    current_y,
                    dx,
                    dy,
                    search_count,
                    total_searches
                )
                future_to_offset[future] = (current_x, current_y, dx, dy)
            
            # 收集结果
            for future in as_completed(future_to_offset):
                result = future.result()
                completed_count += 1
                if result is not None:
                    with results_lock:
                        if result['mean'] > best_mean:
                            best_mean = result['mean']
                            current_x, current_y, dx, dy = future_to_offset[future]
                            best_result = {
                                'mean': result['mean'],
                                'total': result['total'],
                                'area': result['area'],
                                'optimized_offset': (current_x, current_y),
                                'offset_improvement': (dx, dy)
                            }
            
            # 所有位置评估完成，输出结果
            self.log(f"偏移优化搜索完成: 已评估 {completed_count}/{total_searches} 个位置")
            
            # 检查是否找到有效结果
            if best_result is None:
                self.log("警告: 偏移优化未找到有效掩膜", "WARNING")
                return {
                    'mean': 0.0,
                    'total': 0.0,
                    'area': 0,
                    'optimized_offset': base_offset,
                    'offset_improvement': (0, 0)
                }
            
            # 输出总结 (单次日志输出，避免I/O瓶颈)
            improvement_x, improvement_y = best_result['offset_improvement']
            final_x, final_y = best_result['optimized_offset']
            
            summary = (
                f"偏移优化完成总结 (并行处理):\n"
                f"  - 搜索位置数: {total_searches}\n"
                f"  - 并行线程数: {self._max_workers}\n"
                f"  - 基础偏移: ({base_x:+d}, {base_y:+d})\n"
                f"  - 最佳偏移: ({final_x:+d}, {final_y:+d})\n"
                f"  - 偏移改进: ({improvement_x:+d}, {improvement_y:+d})\n"
                f"  - 最佳平均强度: {best_mean:.2f}\n"
                f"  - 细胞面积: {best_result['area']} 像素\n"
                f"  - 总强度: {best_result['total']:.2f}"
            )
            self.log(summary)
            
            return best_result
            
        except Exception as e:
            error_msg = f"偏移优化失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)

    def measure_fluorescence_intensity(self, fluorescence_image, cell_mask, dark_correction=None, offset_correction=None, enable_offset_optimization=False, search_range=5):
        """
        测量荧光强度
        
        Args:
            fluorescence_image: 荧光图像
            cell_mask: 细胞掩膜 (基于明场图像)
            dark_correction: 黑场校正图像
            offset_correction: 偏移校正 (x_offset, y_offset) - 明场相对荧光的偏移
            enable_offset_optimization: 是否启用偏移优化
            search_range: 搜索范围 (±像素数)
            
        Returns:
            字典包含 mean, total, area, 以及可能的优化信息
        """
        try:
            # 如果启用偏移优化，使用优化方法
            if enable_offset_optimization:
                base_offset = offset_correction if offset_correction is not None else (0, 0)
                return self.optimize_offset_for_max_intensity(fluorescence_image, cell_mask, dark_correction, base_offset, search_range)
            
            # 原有的非优化方法
            # 提取R通道 (静默模式)
            fluo_r = self.extract_bayer_r_channel(fluorescence_image, silent=True)
            
            # 应用黑场校正 (静默模式)
            fluo_r_corrected = self.apply_dark_correction(fluo_r, dark_correction, silent=True)
            
            # 应用偏移校正
            if offset_correction is not None:
                x_offset, y_offset = offset_correction
                # 创建偏移后的细胞掩膜
                corrected_mask = self._apply_offset_to_mask(cell_mask, x_offset, y_offset, fluo_r_corrected.shape)
            else:
                corrected_mask = cell_mask
            
            # 在细胞区域内测量
            cell_pixels = fluo_r_corrected[corrected_mask]
            
            if len(cell_pixels) == 0:
                self.log("警告: 细胞掩膜为空", "WARNING")
                return {'mean': 0.0, 'total': 0.0, 'area': 0}
                
            # 计算统计量
            area = len(cell_pixels)
            total_intensity = float(np.sum(cell_pixels))
            mean_intensity = float(np.mean(cell_pixels))
            
            return {
                'mean': mean_intensity,
                'total': total_intensity,
                'area': area
            }
            
        except Exception as e:
            error_msg = f"荧光强度测量失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def _apply_offset_to_mask(self, mask, x_offset, y_offset, target_shape):
        """
        对掩膜应用偏移校正 (优化版本使用数组切片)
        
        Args:
            mask: 原始掩膜 (基于明场图像)
            x_offset: X方向偏移 (像素)
            y_offset: Y方向偏移 (像素)
            target_shape: 目标图像形状 (荧光图像)
            
        Returns:
            偏移校正后的掩膜
        """
        try:
            # 创建新的掩膜
            corrected_mask = np.zeros(target_shape, dtype=bool)
            
            # 快速检查: 如果没有偏移且形状相同，直接返回
            if x_offset == 0 and y_offset == 0 and mask.shape == target_shape:
                return mask.copy()
            
            # 计算源掩膜中需要提取的区域 (考虑偏移后仍在目标范围内的部分)
            # y方向: 源掩膜的y坐标范围
            y_src_start = max(0, -y_offset)
            y_src_end = min(mask.shape[0], target_shape[0] - y_offset)
            
            # x方向: 源掩膜的x坐标范围
            x_src_start = max(0, -x_offset)
            x_src_end = min(mask.shape[1], target_shape[1] - x_offset)
            
            # 如果没有重叠区域，返回空掩膜
            if y_src_start >= y_src_end or x_src_start >= x_src_end:
                return corrected_mask
            
            # 计算目标掩膜中的放置位置
            y_dst_start = y_src_start + y_offset
            y_dst_end = y_dst_start + (y_src_end - y_src_start)
            x_dst_start = x_src_start + x_offset
            x_dst_end = x_dst_start + (x_src_end - x_src_start)
            
            # 使用数组切片直接复制区域 (比逐点操作快得多)
            corrected_mask[y_dst_start:y_dst_end, x_dst_start:x_dst_end] = \
                mask[y_src_start:y_src_end, x_src_start:x_src_end]
            
            return corrected_mask
            
        except Exception as e:
            self.log(f"偏移校正失败: {str(e)}", "ERROR")
            # 如果失败，尝试返回形状匹配的空掩膜
            return np.zeros(target_shape, dtype=bool)
            
    def extract_timestamp_from_arw(self, tiff_path):
        """
        从对应的ARW文件中提取时间戳
        
        Args:
            tiff_path: TIFF文件路径
            
        Returns:
            datetime对象或None
        """
        try:
            # 获取TIFF文件的目录和基础文件名
            tiff_dir = os.path.dirname(tiff_path)
            tiff_basename = os.path.splitext(os.path.basename(tiff_path))[0]
            
            # 可能的ARW文件名模式
            possible_arw_names = [
                f"{tiff_basename}.ARW",
                f"{tiff_basename}.arw",
            ]
            
            # 如果TIFF文件名包含后缀（如-RAWcomposite），尝试去掉后缀
            if '-' in tiff_basename:
                base_name = tiff_basename.split('-')[0]
                possible_arw_names.extend([
                    f"{base_name}.ARW",
                    f"{base_name}.arw",
                ])
            
            # 查找ARW文件
            arw_path = None
            for arw_name in possible_arw_names:
                candidate_path = os.path.join(tiff_dir, arw_name)
                if os.path.exists(candidate_path):
                    arw_path = candidate_path
                    break
            
            if arw_path is None:
                # 最后尝试：扫描目录中的所有ARW文件，按修改时间匹配
                arw_path = self._find_closest_arw_by_time(tiff_path)
                if arw_path is None:
                    self.log(f"未找到对应的ARW文件，尝试的文件名: {possible_arw_names}", "WARNING")
                    return None
            
            # 使用ARW文件的修改时间
            arw_mtime = os.path.getmtime(arw_path)
            timestamp = datetime.fromtimestamp(arw_mtime)
            
            self.log(f"找到ARW文件: {os.path.basename(arw_path)} -> {timestamp}")
            return timestamp
            
        except Exception as e:
            self.log(f"从ARW文件提取时间戳失败: {str(e)}", "ERROR")
            return None
    
    def _find_closest_arw_by_time(self, tiff_path):
        """
        通过修改时间查找最接近的ARW文件
        
        Args:
            tiff_path: TIFF文件路径
            
        Returns:
            最接近的ARW文件路径或None
        """
        try:
            tiff_dir = os.path.dirname(tiff_path)
            tiff_mtime = os.path.getmtime(tiff_path)
            
            # 查找目录中的所有ARW文件
            arw_files = []
            for filename in os.listdir(tiff_dir):
                if filename.lower().endswith('.arw'):
                    arw_path = os.path.join(tiff_dir, filename)
                    arw_mtime = os.path.getmtime(arw_path)
                    time_diff = abs(arw_mtime - tiff_mtime)
                    arw_files.append((arw_path, time_diff))
            
            if not arw_files:
                return None
            
            # 找到时间最接近的ARW文件
            closest_arw = min(arw_files, key=lambda x: x[1])
            
            # 如果时间差小于1小时，认为是匹配的
            if closest_arw[1] < 3600:  # 1小时 = 3600秒
                self.log(f"通过时间匹配找到ARW文件: {os.path.basename(closest_arw[0])}, 时间差: {closest_arw[1]:.1f}秒")
                return closest_arw[0]
            else:
                self.log(f"最接近的ARW文件时间差过大: {closest_arw[1]:.1f}秒", "WARNING")
                return None
                
        except Exception as e:
            self.log(f"按时间查找ARW文件失败: {str(e)}", "ERROR")
            return None
    
    def extract_timestamp_from_exif(self, image_path):
        """
        从EXIF数据中提取时间戳，优先使用对应的ARW文件时间
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            datetime对象或None
        """
        # 优先尝试使用对应的ARW文件时间戳
        arw_timestamp = self.extract_timestamp_from_arw(image_path)
        if arw_timestamp is not None:
            return arw_timestamp
        
        self.log(f"ARW文件不可用，尝试从TIFF EXIF提取时间戳: {os.path.basename(image_path)}", "WARNING")
        
        try:
            # 尝试使用PIL读取EXIF
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeOriginal' or tag == 'DateTime':
                            try:
                                timestamp = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                self.log(f"使用TIFF EXIF时间戳: {timestamp}")
                                return timestamp
                            except ValueError:
                                continue
                                
        except Exception:
            pass
            
        # 如果EXIF读取失败，使用文件修改时间
        try:
            mtime = os.path.getmtime(image_path)
            timestamp = datetime.fromtimestamp(mtime)
            self.log(f"使用TIFF文件修改时间: {timestamp}", "WARNING")
            return timestamp
        except Exception:
            self.log(f"无法获取任何时间戳: {os.path.basename(image_path)}", "ERROR")
            return None
            
            
    def create_preview_image(self, brightfield_image, cell_mask, output_path):
        """
        创建预览图像
        
        Args:
            brightfield_image: 明场图像
            cell_mask: 细胞掩膜
            output_path: 输出路径
        """
        try:
            # 提取R通道用于显示
            bf_r = self.extract_bayer_r_channel(brightfield_image)
            
            # 归一化到0-255用于显示
            bf_display = ((bf_r - np.min(bf_r)) / (np.max(bf_r) - np.min(bf_r)) * 255).astype(np.uint8)
            
            # 创建RGB图像
            rgb_image = np.stack([bf_display, bf_display, bf_display], axis=2)
            
            # 在掩膜区域添加绿色轮廓
            contours, _ = cv2.findContours(cell_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                cv2.drawContours(rgb_image, [contour], -1, (0, 255, 0), 2)
                
            # 添加面积信息
            total_area = np.sum(cell_mask)
            cv2.putText(rgb_image, f'Cell Area: {total_area} pixels', 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                       
            # 保存图像
            cv2.imwrite(output_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
            
        except Exception as e:
            self.log(f"创建预览图像失败: {str(e)}", "ERROR")
            
    def process_batch(self, brightfield_path, fluorescence_folder, darkfield_paths, output_folder, roi=None, offset_correction=None, enable_offset_optimization=False, search_range=5, colormap_style='auto'):
        """
        批量处理荧光图像
        
        Args:
            brightfield_path: 明场图像路径
            fluorescence_folder: 荧光图像文件夹
            darkfield_paths: 黑场图像路径列表
            output_folder: 输出文件夹
            roi: ROI区域 (x, y, width, height)
            offset_correction: 偏移校正 (x_offset, y_offset) - 明场相对荧光的偏移
            enable_offset_optimization: 是否启用偏移优化
            search_range: 搜索范围 (±像素数)
            colormap_style: ROI可视化色图样式 ('auto' 或 'global')
            
        Returns:
            处理是否成功
        """
        try:
            import time
            batch_start_time = time.perf_counter()
            
            self.log("开始批量荧光强度测量")
            
            # 创建输出目录
            from core.file_manager import FileManager
            file_manager = FileManager()
            results_dir = file_manager.create_output_directory(output_folder)
            
            # 1. 加载明场图像并检测细胞
            self.update_progress(0, 100, "加载明场图像...")
            t0 = time.perf_counter()
            bf_image = self.load_tiff_image(brightfield_path)
            t1 = time.perf_counter()
            self.log(f"⏱️ 明场图像加载用时: {(t1-t0)*1000:.1f}ms")
            
            # 2. 计算黑场校正
            self.update_progress(10, 100, "计算黑场校正...")
            dark_correction = None
            if darkfield_paths:
                t0 = time.perf_counter()
                dark_correction = self.calculate_dark_correction(darkfield_paths)
                self.dark_correction = dark_correction
                t1 = time.perf_counter()
                self.log(f"⏱️ 黑场校正计算用时: {(t1-t0)*1000:.1f}ms")
                
            # 3. 检测细胞
            self.update_progress(20, 100, "检测细胞...")
            t0 = time.perf_counter()
            cell_mask = self.detect_cells_in_brightfield(bf_image, dark_correction, roi)
            self.cell_mask = cell_mask
            t1 = time.perf_counter()
            self.log(f"⏱️ 细胞检测用时: {(t1-t0)*1000:.1f}ms")
            
            # 保存细胞掩膜
            mask_path = os.path.join(results_dir, "masks", "cell_mask.png")
            os.makedirs(os.path.dirname(mask_path), exist_ok=True)
            cv2.imwrite(mask_path, (cell_mask * 255).astype(np.uint8))
            
            # 4. 获取荧光图像列表
            self.update_progress(30, 100, "扫描荧光图像...")
            fluorescence_files = file_manager.find_fluorescence_files(fluorescence_folder)
            
            if not fluorescence_files:
                raise Exception("未找到荧光图像文件")
                
            self.log(f"找到 {len(fluorescence_files)} 个荧光图像文件")
            
            # 计算全局色图范围 (如果使用global colormap)
            global_vmin = None
            global_vmax = None
            self.log(f"ROI可视化色图样式: {colormap_style}")
            if colormap_style == 'global':
                self.update_progress(30, 100, "计算全局色图范围...")
                self.log("使用全局色图模式 - 开始计算全局色图范围...")
                all_values = []
                for fluo_path in fluorescence_files:
                    try:
                        fluo_image = self.load_tiff_image(fluo_path, silent=True)
                        fluo_r = self.extract_bayer_r_channel(fluo_image, silent=True)
                        fluo_r_corrected = self.apply_dark_correction(fluo_r, dark_correction, silent=True)
                        
                        # 应用偏移并提取ROI区域的值
                        if offset_correction is not None:
                            x_offset, y_offset = offset_correction
                            corrected_cell_mask = self._apply_offset_to_mask(cell_mask, x_offset, y_offset, fluo_r_corrected.shape)
                        else:
                            corrected_cell_mask = cell_mask
                        
                        # 提取ROI区域
                        if roi and len(roi) == 4:
                            x, y, w, h = roi
                            img_h, img_w = fluo_r_corrected.shape
                            x = max(0, min(x, img_w - 1))
                            y = max(0, min(y, img_h - 1))
                            w = min(w, img_w - x)
                            h = min(h, img_h - y)
                            if w > 0 and h > 0:
                                roi_image = fluo_r_corrected[y:y+h, x:x+w]
                            else:
                                roi_image = fluo_r_corrected
                        else:
                            roi_image = fluo_r_corrected
                        
                        all_values.append(roi_image.min())
                        all_values.append(roi_image.max())
                    except Exception as e:
                        self.log(f"计算全局范围时跳过文件: {os.path.basename(fluo_path)}", "WARNING")
                        continue
                
                if all_values:
                    global_vmin = np.min(all_values)
                    global_vmax = np.max(all_values)
                    self.log(f"全局色图范围: [{global_vmin:.2f}, {global_vmax:.2f}]")
                else:
                    self.log("未能计算全局色图范围，使用自动缩放", "WARNING")
            
            # 5. 处理每个荧光图像
            results = []
            base_timestamp = None
            total_files = len(fluorescence_files)
            
            # 初始化计时统计
            total_load_time = 0.0
            total_measure_time = 0.0
            total_vis_time = 0.0
            
            for i, fluo_path in enumerate(fluorescence_files):
                if self.stop_flag:
                    self.log("处理被用户停止")
                    return False
                    
                # 更细粒度的进度计算: 30% 基础 + 60% 文件处理
                file_progress = 30.0 + (i / total_files) * 60.0
                self.update_progress(file_progress, 100, f"处理荧光图像 {i+1}/{total_files}")
                
                try:
                    # 加载荧光图像 (静默模式)
                    t0 = time.perf_counter()
                    fluo_image = self.load_tiff_image(fluo_path, silent=True)
                    t1 = time.perf_counter()
                    load_time = (t1 - t0) * 1000
                    total_load_time += load_time
                    
                    # 输出前3张图片的详细计时以观察缓存效果
                    if i < 3:
                        self.log(f"⏱️ 图像 #{i+1} 加载用时: {load_time:.1f}ms")
                    
                    # 提取时间戳
                    timestamp = self.extract_timestamp_from_exif(fluo_path)
                    
                    if timestamp is None:
                        # 静默跳过 (不记录日志)
                        continue
                        
                    # 计算相对时间
                    if base_timestamp is None:
                        base_timestamp = timestamp
                        elapsed_s = 0.0
                    else:
                        elapsed_s = (timestamp - base_timestamp).total_seconds()
                        
                    # 测量荧光强度（应用偏移校正和可选的偏移优化）
                    t0 = time.perf_counter()
                    intensity_data = self.measure_fluorescence_intensity(fluo_image, cell_mask, dark_correction, offset_correction, enable_offset_optimization, search_range)
                    t1 = time.perf_counter()
                    measure_time = (t1 - t0) * 1000
                    total_measure_time += measure_time
                    
                    # 输出前3张图片的测量计时（包含偏移优化时间）
                    if i < 3:
                        opt_info = ""
                        if enable_offset_optimization and 'optimized_offset' in intensity_data:
                            opt_x, opt_y = intensity_data['optimized_offset']
                            opt_info = f" (优化偏移: ({opt_x}, {opt_y}))"
                        self.log(f"⏱️ 图像 #{i+1} 测量用时: {measure_time:.1f}ms{opt_info}")
                    
                    # 记录结果
                    result = {
                        'DateTimeOriginal': timestamp.isoformat(),
                        'elapsed_s': round(elapsed_s, 3),
                        'frame_i': i,
                        'Mean': round(intensity_data['mean'], 3),
                        'Total': round(intensity_data['total'], 3),
                        'Area': intensity_data['area'],
                        'filename': os.path.basename(fluo_path)
                    }
                    
                    # 如果启用了偏移优化，添加优化信息
                    if enable_offset_optimization and 'optimized_offset' in intensity_data:
                        opt_x, opt_y = intensity_data['optimized_offset']
                        imp_x, imp_y = intensity_data['offset_improvement']
                        result['Optimized_Offset_X'] = opt_x
                        result['Optimized_Offset_Y'] = opt_y
                        result['Offset_Improvement_X'] = imp_x
                        result['Offset_Improvement_Y'] = imp_y
                    
                    results.append(result)
                    
                    # 创建单张荧光图像的ROI可视化 (静默模式)
                    try:
                        t0 = time.perf_counter()
                        roi_vis_dir = os.path.join(results_dir, "roi_visualizations")
                        os.makedirs(roi_vis_dir, exist_ok=True)
                        roi_vis_path = os.path.join(roi_vis_dir, f"roi_vis_{os.path.splitext(os.path.basename(fluo_path))[0]}.png")
                        
                        # 第一个文件输出详细信息
                        if i == 0:
                            self.log(f"开始创建ROI可视化...")
                            self.log(f"  ROI可视化目录: {os.path.abspath(roi_vis_dir)}")
                            self.log(f"  第一个文件路径: {roi_vis_path}")
                        
                        # 使用优化后的偏移（如果启用了优化），否则使用基础偏移
                        vis_offset = intensity_data.get('optimized_offset', offset_correction) if enable_offset_optimization else offset_correction
                        
                        # 传递完整的细胞掩膜和实际使用的偏移校正参数 (静默模式)
                        self.create_fluorescence_roi_visualization(fluo_image, self.cell_mask, roi, intensity_data, roi_vis_path, elapsed_s, vis_offset, silent=True, global_vmin=global_vmin, global_vmax=global_vmax)
                        t1 = time.perf_counter()
                        vis_time = (t1 - t0) * 1000
                        total_vis_time += vis_time
                            
                    except Exception as vis_error:
                        # 静默失败 (仅记录关键错误)
                        if i == 0:  # 仅在第一个文件失败时警告
                            self.log(f"创建ROI可视化失败: {str(vis_error)}", "WARNING")
                    
                except Exception as e:
                    # 静默失败 (仅记录关键错误)
                    if i == 0:  # 仅在第一个文件失败时警告
                        self.log(f"处理文件失败: {str(e)}", "WARNING")
                    continue
                    
            # 6. 保存结果
            self.update_progress(90, 100, "保存结果...")
            
            if results:
                # 保存CSV
                csv_path = os.path.join(results_dir, "csv", "fluorescence_intensity_results.csv")
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                
                df = pd.DataFrame(results)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                # 创建叠加图像 (静默模式)
                try:
                    overlay_path = os.path.join(results_dir, "images", "cell_overlay.png")
                    os.makedirs(os.path.dirname(overlay_path), exist_ok=True)
                    self.create_overlay_image(bf_image, cell_mask, overlay_path)
                except Exception as overlay_error:
                    self.log(f"创建明场叠加图像失败: {str(overlay_error)}", "WARNING")
                
                # 保存处理日志
                log_path = os.path.join(results_dir, "logs", "processing_log.txt")
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                self.save_processing_log(log_path, len(results), len(fluorescence_files))
                
                # 生成独立的色标尺图像（如果使用全局色图）
                if global_vmin is not None and global_vmax is not None:
                    try:
                        colorbar_path = os.path.join(results_dir, "roi_visualizations", "colorbar_reference.png")
                        colorbar_abs_path = os.path.abspath(colorbar_path)
                        self.log(f"正在生成独立色标尺（PNG + SVG矢量图）...")
                        self.log(f"  输出路径: {colorbar_abs_path}")
                        self.log(f"  全局色图范围: vmin={global_vmin:.2f}, vmax={global_vmax:.2f}")
                        
                        # 确保目录存在
                        colorbar_dir = os.path.dirname(colorbar_abs_path)
                        if not os.path.exists(colorbar_dir):
                            os.makedirs(colorbar_dir, exist_ok=True)
                            self.log(f"  创建目录: {colorbar_dir}")
                        
                        self._create_standalone_colorbar(colorbar_abs_path, global_vmin, global_vmax)
                        
                        # 验证PNG文件
                        png_exists = os.path.exists(colorbar_abs_path)
                        svg_path = colorbar_abs_path.replace('.png', '.svg')
                        svg_exists = os.path.exists(svg_path)
                        
                        if png_exists and svg_exists:
                            png_size = os.path.getsize(colorbar_abs_path)
                            svg_size = os.path.getsize(svg_path)
                            self.log(f"✓ 独立色标尺已生成!")
                            self.log(f"  PNG (高分辨率位图): {png_size} bytes")
                            self.log(f"  SVG (无损矢量图): {svg_size} bytes")
                            self.log(f"  路径: {colorbar_dir}")
                        else:
                            if not png_exists:
                                self.log(f"✗ PNG文件未创建: {colorbar_abs_path}", "ERROR")
                            if not svg_exists:
                                self.log(f"✗ SVG文件未创建: {svg_path}", "ERROR")
                    except Exception as colorbar_error:
                        self.log(f"✗ 生成色标尺失败: {str(colorbar_error)}", "ERROR")
                        import traceback
                        self.log(f"详细错误: {traceback.format_exc()}", "ERROR")
                else:
                    self.log("未使用全局色图模式，不生成独立色标尺")
                
                self.update_progress(100, 100, "处理完成！")
                
                # 计算总用时
                batch_end_time = time.perf_counter()
                total_batch_time = batch_end_time - batch_start_time
                
                # 计算平均用时
                num_processed = len(results)
                avg_load_time = total_load_time / num_processed if num_processed > 0 else 0
                avg_measure_time = total_measure_time / num_processed if num_processed > 0 else 0
                avg_vis_time = total_vis_time / num_processed if num_processed > 0 else 0
                avg_total_per_image = (total_load_time + total_measure_time + total_vis_time) / num_processed if num_processed > 0 else 0
                
                # 批量输出最终总结 (单次日志输出，避免I/O瓶颈)
                colorbar_line = ""
                if global_vmin is not None and global_vmax is not None:
                    colorbar_line = f"  - 色标尺参考: roi_visualizations/colorbar_reference.png + .svg (全局缩放矢量图)\n"
                
                completion_summary = (
                    f"\n批量处理完成！\n"
                    f"成功处理: {len(results)}/{len(fluorescence_files)} 个文件\n"
                    f"结果目录: {results_dir}\n"
                    f"  - CSV数据: csv/fluorescence_intensity_results.csv\n"
                    f"  - 细胞掩膜: masks/cell_mask.png\n"
                    f"  - ROI可视化: roi_visualizations/ ({len(results)} 个文件)\n"
                    f"{colorbar_line}"
                    f"  - 明场叠加图: images/cell_overlay.png\n"
                    f"\n⏱️ 性能统计:\n"
                    f"  总用时: {total_batch_time:.2f}s\n"
                    f"  单图平均:\n"
                    f"    - 加载: {avg_load_time:.1f}ms\n"
                    f"    - 测量: {avg_measure_time:.1f}ms\n"
                    f"    - 可视化: {avg_vis_time:.1f}ms\n"
                    f"    - 总计: {avg_total_per_image:.1f}ms\n"
                    f"  吞吐量: {num_processed / total_batch_time:.2f} 图像/秒"
                )
                self.log(completion_summary)
                
                return True
            else:
                raise Exception("没有成功处理任何文件")
                
        except Exception as e:
            error_msg = f"批量处理失败: {str(e)}"
            self.log(error_msg, "ERROR")
            return False
            
    def create_overlay_image(self, brightfield_image, cell_mask, output_path):
        """
        创建叠加图像用于质量控制
        
        Args:
            brightfield_image: 明场图像
            cell_mask: 细胞掩膜
            output_path: 输出路径
        """
        try:
            # 提取R通道
            bf_r = self.extract_bayer_r_channel(brightfield_image)
            
            # 归一化到0-255
            bf_normalized = ((bf_r - np.min(bf_r)) / (np.max(bf_r) - np.min(bf_r)) * 255).astype(np.uint8)
            
            # 创建RGB图像
            rgb_image = np.stack([bf_normalized, bf_normalized, bf_normalized], axis=2)
            
            # 添加绿色轮廓
            contours, _ = cv2.findContours(cell_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                cv2.drawContours(rgb_image, [contour], -1, (0, 255, 0), 3)
                
            # 添加信息文本
            total_area = np.sum(cell_mask)
            info_text = [
                f'Cell Area: {total_area} pixels',
                f'Processing Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                f'Parameters: sigma={self.gaussian_sigma}, method={self.threshold_method}'
            ]
            
            for i, text in enumerate(info_text):
                y_pos = 30 + i * 30
                cv2.putText(rgb_image, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                           
            # 保存高分辨率PNG - 使用多种方法确保成功
            try:
                # 方法1: 使用cv2.imwrite
                bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
                success = cv2.imwrite(output_path, bgr_image)
                
                if success:
                    self.log(f"叠加图像已保存: {output_path}")
                else:
                    # 方法2: 使用PIL保存
                    self.log("cv2.imwrite失败，尝试使用PIL保存叠加图像", "WARNING")
                    from PIL import Image
                    pil_image = Image.fromarray(rgb_image)
                    pil_image.save(output_path)
                    
                    if os.path.exists(output_path):
                        self.log(f"叠加图像已通过PIL保存: {output_path}")
                    else:
                        raise Exception("PIL保存叠加图像也失败")
                        
            except Exception as save_error:
                self.log(f"保存叠加图像失败: {str(save_error)}", "ERROR")
            
        except Exception as e:
            self.log(f"创建叠加图像失败: {str(e)}", "ERROR")
            
    def create_fluorescence_roi_visualization(self, fluorescence_image, cell_mask, roi, intensity_data, output_path, elapsed_time, offset_correction=None, silent=False, global_vmin=None, global_vmax=None):
        """
        创建荧光图像的ROI可视化，包含细胞轮廓和测量值
        
        Args:
            fluorescence_image: 荧光图像
            cell_mask: 细胞掩膜 (完整尺寸，基于明场图像)
            roi: ROI区域 (x, y, width, height)
            intensity_data: 强度测量数据
            output_path: 输出路径
            elapsed_time: 经过的时间（秒）
            offset_correction: 偏移校正 (x_offset, y_offset)
            silent: 是否静默执行 (不输出日志)
            global_vmin: 全局色图最小值 (用于global colormap style)
            global_vmax: 全局色图最大值 (用于global colormap style)
        """
        try:
            # 确保numpy可用
            import numpy as np
            
            # 提取荧光图像的R通道 (静默模式)
            fluo_r = self.extract_bayer_r_channel(fluorescence_image, silent=True)
            
            # 应用黑场校正
            if hasattr(self, 'dark_correction') and self.dark_correction is not None:
                fluo_r_corrected = np.clip(fluo_r.astype(np.float32) - self.dark_correction, 0, None)
            else:
                fluo_r_corrected = fluo_r.astype(np.float32)
            
            # 应用偏移校正到细胞掩膜
            if offset_correction is not None and cell_mask is not None:
                x_offset, y_offset = offset_correction
                corrected_cell_mask = self._apply_offset_to_mask(cell_mask, x_offset, y_offset, fluo_r_corrected.shape)
            else:
                corrected_cell_mask = cell_mask
            
            # 处理ROI区域
            if roi and len(roi) == 4:
                x, y, w, h = roi
                
                # 确保ROI在图像范围内
                img_h, img_w = fluo_r_corrected.shape
                x = max(0, min(x, img_w - 1))
                y = max(0, min(y, img_h - 1))
                w = min(w, img_w - x)
                h = min(h, img_h - y)
                
                if w <= 0 or h <= 0:
                    if not silent:
                        self.log("ROI区域无效，使用全图", "WARNING")
                    roi_image = fluo_r_corrected.copy()
                    roi_mask = corrected_cell_mask.copy() if corrected_cell_mask is not None else None
                else:
                    # 截取ROI区域
                    roi_image = fluo_r_corrected[y:y+h, x:x+w].copy()
                    roi_mask = corrected_cell_mask[y:y+h, x:x+w].copy() if corrected_cell_mask is not None else None
            else:
                # 如果没有ROI，使用整个图像
                roi_image = fluo_r_corrected.copy()
                roi_mask = corrected_cell_mask.copy() if corrected_cell_mask is not None else None
            
            # 归一化到0-255用于显示
            # 使用全局范围（如果提供）或局部范围
            if global_vmin is not None and global_vmax is not None:
                # 全局缩放模式：使用所有图像的统一范围
                vmin = global_vmin
                vmax = global_vmax
            else:
                # 自动缩放模式：使用当前图像的范围
                vmin = roi_image.min()
                vmax = roi_image.max()
            
            if vmax > vmin:
                roi_normalized = np.clip(((roi_image - vmin) / (vmax - vmin) * 255), 0, 255).astype(np.uint8)
            else:
                roi_normalized = np.zeros_like(roi_image, dtype=np.uint8)
            
            # 创建伪彩色图像（使用jet colormap）
            roi_colored = cv2.applyColorMap(roi_normalized, cv2.COLORMAP_JET)
            
            # 验证图像数据
            if roi_colored is None or roi_colored.size == 0:
                raise Exception("伪彩色图像创建失败或为空")
            
            if len(roi_colored.shape) != 3 or roi_colored.shape[2] != 3:
                raise Exception(f"图像格式错误，期望3通道，实际: {roi_colored.shape}")
            
            # 绘制细胞轮廓
            if roi_mask is not None and roi_mask.size > 0:
                contours, _ = cv2.findContours(roi_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 绘制轮廓（白色，细线条）
                for contour in contours:
                    cv2.drawContours(roi_colored, [contour], -1, (255, 255, 255), 1)
            
            # Text overlay disabled - clean visualization only
            
            # 保存图像 - 简化的保存方法
            self._save_roi_image(roi_colored, output_path)
            
        except Exception as e:
            if not silent:
                self.log(f"创建荧光ROI可视化失败: {str(e)}", "ERROR")
                import traceback
                self.log(f"详细错误信息: {traceback.format_exc()}", "ERROR")
            
    def _create_standalone_colorbar(self, output_path, vmin, vmax):
        """
        创建高分辨率独立色标尺图像（PNG + SVG矢量格式）
        
        Args:
            output_path: 输出路径（PNG格式）
            vmin: 色图最小值
            vmax: 色图最大值
        """
        import numpy as np
        from PIL import Image as PILImage
        
        # 色标尺参数（高分辨率）
        colorbar_width = 200  # 色标尺总宽度
        colorbar_height = 800  # 色标尺主体高度（不含顶部和底部白边）
        top_padding = 60  # 顶部白边
        bottom_padding = 60  # 底部白边
        total_height = colorbar_height + top_padding + bottom_padding  # 总高度
        bar_width = 80  # 实际色条宽度
        padding = 20  # 边距
        
        # 创建色标尺画布（白色背景）
        colorbar_canvas = np.ones((colorbar_height, colorbar_width, 3), dtype=np.uint8) * 255
        
        # 生成高分辨率垂直渐变色条
        gradient = np.linspace(255, 0, colorbar_height).astype(np.uint8)
        gradient_colored = cv2.applyColorMap(gradient[:, np.newaxis], cv2.COLORMAP_JET)
        
        # 将色条绘制到画布上（居中放置）- 需要将1像素宽的渐变扩展到bar_width像素
        bar_x_start = 50  # 左侧留出空间给标题
        # 将单列渐变重复bar_width次以填充整个色条宽度
        gradient_bar = np.tile(gradient_colored[:, 0, :], (bar_width, 1, 1)).transpose(1, 0, 2)
        colorbar_canvas[:, bar_x_start:bar_x_start + bar_width] = gradient_bar
        
        # 添加刻度和数值标签
        num_ticks = 21  # 刻度数量（高分辨率，更多刻度）
        tick_positions = np.linspace(0, colorbar_height - 1, num_ticks).astype(int)
        tick_values = np.linspace(vmax, vmin, num_ticks)  # 从上到下：高到低
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        font_color = (0, 0, 0)  # 黑色
        
        for tick_pos, tick_val in zip(tick_positions, tick_values):
            # 绘制刻度线（从色条延伸）
            tick_x_start = bar_x_start + bar_width
            tick_x_end = tick_x_start + 8
            cv2.line(colorbar_canvas, (tick_x_start, tick_pos), (tick_x_end, tick_pos), font_color, 2)
            
            # 绘制数值标签
            label = f'{tick_val:.0f}'
            text_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
            text_x = tick_x_end + 5
            text_y = tick_pos + text_size[1] // 2
            cv2.putText(colorbar_canvas, label, (text_x, text_y), font, font_scale, font_color, font_thickness, cv2.LINE_AA)
        
        # 添加标题 "Intensity"（竖直方向，在左侧）
        title = "Intensity"
        title_font_scale = 0.7
        title_thickness = 2
        
        # 计算标题位置（居中）
        title_size = cv2.getTextSize(title, font, title_font_scale, title_thickness)[0]
        title_x = 10
        title_y = colorbar_height // 2 + title_size[0] // 2
        
        # 创建旋转的标题文本（使用临时画布）
        title_canvas = np.ones((title_size[0] + 20, title_size[1] + 20, 3), dtype=np.uint8) * 255
        cv2.putText(title_canvas, title, (10, title_size[1] + 5), font, title_font_scale, font_color, title_thickness, cv2.LINE_AA)
        
        # 旋转90度（逆时针）
        title_rotated = cv2.rotate(title_canvas, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # 将旋转后的标题粘贴到色标尺画布上
        title_h, title_w = title_rotated.shape[:2]
        y_start = max(0, title_y - title_h // 2)
        y_end = min(colorbar_height, y_start + title_h)
        x_end = min(colorbar_width, title_x + title_w)
        actual_h = y_end - y_start
        actual_w = x_end - title_x
        
        if actual_h > 0 and actual_w > 0:
            colorbar_canvas[y_start:y_end, title_x:x_end] = title_rotated[:actual_h, :actual_w, :]
        
        # 添加顶部和底部白边，创建最终画布
        final_canvas = np.ones((total_height, colorbar_width, 3), dtype=np.uint8) * 255
        final_canvas[top_padding:top_padding + colorbar_height, :] = colorbar_canvas
        
        # 保存PNG图像
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            self.log(f"  [colorbar] 创建输出目录: {output_dir}")
        
        self.log(f"  [colorbar] 转换图像格式...")
        image_rgb = cv2.cvtColor(final_canvas, cv2.COLOR_BGR2RGB)
        pil_image = PILImage.fromarray(image_rgb)
        
        self.log(f"  [colorbar] 保存PNG文件: {output_path}")
        pil_image.save(output_path, "PNG", dpi=(300, 300))
        
        # 立即验证PNG
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            self.log(f"  [colorbar] ✓ PNG文件已保存 ({size} bytes)")
        else:
            self.log(f"  [colorbar] ✗ PNG文件保存失败", "ERROR")
        
        # 生成SVG矢量图
        svg_path = output_path.replace('.png', '.svg')
        self._create_colorbar_svg(svg_path, vmin, vmax, colorbar_width, colorbar_height, top_padding, bottom_padding, bar_width)
        
        if os.path.exists(svg_path):
            svg_size = os.path.getsize(svg_path)
            self.log(f"  [colorbar] ✓ SVG矢量图已保存 ({svg_size} bytes)")
        else:
            self.log(f"  [colorbar] ✗ SVG文件保存失败", "ERROR")
    
    def _create_colorbar_svg(self, svg_path, vmin, vmax, width, height, top_pad, bottom_pad, bar_width):
        """
        创建SVG矢量格式色标尺
        
        Args:
            svg_path: SVG输出路径
            vmin: 最小值
            vmax: 最大值
            width: 画布宽度
            height: 色条高度（不含padding）
            top_pad: 顶部白边
            bottom_pad: 底部白边
            bar_width: 色条宽度
        """
        total_height = height + top_pad + bottom_pad
        bar_x = 50  # 色条左侧位置
        bar_y = top_pad  # 色条顶部位置（考虑padding）
        
        # JET colormap的关键颜色点（从上到下：红→黄→绿→青→蓝）
        jet_colors = [
            (0.0, '#8B0000'),    # 深红
            (0.125, '#FF0000'),  # 红
            (0.25, '#FF7F00'),   # 橙
            (0.375, '#FFFF00'),  # 黄
            (0.5, '#00FF00'),    # 绿
            (0.625, '#00FFFF'),  # 青
            (0.75, '#0000FF'),   # 蓝
            (0.875, '#00007F'),  # 深蓝
            (1.0, '#000080')     # 更深蓝
        ]
        
        # 生成SVG内容
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="jet-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
'''
        
        # 添加颜色渐变点
        for offset, color in jet_colors:
            svg_content += f'            <stop offset="{offset*100:.1f}%" style="stop-color:{color};stop-opacity:1" />\n'
        
        svg_content += '''        </linearGradient>
    </defs>
    
    <!-- 白色背景 -->
    <rect width="{}" height="{}" fill="white"/>
    
    <!-- 色条 -->
    <rect x="{}" y="{}" width="{}" height="{}" fill="url(#jet-gradient)" stroke="black" stroke-width="1"/>
    
'''.format(width, total_height, bar_x, bar_y, bar_width, height)
        
        # 添加刻度和标签
        num_ticks = 21
        for i in range(num_ticks):
            tick_y = bar_y + (i / (num_ticks - 1)) * height
            tick_value = vmax - (i / (num_ticks - 1)) * (vmax - vmin)
            tick_x_end = bar_x + bar_width + 8
            
            # 刻度线
            svg_content += f'    <line x1="{bar_x + bar_width}" y1="{tick_y}" x2="{tick_x_end}" y2="{tick_y}" stroke="black" stroke-width="2"/>\n'
            
            # 数值标签
            svg_content += f'    <text x="{tick_x_end + 5}" y="{tick_y + 4}" font-family="Arial" font-size="12" fill="black">{tick_value:.0f}</text>\n'
        
        # 添加"Intensity"标签（旋转90度）
        label_x = 15
        label_y = top_pad + height / 2
        svg_content += f'''    <text x="{label_x}" y="{label_y}" font-family="Arial" font-size="14" fill="black" 
          transform="rotate(-90 {label_x} {label_y})" text-anchor="middle" font-weight="bold">Intensity</text>
'''
        
        svg_content += '</svg>'
        
        # 保存SVG文件
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
    
    def _save_roi_image(self, image, output_path):
        """
        保存ROI图像的简化方法
        
        Args:
            image: 要保存的图像 (BGR格式)
            output_path: 输出路径
        """
        try:
            # 获取绝对路径
            abs_path = os.path.abspath(output_path)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(abs_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 方法1: 使用PIL保存（最可靠）
            from PIL import Image as PILImage
            
            # 转换BGR到RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = PILImage.fromarray(image_rgb)
            
            # 保存为PNG
            pil_image.save(abs_path, "PNG")
            
            # 立即验证保存结果
            import time
            time.sleep(0.01)  # 短暂等待确保文件系统同步
            
            if os.path.exists(abs_path):
                file_size = os.path.getsize(abs_path)
                # 仅在保存前3个文件时详细输出，避免日志刷屏
                if abs_path.endswith(("_0.png", "_1.png", "_2.png")) or "colorbar" in abs_path:
                    self.log(f"✓ ROI图像已保存: {os.path.basename(abs_path)} ({file_size} bytes)")
                    self.log(f"  完整路径: {abs_path}")
            else:
                self.log(f"✗ ROI图像保存失败: 文件未创建", "ERROR")
                self.log(f"  预期路径: {abs_path}", "ERROR")
                
        except Exception as e:
            self.log(f"ROI图像保存失败: {str(e)}", "ERROR")
            
            # 备用方法：保存到用户桌面
            try:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                backup_filename = f"roi_backup_{datetime.now().strftime('%H%M%S')}.png"
                backup_path = os.path.join(desktop, backup_filename)
                
                from PIL import Image as PILImage
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = PILImage.fromarray(image_rgb)
                pil_image.save(backup_path, "PNG")
                
                self.log(f"ROI图像已保存到桌面: {backup_path}", "WARNING")
                
            except Exception as backup_error:
                self.log(f"备用保存也失败: {str(backup_error)}", "ERROR")
            
    def save_processing_log(self, log_path, processed_count, total_count):
        """
        保存处理日志
        
        Args:
            log_path: 日志文件路径
            processed_count: 成功处理的文件数
            total_count: 总文件数
        """
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("批量荧光强度测量处理日志\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"软件版本: 1.0\n\n")
                
                f.write("处理参数:\n")
                f.write(f"  高斯模糊 σ: {self.gaussian_sigma}\n")
                f.write(f"  阈值方法: {self.threshold_method}\n")
                f.write(f"  最小面积: {self.min_area}\n")
                f.write(f"  关闭半径: {self.closing_radius}\n")
                f.write(f"  打开半径: {self.opening_radius}\n")
                f.write(f"  最大连通域: {self.max_components}\n\n")
                
                f.write("处理结果:\n")
                f.write(f"  总文件数: {total_count}\n")
                f.write(f"  成功处理: {processed_count}\n")
                f.write(f"  失败文件: {total_count - processed_count}\n")
                f.write(f"  成功率: {processed_count/total_count*100:.1f}%\n\n")
                
                if self.cell_mask is not None:
                    cell_area = np.sum(self.cell_mask)
                    f.write(f"细胞检测结果:\n")
                    f.write(f"  细胞总面积: {cell_area} 像素\n")
                    
            self.log(f"处理日志已保存: {log_path}")
            
        except Exception as e:
            self.log(f"保存处理日志失败: {str(e)}", "ERROR")
