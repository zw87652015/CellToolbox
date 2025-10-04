#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查导入依赖 - 验证所有必需的包是否正确安装
Check Imports - Verify all required packages are properly installed
"""

import sys

def check_import(module_name, import_statement=None):
    """检查单个模块导入"""
    try:
        if import_statement:
            exec(import_statement)
        else:
            __import__(module_name)
        print(f"✅ {module_name} - 导入成功")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - 导入失败: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} - 其他错误: {e}")
        return False

def main():
    """主检查函数"""
    print("=" * 60)
    print("批量荧光强度测量工具 - 依赖检查")
    print("=" * 60)
    
    # 基础Python模块
    print("\n📦 基础Python模块:")
    basic_modules = [
        'tkinter',
        'os',
        'sys', 
        'threading',
        'logging',
        'datetime',
        'json',
        'tempfile',
        'argparse'
    ]
    
    basic_success = 0
    for module in basic_modules:
        if check_import(module):
            basic_success += 1
    
    # 科学计算包
    print("\n🔬 科学计算包:")
    scientific_modules = [
        ('numpy', 'import numpy as np'),
        ('scipy', 'import scipy'),
        ('pandas', 'import pandas as pd')
    ]
    
    scientific_success = 0
    for module, import_stmt in scientific_modules:
        if check_import(module, import_stmt):
            scientific_success += 1
    
    # 图像处理包
    print("\n🖼️  图像处理包:")
    image_modules = [
        ('opencv-python', 'import cv2'),
        ('scikit-image', 'from skimage import filters, morphology, measure, segmentation'),
        ('tifffile', 'import tifffile'),
        ('Pillow', 'from PIL import Image, ExifTags')
    ]
    
    image_success = 0
    for module, import_stmt in image_modules:
        if check_import(module, import_stmt):
            image_success += 1
    
    # 可视化包
    print("\n📊 可视化包:")
    viz_modules = [
        ('matplotlib', 'import matplotlib.pyplot as plt'),
        ('matplotlib', 'import matplotlib.patches as patches')
    ]
    
    viz_success = 0
    for module, import_stmt in viz_modules:
        if check_import(module, import_stmt):
            viz_success += 1
    
    # 测试自定义模块
    print("\n🔧 自定义模块:")
    custom_modules = [
        'file_manager',
        'config_manager', 
        'image_processor'
    ]
    
    custom_success = 0
    for module in custom_modules:
        if check_import(module):
            custom_success += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 检查总结:")
    print(f"基础模块: {basic_success}/{len(basic_modules)}")
    print(f"科学计算: {scientific_success}/{len(scientific_modules)}")
    print(f"图像处理: {image_success}/{len(image_modules)}")
    print(f"可视化: {viz_success}/{len(viz_modules)}")
    print(f"自定义模块: {custom_success}/{len(custom_modules)}")
    
    total_success = basic_success + scientific_success + image_success + viz_success + custom_success
    total_modules = len(basic_modules) + len(scientific_modules) + len(image_modules) + len(viz_modules) + len(custom_modules)
    
    print(f"\n总体成功率: {total_success}/{total_modules} ({total_success/total_modules*100:.1f}%)")
    
    if total_success == total_modules:
        print("🎉 所有依赖检查通过！应用程序应该可以正常运行。")
        return True
    else:
        print("⚠️  存在依赖问题，请安装缺失的包:")
        print("pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
