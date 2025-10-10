"""
工具函数模块
提供文件验证、路径处理和其他辅助功能
"""

import os
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_image_file(path):
    """
    验证图像文件是否有效（支持TIFF和PNG）
    
    Args:
        path: 文件路径
        
    Returns:
        bool: 是否为有效的图像文件
    """
    if not os.path.exists(path):
        logger.error(f"文件不存在: {path}")
        return False
    
    # 检查文件扩展名
    ext = Path(path).suffix.lower()
    if ext not in ['.tif', '.tiff', '.png']:
        logger.error(f"不支持的图像格式: {path}（仅支持TIFF和PNG）")
        return False
    
    return True


def validate_tiff_file(path):
    """向后兼容的函数名，调用validate_image_file"""
    return validate_image_file(path)


def generate_output_filename(input_path, scale_factor, output_resolution, format='png'):
    """
    生成输出文件名
    格式: 原文件名_放大倍数x_分辨率.png
    
    Args:
        input_path: 输入文件路径
        scale_factor: 放大倍数
        output_resolution: 输出分辨率 (width, height)
        format: 输出格式
        
    Returns:
        str: 输出文件名
    """
    input_file = Path(input_path)
    stem = input_file.stem
    
    width, height = output_resolution
    output_name = f"{stem}_{scale_factor}x_{width}x{height}.{format.lower()}"
    
    return output_name


def format_file_size(size_bytes):
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def check_file_exists(path):
    """
    检查文件是否存在
    
    Args:
        path: 文件路径
        
    Returns:
        bool: 文件是否存在
    """
    return os.path.exists(path)


def get_safe_save_path(path):
    """
    获取安全的保存路径（如果文件已存在，生成新的文件名）
    
    Args:
        path: 原始路径
        
    Returns:
        str: 安全的保存路径
    """
    if not os.path.exists(path):
        return path
    
    file_path = Path(path)
    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent
    
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not os.path.exists(new_path):
            return str(new_path)
        counter += 1


def validate_scale_factor(scale_factor, min_scale=1, max_scale=50):
    """
    验证放大倍数是否在有效范围内
    
    Args:
        scale_factor: 放大倍数
        min_scale: 最小倍数
        max_scale: 最大倍数
        
    Returns:
        bool: 是否有效
    """
    try:
        scale = int(scale_factor)
        return min_scale <= scale <= max_scale
    except (ValueError, TypeError):
        return False


def estimate_processing_time(width, height, scale_factor):
    """
    估算处理时间（粗略估计）
    
    Args:
        width: 图像宽度
        height: 图像高度
        scale_factor: 放大倍数
        
    Returns:
        float: 估算的处理时间（秒）
    """
    # 基于经验的粗略估算：每百万像素约需0.1秒
    total_pixels = width * height * scale_factor * scale_factor
    time_estimate = (total_pixels / 1_000_000) * 0.1
    return max(0.1, time_estimate)


def format_resolution(width, height):
    """
    格式化分辨率显示
    
    Args:
        width: 宽度
        height: 高度
        
    Returns:
        str: 格式化的分辨率字符串
    """
    megapixels = (width * height) / 1_000_000
    return f"{width} × {height} ({megapixels:.1f} MP)"


def create_directory_if_not_exists(directory):
    """
    如果目录不存在则创建
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"创建目录: {directory}")
