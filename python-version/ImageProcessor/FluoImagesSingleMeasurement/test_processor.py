#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 荧光图像处理器
Test Script - Fluorescence Image Processor
"""

import numpy as np
import cv2
from PIL import Image
import tempfile
import logging
from pathlib import Path

from image_processor import FluoImageProcessor


def create_synthetic_test_image(width=512, height=512, num_cells=5):
    """
    创建合成测试图像
    
    Args:
        width: 图像宽度
        height: 图像高度
        num_cells: 细胞数量
        
    Returns:
        16位灰度图像
    """
    # 创建背景（带渐变）
    image = np.zeros((height, width), dtype=np.uint16)
    
    # 添加背景渐变
    for i in range(height):
        for j in range(width):
            # 从左上到右下的渐变
            gradient_value = 500 + int(1000 * (i + j) / (height + width))
            image[i, j] = gradient_value
    
    # 添加高斯噪声
    noise = np.random.normal(0, 100, (height, width))
    image = np.clip(image + noise, 0, 65535).astype(np.uint16)
    
    # 添加荧光"细胞"
    np.random.seed(42)
    for _ in range(num_cells):
        # 随机位置
        cx = np.random.randint(100, width - 100)
        cy = np.random.randint(100, height - 100)
        
        # 随机大小
        radius = np.random.randint(20, 50)
        
        # 随机强度
        intensity = np.random.randint(3000, 8000)
        
        # 绘制高斯斑点
        y, x = np.ogrid[-cy:height-cy, -cx:width-cx]
        mask = x*x + y*y <= radius*radius
        
        # 添加高斯衰减
        for i in range(height):
            for j in range(width):
                dist = np.sqrt((i - cy)**2 + (j - cx)**2)
                if dist < radius:
                    gaussian = np.exp(-(dist**2) / (2 * (radius/2)**2))
                    image[i, j] = min(65535, int(image[i, j] + intensity * gaussian))
    
    return image


def test_basic_processing():
    """测试基本处理流程"""
    print("=" * 60)
    print("测试1: 基本处理流程")
    print("=" * 60)
    
    # 创建测试图像
    print("创建合成测试图像...")
    test_image = create_synthetic_test_image(num_cells=5)
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
        Image.fromarray(test_image).save(tmp_path)
    
    try:
        # 创建处理器
        processor = FluoImageProcessor()
        
        # 处理图像
        measurements = processor.process_image(tmp_path)
        
        # 验证结果
        print(f"\n检测到 {len(measurements)} 个荧光区域")
        assert len(measurements) > 0, "应该检测到至少一个区域"
        
        # 显示测量结果
        for i, m in enumerate(measurements[:3], 1):  # 只显示前3个
            print(f"区域 {i}:")
            print(f"  位置: ({m['centroid_x']:.1f}, {m['centroid_y']:.1f})")
            print(f"  面积: {m['area_pixels']} 像素")
            print(f"  平均强度: {m['mean_intensity']:.2f}")
            print(f"  总强度: {m['total_intensity']:.2f}")
        
        print("\n✓ 基本处理流程测试通过")
        return True
        
    finally:
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)


def test_roi_processing():
    """测试ROI处理"""
    print("\n" + "=" * 60)
    print("测试2: ROI处理")
    print("=" * 60)
    
    # 创建测试图像
    print("创建合成测试图像...")
    test_image = create_synthetic_test_image(num_cells=10)
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
        Image.fromarray(test_image).save(tmp_path)
    
    try:
        # 创建处理器
        processor = FluoImageProcessor()
        
        # 定义ROI（左上角四分之一）
        roi = (0, 0, 256, 256)
        print(f"使用ROI: {roi}")
        
        # 处理图像
        measurements = processor.process_image(tmp_path, roi=roi)
        
        print(f"\n检测到 {len(measurements)} 个荧光区域（ROI内）")
        
        # 验证所有检测都在ROI内
        for m in measurements:
            cx, cy = m['centroid_x'], m['centroid_y']
            assert 0 <= cx <= 256 and 0 <= cy <= 256, f"检测超出ROI范围: ({cx}, {cy})"
        
        print("✓ ROI处理测试通过")
        return True
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_parameter_variations():
    """测试不同参数配置"""
    print("\n" + "=" * 60)
    print("测试3: 参数变化测试")
    print("=" * 60)
    
    # 创建测试图像
    test_image = create_synthetic_test_image(num_cells=5)
    
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
        Image.fromarray(test_image).save(tmp_path)
    
    try:
        # 测试不同的参数组合
        configs = [
            {'tophat_element_size': 10, 'adaptive_block_size': 31},
            {'tophat_element_size': 20, 'adaptive_block_size': 51},
            {'tophat_element_shape': 'rect', 'adaptive_method': 'mean'},
        ]
        
        for i, config in enumerate(configs, 1):
            print(f"\n配置 {i}: {config}")
            processor = FluoImageProcessor(config)
            measurements = processor.process_image(tmp_path)
            print(f"  检测到 {len(measurements)} 个区域")
        
        print("\n✓ 参数变化测试通过")
        return True
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_output_files():
    """测试输出文件生成"""
    print("\n" + "=" * 60)
    print("测试4: 输出文件生成")
    print("=" * 60)
    
    # 创建测试图像
    test_image = create_synthetic_test_image(num_cells=5)
    
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
        Image.fromarray(test_image).save(tmp_path)
    
    # 创建临时输出目录
    import tempfile
    output_dir = Path(tempfile.mkdtemp())
    
    try:
        # 处理图像
        processor = FluoImageProcessor()
        measurements = processor.process_image(tmp_path)
        
        # 保存CSV
        csv_path = output_dir / "measurements.csv"
        processor.save_measurements_to_csv(str(csv_path))
        assert csv_path.exists(), "CSV文件应该被创建"
        print(f"✓ CSV文件已创建: {csv_path}")
        
        # 保存结果图像
        image_path = output_dir / "result.png"
        processor.create_overlay_image(str(image_path))
        assert image_path.exists(), "结果图像应该被创建"
        print(f"✓ 结果图像已创建: {image_path}")
        
        print("\n✓ 输出文件生成测试通过")
        return True
        
    finally:
        # 清理
        Path(tmp_path).unlink(missing_ok=True)
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)


def main():
    """运行所有测试"""
    # 设置日志
    logging.basicConfig(
        level=logging.WARNING,  # 只显示警告和错误
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("荧光图像处理器测试套件")
    print("=" * 60)
    
    tests = [
        ("基本处理流程", test_basic_processing),
        ("ROI处理", test_roi_processing),
        ("参数变化", test_parameter_variations),
        ("输出文件生成", test_output_files),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
