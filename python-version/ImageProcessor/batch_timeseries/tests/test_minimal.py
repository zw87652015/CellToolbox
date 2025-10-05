#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小测试 - 验证基本功能
Minimal Test - Verify basic functionality
"""

import sys
import os

def test_basic_imports():
    """测试基本导入"""
    print("测试基本导入...")
    
    try:
        import tkinter as tk
        print("✅ tkinter 导入成功")
    except ImportError as e:
        print(f"❌ tkinter 导入失败: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy 导入成功")
    except ImportError as e:
        print(f"❌ numpy 导入失败: {e}")
        return False
    
    try:
        import cv2
        print("✅ opencv 导入成功")
    except ImportError as e:
        print(f"❌ opencv 导入失败: {e}")
        return False
    
    try:
        from skimage import filters, morphology, measure
        print("✅ scikit-image 导入成功")
    except ImportError as e:
        print(f"❌ scikit-image 导入失败: {e}")
        return False
    
    try:
        import tifffile
        print("✅ tifffile 导入成功")
    except ImportError as e:
        print(f"❌ tifffile 导入失败: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas 导入成功")
    except ImportError as e:
        print(f"❌ pandas 导入失败: {e}")
        return False
    
    return True

def test_custom_modules():
    """测试自定义模块导入"""
    print("\n测试自定义模块...")
    
    try:
        from core.file_manager import FileManager
        print("✅ FileManager 导入成功")
    except ImportError as e:
        print(f"❌ FileManager 导入失败: {e}")
        return False
    
    try:
        from config_manager import ConfigManager
        print("✅ ConfigManager 导入成功")
    except ImportError as e:
        print(f"❌ ConfigManager 导入失败: {e}")
        return False
    
    try:
        from core.image_processor import ImageProcessor
        print("✅ ImageProcessor 导入成功")
    except ImportError as e:
        print(f"❌ ImageProcessor 导入失败: {e}")
        return False
    
    return True

def test_gui_creation():
    """测试GUI创建"""
    print("\n测试GUI创建...")
    
    try:
        import tkinter as tk
        from tkinter import ttk
        
        # 创建根窗口
        root = tk.Tk()
        root.title("测试窗口")
        root.geometry("400x300")
        
        # 添加一些基本组件
        label = ttk.Label(root, text="批量荧光强度测量工具")
        label.pack(pady=20)
        
        button = ttk.Button(root, text="测试按钮")
        button.pack(pady=10)
        
        # 立即销毁窗口（不显示）
        root.destroy()
        
        print("✅ GUI创建测试成功")
        return True
        
    except Exception as e:
        print(f"❌ GUI创建测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("批量荧光强度测量工具 - 最小测试")
    print("=" * 50)
    
    # 测试基本导入
    if not test_basic_imports():
        print("\n❌ 基本导入测试失败")
        return False
    
    # 测试自定义模块
    if not test_custom_modules():
        print("\n❌ 自定义模块测试失败")
        return False
    
    # 测试GUI创建
    if not test_gui_creation():
        print("\n❌ GUI创建测试失败")
        return False
    
    print("\n🎉 所有测试通过！")
    print("现在可以尝试运行主应用程序:")
    print("python batch_fluo_measurement.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
