#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图像保存功能
"""

import numpy as np
import cv2
import os
from PIL import Image

def test_save():
    """测试保存功能"""
    print("测试图像保存功能...")
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    # 测试保存到桌面
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    test_path = os.path.join(desktop, "test_roi_save.png")
    
    try:
        # 使用PIL保存
        pil_image = Image.fromarray(test_image)
        pil_image.save(test_path, "PNG")
        
        if os.path.exists(test_path):
            file_size = os.path.getsize(test_path)
            print(f"✅ 测试成功！图像已保存: {test_path} ({file_size} bytes)")
        else:
            print("❌ 保存失败：文件未创建")
            
    except Exception as e:
        print(f"❌ 保存失败：{str(e)}")

if __name__ == "__main__":
    test_save()
