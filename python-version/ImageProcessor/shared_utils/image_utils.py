#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common Image Processing Utilities

Shared image processing functions used across multiple fluorescence
measurement projects.
"""

import numpy as np
import cv2
import tifffile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_tiff_image(filepath, use_memory_mapping=False):
    """
    加载TIFF图像
    
    Args:
        filepath: TIFF文件路径
        use_memory_mapping: 是否使用内存映射（大文件）
        
    Returns:
        numpy数组图像数据
    """
    try:
        if use_memory_mapping:
            return tifffile.memmap(filepath, mode='r')
        else:
            return tifffile.imread(filepath)
    except Exception as e:
        logger.error(f"加载TIFF图像失败: {str(e)}")
        raise


def normalize_to_uint8(image):
    """
    将图像归一化到uint8 (0-255)范围
    
    Args:
        image: 输入图像
        
    Returns:
        uint8格式图像
    """
    if image.dtype == np.uint8:
        return image
        
    img_min = np.min(image)
    img_max = np.max(image)
    
    if img_max == img_min:
        return np.zeros_like(image, dtype=np.uint8)
        
    normalized = ((image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    return normalized


def split_bayer_rggb(image):
    """
    拆分RGGB Bayer模式图像
    
    Args:
        image: 输入Bayer图像
        
    Returns:
        (R, G1, G2, B) 四个通道
    """
    if len(image.shape) != 2:
        raise ValueError("输入必须是单通道Bayer图像")
        
    height, width = image.shape
    
    if height % 2 != 0 or width % 2 != 0:
        raise ValueError("Bayer图像尺寸必须为偶数")
    
    # RGGB模式拆分
    R = image[0::2, 0::2].astype(np.float32)   # 红色通道
    G1 = image[0::2, 1::2].astype(np.float32)  # 绿色通道1
    G2 = image[1::2, 0::2].astype(np.float32)  # 绿色通道2
    B = image[1::2, 1::2].astype(np.float32)   # 蓝色通道
    
    return R, G1, G2, B


def apply_dark_field_correction(image, dark_field=None, corner_size=50):
    """
    应用黑场校正
    
    Args:
        image: 输入图像
        dark_field: 黑场图像（可选）
        corner_size: 如果没有黑场图像，使用四角区域计算黑场
        
    Returns:
        校正后的图像
    """
    if dark_field is not None:
        # 使用提供的黑场图像
        corrected = image.astype(np.float32) - dark_field.astype(np.float32)
    else:
        # 使用四角区域估计黑场
        h, w = image.shape[:2]
        corners = [
            image[0:corner_size, 0:corner_size],
            image[0:corner_size, w-corner_size:w],
            image[h-corner_size:h, 0:corner_size],
            image[h-corner_size:h, w-corner_size:w]
        ]
        dark_level = np.median(np.concatenate([c.flatten() for c in corners]))
        corrected = image.astype(np.float32) - dark_level
    
    # 裁剪负值
    corrected = np.clip(corrected, 0, None)
    
    return corrected


def create_overlay_image(original, mask, contours=None, color=(0, 255, 0)):
    """
    创建叠加图像用于质量控制
    
    Args:
        original: 原始图像
        mask: 二值掩膜
        contours: 轮廓列表（可选）
        color: 轮廓颜色 (B, G, R)
        
    Returns:
        RGB叠加图像
    """
    # 转换为uint8
    display = normalize_to_uint8(original)
    
    # 转换为RGB
    if len(display.shape) == 2:
        display = cv2.cvtColor(display, cv2.COLOR_GRAY2BGR)
    
    # 绘制掩膜
    if mask is not None:
        display[mask > 0] = (display[mask > 0] * 0.7 + np.array(color) * 0.3).astype(np.uint8)
    
    # 绘制轮廓
    if contours is not None:
        cv2.drawContours(display, contours, -1, color, 2)
    
    return display


def get_image_info(image):
    """
    获取图像信息
    
    Args:
        image: 输入图像
        
    Returns:
        字典包含图像信息
    """
    return {
        'shape': image.shape,
        'dtype': str(image.dtype),
        'min': np.min(image),
        'max': np.max(image),
        'mean': np.mean(image),
        'std': np.std(image)
    }


def validate_image_dimensions(image, must_be_even=False):
    """
    验证图像尺寸
    
    Args:
        image: 输入图像
        must_be_even: 是否要求偶数尺寸
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    if len(image.shape) < 2:
        raise ValueError("图像必须至少有两个维度")
    
    height, width = image.shape[:2]
    
    if must_be_even:
        if height % 2 != 0 or width % 2 != 0:
            raise ValueError(f"图像尺寸必须为偶数，当前: {width}×{height}")
    
    if height < 10 or width < 10:
        raise ValueError(f"图像尺寸太小: {width}×{height}")
    
    return True
