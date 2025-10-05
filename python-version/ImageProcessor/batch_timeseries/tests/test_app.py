#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证批量荧光强度测量工具
Test Script - Validate Batch Fluorescence Measurement Tool
"""

import numpy as np
import cv2
import tifffile
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import json

def create_synthetic_test_data(output_dir):
    """创建合成测试数据"""
    print("创建合成测试数据...")
    
    # 创建测试目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 图像参数
    width, height = 512, 512  # 偶数尺寸
    cell_center = (256, 256)
    cell_radius = 50
    
    # 1. 创建明场图像
    print("  创建明场图像...")
    brightfield = np.random.randint(800, 1200, (height, width), dtype=np.uint16)
    
    # 添加细胞（较暗的圆形区域）
    y, x = np.ogrid[:height, :width]
    mask = (x - cell_center[0])**2 + (y - cell_center[1])**2 <= cell_radius**2
    brightfield[mask] = np.random.randint(400, 600, np.sum(mask))
    
    bf_path = os.path.join(output_dir, "brightfield_BF.tif")
    tifffile.imwrite(bf_path, brightfield)
    
    # 2. 创建黑场图像
    print("  创建黑场图像...")
    darkfield = np.random.randint(50, 100, (height, width), dtype=np.uint16)
    dark_path = os.path.join(output_dir, "dark_field.tif")
    tifffile.imwrite(dark_path, darkfield)
    
    # 3. 创建荧光图像序列
    print("  创建荧光图像序列...")
    fluorescence_dir = os.path.join(output_dir, "fluorescence")
    os.makedirs(fluorescence_dir, exist_ok=True)
    
    base_time = datetime.now()
    fluorescence_files = []
    
    for i in range(5):  # 创建5张荧光图像
        # 基础荧光背景
        fluo_image = np.random.randint(200, 400, (height, width), dtype=np.uint16)
        
        # 细胞区域荧光强度随时间变化
        cell_intensity = 1000 + i * 200 + np.random.randint(-50, 50)
        fluo_image[mask] = np.random.randint(
            cell_intensity - 100, 
            cell_intensity + 100, 
            np.sum(mask)
        )
        
        # 保存图像
        filename = f"fluorescence_{i:03d}.tif"
        file_path = os.path.join(fluorescence_dir, filename)
        tifffile.imwrite(file_path, fluo_image)
        
        # 修改文件时间戳
        file_time = base_time + timedelta(seconds=i * 30)
        timestamp = file_time.timestamp()
        os.utime(file_path, (timestamp, timestamp))
        
        fluorescence_files.append(file_path)
        
    print(f"  创建了 {len(fluorescence_files)} 个荧光图像文件")
    
    return {
        'brightfield': bf_path,
        'darkfield': [dark_path],
        'fluorescence_folder': fluorescence_dir,
        'fluorescence_files': fluorescence_files
    }

def test_file_manager():
    """测试文件管理器"""
    print("\n测试文件管理器...")
    
    from core.file_manager import FileManager
    
    file_manager = FileManager()
    
    # 测试文件验证
    print("  测试文件验证...")
    valid, msg = file_manager.validate_file_exists(__file__)
    assert valid, f"文件验证失败: {msg}"
    
    # 测试目录验证
    print("  测试目录验证...")
    valid, msg = file_manager.validate_directory_exists(os.path.dirname(__file__))
    assert valid, f"目录验证失败: {msg}"
    
    print("  文件管理器测试通过")

def test_config_manager():
    """测试配置管理器"""
    print("\n测试配置管理器...")
    
    from config_manager import ConfigManager
    
    config_manager = ConfigManager()
    
    # 测试默认配置
    print("  测试默认配置...")
    config = config_manager.load_config()
    assert 'processing_parameters' in config
    assert 'file_paths' in config
    
    # 测试配置验证
    print("  测试配置验证...")
    valid, errors = config_manager.validate_config(config)
    assert valid, f"配置验证失败: {errors}"
    
    print("  配置管理器测试通过")

def test_image_processor_with_synthetic_data():
    """使用合成数据测试图像处理器"""
    print("\n测试图像处理器...")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试数据
        test_data = create_synthetic_test_data(temp_dir)
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "output")
        
        from core.image_processor import ImageProcessor
        
        # 创建处理器
        processor = ImageProcessor(
            gaussian_sigma=1.5,
            threshold_method='otsu',
            min_area=100,  # 降低面积阈值以检测合成细胞
            progress_callback=lambda c, t, m: print(f"    进度: {c}/{t} {m}"),
            log_callback=lambda msg, level='INFO': print(f"    {level}: {msg}")
        )
        
        # 测试预览
        print("  测试细胞检测预览...")
        try:
            processor.preview_cell_detection(
                test_data['brightfield'],
                test_data['darkfield']
            )
            print("    预览测试通过")
        except Exception as e:
            print(f"    预览测试失败: {e}")
            
        # 测试批量处理
        print("  测试批量处理...")
        try:
            success = processor.process_batch(
                brightfield_path=test_data['brightfield'],
                fluorescence_folder=test_data['fluorescence_folder'],
                darkfield_paths=test_data['darkfield'],
                output_folder=output_dir
            )
            
            if success:
                print("    批量处理测试通过")
                
                # 验证输出文件
                results_dir = os.path.join(output_dir, "results")
                csv_file = os.path.join(results_dir, "csv", "fluorescence_intensity_results.csv")
                
                if os.path.exists(csv_file):
                    print("    CSV文件生成成功")
                    
                    # 读取并验证CSV内容
                    import pandas as pd
                    df = pd.read_csv(csv_file)
                    
                    print(f"    CSV行数: {len(df)}")
                    print(f"    CSV列: {list(df.columns)}")
                    
                    # 验证第一行elapsed_s为0
                    if len(df) > 0 and df.iloc[0]['elapsed_s'] == 0.0:
                        print("    时间戳验证通过")
                    else:
                        print("    时间戳验证失败")
                        
                else:
                    print("    CSV文件未生成")
                    
            else:
                print("    批量处理测试失败")
                
        except Exception as e:
            print(f"    批量处理测试异常: {e}")
            import traceback
            traceback.print_exc()

def test_cli_interface():
    """测试命令行界面"""
    print("\n测试命令行界面...")
    
    # 创建临时目录和测试数据
    with tempfile.TemporaryDirectory() as temp_dir:
        test_data = create_synthetic_test_data(temp_dir)
        output_dir = os.path.join(temp_dir, "cli_output")
        
        # 构建CLI命令
        import subprocess
        import sys
        
        cmd = [
            sys.executable, "cli.py",
            "-i", test_data['fluorescence_folder'],
            "-b", test_data['brightfield'],
            "-d"] + test_data['darkfield'] + [
            "-o", output_dir,
            "--sigma", "1.5",
            "--threshold", "otsu",
            "--min-area", "100",
            "--log-level", "INFO"
        ]
        
        try:
            print("  执行CLI命令...")
            print(f"    命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=os.path.dirname(__file__)
            )
            
            if result.returncode == 0:
                print("    CLI测试通过")
                print(f"    输出: {result.stdout[-200:]}")  # 显示最后200字符
            else:
                print("    CLI测试失败")
                print(f"    错误: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("    CLI测试超时")
        except Exception as e:
            print(f"    CLI测试异常: {e}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("批量荧光强度测量工具 - 测试脚本")
    print("=" * 60)
    
    try:
        # 基础组件测试
        test_file_manager()
        test_config_manager()
        
        # 核心功能测试
        test_image_processor_with_synthetic_data()
        
        # CLI界面测试
        if os.path.exists("cli.py"):
            test_cli_interface()
        else:
            print("\n跳过CLI测试 (cli.py不存在)")
            
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
