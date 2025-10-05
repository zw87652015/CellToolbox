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
        
        # 缓存变量
        self.cell_mask = None
        self.dark_correction = None
        
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
        
    def load_tiff_image(self, file_path, use_memmap=None):
        """
        加载TIFF图像，支持16位和BigTIFF
        
        Args:
            file_path: 图像文件路径
            use_memmap: 是否使用内存映射，None为自动判断
            
        Returns:
            numpy数组形式的图像数据
        """
        try:
            # 检查文件大小决定是否使用内存映射
            if use_memmap is None:
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                use_memmap = file_size_mb > 500  # 大于500MB使用内存映射
                
            if use_memmap:
                self.log(f"使用内存映射加载大文件: {os.path.basename(file_path)}")
                # 使用内存映射加载大文件
                with tifffile.TiffFile(file_path) as tif:
                    image = tif.asarray(out='memmap')
            else:
                # 直接加载到内存
                image = tifffile.imread(file_path)
                
            self.log(f"成功加载图像: {os.path.basename(file_path)}, 形状: {image.shape}, 数据类型: {image.dtype}")
            
            # 验证图像尺寸（必须为偶数，用于Bayer拆分）
            if image.shape[0] % 2 != 0 or image.shape[1] % 2 != 0:
                raise ValueError(f"Bayer 尺寸非法: 图像尺寸必须为偶数 {image.shape}")
                
            return image
            
        except Exception as e:
            error_msg = f"加载TIFF图像失败 {file_path}: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def extract_bayer_r_channel(self, image):
        """
        从Bayer图像中提取R通道 (RGGB模式)
        
        Args:
            image: 输入的Bayer图像
            
        Returns:
            R通道图像 (float32)
        """
        try:
            # RGGB模式: R = 偶行偶列
            r_channel = image[0::2, 0::2].astype(np.float32)
            
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
            
    def apply_dark_correction(self, image, dark_correction):
        """
        应用黑场校正
        
        Args:
            image: 输入图像
            dark_correction: 黑场校正图像
            
        Returns:
            校正后的图像
        """
        if dark_correction is None:
            return image
            
        try:
            # 减去黑场并限制最小值为0
            corrected = image - dark_correction
            corrected = np.maximum(corrected, 0)
            
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
            self.log("开始明场细胞检测")
            
            # 提取R通道
            bf_r = self.extract_bayer_r_channel(brightfield_image)
            
            # 应用黑场校正
            bf_r_corrected = self.apply_dark_correction(bf_r, dark_correction)
            
            # 应用ROI限制
            if roi is not None:
                x, y, w, h = roi
                self.log(f"应用ROI限制: ({x}, {y}) 尺寸: {w}×{h}")
                
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
            self.log(f"应用高斯模糊，σ = {gaussian_sigma}")
            blurred = filters.gaussian(processing_image, sigma=gaussian_sigma, preserve_range=True)
            
            # 自动阈值分割
            self.log(f"应用阈值分割，方法: {threshold_method}")
            if threshold_method == 'otsu':
                threshold = filters.threshold_otsu(blurred)
            elif threshold_method == 'triangle':
                threshold = filters.threshold_triangle(blurred)
            else:
                raise ValueError(f"不支持的阈值方法: {threshold_method}")
                
            binary_mask = blurred < threshold  # 细胞通常比背景暗
            
            # 形态学处理
            self.log("应用形态学处理")
            
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
                self.log(f"应用边缘平滑，半径 = {smoothing_radius}")
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
            
            self.log(f"检测到 {len(regions)} 个连通域")
            
            # 保留最大的几个连通域
            if len(regions) > self.max_components:
                # 按面积排序
                regions_sorted = sorted(regions, key=lambda x: x.area, reverse=True)
                keep_labels = [r.label for r in regions_sorted[:self.max_components]]
                
                # 创建新的掩膜
                final_mask = np.zeros_like(labeled_mask, dtype=bool)
                for label in keep_labels:
                    final_mask |= (labeled_mask == label)
                    
                self.log(f"保留最大的 {self.max_components} 个连通域")
            else:
                final_mask = binary_mask
                
            # 应用ROI限制到最终掩膜
            if roi is not None:
                final_mask = final_mask & roi_mask
                self.log("已将细胞掩膜限制在ROI区域内")
            
            # 计算最终统计信息
            final_regions = measure.regionprops(measure.label(final_mask))
            total_area = sum(r.area for r in final_regions)
            
            self.log(f"细胞检测完成，最终细胞数: {len(final_regions)}, 总面积: {total_area} 像素")
            
            return final_mask
            
        except Exception as e:
            error_msg = f"明场细胞检测失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)
            
    def optimize_offset_for_max_intensity(self, fluorescence_image, cell_mask, dark_correction=None, base_offset=(0, 0), search_range=5):
        """
        优化偏移量以获得最大平均荧光强度
        
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
            # 提取R通道
            fluo_r = self.extract_bayer_r_channel(fluorescence_image)
            
            # 应用黑场校正
            fluo_r_corrected = self.apply_dark_correction(fluo_r, dark_correction)
            
            base_x, base_y = base_offset
            best_mean = -1
            best_offset = base_offset
            best_result = None
            
            # 搜索范围内的所有偏移组合 (11x11 = 121 tries)
            search_count = 0
            total_searches = (2 * search_range + 1) ** 2
            
            self.log(f"开始偏移优化搜索: 基础偏移=({base_x}, {base_y}), 搜索范围=±{search_range}像素")
            
            for dx in range(-search_range, search_range + 1):
                for dy in range(-search_range, search_range + 1):
                    search_count += 1
                    
                    # 计算当前偏移
                    current_x = base_x + dx
                    current_y = base_y + dy
                    
                    # 应用偏移到掩膜
                    corrected_mask = self._apply_offset_to_mask(cell_mask, current_x, current_y, fluo_r_corrected.shape)
                    
                    # 测量强度
                    cell_pixels = fluo_r_corrected[corrected_mask]
                    
                    if len(cell_pixels) > 0:
                        mean_intensity = float(np.mean(cell_pixels))
                        
                        # 显示每个偏移参数下的Mean值
                        self.log(f"偏移({current_x:+3d}, {current_y:+3d}) -> Mean: {mean_intensity:.2f} (搜索 {search_count}/{total_searches})")
                        
                        # 如果找到更高的平均强度，更新最佳结果
                        if mean_intensity > best_mean:
                            best_mean = mean_intensity
                            best_offset = (current_x, current_y)
                            
                            # 计算完整的强度数据
                            area = len(cell_pixels)
                            total_intensity = float(np.sum(cell_pixels))
                            
                            best_result = {
                                'mean': mean_intensity,
                                'total': total_intensity,
                                'area': area,
                                'optimized_offset': best_offset,
                                'offset_improvement': (dx, dy)
                            }
                            
                            self.log(f"*** 发现更佳偏移: ({current_x:+3d}, {current_y:+3d}) -> Mean: {mean_intensity:.2f} ***")
                    else:
                        # 如果掩膜为空，也记录这个情况
                        self.log(f"偏移({current_x:+3d}, {current_y:+3d}) -> Mean: 0.00 (掩膜为空) (搜索 {search_count}/{total_searches})")
            
            if best_result is None:
                self.log("警告: 偏移优化未找到有效掩膜", "WARNING")
                return {
                    'mean': 0.0, 
                    'total': 0.0, 
                    'area': 0,
                    'optimized_offset': base_offset,
                    'offset_improvement': (0, 0)
                }
            
            improvement_x, improvement_y = best_result['offset_improvement']
            final_x, final_y = best_result['optimized_offset']
            
            self.log(f"偏移优化完成总结:")
            self.log(f"  - 搜索位置数: {total_searches}")
            self.log(f"  - 基础偏移: ({base_x:+d}, {base_y:+d})")
            self.log(f"  - 最佳偏移: ({final_x:+d}, {final_y:+d})")
            self.log(f"  - 偏移改进: ({improvement_x:+d}, {improvement_y:+d})")
            self.log(f"  - 最佳平均强度: {best_mean:.2f}")
            self.log(f"  - 细胞面积: {best_result['area']} 像素")
            self.log(f"  - 总强度: {best_result['total']:.2f}")
            
            return best_result
            
        except Exception as e:
            error_msg = f"偏移优化失败: {str(e)}"
            self.log(error_msg, "ERROR")
            raise Exception(error_msg)

    def measure_fluorescence_intensity(self, fluorescence_image, cell_mask, dark_correction=None, offset_correction=None, enable_offset_optimization=False):
        """
        测量荧光强度
        
        Args:
            fluorescence_image: 荧光图像
            cell_mask: 细胞掩膜 (基于明场图像)
            dark_correction: 黑场校正图像
            offset_correction: 偏移校正 (x_offset, y_offset) - 明场相对荧光的偏移
            enable_offset_optimization: 是否启用偏移优化
            
        Returns:
            字典包含 mean, total, area, 以及可能的优化信息
        """
        try:
            # 如果启用偏移优化，使用优化方法
            if enable_offset_optimization:
                base_offset = offset_correction if offset_correction is not None else (0, 0)
                return self.optimize_offset_for_max_intensity(fluorescence_image, cell_mask, dark_correction, base_offset)
            
            # 原有的非优化方法
            # 提取R通道
            fluo_r = self.extract_bayer_r_channel(fluorescence_image)
            
            # 应用黑场校正
            fluo_r_corrected = self.apply_dark_correction(fluo_r, dark_correction)
            
            # 应用偏移校正
            if offset_correction is not None:
                x_offset, y_offset = offset_correction
                self.log(f"应用偏移校正: X={x_offset}, Y={y_offset} 像素")
                
                # 创建偏移后的细胞掩膜
                corrected_mask = self._apply_offset_to_mask(cell_mask, x_offset, y_offset, fluo_r_corrected.shape)
                self.log(f"偏移校正后掩膜面积: {np.sum(corrected_mask)} 像素 (原始: {np.sum(cell_mask)} 像素)")
            else:
                corrected_mask = cell_mask
                self.log("未应用偏移校正")
            
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
        对掩膜应用偏移校正
        
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
            
            # 获取原始掩膜的有效区域
            mask_y, mask_x = np.where(mask)
            
            if len(mask_y) == 0:
                self.log("原始掩膜为空", "WARNING")
                return corrected_mask
            
            # 应用偏移校正
            # 如果明场相对荧光向上偏移16像素，那么要在荧光图像中找到对应位置，需要向下偏移16像素
            new_x = mask_x + x_offset  # X偏移校正
            new_y = mask_y + y_offset  # Y偏移校正 (正值表示明场向上偏移，需要向下校正)
            
            # 边界检查
            valid_indices = (
                (new_x >= 0) & (new_x < target_shape[1]) &
                (new_y >= 0) & (new_y < target_shape[0])
            )
            
            valid_x = new_x[valid_indices]
            valid_y = new_y[valid_indices]
            
            # 设置偏移后的掩膜
            if len(valid_x) > 0:
                corrected_mask[valid_y, valid_x] = True
                
            self.log(f"偏移校正完成: 原始点数={len(mask_y)}, 校正后有效点数={len(valid_x)}, 偏移量=({x_offset},{y_offset})")
            
            return corrected_mask
            
        except Exception as e:
            self.log(f"偏移校正失败: {str(e)}", "ERROR")
            return mask  # 返回原始掩膜作为备用
            
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
            
    def process_batch(self, brightfield_path, fluorescence_folder, darkfield_paths, output_folder, roi=None, offset_correction=None, enable_offset_optimization=False):
        """
        批量处理荧光图像
        
        Args:
            brightfield_path: 明场图像路径
            fluorescence_folder: 荧光图像文件夹
            darkfield_paths: 黑场图像路径列表
            output_folder: 输出文件夹
            roi: ROI区域 (x, y, width, height)
            offset_correction: 偏移校正 (x_offset, y_offset) - 明场相对荧光的偏移
            enable_offset_optimization: 是否启用偏移优化 (±5像素搜索)
            
        Returns:
            处理是否成功
        """
        try:
            self.log("开始批量荧光强度测量")
            
            # 创建输出目录
            from file_manager import FileManager
            file_manager = FileManager()
            results_dir = file_manager.create_output_directory(output_folder)
            
            # 1. 加载明场图像并检测细胞
            self.update_progress(0, 100, "加载明场图像...")
            bf_image = self.load_tiff_image(brightfield_path)
            
            # 2. 计算黑场校正
            self.update_progress(10, 100, "计算黑场校正...")
            dark_correction = None
            if darkfield_paths:
                dark_correction = self.calculate_dark_correction(darkfield_paths)
                self.dark_correction = dark_correction
                
            # 3. 检测细胞
            self.update_progress(20, 100, "检测细胞...")
            cell_mask = self.detect_cells_in_brightfield(bf_image, dark_correction, roi)
            self.cell_mask = cell_mask
            
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
            
            # 5. 处理每个荧光图像
            results = []
            base_timestamp = None
            
            for i, fluo_path in enumerate(fluorescence_files):
                if self.stop_flag:
                    self.log("处理被用户停止")
                    return False
                    
                progress = 30 + (i / len(fluorescence_files)) * 60
                self.update_progress(progress, 100, f"处理荧光图像 {i+1}/{len(fluorescence_files)}")
                
                try:
                    # 加载荧光图像
                    fluo_image = self.load_tiff_image(fluo_path)
                    
                    # 提取时间戳
                    timestamp = self.extract_timestamp_from_exif(fluo_path)
                    
                    if timestamp is None:
                        self.log(f"跳过无时间戳的文件: {os.path.basename(fluo_path)}", "WARNING")
                        continue
                        
                    # 计算相对时间
                    if base_timestamp is None:
                        base_timestamp = timestamp
                        elapsed_s = 0.0
                    else:
                        elapsed_s = (timestamp - base_timestamp).total_seconds()
                        
                    # 测量荧光强度（应用偏移校正和可选的偏移优化）
                    intensity_data = self.measure_fluorescence_intensity(fluo_image, cell_mask, dark_correction, offset_correction, enable_offset_optimization)
                    
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
                    
                    # 创建单张荧光图像的ROI可视化
                    try:
                        roi_vis_dir = os.path.join(results_dir, "roi_visualizations")
                        os.makedirs(roi_vis_dir, exist_ok=True)
                        roi_vis_path = os.path.join(roi_vis_dir, f"roi_vis_{os.path.splitext(os.path.basename(fluo_path))[0]}.png")
                        self.log(f"创建ROI可视化: {roi_vis_path}")
                        
                        # 传递完整的细胞掩膜和偏移校正参数
                        self.create_fluorescence_roi_visualization(fluo_image, self.cell_mask, roi, intensity_data, roi_vis_path, elapsed_s, offset_correction)
                        
                        # 验证文件是否创建成功
                        if os.path.exists(roi_vis_path):
                            file_size = os.path.getsize(roi_vis_path)
                            self.log(f"ROI可视化已保存: {roi_vis_path} (大小: {file_size} bytes)")
                        else:
                            self.log(f"ROI可视化文件未创建: {roi_vis_path}", "ERROR")
                            
                    except Exception as vis_error:
                        self.log(f"创建ROI可视化失败 {os.path.basename(fluo_path)}: {str(vis_error)}", "ERROR")
                        import traceback
                        self.log(f"ROI可视化详细错误: {traceback.format_exc()}", "ERROR")
                    
                except Exception as e:
                    self.log(f"处理文件失败 {os.path.basename(fluo_path)}: {str(e)}", "ERROR")
                    continue
                    
            # 6. 保存结果
            self.update_progress(90, 100, "保存结果...")
            
            if results:
                # 保存CSV
                csv_path = os.path.join(results_dir, "csv", "fluorescence_intensity_results.csv")
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                
                df = pd.DataFrame(results)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                # 创建叠加图像
                try:
                    overlay_path = os.path.join(results_dir, "images", "cell_overlay.png")
                    os.makedirs(os.path.dirname(overlay_path), exist_ok=True)
                    self.log(f"创建明场叠加图像: {overlay_path}")
                    self.create_overlay_image(bf_image, cell_mask, overlay_path)
                except Exception as overlay_error:
                    self.log(f"创建明场叠加图像失败: {str(overlay_error)}", "ERROR")
                
                # 保存处理日志
                log_path = os.path.join(results_dir, "logs", "processing_log.txt")
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                self.save_processing_log(log_path, len(results), len(fluorescence_files))
                
                self.update_progress(100, 100, "处理完成！")
                self.log(f"批量处理完成！成功处理 {len(results)}/{len(fluorescence_files)} 个文件")
                self.log(f"结果已保存到: {results_dir}")
                self.log(f"- CSV数据: csv/fluorescence_intensity_results.csv")
                self.log(f"- 细胞掩膜: masks/cell_mask.png")
                self.log(f"- 明场叠加图: images/cell_overlay.png")
                self.log(f"- ROI可视化: roi_visualizations/ ({len(results)} 张图像)")
                
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
            
    def create_fluorescence_roi_visualization(self, fluorescence_image, cell_mask, roi, intensity_data, output_path, elapsed_time, offset_correction=None):
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
        """
        try:
            # 确保numpy可用
            import numpy as np
            self.log(f"开始创建ROI可视化，荧光图像形状: {fluorescence_image.shape}")
            if cell_mask is not None:
                self.log(f"细胞掩膜形状: {cell_mask.shape}")
            
            # 提取荧光图像的R通道
            fluo_r = self.extract_bayer_r_channel(fluorescence_image)
            self.log(f"R通道提取完成，形状: {fluo_r.shape}")
            
            # 应用黑场校正
            if hasattr(self, 'dark_correction') and self.dark_correction is not None:
                fluo_r_corrected = np.clip(fluo_r.astype(np.float32) - self.dark_correction, 0, None)
                self.log("已应用黑场校正")
            else:
                fluo_r_corrected = fluo_r.astype(np.float32)
                self.log("未应用黑场校正")
            
            # 应用偏移校正到细胞掩膜
            if offset_correction is not None and cell_mask is not None:
                x_offset, y_offset = offset_correction
                self.log(f"可视化中应用偏移校正: X={x_offset}, Y={y_offset}")
                corrected_cell_mask = self._apply_offset_to_mask(cell_mask, x_offset, y_offset, fluo_r_corrected.shape)
            else:
                corrected_cell_mask = cell_mask
                self.log("可视化中未应用偏移校正")
            
            # 处理ROI区域
            if roi and len(roi) == 4:
                x, y, w, h = roi
                self.log(f"ROI参数: ({x}, {y}) 尺寸: {w}×{h}")
                
                # 确保ROI在图像范围内
                img_h, img_w = fluo_r_corrected.shape
                x = max(0, min(x, img_w - 1))
                y = max(0, min(y, img_h - 1))
                w = min(w, img_w - x)
                h = min(h, img_h - y)
                
                if w <= 0 or h <= 0:
                    self.log("ROI区域无效，使用全图", "WARNING")
                    roi_image = fluo_r_corrected.copy()
                    roi_mask = corrected_cell_mask.copy() if corrected_cell_mask is not None else None
                else:
                    self.log(f"调整后ROI: ({x}, {y}) 尺寸: {w}×{h}")
                    
                    # 截取ROI区域
                    roi_image = fluo_r_corrected[y:y+h, x:x+w].copy()
                    roi_mask = corrected_cell_mask[y:y+h, x:x+w].copy() if corrected_cell_mask is not None else None
                    self.log(f"ROI图像形状: {roi_image.shape}")
            else:
                # 如果没有ROI，使用整个图像
                roi_image = fluo_r_corrected.copy()
                roi_mask = corrected_cell_mask.copy() if corrected_cell_mask is not None else None
                self.log("使用全图模式")
            
            # 归一化到0-255用于显示
            if roi_image.max() > roi_image.min():
                roi_normalized = ((roi_image - roi_image.min()) / (roi_image.max() - roi_image.min()) * 255).astype(np.uint8)
                self.log(f"图像归一化完成，范围: {roi_image.min():.1f} - {roi_image.max():.1f}")
            else:
                roi_normalized = np.zeros_like(roi_image, dtype=np.uint8)
                self.log("图像强度均匀，使用零图像")
            
            # 创建伪彩色图像（使用jet colormap）
            roi_colored = cv2.applyColorMap(roi_normalized, cv2.COLORMAP_JET)
            self.log(f"伪彩色图像创建完成，形状: {roi_colored.shape}")
            
            # 验证图像数据
            if roi_colored is None or roi_colored.size == 0:
                raise Exception("伪彩色图像创建失败或为空")
            
            if len(roi_colored.shape) != 3 or roi_colored.shape[2] != 3:
                raise Exception(f"图像格式错误，期望3通道，实际: {roi_colored.shape}")
                
            self.log(f"图像数据验证通过，数据类型: {roi_colored.dtype}, 值范围: {roi_colored.min()}-{roi_colored.max()}")
            
            # 绘制细胞轮廓
            if roi_mask is not None and roi_mask.size > 0:
                contours, _ = cv2.findContours(roi_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                self.log(f"找到 {len(contours)} 个轮廓")
                
                # 绘制轮廓（白色，较粗的线条）
                for i, contour in enumerate(contours):
                    cv2.drawContours(roi_colored, [contour], -1, (255, 255, 255), 2)
                    self.log(f"绘制轮廓 {i+1}, 点数: {len(contour)}")
            else:
                self.log("没有细胞掩膜或掩膜为空")
            
            # 添加测量信息文本
            try:
                info_texts = [
                    f"Time: {elapsed_time:.1f}s",
                    f"Mean: {intensity_data.get('mean', 0):.1f}",
                    f"Total: {intensity_data.get('total', 0):.0f}",
                    f"Area: {intensity_data.get('area', 0)} px"
                ]
                
                # 添加偏移校正信息
                if offset_correction is not None:
                    x_offset, y_offset = offset_correction
                    info_texts.append(f"Offset: ({x_offset},{y_offset})")
                else:
                    info_texts.append("Offset: None")
                
                # 计算文本位置和背景
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1
                text_color = (255, 255, 255)  # 白色文字
                
                # 添加文本（简化版本）
                for i, text in enumerate(info_texts):
                    y_pos = 20 + i * 20
                    cv2.putText(roi_colored, text, (10, y_pos), font, font_scale, text_color, thickness)
                
                self.log("文本信息已添加")
                
            except Exception as text_error:
                self.log(f"添加文本信息失败: {str(text_error)}", "WARNING")
            
            # 保存图像 - 简化的保存方法
            self._save_roi_image(roi_colored, output_path)
            
        except Exception as e:
            self.log(f"创建荧光ROI可视化失败: {str(e)}", "ERROR")
            import traceback
            self.log(f"详细错误信息: {traceback.format_exc()}", "ERROR")
            
    def _save_roi_image(self, image, output_path):
        """
        保存ROI图像的简化方法
        
        Args:
            image: 要保存的图像 (BGR格式)
            output_path: 输出路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 方法1: 使用PIL保存（最可靠）
            from PIL import Image as PILImage
            
            # 转换BGR到RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = PILImage.fromarray(image_rgb)
            
            # 保存为PNG
            pil_image.save(output_path, "PNG")
            
            # 验证保存结果
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.log(f"ROI图像保存成功: {output_path} ({file_size} bytes)")
            else:
                self.log(f"ROI图像保存失败: 文件未创建", "ERROR")
                
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
