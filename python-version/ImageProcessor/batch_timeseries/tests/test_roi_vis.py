#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ROI可视化功能
"""

import numpy as np
import cv2
import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.image_processor import ImageProcessor

def test_roi_visualization():
    """测试ROI可视化功能"""
    print("开始测试ROI可视化功能...")
    
    # 创建测试图像处理器
    processor = ImageProcessor()
    
    # 创建模拟的荧光图像 (4688x7028, 16-bit)
    print("创建模拟荧光图像...")
    fluorescence_image = np.random.randint(100, 1000, (4688, 7028), dtype=np.uint16)
    
    # 在中心区域添加一个亮斑模拟细胞
    center_y, center_x = 2344, 3514
    y_start, y_end = center_y - 50, center_y + 50
    x_start, x_end = center_x - 50, center_x + 50
    fluorescence_image[y_start:y_end, x_start:x_end] += 2000
    
    # 创建模拟的细胞掩膜
    print("创建模拟细胞掩膜...")
    cell_mask = np.zeros((2344, 3514), dtype=bool)
    # 在ROI区域内创建一个圆形掩膜
    roi_center_y, roi_center_x = 25, 30  # ROI内的相对坐标
    y, x = np.ogrid[:100, :100]
    mask_circle = (x - roi_center_x)**2 + (y - roi_center_y)**2 <= 20**2
    cell_mask[1700:1800, 3400:3500] = mask_circle
    
    # 定义ROI区域
    roi = (3400, 1700, 100, 100)  # (x, y, width, height)
    
    # 创建模拟的强度数据
    intensity_data = {
        'mean': 1250.5,
        'total': 125050,
        'area': 100
    }
    
    # 测试输出路径
    output_path = "test_roi_visualization.png"
    elapsed_time = 15.3
    
    try:
        print("调用ROI可视化方法...")
        processor.create_fluorescence_roi_visualization(
            fluorescence_image, cell_mask, roi, intensity_data, output_path, elapsed_time
        )
        
        if os.path.exists(output_path):
            print(f"✅ 测试成功！ROI可视化图像已保存: {output_path}")
            
            # 检查图像
            test_image = cv2.imread(output_path)
            if test_image is not None:
                print(f"✅ 图像验证成功，尺寸: {test_image.shape}")
            else:
                print("❌ 图像文件损坏")
        else:
            print("❌ 测试失败！未找到输出文件")
            
    except Exception as e:
        print(f"❌ 测试失败！错误: {str(e)}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_roi_visualization()
