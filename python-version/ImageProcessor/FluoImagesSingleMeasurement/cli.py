#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行接口 - 荧光单张图像测量
Command Line Interface - Fluorescence Single Image Measurement
"""

import argparse
import logging
import sys
from pathlib import Path

from image_processor import FluoImageProcessor
import config_manager


def setup_logging(verbose: bool = False):
    """设置日志系统"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='荧光单张图像测量工具 - 基于白帽变换和自适应阈值',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本用法
  python cli.py -i image.tif -o output
  
  # 指定ROI区域
  python cli.py -i image.tif -o output --roi 100 100 500 500
  
  # 自定义参数
  python cli.py -i image.tif -o output --tophat-size 20 --adaptive-block 51
  
  # 使用配置文件
  python cli.py -i image.tif -o output --config my_config.json
  
  # 仅保存CSV不保存图像
  python cli.py -i image.tif -o results.csv --no-image
        """
    )
    
    # 必需参数
    parser.add_argument('-i', '--input', required=True,
                       help='输入荧光图像路径 (TIFF/PNG)')
    parser.add_argument('-o', '--output', required=True,
                       help='输出路径（目录或CSV文件名）')
    
    # ROI参数
    parser.add_argument('--roi', type=int, nargs=4, metavar=('X', 'Y', 'W', 'H'),
                       help='ROI区域 (x y width height)')
    
    # Bayer RAW参数
    parser.add_argument('--bayer', action='store_true',
                       help='启用Bayer RAW模式（提取R通道）')
    parser.add_argument('--bayer-pattern', choices=['RGGB', 'BGGR', 'GRBG', 'GBRG'], 
                       default=None,
                       help='Bayer模式（默认: RGGB）')
    
    # 白帽变换参数
    parser.add_argument('--tophat-size', type=int, default=None,
                       help='白帽结构元素大小（默认: 15）')
    parser.add_argument('--tophat-shape', choices=['disk', 'rect'], default=None,
                       help='白帽结构元素形状（默认: disk）')
    
    # 高斯模糊参数
    parser.add_argument('--gaussian-sigma', type=float, default=None,
                       help='高斯模糊sigma值（默认: 1.0）')
    parser.add_argument('--no-gaussian', action='store_true',
                       help='禁用高斯模糊')
    
    # 自适应阈值参数
    parser.add_argument('--adaptive-method', choices=['gaussian', 'mean'], default=None,
                       help='自适应阈值方法（默认: gaussian）')
    parser.add_argument('--adaptive-block', type=int, default=None,
                       help='自适应阈值窗口大小（默认: 41）')
    parser.add_argument('--adaptive-c', type=int, default=None,
                       help='自适应阈值常数C（默认: 2）')
    
    # 后处理参数
    parser.add_argument('--min-size', type=int, default=None,
                       help='最小对象面积（默认: 50）')
    parser.add_argument('--closing-size', type=int, default=None,
                       help='闭运算大小（默认: 3）')
    
    # 配置文件
    parser.add_argument('--config', type=str,
                       help='配置文件路径（JSON格式）')
    parser.add_argument('--save-config', type=str,
                       help='保存当前参数到配置文件')
    
    # 输出控制
    parser.add_argument('--no-image', action='store_true',
                       help='不保存结果图像')
    parser.add_argument('--no-csv', action='store_true',
                       help='不保存CSV文件')
    
    # 其他选项
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # 检查输入文件
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"输入文件不存在: {input_path}")
            return 1
        
        # 加载配置
        if args.config:
            config = config_manager.load_config(Path(args.config))
            logger.info(f"使用配置文件: {args.config}")
        else:
            config = config_manager.get_default_config()
        
        # 更新配置（命令行参数覆盖配置文件）
        if args.bayer:
            config['is_bayer'] = True
            logger.info("启用Bayer RAW模式")
        if args.bayer_pattern is not None:
            config['bayer_pattern'] = args.bayer_pattern
        if args.tophat_size is not None:
            config['tophat_element_size'] = args.tophat_size
        if args.tophat_shape is not None:
            config['tophat_element_shape'] = args.tophat_shape
        if args.gaussian_sigma is not None:
            config['gaussian_sigma'] = args.gaussian_sigma
        if args.no_gaussian:
            config['enable_gaussian'] = False
        if args.adaptive_method is not None:
            config['adaptive_method'] = args.adaptive_method
        if args.adaptive_block is not None:
            config['adaptive_block_size'] = args.adaptive_block
        if args.adaptive_c is not None:
            config['adaptive_c'] = args.adaptive_c
        if args.min_size is not None:
            config['min_object_size'] = args.min_size
        if args.closing_size is not None:
            config['closing_size'] = args.closing_size
        
        # 保存配置（如果指定）
        if args.save_config:
            config_manager.save_config(config, Path(args.save_config))
            logger.info(f"配置已保存到: {args.save_config}")
        
        # 处理ROI
        roi = None
        if args.roi:
            roi = tuple(args.roi)
            logger.info(f"使用ROI: {roi}")
        
        # 创建处理器
        processor = FluoImageProcessor(config)
        
        # 处理图像
        logger.info("=" * 60)
        logger.info("开始处理")
        logger.info("=" * 60)
        
        measurements = processor.process_image(str(input_path), roi)
        
        # 确定输出路径
        output_path = Path(args.output)
        
        if output_path.suffix.lower() == '.csv':
            # 如果输出是CSV文件
            csv_path = output_path
            output_dir = output_path.parent
        else:
            # 如果输出是目录
            output_dir = output_path
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_path = output_dir / f"{input_path.stem}_measurements.csv"
        
        # 保存CSV
        if not args.no_csv:
            processor.save_measurements_to_csv(str(csv_path))
            logger.info(f"测量结果已保存: {csv_path}")
        
        # 保存结果图像
        if not args.no_image:
            if output_path.suffix.lower() == '.csv':
                image_path = output_path.parent / f"{input_path.stem}_result.png"
            else:
                image_path = output_dir / f"{input_path.stem}_result.png"
            
            processor.create_overlay_image(str(image_path))
            logger.info(f"结果图像已保存: {image_path}")
        
        # 统计信息
        total_area = sum(m.get('area_pixels', 0) for m in measurements)
        total_intensity = sum(m.get('total_intensity', 0) for m in measurements)
        
        logger.info("=" * 60)
        logger.info("处理结果统计:")
        logger.info(f"  检测到荧光区域数: {len(measurements)}")
        logger.info(f"  总面积: {total_area} 像素")
        logger.info(f"  总强度: {total_intensity:.2f}")
        logger.info("=" * 60)
        logger.info("处理完成!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n用户中断")
        return 1
    except Exception as e:
        logger.error(f"处理失败: {str(e)}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
