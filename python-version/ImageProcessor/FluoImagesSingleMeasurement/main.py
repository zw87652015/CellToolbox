#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
荧光单张图像测量工具 - 主入口
Fluorescence Single Image Measurement Tool - Main Entry Point
"""

import sys
import argparse


def check_dependencies():
    """检查依赖是否安装"""
    missing = []
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import skimage
    except ImportError:
        missing.append("scikit-image")
    
    try:
        import PIL
    except ImportError:
        missing.append("Pillow")
    
    if missing:
        print("错误: 缺少以下依赖包:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\n请运行以下命令安装:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='荧光单张图像测量工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--gui', action='store_true',
                       help='启动GUI界面（默认）')
    parser.add_argument('--cli', action='store_true',
                       help='使用命令行模式')
    parser.add_argument('--test', action='store_true',
                       help='运行测试套件')
    
    # 如果没有参数，默认启动GUI
    if len(sys.argv) == 1:
        args = argparse.Namespace(gui=True, cli=False, test=False)
    else:
        args, unknown = parser.parse_known_args()
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 根据参数启动相应模式
    if args.test:
        print("运行测试套件...")
        import test_processor
        return test_processor.main()
    
    elif args.cli or (not args.gui and unknown):
        print("命令行模式")
        # 传递剩余参数给CLI
        sys.argv = [sys.argv[0]] + unknown
        import cli
        return cli.main()
    
    else:  # 默认GUI模式
        print("启动GUI界面...")
        try:
            import tkinter as tk
        except ImportError:
            print("错误: tkinter未安装")
            print("在某些Linux系统上，需要安装: python3-tk")
            return 1
        
        from gui_app import main as gui_main
        gui_main()
        return 0


if __name__ == "__main__":
    sys.exit(main())
