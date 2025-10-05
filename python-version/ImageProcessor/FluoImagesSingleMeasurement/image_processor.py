#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
荧光单张图像处理器 - 基于白帽变换和自适应阈值
Fluorescence Single Image Processor - White Top-Hat + Adaptive Threshold
"""

import cv2
import numpy as np
from skimage import morphology, measure
from PIL import Image
import logging
from typing import Tuple, Dict, List, Optional
from pathlib import Path


class FluoImageProcessor:
    """荧光图像处理器类"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化处理器
        
        Args:
            config: 配置字典，包含处理参数
        """
        self.logger = logging.getLogger(__name__)
        
        # 默认参数
        self.config = {
            # Bayer图像处理参数
            'is_bayer': False,  # 是否为Bayer RAW图像
            'bayer_pattern': 'RGGB',  # Bayer模式 (RGGB, BGGR, GRBG, GBRG)
            'use_r_channel': True,  # 使用R通道进行荧光测量
            
            # 白帽变换参数
            'tophat_element_size': 15,  # 结构元素大小（像素），根据细胞大小调整
            'tophat_element_shape': 'disk',  # 结构元素形状: 'disk' 或 'rect'
            
            # 高斯模糊参数
            'gaussian_sigma': 1.0,  # 高斯模糊sigma值
            'enable_gaussian': True,  # 是否启用高斯模糊
            
            # 自适应阈值参数
            'adaptive_method': 'gaussian',  # 'gaussian' 或 'mean'
            'adaptive_block_size': 41,  # 自适应阈值窗口大小（必须为奇数）
            'adaptive_c': 2,  # 从均值中减去的常数
            
            # 形态学后处理参数
            'min_object_size': 50,  # 最小对象面积（像素）
            'closing_size': 3,  # 闭运算结构元素大小
            
            # 测量参数
            'measure_metrics': ['area', 'mean_intensity', 'total_intensity'],  # 测量指标
        }
        
        # 更新配置
        if config:
            self.config.update(config)
            
        # 图像数据
        self.original_image = None
        self.processed_image = None
        self.mask = None
        self.measurements = []
        
    def extract_bayer_r_channel(self, image: np.ndarray) -> np.ndarray:
        """
        从Bayer RAW图像提取R通道
        
        Args:
            image: Bayer RAW图像
            
        Returns:
            R通道图像
        """
        pattern = self.config.get('bayer_pattern', 'RGGB')
        height, width = image.shape
        
        # 验证尺寸为偶数
        if height % 2 != 0 or width % 2 != 0:
            self.logger.warning(f"Bayer图像尺寸不是偶数: {image.shape}，裁剪到偶数尺寸")
            height = height - (height % 2)
            width = width - (width % 2)
            image = image[:height, :width]
        
        self.logger.info(f"提取Bayer模式 {pattern} 的R通道")
        
        # 根据Bayer模式提取R通道
        if pattern == 'RGGB':
            # R在偶数行偶数列
            r_channel = image[0::2, 0::2]
        elif pattern == 'BGGR':
            # R在奇数行奇数列
            r_channel = image[1::2, 1::2]
        elif pattern == 'GRBG':
            # R在偶数行奇数列
            r_channel = image[0::2, 1::2]
        elif pattern == 'GBRG':
            # R在奇数行偶数列
            r_channel = image[1::2, 0::2]
        else:
            raise ValueError(f"不支持的Bayer模式: {pattern}")
        
        self.logger.info(f"R通道尺寸: {r_channel.shape}")
        return r_channel
    
    def load_image(self, image_path: str) -> np.ndarray:
        """
        加载16位灰度TIFF图像（支持Bayer RAW）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            加载的图像（16位或归一化浮点型）
        """
        try:
            # 使用PIL加载TIFF以支持16位
            pil_image = Image.open(image_path)
            image = np.array(pil_image)
            
            self.logger.info(f"加载图像: {image_path}")
            self.logger.info(f"图像尺寸: {image.shape}, 数据类型: {image.dtype}")
            
            # 处理Bayer RAW图像
            if self.config.get('is_bayer', False) and len(image.shape) == 2:
                self.logger.info("检测到Bayer RAW图像，提取R通道")
                image = self.extract_bayer_r_channel(image)
            elif len(image.shape) == 3:
                # 如果是RGB，转换为灰度
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                self.logger.info("转换彩色图像为灰度图")
            
            # 保存原始图像
            self.original_image = image.copy()
            
            # 转换为浮点型以保持精度
            if image.dtype == np.uint16:
                # 归一化到0-1范围
                self.processed_image = image.astype(np.float32) / 65535.0
            elif image.dtype == np.uint8:
                self.processed_image = image.astype(np.float32) / 255.0
            else:
                self.processed_image = image.astype(np.float32)
                
            return self.original_image
            
        except Exception as e:
            self.logger.error(f"加载图像失败: {str(e)}")
            raise
            
    def apply_roi(self, roi: Optional[Tuple[int, int, int, int]] = None):
        """
        应用ROI掩膜
        
        Args:
            roi: ROI坐标 (x, y, width, height)，None表示处理整张图像
        """
        if roi is None:
            self.logger.info("处理整张图像（无ROI限制）")
            return
            
        x, y, w, h = roi
        self.logger.info(f"应用ROI: ({x}, {y}) 尺寸: {w}×{h}")
        
        # 创建ROI掩膜
        roi_mask = np.zeros_like(self.processed_image, dtype=bool)
        roi_mask[y:y+h, x:x+w] = True
        
        # 应用掩膜（ROI外的区域设为0）
        self.processed_image = self.processed_image * roi_mask
        
    def apply_white_tophat(self) -> np.ndarray:
        """
        应用白帽变换以提取比背景亮的结构
        
        Returns:
            白帽变换后的图像
        """
        try:
            element_size = self.config['tophat_element_size']
            element_shape = self.config['tophat_element_shape']
            
            self.logger.info(f"应用白帽变换 - 元素: {element_shape}, 大小: {element_size}")
            
            # 创建结构元素
            if element_shape == 'disk':
                # 使用圆形结构元素
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                                   (element_size, element_size))
            else:  # 'rect'
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                                   (element_size, element_size))
            
            # 转换为uint16进行形态学操作（保持精度）
            img_uint16 = (self.processed_image * 65535).astype(np.uint16)
            
            # 白帽变换: 原图 - 开运算结果
            tophat = cv2.morphologyEx(img_uint16, cv2.MORPH_TOPHAT, kernel)
            
            # 转回浮点型
            self.processed_image = tophat.astype(np.float32) / 65535.0
            
            self.logger.info(f"白帽变换完成，值范围: [{self.processed_image.min():.4f}, {self.processed_image.max():.4f}]")
            
            return self.processed_image
            
        except Exception as e:
            self.logger.error(f"白帽变换失败: {str(e)}")
            raise
            
    def apply_gaussian_blur(self) -> np.ndarray:
        """
        应用高斯模糊以抑制噪声
        
        Returns:
            模糊后的图像
        """
        if not self.config['enable_gaussian']:
            self.logger.info("跳过高斯模糊")
            return self.processed_image
            
        try:
            sigma = self.config['gaussian_sigma']
            self.logger.info(f"应用高斯模糊 - sigma: {sigma}")
            
            # 计算核大小（通常是6*sigma + 1）
            ksize = int(6 * sigma + 1)
            if ksize % 2 == 0:
                ksize += 1  # 确保是奇数
                
            # 应用高斯模糊
            blurred = cv2.GaussianBlur(self.processed_image, (ksize, ksize), sigma)
            self.processed_image = blurred
            
            return self.processed_image
            
        except Exception as e:
            self.logger.error(f"高斯模糊失败: {str(e)}")
            raise
            
    def apply_adaptive_threshold(self) -> np.ndarray:
        """
        应用自适应阈值分割
        
        Returns:
            二值化掩膜
        """
        try:
            method = self.config['adaptive_method']
            block_size = self.config['adaptive_block_size']
            C = self.config['adaptive_c']
            
            self.logger.info(f"应用自适应阈值 - 方法: {method}, 窗口: {block_size}, C: {C}")
            
            # 确保block_size是奇数
            if block_size % 2 == 0:
                block_size += 1
                self.logger.warning(f"自适应窗口大小调整为奇数: {block_size}")
            
            # 转换为uint8进行阈值处理
            img_uint8 = (self.processed_image * 255).astype(np.uint8)
            
            # 选择自适应方法
            if method == 'gaussian':
                adaptive_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
            else:  # 'mean'
                adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C
            
            # 应用自适应阈值
            binary = cv2.adaptiveThreshold(
                img_uint8,
                255,
                adaptive_method,
                cv2.THRESH_BINARY,
                block_size,
                C
            )
            
            # 转换为布尔掩膜
            self.mask = binary > 0
            
            self.logger.info(f"阈值分割完成，检测到 {np.sum(self.mask)} 个前景像素")
            
            return self.mask
            
        except Exception as e:
            self.logger.error(f"自适应阈值失败: {str(e)}")
            raise
            
    def apply_morphological_postprocessing(self) -> np.ndarray:
        """
        应用形态学后处理清理掩膜
        
        Returns:
            清理后的掩膜
        """
        try:
            min_size = self.config['min_object_size']
            closing_size = self.config['closing_size']
            
            self.logger.info(f"形态学后处理 - 最小面积: {min_size}, 闭运算: {closing_size}")
            
            # 1. 移除小对象
            self.mask = morphology.remove_small_objects(
                self.mask.astype(bool), 
                min_size=min_size
            )
            
            # 2. 闭运算填充小孔
            if closing_size > 0:
                selem = morphology.disk(closing_size)
                self.mask = morphology.binary_closing(self.mask, selem)
            
            self.logger.info(f"后处理完成，保留 {np.sum(self.mask)} 个前景像素")
            
            return self.mask
            
        except Exception as e:
            self.logger.error(f"形态学后处理失败: {str(e)}")
            raise
            
    def measure_fluorescence(self) -> List[Dict]:
        """
        测量荧光区域的强度和属性
        
        Returns:
            测量结果列表，每个元素是一个字典
        """
        try:
            self.logger.info("开始测量荧光区域...")
            
            # 连通域标记
            labeled_mask = measure.label(self.mask, connectivity=2)
            num_regions = labeled_mask.max()
            
            self.logger.info(f"检测到 {num_regions} 个独立荧光区域")
            
            # 提取区域属性
            regions = measure.regionprops(labeled_mask, intensity_image=self.original_image)
            
            self.measurements = []
            for i, region in enumerate(regions, 1):
                measurement = {
                    'label': i,
                    'centroid_x': region.centroid[1],  # 列坐标
                    'centroid_y': region.centroid[0],  # 行坐标
                }
                
                # 根据配置添加测量指标
                if 'area' in self.config['measure_metrics']:
                    measurement['area_pixels'] = region.area
                    
                if 'mean_intensity' in self.config['measure_metrics']:
                    measurement['mean_intensity'] = region.mean_intensity
                    
                if 'total_intensity' in self.config['measure_metrics']:
                    # 总强度 = 平均强度 × 面积
                    measurement['total_intensity'] = region.mean_intensity * region.area
                    
                # 边界框
                measurement['bbox'] = region.bbox  # (min_row, min_col, max_row, max_col)
                
                self.measurements.append(measurement)
            
            self.logger.info(f"测量完成，共 {len(self.measurements)} 个区域")
            
            return self.measurements
            
        except Exception as e:
            self.logger.error(f"测量荧光失败: {str(e)}")
            raise
            
    def process_image(self, image_path: str, roi: Optional[Tuple[int, int, int, int]] = None) -> List[Dict]:
        """
        完整处理流程
        
        Args:
            image_path: 图像文件路径
            roi: ROI坐标 (x, y, width, height)
            
        Returns:
            测量结果列表
        """
        self.logger.info("=" * 60)
        self.logger.info("开始处理荧光图像")
        self.logger.info("=" * 60)
        
        # 1. 加载图像
        self.load_image(image_path)
        
        # 2. 应用ROI
        self.apply_roi(roi)
        
        # 3. 白帽变换
        self.apply_white_tophat()
        
        # 4. 高斯模糊（可选）
        self.apply_gaussian_blur()
        
        # 5. 自适应阈值
        self.apply_adaptive_threshold()
        
        # 6. 形态学后处理
        self.apply_morphological_postprocessing()
        
        # 7. 测量荧光
        measurements = self.measure_fluorescence()
        
        self.logger.info("=" * 60)
        self.logger.info("处理完成")
        self.logger.info("=" * 60)
        
        return measurements
        
    def create_overlay_image(self, output_path: Optional[str] = None) -> np.ndarray:
        """
        创建叠加了检测结果的可视化图像
        
        Args:
            output_path: 输出路径，None表示不保存
            
        Returns:
            可视化图像（RGB）
        """
        try:
            self.logger.info("创建可视化叠加图像...")
            
            # 归一化原始图像到0-255
            display_img = self.original_image.astype(np.float32)
            display_img = ((display_img - display_img.min()) / 
                          (display_img.max() - display_img.min()) * 255).astype(np.uint8)
            
            # 转换为RGB
            overlay = cv2.cvtColor(display_img, cv2.COLOR_GRAY2RGB)
            
            # 绘制检测到的区域轮廓
            contours, _ = cv2.findContours(
                self.mask.astype(np.uint8),
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # 绘制绿色轮廓
            cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)
            
            # 绘制质心和标签
            for measurement in self.measurements:
                cx = int(measurement['centroid_x'])
                cy = int(measurement['centroid_y'])
                label = measurement['label']
                
                # 绘制质心
                cv2.circle(overlay, (cx, cy), 3, (255, 0, 0), -1)
                
                # 绘制标签
                cv2.putText(overlay, str(label), (cx + 5, cy - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # 添加信息文字
            info_text = f"Detected: {len(self.measurements)} regions"
            cv2.putText(overlay, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 保存图像
            if output_path:
                cv2.imwrite(output_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
                self.logger.info(f"可视化图像已保存: {output_path}")
            
            return overlay
            
        except Exception as e:
            self.logger.error(f"创建叠加图像失败: {str(e)}")
            raise
            
    def save_measurements_to_csv(self, output_path: str):
        """
        保存测量结果到CSV文件
        
        Args:
            output_path: CSV输出路径
        """
        try:
            import csv
            
            self.logger.info(f"保存测量结果到CSV: {output_path}")
            
            if not self.measurements:
                self.logger.warning("没有测量数据可保存")
                return
            
            # 获取所有键（列名）
            fieldnames = list(self.measurements[0].keys())
            # 移除bbox（太长）
            if 'bbox' in fieldnames:
                fieldnames.remove('bbox')
            
            # 写入CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for measurement in self.measurements:
                    # 创建副本，移除bbox
                    row = {k: v for k, v in measurement.items() if k != 'bbox'}
                    writer.writerow(row)
            
            self.logger.info(f"成功保存 {len(self.measurements)} 条测量数据")
            
        except Exception as e:
            self.logger.error(f"保存CSV失败: {str(e)}")
            raise


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("荧光图像处理器模块")
    print("请通过GUI或CLI使用此处理器")
