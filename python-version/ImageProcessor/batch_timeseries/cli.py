#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行界面 - 批量荧光强度测量工具
Command Line Interface - Batch Fluorescence Measurement Tool
"""

import argparse
import os
import sys
import logging
from datetime import datetime

from core.image_processor import ImageProcessor
from core.file_manager import FileManager
from config_manager import ConfigManager

def setup_logging(log_level='INFO'):
    """设置日志系统"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler('batch_fluo_cli.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_inputs(args, file_manager, logger):
    """验证输入参数"""
    errors = []
    
    # 验证明场图像
    if not args.brightfield:
        errors.append("必须指定明场图像文件 (-b/--brightfield)")
    else:
        valid, msg = file_manager.validate_file_exists(args.brightfield)
        if not valid:
            errors.append(f"明场图像: {msg}")
            
    # 验证荧光图像文件夹
    if not args.input:
        errors.append("必须指定荧光图像文件夹 (-i/--input)")
    else:
        valid, msg = file_manager.validate_directory_exists(args.input)
        if not valid:
            errors.append(f"荧光图像文件夹: {msg}")
            
    # 验证输出文件夹
    if not args.output:
        errors.append("必须指定输出文件夹 (-o/--output)")
    else:
        # 输出文件夹可以不存在，会自动创建
        if os.path.exists(args.output) and not os.path.isdir(args.output):
            errors.append("输出路径不是文件夹")
            
    # 验证黑场图像（可选）
    if args.dark:
        for dark_file in args.dark:
            valid, msg = file_manager.validate_file_exists(dark_file)
            if not valid:
                errors.append(f"黑场图像 {dark_file}: {msg}")
                
    # 验证参数范围
    if args.sigma <= 0 or args.sigma > 10:
        errors.append("高斯模糊参数必须在0-10之间")
        
    if args.min_area <= 0:
        errors.append("最小面积必须大于0")
        
    if args.threshold not in ['otsu', 'triangle']:
        errors.append("阈值方法必须是 'otsu' 或 'triangle'")
        
    return errors

def print_progress(current, total, message=""):
    """打印进度信息"""
    if total > 0:
        progress = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f'\r进度: |{bar}| {progress:.1f}% ({current}/{total}) {message}', end='', flush=True)
    if current == total:
        print()  # 换行

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='批量荧光强度测量工具 - 命令行版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python cli.py -i ./fluorescence_images -b ./brightfield.tif -o ./results
  python cli.py -i ./images -b ./bf.tif -d ./dark1.tif ./dark2.tif -o ./output --sigma 1.5
  python cli.py -i ./images -b ./bf.tif -o ./results --roi 100 100 200 200
  python cli.py --config config.json -i ./images -o ./results --preview-only

输出文件:
  results/csv/fluorescence_intensity_results.csv  - 荧光强度数据
  results/images/cell_overlay.png                 - 叠加图像
  results/masks/cell_mask.png                     - 细胞掩膜
  results/logs/processing_log.txt                 - 处理日志
        '''
    )
    
    # 必需参数
    parser.add_argument('-i', '--input', 
                       help='荧光图像文件夹路径', 
                       required=True)
    parser.add_argument('-b', '--brightfield', 
                       help='明场图像文件路径', 
                       required=True)
    parser.add_argument('-o', '--output', 
                       help='输出文件夹路径', 
                       required=True)
    
    # 可选参数
    parser.add_argument('-d', '--dark', 
                       nargs='+', 
                       help='黑场图像文件路径（可多个）')
    parser.add_argument('--sigma', 
                       type=float, 
                       default=1.5, 
                       help='高斯模糊参数 (默认: 1.5)')
    parser.add_argument('--threshold', 
                       choices=['otsu', 'triangle'], 
                       default='otsu', 
                       help='阈值算法 (默认: otsu)')
    parser.add_argument('--min-area', 
                       type=int, 
                       default=500, 
                       help='最小细胞面积 (默认: 500)')
    parser.add_argument('--closing-radius', 
                       type=int, 
                       default=3, 
                       help='形态学关闭半径 (默认: 3)')
    parser.add_argument('--opening-radius', 
                       type=int, 
                       default=2, 
                       help='形态学打开半径 (默认: 2)')
    parser.add_argument('--max-components', 
                       type=int, 
                       default=1, 
                       help='保留的最大连通域数 (默认: 1)')
    parser.add_argument('--roi', 
                       nargs=4, 
                       type=int, 
                       metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                       help='ROI区域坐标 (x y width height)')
    parser.add_argument('--offset', 
                       nargs=2, 
                       type=int, 
                       metavar=('X_OFFSET', 'Y_OFFSET'),
                       help='明场相对荧光的偏移校正 (x_offset y_offset)')
    parser.add_argument('--optimize-offset', 
                       action='store_true', 
                       help='启用偏移优化 (在±5像素范围内搜索最佳偏移)')
    
    # 配置和日志选项
    parser.add_argument('--config', 
                       help='配置文件路径 (JSON格式)')
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', 
                       help='日志级别 (默认: INFO)')
    parser.add_argument('--preview-only', 
                       action='store_true', 
                       help='仅预览细胞检测结果，不进行批量处理')
    parser.add_argument('--save-config', 
                       help='保存当前参数到配置文件')
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging(args.log_level)
    logger.info("=" * 60)
    logger.info("批量荧光强度测量工具 - 命令行版本启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # 初始化组件
        file_manager = FileManager()
        config_manager = ConfigManager()
        
        # 加载配置文件（如果指定）
        if args.config:
            if os.path.exists(args.config):
                with open(args.config, 'r', encoding='utf-8') as f:
                    import json
                    config = json.load(f)
                    
                # 从配置文件更新参数（命令行参数优先）
                params = config.get('processing_parameters', {})
                if not hasattr(args, 'sigma_set'):
                    args.sigma = params.get('gaussian_sigma', args.sigma)
                if not hasattr(args, 'threshold_set'):
                    args.threshold = params.get('threshold_method', args.threshold)
                # ... 其他参数类似处理
                    
                logger.info(f"已加载配置文件: {args.config}")
            else:
                logger.warning(f"配置文件不存在: {args.config}")
        
        # 验证输入参数
        logger.info("验证输入参数...")
        errors = validate_inputs(args, file_manager, logger)
        
        if errors:
            logger.error("输入参数验证失败:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)
            
        logger.info("输入参数验证通过")
        
        # 显示处理参数
        logger.info("处理参数:")
        logger.info(f"  明场图像: {args.brightfield}")
        logger.info(f"  荧光图像文件夹: {args.input}")
        logger.info(f"  黑场图像: {args.dark if args.dark else '无'}")
        logger.info(f"  输出文件夹: {args.output}")
        logger.info(f"  高斯模糊 σ: {args.sigma}")
        logger.info(f"  阈值方法: {args.threshold}")
        logger.info(f"  最小面积: {args.min_area}")
        if args.roi:
            logger.info(f"  ROI区域: ({args.roi[0]}, {args.roi[1]}) 尺寸: {args.roi[2]}×{args.roi[3]}")
        else:
            logger.info("  ROI区域: 未指定 (使用整个图像)")
        
        # 扫描输入文件
        logger.info("扫描输入文件...")
        fluorescence_files = file_manager.find_fluorescence_files(args.input)
        logger.info(f"找到 {len(fluorescence_files)} 个荧光图像文件")
        
        if len(fluorescence_files) == 0:
            logger.error("未找到荧光图像文件")
            sys.exit(1)
            
        # 创建图像处理器
        image_processor = ImageProcessor(
            gaussian_sigma=args.sigma,
            threshold_method=args.threshold,
            min_area=args.min_area,
            closing_radius=args.closing_radius,
            opening_radius=args.opening_radius,
            max_components=args.max_components,
            progress_callback=print_progress,
            log_callback=lambda msg, level='INFO': logger.log(
                getattr(logging, level), msg
            )
        )
        
        # 预览模式
        if args.preview_only:
            logger.info("开始预览细胞检测...")
            roi_tuple = tuple(args.roi) if args.roi else None
            image_processor.preview_cell_detection(
                args.brightfield, 
                args.dark if args.dark else [],
                roi_tuple
            )
            logger.info("预览完成，请查看 cell_detection_preview.png")
            return
            
        # 批量处理
        logger.info("开始批量处理...")
        roi_tuple = tuple(args.roi) if args.roi else None
        offset_tuple = tuple(args.offset) if args.offset else None
        
        # 如果启用了偏移优化，记录相关信息
        if args.optimize_offset:
            logger.info("启用偏移优化: 将在±5像素范围内搜索最佳偏移 (121次尝试/图像)")
            if offset_tuple:
                logger.info(f"基础偏移: X={offset_tuple[0]}, Y={offset_tuple[1]}")
        elif offset_tuple:
            logger.info(f"使用固定偏移校正: X={offset_tuple[0]}, Y={offset_tuple[1]}")
            
        success = image_processor.process_batch(
            brightfield_path=args.brightfield,
            fluorescence_folder=args.input,
            darkfield_paths=args.dark if args.dark else [],
            output_folder=args.output,
            roi=roi_tuple,
            offset_correction=offset_tuple,
            enable_offset_optimization=args.optimize_offset
        )
        
        if success:
            logger.info("批量处理成功完成！")
            logger.info(f"结果已保存到: {args.output}")
            
            # 显示输出文件
            results_dir = os.path.join(args.output, "results")
            if os.path.exists(results_dir):
                logger.info("输出文件:")
                for root, dirs, files in os.walk(results_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, args.output)
                        logger.info(f"  - {rel_path}")
        else:
            logger.error("批量处理失败")
            sys.exit(1)
            
        # 保存配置（如果指定）
        if args.save_config:
            config = {
                'processing_parameters': {
                    'gaussian_sigma': args.sigma,
                    'threshold_method': args.threshold,
                    'min_area': args.min_area,
                    'closing_radius': args.closing_radius,
                    'opening_radius': args.opening_radius,
                    'max_components': args.max_components
                },
                'file_paths': {
                    'brightfield_path': args.brightfield,
                    'fluorescence_folder': args.input,
                    'darkfield_paths': ';'.join(args.dark) if args.dark else '',
                    'output_folder': args.output
                }
            }
            
            config_manager.save_config(config)
            logger.info(f"配置已保存到: {args.save_config}")
            
    except KeyboardInterrupt:
        logger.info("用户中断处理")
        sys.exit(1)
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")
        logger.exception("详细错误信息:")
        sys.exit(1)
    finally:
        logger.info("=" * 60)
        logger.info(f"程序结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

if __name__ == "__main__":
    main()
